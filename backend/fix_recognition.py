"""修复灭火器识别算法的脚本"""
import re

with open('app/ai/training_inference_service.py', 'r') as f:
    content = f.read()

# 修复1: asymmetry_score计算
old_asymmetry = '        asymmetry_score = min(features["arm_asymmetry"] / 80.0, 1.0)'
new_asymmetry = '''        # 非对称分数：合理范围20-100度给高分，过大过小都降低
        raw_asymmetry = features["arm_asymmetry"]
        if 20 <= raw_asymmetry <= 100:
            asymmetry_score = raw_asymmetry / 80.0
        elif raw_asymmetry < 20:
            asymmetry_score = raw_asymmetry / 20.0 * 0.3
        else:
            asymmetry_score = max(0.0, 1.0 - (raw_asymmetry - 100) / 80.0)'''

if old_asymmetry not in content:
    print('ERROR: old_asymmetry not found')
else:
    content = content.replace(old_asymmetry, new_asymmetry, 1)
    print('Fixed asymmetry_score')

# 修复2: 替换return块中的步骤评分公式
old_return = '''        return {
            # step1 准备阶段：姿态可见 + 视频早期 + 身体稳定（低权重）
            1: min(1.0, 0.35 * pose_score + 0.15 * stable_body_score + 0.35 * early_stage + 0.15 * (1.0 - extinguisher_score)),
            # step2 提灭火器：灭火器出现 + 手臂弯曲 + 偏早期
            2: min(1.0, 0.30 * extinguisher_score + 0.25 * arm_bent_score + 0.10 * stable_body_score + 0.10 * both_arms_score + 0.15 * early_stage + 0.10 * mid_stage),
            # step3 拔保险销：双臂非对称 + 灭火器出现（移除 arm_bent_score，因为拔销时拉销手臂通常是伸展的）
            3: min(1.0, 0.25 * extinguisher_score + 0.35 * asymmetry_score + 0.15 * stable_body_score + 0.10 * continuity_score + 0.15 * mid_stage),
            # step4 握喷管：双臂可见 + 握持姿态（降低 nozzle_control 条件，放宽手臂角度要求）
            4: min(1.0, 0.25 * extinguisher_score + 0.20 * both_arms_score + 0.20 * nozzle_control_score + 0.10 * stable_body_score + 0.10 * continuity_score + 0.15 * mid_stage),
            # step5 瞄准火源：手臂伸展 + 瞄准姿态
            5: min(1.0, 0.25 * extinguisher_score + 0.30 * aiming_score + 0.15 * arm_extended_score + 0.10 * stable_body_score + 0.10 * continuity_score + 0.10 * late_stage),
            # step6 压把手：手臂运动 + 后期阶段
            6: min(1.0, 0.20 * extinguisher_score + 0.20 * aiming_score + 0.15 * arm_extended_score + 0.20 * motion_score + 0.10 * continuity_score + 0.15 * final_stage),
        }'''

new_return = '''        # 基于时序约束的步骤评分
        # step1: 0-25%
        score1 = min(1.0, 0.35 * pose_score + 0.20 * stable_body_score + 0.45 * early_stage) if video_ratio <= 0.25 else 0.0
        # step2: 10-45%
        score2 = min(1.0, 0.30 * extinguisher_score + 0.30 * arm_bent_score + 0.15 * early_stage + 0.15 * mid_stage) if 0.08 <= video_ratio <= 0.45 else 0.0
        # step3: 15-50%
        score3 = min(1.0, 0.35 * extinguisher_score + 0.30 * asymmetry_score + 0.20 * mid_stage) if 0.12 <= video_ratio <= 0.50 else 0.0
        # step4: 20-55%
        score4 = min(1.0, 0.30 * extinguisher_score + 0.25 * nozzle_control_score + 0.25 * both_arms_score + 0.20 * mid_stage) if 0.18 <= video_ratio <= 0.55 else 0.0
        # step5: 35-75%
        score5 = min(1.0, 0.30 * aiming_score + 0.25 * arm_extended_score + 0.20 * extinguisher_score + 0.15 * late_stage) if 0.30 <= video_ratio <= 0.75 else 0.0
        # step6: 55%+
        score6 = min(1.0, 0.30 * extinguisher_score + 0.25 * aiming_score + 0.20 * arm_extended_score + 0.25 * final_stage) if video_ratio >= 0.55 else 0.0

        return {1: score1, 2: score2, 3: score3, 4: score4, 5: score5, 6: score6}'''

if old_return not in content:
    print('ERROR: old_return not found')
    # 搜索
    for i, line in enumerate(content.split('\n')):
        if 'step1 准备阶段' in line or 'return {' in line:
            print(f'{i}: {line[:80]}')
else:
    content = content.replace(old_return, new_return, 1)
    print('Fixed step formulas')

# 修复3: 简化_is_step_segment_valid判断
old_valid = '''    def _is_step_segment_valid(self, segment: Dict[str, Any]) -> bool:
        """判断步骤片段是否视为有效。

        允许较短的"掠过式"片段被计入——教学视频中每个动作往往只停留 1-2 秒，
        再苛刻的时长要求会让整个状态机对教学视频几乎完全失效。
        """
        # 原先是 duration_range 下限 * 0.3（约 1-3 秒），这里再放宽到 * 0.15
        min_seconds = max(0.5, STEP_BY_KEY[segment["step_key"]]["duration_range"][0] * 0.15)
        duration = segment["end_timestamp"] - segment["start_timestamp"]
        return segment["frame_count"] >= 2 and duration >= min_seconds'''

new_valid = '''    def _is_step_segment_valid(self, segment: Dict[str, Any]) -> bool:
        """判断步骤片段是否视为有效。

        简化判断：只要求帧数>=2，不对时长做严格要求。
        """
        return segment["frame_count"] >= 2'''

if old_valid not in content:
    print('ERROR: old_valid not found')
else:
    content = content.replace(old_valid, new_valid, 1)
    print('Fixed _is_step_segment_valid')

with open('app/ai/training_inference_service.py', 'w') as f:
    f.write(content)
print('Done')