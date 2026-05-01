"""灭火器识别测试脚本"""
import sys
sys.path.insert(0, '.')
import json

from app.ai.training_inference_service import TrainingInferenceService


def main():
    # 使用较低的置信度阈值以检测到视频中的灭火器
    service = TrainingInferenceService(yolo_conf_threshold=0.25)
    try:
        result = service.analyze_video('/home/yw/FireTrain/data/test_video/test_video.mp4')
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        service.close()
        return

    if result is None:
        print("Error: result is None")
        service.close()
        return

    print('=' * 60)
    print('灭火器六步法识别测试结果')
    print('=' * 60)

    print('\n### 视频信息 ###')
    print(f'视频时长: {result.get("video_duration", 0):.2f}秒')
    print(f'处理帧数: {result.get("processed_frames", 0)}')
    print(f'FPS: {result.get("fps", 0):.2f}')

    print('\n### 检测统计 ###')
    detection_stats = result.get('detection_stats', {})
    for class_name, stats in detection_stats.items():
        print(f'{class_name}: 帧数={stats.get("frame_count", 0)}, 最大置信度={stats.get("max_confidence", 0):.3f}')

    print('\n### 姿态统计 ###')
    pose_stats = result.get('pose_stats_summary', {})
    for angle_name, stats in pose_stats.items():
        print(f'{angle_name}: 均值={stats.get("mean", 0):.1f}°, 范围=[{stats.get("min", 0):.1f}, {stats.get("max", 0):.1f}]')

    print('\n### 步骤识别结果 ###')
    step_sequence = result.get('step_sequence', [])
    print(f'识别到 {len(step_sequence)} 个步骤:')
    for step in step_sequence:
        duration = step['end_timestamp'] - step['start_timestamp']
        print(f"  {step['step_index']}. {step['step_name']}: "
              f"置信度={step['confidence']:.3f}, "
              f"时长={duration:.2f}秒, "
              f"灭火器可见率={step['extinguisher_presence_ratio']:.1%}")

    # 从analysis_summary获取completed_steps
    analysis_summary = result.get('analysis_summary', {})
    completed_steps = analysis_summary.get('completed_steps', [])
    missing_steps = analysis_summary.get('missing_steps', [])

    print('\n### 完成情况 ###')
    print(f'完成: {result.get("completed_steps_count", 0)}/6')
    print(f'已完成: {completed_steps}')
    print(f'缺失: {missing_steps}')

    print('\n### 步骤详情 ###')
    for key, summary in result.get('step_feature_summary', {}).items():
        status = '✓' if summary['completed'] else '✗'
        print(f"{status} {summary['step_name']}:")
        print(f"    confidence={summary['confidence']}, duration={summary['duration']}s")
        print(f"    extinguisher_ratio={summary['extinguisher_presence_ratio']:.1%}, pose_quality={summary['pose_quality_score']}")
        if summary['issues']:
            print(f"    issues: {summary['issues']}")

    # 保存详细结果
    # Handle Decimal serialization issue
    result_copy = json.loads(json.dumps(result, default=str))
    with open('/tmp/fire_extinguisher_test_result.json', 'w', encoding='utf-8') as f:
        json.dump(result_copy, f, ensure_ascii=False, indent=2)
    print('\n详细结果已保存到 /tmp/fire_extinguisher_test_result.json')

    service.close()


if __name__ == '__main__':
    main()