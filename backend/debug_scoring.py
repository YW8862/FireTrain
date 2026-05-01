"""详细调试步骤识别"""
import sys
sys.path.insert(0, '.')
import json
import cv2

from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
from app.ai.pose_analyzer import PoseAnalyzer


def main():
    print("=" * 70)
    print("详细调试步骤识别问题")
    print("=" * 70)

    yolo_detector = FireExtinguisherDetector(conf_threshold=0.25)
    pose_analyzer = PoseAnalyzer()

    video_path = '/home/yw/FireTrain/data/test_video/test_video.mp4'
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_duration = total_frames / fps
    frame_skip = 2  # 与 TrainingInferenceService 一致

    # 模拟 TrainingInferenceService 的特征提取
    frame_results = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_skip == 0:
            timestamp = frame_idx / fps

            # YOLO检测
            detections = yolo_detector.detect_frame(frame)
            fire_exts = [d for d in detections if d.get('class_name') == 'fire_extinguisher']
            extinguisher_detected = len(fire_exts) > 0
            extinguisher_conf = max((d.get('confidence', 0) for d in fire_exts), default=0.0)

            # 姿态检测
            pose_result = pose_analyzer.analyze_pose(frame)
            if pose_result:
                angles = pose_result.get('angles', {})
                right_arm = angles.get('right_arm')
                left_arm = angles.get('left_arm')
                body = angles.get('body')
            else:
                right_arm = left_arm = body = None

            # 计算特征（与 _extract_frame_features 一致）
            arm_angles = [a for a in (right_arm, left_arm) if a is not None]
            arm_bent = any(65 <= a <= 130 for a in arm_angles) if arm_angles else False
            arm_extended = any(a >= 145 for a in arm_angles) if arm_angles else False
            arm_asymmetry = abs(right_arm - left_arm) if (right_arm is not None and left_arm is not None) else 0.0
            stable_body = body is not None and body <= 35
            both_arms_visible = len(arm_angles) >= 2
            nozzle_control_posture = bool(
                fire_exts and len(arm_angles) >= 2 and
                max(arm_angles) >= 90 and 50 <= min(arm_angles) <= 140
            ) if arm_angles else False
            aiming_posture = bool(fire_exts and arm_extended and stable_body)

            features = {
                'extinguisher_detected': extinguisher_detected,
                'extinguisher_confidence': float(extinguisher_conf),
                'pose_available': pose_result is not None,
                'right_arm': right_arm,
                'left_arm': left_arm,
                'body': body,
                'stable_body': stable_body,
                'arm_bent': arm_bent,
                'arm_extended': arm_extended,
                'arm_asymmetry': arm_asymmetry,
                'both_arms_visible': both_arms_visible,
                'nozzle_control_posture': nozzle_control_posture,
                'aiming_posture': aiming_posture,
                'detected_actions': [],
            }
            if extinguisher_detected:
                features['detected_actions'].append('extinguisher_detected')
            if pose_result:
                features['detected_actions'].append('pose_detected')
            if arm_bent:
                features['detected_actions'].append('arm_bent')
            if arm_extended:
                features['detected_actions'].append('arm_extended')

            frame_results.append({
                'frame_idx': frame_idx,
                'timestamp': timestamp,
                'features': features
            })

        frame_idx += 1

    cap.release()
    yolo_detector.close()
    pose_analyzer.close()

    # 模拟 _score_step_candidates
    def score_step_candidates(timestamp, features, recent_features, total_duration):
        video_ratio = max(0.0, min(timestamp / total_duration, 1.0))

        extinguisher_score = 1.0 if features['extinguisher_detected'] else 0.0
        pose_score = 1.0 if features['pose_available'] else 0.0
        stable_body_score = 1.0 if features['stable_body'] else 0.0
        arm_bent_score = 1.0 if features['arm_bent'] else 0.0
        arm_extended_score = 1.0 if features['arm_extended'] else 0.0
        asymmetry_score = min(features['arm_asymmetry'] / 80.0, 1.0)
        both_arms_score = 1.0 if features['both_arms_visible'] else 0.0
        nozzle_control_score = 1.0 if features['nozzle_control_posture'] else 0.0
        aiming_score = 1.0 if features['aiming_posture'] else 0.0
        continuity_score = sum(1 for f in recent_features if f['extinguisher_detected']) / len(recent_features) if recent_features else 0.0

        early_stage = 1.0 if video_ratio <= 0.30 else (0.6 if video_ratio <= 0.50 else 0.3)
        mid_stage = 1.0 if 0.15 <= video_ratio <= 0.70 else 0.5
        late_stage = 1.0 if video_ratio >= 0.40 else 0.5
        final_stage = 1.0 if video_ratio >= 0.55 else (0.6 if video_ratio >= 0.30 else 0.3)
        step5_aiming_weight = 0.05 if video_ratio <= 0.45 else (0.15 if video_ratio <= 0.65 else 0.30)

        step1 = min(1.0, 0.35 * pose_score + 0.15 * stable_body_score + 0.35 * early_stage + 0.15 * (1.0 - extinguisher_score))
        step2 = min(1.0, 0.30 * extinguisher_score + 0.25 * arm_bent_score + 0.10 * stable_body_score + 0.10 * both_arms_score + 0.15 * early_stage + 0.10 * mid_stage)
        step3 = min(1.0, 0.25 * extinguisher_score + 0.35 * asymmetry_score + 0.15 * stable_body_score + 0.10 * continuity_score + 0.25 * mid_stage)
        step4 = min(1.0, 0.25 * extinguisher_score + 0.20 * both_arms_score + 0.20 * nozzle_control_score + 0.10 * stable_body_score + 0.10 * continuity_score + 0.25 * mid_stage)
        step5 = min(1.0, 0.25 * extinguisher_score + step5_aiming_weight * aiming_score + 0.15 * arm_extended_score + 0.10 * stable_body_score + 0.10 * continuity_score + 0.10 * late_stage)
        step6 = min(1.0, 0.20 * extinguisher_score + 0.20 * aiming_score + 0.15 * arm_extended_score + 0.20 * 0 + 0.10 * continuity_score + 0.15 * final_stage)

        return {1: step1, 2: step2, 3: step3, 4: step4, 5: step5, 6: step6}

    # 分析前50帧的分数
    print(f"\n总帧数: {frame_idx}, 处理帧数: {len(frame_results)}, 时长: {total_duration:.2f}秒")
    print(f"\n前50帧的步骤分数:")
    print(f"{'帧':>4} {'时间':>6} {'比例':>6} {'step1':>7} {'step2':>7} {'step3':>7} {'step4':>7} {'step5':>7} {'step6':>7} {'最大步骤':>8}")
    print("-" * 80)

    for i, fr in enumerate(frame_results[:50]):
        scores = score_step_candidates(fr['timestamp'], fr['features'], [fr['features']], total_duration)
        max_step = max(scores.items(), key=lambda x: x[1])
        print(f"{fr['frame_idx']:>4} {fr['timestamp']:>6.2f} {fr['timestamp']/total_duration:>6.3f} "
              f"{scores[1]:>7.3f} {scores[2]:>7.3f} {scores[3]:>7.3f} {scores[4]:>7.3f} {scores[5]:>7.3f} {scores[6]:>7.3f} "
              f"step{max_step[0]:>3}({max_step[1]:>5.3f})")

    # 分析为什么 step6 被选中
    print("\n\n=== 分析 step6 的分数构成 ===")
    print("step6公式: 0.20*extinguisher + 0.20*aiming + 0.15*arm_extended + 0.20*motion + 0.10*continuity + 0.15*final_stage")

    # 找一个step6得分较高的帧
    for fr in frame_results[200:250:10]:  # 视频中后期
        scores = score_step_candidates(fr['timestamp'], fr['features'], [fr['features']], total_duration)
        print(f"\n帧 {fr['frame_idx']} (时间={fr['timestamp']:.2f}s):")
        print(f"  extinguisher={fr['features']['extinguisher_detected']}, arm_extended={fr['features']['arm_extended']}")
        print(f"  aiming_posture={fr['features']['aiming_posture']}, stable_body={fr['features']['stable_body']}")
        print(f"  video_ratio={fr['timestamp']/total_duration:.3f}")
        print(f"  final_stage=1.0 (video_ratio > 0.55)")
        print(f"  step6 = 0.20*1 + 0.20*1 + 0.15*1 + 0.20*0 + 0.10*1 + 0.15*1 = {scores[6]:.3f}")


if __name__ == '__main__':
    main()