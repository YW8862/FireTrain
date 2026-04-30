"""诊断脚本：逐帧输出步骤评分，定位识别失败原因。"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai.training_inference_service import TrainingInferenceService

VIDEO_PATH = "/home/yw/FireTrain/data/videos/admin_uploads/2acfb967-a095-4dcf-be7f-b7582a7535ad.mp4"

svc = TrainingInferenceService()
result = svc.analyze_video(VIDEO_PATH)

frame_results = result["frame_results"]
total_duration = result["video_duration"]
total_frames = len(frame_results)

print(f"=== 视频信息 ===")
print(f"时长: {total_duration:.2f}s, 总帧数: {result['total_frames']}, 分析帧数: {total_frames}")
print(f"FPS: {result['fps']:.2f}")
print()

# 每隔若干帧采样输出评分
sample_interval = max(1, total_frames // 30)
window_size = 9

print(f"=== 逐帧步骤评分采样 (每 {sample_interval} 帧) ===")
print(f"{'idx':>4} {'time':>6} {'ratio':>5} | {'s1':>5} {'s2':>5} {'s3':>5} {'s4':>5} {'s5':>5} {'s6':>5} | {'ext':>3} {'pose':>4} {'stab':>4} {'bent':>4} {'extd':>4} {'asym':>5} {'nozz':>4} {'aim':>4} {'body':>6}")

for idx in range(0, total_frames, sample_interval):
    fd = frame_results[idx]
    ts = fd["timestamp"]
    feat = fd["frame_features"]
    recent = [item["frame_features"] for item in frame_results[max(0, idx - window_size + 1):idx + 1]]
    scores = svc._score_step_candidates(ts, feat, recent, total_duration)
    ratio = ts / total_duration if total_duration > 0 else 0

    body_val = feat.get("body")
    body_str = f"{body_val:6.1f}" if body_val is not None else "  None"

    print(f"{idx:4d} {ts:6.2f} {ratio:5.2f} | "
          f"{scores[1]:5.3f} {scores[2]:5.3f} {scores[3]:5.3f} {scores[4]:5.3f} {scores[5]:5.3f} {scores[6]:5.3f} | "
          f"{'Y' if feat['extinguisher_detected'] else 'N':>3} "
          f"{'Y' if feat['pose_available'] else 'N':>4} "
          f"{'Y' if feat['stable_body'] else 'N':>4} "
          f"{'Y' if feat['arm_bent'] else 'N':>4} "
          f"{'Y' if feat['arm_extended'] else 'N':>4} "
          f"{feat['arm_asymmetry']:5.1f} "
          f"{'Y' if feat['nozzle_control_posture'] else 'N':>4} "
          f"{'Y' if feat['aiming_posture'] else 'N':>4} "
          f"{body_str}")

print()
print(f"=== 步骤识别结果 ===")
step_seq = result["analysis_summary"]["step_sequence"]
for step in step_seq:
    print(f"  {step['step_key']}: {step['step_name']} | "
          f"时间 {step['start_timestamp']:.2f}-{step['end_timestamp']:.2f}s | "
          f"帧数 {step['frame_count']} | "
          f"置信度 {step['confidence']:.3f} | "
          f"峰值 {step['peak_confidence']:.3f}")

print()
completed = result["analysis_summary"]["completed_steps"]
missing = result["analysis_summary"]["missing_steps"]
print(f"已识别: {completed}")
print(f"缺失: {missing}")

svc.close()
