"""详细分析灭火器识别问题"""
import sys
sys.path.insert(0, '.')
import json
import cv2

from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
from app.ai.pose_analyzer import PoseAnalyzer


def analyze_video_frames():
    """逐帧分析视频内容"""
    print("=" * 60)
    print("逐帧分析")
    print("=" * 60)

    yolo_detector = FireExtinguisherDetector(conf_threshold=0.25)
    pose_analyzer = PoseAnalyzer()

    video_path = '/home/yw/FireTrain/data/test_video/test_video.mp4'
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_duration = total_frames / fps

    frame_idx = 0
    frame_skip = 2  # 每2帧分析一次
    samples = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_skip != 0:
            frame_idx += 1
            continue

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

        # 计算特征
        arm_angles = [a for a in (right_arm, left_arm) if a is not None]
        arm_bent = any(65 <= a <= 130 for a in arm_angles) if arm_angles else False
        arm_extended = any(a >= 145 for a in arm_angles) if arm_angles else False
        arm_asymmetry = abs(right_arm - left_arm) if (right_arm is not None and left_arm is not None) else 0.0
        stable_body = body is not None and body <= 35

        samples.append({
            'frame': frame_idx,
            'timestamp': round(timestamp, 2),
            'video_ratio': round(timestamp / total_duration, 3),
            'extinguisher_detected': extinguisher_detected,
            'extinguisher_conf': round(extinguisher_conf, 3),
            'right_arm': round(right_arm, 1) if right_arm else None,
            'left_arm': round(left_arm, 1) if left_arm else None,
            'body': round(body, 1) if body else None,
            'arm_bent': arm_bent,
            'arm_extended': arm_extended,
            'arm_asymmetry': round(arm_asymmetry, 1),
            'stable_body': stable_body,
        })

        frame_idx += 1

    cap.release()
    yolo_detector.close()
    pose_analyzer.close()

    # 分析数据
    print(f"\n总帧数: {frame_idx}, 分析帧数: {len(samples)}, 时长: {total_duration:.2f}秒")
    print(f"\n前30帧数据:")
    print(f"{'帧':>4} {'时间':>6} {'比例':>6} {'灭火器':>8} {'右臂':>6} {'左臂':>6} {'身体':>6} {'弯曲':>6} {'伸展':>6} {'非对称':>7} {'稳定':>5}")
    print("-" * 90)
    for s in samples[:30]:
        print(f"{s['frame']:>4} {s['timestamp']:>6.2f} {s['video_ratio']:>6.3f} "
              f"{str(s['extinguisher_detected']):>8} {str(s['right_arm']):>6} {str(s['left_arm']):>6} "
              f"{str(s['body']):>6} {str(s['arm_bent']):>6} {str(s['arm_extended']):>6} "
              f"{s['arm_asymmetry']:>7.1f} {str(s['stable_body']):>5}")

    # 统计各阶段
    print("\n\n各阶段统计:")
    stage_boundaries = [(0, 0.15), (0.15, 0.30), (0.30, 0.45), (0.45, 0.60), (0.60, 0.80), (0.80, 1.0)]
    for start, end in stage_boundaries:
        stage_samples = [s for s in samples if start <= s['video_ratio'] < end]
        if stage_samples:
            ext_count = sum(1 for s in stage_samples if s['extinguisher_detected'])
            arm_bent_count = sum(1 for s in stage_samples if s['arm_bent'])
            arm_ext_count = sum(1 for s in stage_samples if s['arm_extended'])
            print(f"  {start:.0%}-{end:.0%}: {len(stage_samples)}帧, "
                  f"灭火器={ext_count/len(stage_samples):.0%}, "
                  f"手臂弯曲={arm_bent_count/len(stage_samples):.0%}, "
                  f"手臂伸展={arm_ext_count/len(stage_samples):.0%}")

    return samples


if __name__ == '__main__':
    analyze_video_frames()