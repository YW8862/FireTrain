第一阶段：先把运行基础修好
[ ] 准备最小可验证资源：一段真实训练视频、一个可加载的 YOLO ONNX 模型、一个可用的 LLM_API_KEY。
[x] 明确 YOLO 模型到底是什么。 已确认使用自训练 ONNX 灭火器检测模型，代码默认按 fire_extinguisher 类别处理。
[x] 统一路径配置，只通过 settings 取路径，不再写死 ../data/...。 已完成，兼容 make local-up 和 docker-compose。 重点文件：backend/app/core/config.py、backend/app/api/training.py、backend/app/api/admin_videos.py。
[x] 给 docker-compose.yml 显式传入这些环境变量： MODEL_DIR=/app/data/models、VIDEO_DIR=/app/data/videos、MATPLOTLIB_CACHE_DIR=/app/data/matplotlib_cache。
[x] 把上传目录改成走配置，例如普通用户上传写到 settings.VIDEO_DIR，管理员上传写到 settings.VIDEO_DIR/admin_uploads。
[x] 修一下 cleanup_service 的启动方式，避免协程未 await 的警告污染日志。 已完成启动/停止钩子接入。 重点文件：backend/app/services/cleanup_service.py、backend/app/main.py。
第二阶段：把检测逻辑和业务判断对齐
[x] 检查 backend/app/ai/fire_extinguisher_detector.py 的 self.names 和 DEFAULT_CONFIG["classes"]，确认实际输出类别名。
[x] 如果当前模型只能检测 person，先把 precheck 逻辑改成“检测到人 + 有姿态结果 + 有步骤特征”即可通过，不要强依赖 fire_extinguisher。 重点文件：backend/app/api/training.py。
[x] 如果你已经有自定义灭火器模型，就把检测类别、类别名、预检测条件统一成同一套命名，不要一处叫 fire_extinguisher，另一处根本识别不出来。
[x] 在 TrainingInferenceService.analyze_video() 的返回里补充显式摘要字段，例如： extinguisher_detected、person_detected、has_pose、completed_steps_count、pose_stats_summary。 这样后面校验和提示词拼接都不用再猜。
[x] 审查动作识别逻辑。 现在 _recognize_action_sequence() 还是“按时间每 5 秒切一步”的简化版，这只能算占位逻辑，还不算真实动作识别。 重点文件：backend/app/ai/training_inference_service.py。
第三阶段：先把普通用户后端主链路打通
[x] 修复 TrainingService 和 TrainingRepository 的更新接口不匹配问题。 已统一为 update(training, update_data)。 重点文件：backend/app/services/training_service.py、backend/app/repositories/training_repository.py。
[x] 在 TrainingService 里补出真正的统一主流程，不要再在不同 API 里各写一套。 已收口到 complete_training_with_ai_analysis(training_id, use_ai_scoring=True)。
[x] 在这个核心方法里按顺序实现： 读取训练记录 -> 校验状态 -> 校验视频存在 -> 调 TrainingInferenceService.analyze_video() -> 校验检测结果 -> LLM 评分或 fallback -> 持久化结果。
[x] 新增 _validate_detection_result()。 已覆盖灭火器检测、人/姿态、步骤特征、训练时长等校验。
[x] 新增 _generate_zero_score_result()。 当视频无效、没检测到有效动作、或者明确判 0 分时，返回结构已与正常评分结构对齐。
[x] 新增 _score_with_llm_or_fallback()。 已实现 LLMScoringService.from_settings() 优先，失败回退规则评分。
[x] 把 LLMScoringService 真正接到这条主链路里。 已接入普通用户训练完成流程。 重点文件：backend/app/ai/llm_scoring_service.py、backend/app/services/training_service.py。
[x] 修复规则引擎 fallback。 TrainingInferenceService.generate_ai_scores() 与 RuleEngine.evaluate() 已统一成异步调用。 重点文件：backend/app/ai/training_inference_service.py、backend/app/ai/rule_engine.py。
[x] 去掉当前那段“total_detections * 10 就算总分”的简化评分逻辑，这只是临时占位，不能作为正式链路。
第四阶段：把评分结果按前端可消费的格式落库
[x] 确定评分结果的标准结构，只保留一套。 已统一为： total_score、performance_level、dimension_scores、step_scores、feedback、suggestions。
[x] 统一 performance_level 的表示。 后端与接口统一使用 excellent/good/pass/fail，中文展示由前端映射。
[x] 为了兼容当前报告页，先把这几个元数据一并塞进 training.step_scores： _suggestions、_dimension_scores、_performance_level。 重点文件：backend/app/services/training_service.py。
[x] 同时保留 training.feedback 作为整体评价文本。
[x] 让 GET /api/training/{id} 能稳定返回： suggestions、dimension_scores、step_scores、feedback、status。 重点文件：backend/app/api/training.py。
第五阶段：把管理员上传链路改成复用同一套能力
[x] 删除 admin_videos.py 里对不存在方法的调用，已补齐 TrainingService 实例化并修复训练类型归一化的断点。
[x] 管理员上传接口已收口为：保存文件、创建训练记录、启动后台任务；后台任务真正执行的仍是 `TrainingService.complete_training_with_ai_analysis()` 统一主流程。
[x] 当前管理员后台任务已不再依赖 `ActionLogRepository`；训练详情接口继续返回 `action_count=0` / `actions=None` 占位，不会阻塞分析完成。
[x] 管理员上传完成后已补状态轮询：后端新增状态查询接口，前端自动轮询到 `done/failed` 后再允许查看报告。 重点文件：backend/app/api/admin_videos.py、frontend/src/views/admin/AdminVideoUpload.vue。
第六阶段：补前端，让用户真正能走完流程
[x] `frontend/src/api/training.js` 已给 `completeTraining()` 增加 `use_ai_scoring` 参数透传。
[x] `frontend/src/views/TrainingView.vue` 已保留“上传 -> 预检测 -> 完成训练”顺序，并改成按后端真实返回展示错误，不再提示不存在的“模拟评分”。
[x] 预检测返回“无有效动作”时，前端已明确提示继续提交大概率会得到 0 分。
[x] `ReportView.vue` 和 `AdminReportView.vue` 已统一使用同一套 `performance_level` 解析逻辑，不再按总分猜等级。
[x] 当 `dimension_scores` 或 `suggestions` 缺失时，前端已明确显示“暂无数据”，不再伪造 0 分或降级展示。
第七阶段：补测试，不然以后还会再断
[x] `backend/tests/test_training_module.py` 已重写为带鉴权版本，不再依赖匿名访问。
[x] 已增加“带认证”的完整接口测试，覆盖：登录 -> 开始训练 -> 上传文件 -> 预检测 -> 完成训练 -> 查看详情。
[x] 已补一组 `TrainingService` 单测，覆盖：LLM 成功、LLM 失败 fallback、无视频、无姿态、无有效动作、0 分结果。
[x] 已增加管理员链路测试，覆盖：管理员上传 -> 后台任务启动 -> 状态从 `processing` 到 `done/failed`。
[x] 已扩展 `backend/scripts/test_ai_integration.py` 为手工冒烟脚本，支持可选真实 LLM 调用（`--with-llm`）。
第八阶段：最终验收清单
[x] 普通用户上传文件落盘链路已验证：`save_upload_file()` 单测通过，带认证上传接口测试也已覆盖服务器落盘行为。
[ ] `precheck` 已修复“异常即放行”问题，不再永远放行；但当前环境缺少真实模型和真实视频，尚未完成“基于真实检测结果”的最终实测验收。
[ ] `complete` 主链路代码已具备触发 YOLO / MediaPipe / 提示词拼接 / 外部 LLM 评分的能力，但当前环境 `.env` 未配置 `LLM_API_KEY`、`data/` 下也没有真实模型/视频，无法完成真实链路实测。
[x] 当 LLM 不可用时，系统能自动降级到规则引擎评分，而不是 500。 已由 `TrainingService` 单测覆盖。
[x] 训练详情页展示字段已对齐：总分、等级、步骤分、维度分、整体反馈、改进建议都已由详情接口测试和前端报告页实现覆盖。
[x] 管理员上传视频后的状态变化已验证：测试覆盖 `processing -> done/failed`，前端轮询与管理员报告页路由也已补齐。
[ ] `docker-compose` 验证已尝试，但构建耗时过长（当前仍停在 backend 镜像依赖安装阶段），按本轮要求直接放弃，不再继续等待。