"""AI 综合评分演示

演示如何结合 YOLOv8 检测、MediaPipe 姿态分析和评分服务进行综合评分。
"""
import cv2
import asyncio
from decimal import Decimal
from app.ai.fire_extinguisher_detector import FireExtinguisherDetector
from app.ai.pose_analyzer import PoseAnalyzer
from app.services.scoring_service import ScoringService


async def analyze_training_video(video_path: str):
    """分析训练视频并生成综合评分
    
    Args:
        video_path: 视频文件路径
    """
    print("=" * 60)
    print("FireTrain AI 综合评分系统")
    print("=" * 60)
    
    # 初始化各个模块
    detector = FireExtinguisherDetector(
        model_path="yolov8n.pt",
        conf_threshold=0.5,
        img_size=640,
        device="cpu"
    )
    
    pose_analyzer = PoseAnalyzer(
        model_complexity=1,
        smooth_landmarks=True
    )
    
    scoring_service = ScoringService()
    
    try:
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"错误：无法打开视频 {video_path}")
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        print(f"\n视频信息:")
        print(f"  - 总帧数：{total_frames}")
        print(f"  - FPS: {fps:.2f}")
        print(f"  - 时长：{duration:.2f}秒")
        print()
        
        # 抽帧处理（每秒 5 帧）
        frame_skip = max(1, int(fps / 5))
        
        all_detections = []
        all_pose_results = []
        frame_count = 0
        processed_frames = 0
        
        print("开始分析...")
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # 抽帧处理
            if frame_count % frame_skip == 0:
                print(f"\r处理进度：{processed_frames}/{min(total_frames // frame_skip, 30)}", end="")
                
                # YOLOv8 检测
                detections = detector.detect_frame(frame)
                
                # MediaPipe 姿态分析
                pose_result = pose_analyzer.analyze_pose(frame, "fire_extinguisher")
                
                if detections or pose_result:
                    all_detections.append({
                        "frame_idx": processed_frames,
                        "detections": detections
                    })
                    
                    if pose_result:
                        all_pose_results.append(pose_result)
                
                processed_frames += 1
                
                # 限制最多处理 30 帧
                if processed_frames >= 30:
                    break
            
            frame_count += 1
        
        cap.release()
        print("\n")
        
        # 统计检测结果
        total_person_detections = sum(
            1 for det_group in all_detections 
            for det in det_group["detections"] 
            if det["class_name"] == "person"
        )
        
        print(f"检测结果:")
        print(f"  - 处理帧数：{processed_frames}")
        print(f"  - 检测到人数：{total_person_detections}")
        print(f"  - 检出率：{total_person_detections / processed_frames:.1%}")
        print(f"  - 有效姿态帧数：{len(all_pose_results)}")
        print()
        
        # 准备帧数据用于评分
        frame_data = []
        for i in range(len(all_pose_results)):
            if i < len(all_detections):
                frame_data.append({
                    "keypoints": all_pose_results[i]
                })
        
        # 使用评分服务进行综合评分
        print("计算评分...")
        score_result = await scoring_service.score_training(
            training_type="fire_extinguisher",
            frame_data=frame_data,
            duration_seconds=Decimal(str(duration)),
            use_pose_analysis=len(frame_data) > 0
        )
        
        # 显示评分结果
        print("\n" + "=" * 60)
        print("评分结果")
        print("=" * 60)
        print(f"总分：{score_result['total_score']:.2f}")
        print(f"反馈：{score_result['feedback']}")
        print()
        
        print("步骤分数:")
        for step_key, step_data in score_result["step_scores"].items():
            print(f"  {step_data['step_name']}: {step_data['score']:.2f}分 ({step_data['level']})")
        
        print()
        print("改进建议:")
        for suggestion in score_result["suggestions"]:
            print(f"  - {suggestion}")
        
        print()
        print("=" * 60)
        print("分析完成!")
        print("=" * 60)
        
        return score_result
        
    finally:
        detector.close()
        pose_analyzer.close()


async def demo_image_detection(image_path: str):
    """演示图像检测和姿态分析
    
    Args:
        image_path: 图像文件路径
    """
    print("\n" + "=" * 60)
    print("单帧图像分析演示")
    print("=" * 60)
    
    detector = FireExtinguisherDetector(model_path="yolov8n.pt")
    pose_analyzer = PoseAnalyzer()
    
    try:
        # 读取图像
        image = cv2.imread(image_path)
        
        if image is None:
            print(f"错误：无法读取图像 {image_path}")
            return
        
        print(f"\n图像尺寸：{image.shape[1]}x{image.shape[0]}")
        
        # YOLOv8 检测
        print("\n运行 YOLOv8 检测...")
        detections = detector.detect_frame(image)
        
        print(f"检测到 {len(detections)} 个目标")
        for det in detections:
            print(f"  - {det['class_name']} (置信度：{det['confidence']:.2f})")
            print(f"    位置：{det['bbox']}")
        
        # MediaPipe 姿态分析
        print("\n运行 MediaPipe 姿态分析...")
        pose_result = pose_analyzer.analyze_pose(image, "fire_extinguisher")
        
        if pose_result:
            print("检测到人体姿态:")
            for angle_name, angle_value in pose_result.get("angles", {}).items():
                print(f"  - {angle_name}: {angle_value:.1f}°")
            
            print("\n姿态评分:")
            for score_name, score_data in pose_result.get("scores", {}).items():
                print(f"  - {score_name}: {score_data['score']}分 ({score_data['level']})")
        else:
            print("未检测到有效人体姿态")
        
        # 绘制结果
        annotated_image = detector.draw_detections(image.copy(), detections)
        
        if pose_result:
            annotated_image = pose_analyzer.draw_pose_landmarks(
                annotated_image,
                pose_result["keypoints"]
            )
        
        output_path = "analysis_result.jpg"
        cv2.imwrite(output_path, annotated_image)
        print(f"\n结果已保存到：{output_path}")
        
    finally:
        detector.close()
        pose_analyzer.close()


if __name__ == "__main__":
    import sys
    
    print("\nFireTrain AI 综合评分演示系统")
    print("=" * 60)
    print("功能:")
    print("  1. YOLOv8 目标检测")
    print("  2. MediaPipe 姿态分析")
    print("  3. 综合评分")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        
        # 判断是视频还是图像
        if input_path.lower().endswith((".mp4", ".avi", ".mov")):
            # 视频分析
            asyncio.run(analyze_training_video(input_path))
        else:
            # 图像分析
            asyncio.run(demo_image_detection(input_path))
    else:
        print("\n使用方法:")
        print("  python demo_ai_scoring.py <视频文件或图像路径>")
        print("\n示例:")
        print("  python demo_ai_scoring.py training_video.mp4")
        print("  python demo_ai_scoring.py test_image.jpg")
        print()
