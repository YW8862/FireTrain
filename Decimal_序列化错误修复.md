# 🔧 Decimal 序列化错误修复

## 问题描述

点击"完成训练"按钮时，后端报错：

```
TypeError: Object of type Decimal is not JSON serializable
```

**完整错误栈**：
```
sqlalchemy.exc.StatementError: (builtins.TypeError) Object of type Decimal is not JSON serializable
[SQL: UPDATE training_records SET status=?, total_score=?, step_scores=?, ...]
```

## 根本原因

### 1. 数据类型不匹配

- **ScoringService** 返回的评分数据中使用 `Decimal` 类型（用于精确计算）
- **数据库字段** `step_scores` 是 JSON 类型，需要标准的 Python 数据类型
- **JSON 序列化** 不支持 `Decimal` 类型，只支持 `int` 和 `float`

### 2. 代码位置

**文件**：`backend/app/services/training_service.py`

**问题代码**（第 148-167 行）：
```python
return {
    "total_score": Decimal(str(result["total_score"])),  # ❌ Decimal 无法序列化
    "step_scores": result["step_scores"],                # ❌ 包含 Decimal 对象
    "feedback": result["feedback"],
    "suggestions": result.get("suggestions", []),
    "action_logs": result.get("action_logs", [])
}
```

### 3. 数据流向

```
ScoringService.score_training()
    ↓
返回 dict，包含 Decimal 对象
    ↓
TrainingService.generate_mock_score()
    ↓
直接返回（未转换类型）
    ↓
TrainingRepository.complete_training()
    ↓
保存到数据库（step_scores 是 JSON 字段）
    ↓
SQLAlchemy 尝试 JSON 序列化
    ↓
❌ TypeError: Decimal is not JSON serializable
```

## 修复方案

### 修改内容

**文件**：`backend/app/services/training_service.py`

**修改后代码**（第 148-175 行）：
```python
async def generate_mock_score(self, training_type: str) -> dict:
    """生成模拟分数"""
    scoring_service = ScoringService()
    result = await scoring_service.score_training(training_type=training_type)
    
    # 将 Decimal 转换为 float，使其可以被 JSON 序列化
    def convert_decimal_to_float(obj):
        """递归转换对象中的 Decimal 为 float"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_decimal_to_float(item) for item in obj]
        else:
            return obj
    
    return {
        "total_score": float(result["total_score"]),           # ✅ 转换为 float
        "step_scores": convert_decimal_to_float(result["step_scores"]),  # ✅ 递归转换
        "feedback": result["feedback"],
        "suggestions": result.get("suggestions", []),
        "action_logs": convert_decimal_to_float(result.get("action_logs", []))  # ✅ 递归转换
    }
```

### 修复要点

1. **添加辅助函数** `convert_decimal_to_float()`
   - 递归处理嵌套的 dict 和 list
   - 将所有 `Decimal` 对象转换为 `float`

2. **转换返回值**
   - `total_score`: 直接转换为 `float`
   - `step_scores`: 使用辅助函数递归转换
   - `action_logs`: 同样递归转换

3. **保持精度**
   - `float()` 转换保留足够的精度用于显示
   - 对于评分系统（0-100），float 精度完全够用

## 技术说明

### 为什么使用 Decimal？

**优点**：
- ✅ 精确的十进制运算（避免浮点误差）
- ✅ 适合金融、评分等对精度敏感的场景

**缺点**：
- ❌ 不能被 JSON 原生序列化
- ❌ 需要额外转换才能存储到 JSON 字段

### 转换策略对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| `Decimal → String` | 精度完全保留 | 读取时需要转换回来 | 高精度要求场景 |
| `Decimal → Float` | 简单直接，JSON 友好 | 可能有微小精度损失 | 评分、统计等展示场景 ✅ |
| 自定义 JSON Encoder | 灵活可控 | 增加复杂度 | 复杂业务逻辑 |

**本项目选择**：`Decimal → Float`
- 评分系统不需要极端精度
- 简化序列化处理
- 符合 JSON 标准

## 验证方法

### 1. 测试 API

```bash
curl -k -X POST https://117.72.44.96:8000/api/training/complete/{training_id}
```

**预期响应**：
```json
{
  "message": "训练已完成",
  "training_id": 60,
  "status": "done",
  "total_score": 72.69,
  "feedback": "合格！但还有提升空间，建议多加练习",
  "scoring_details": {
    "total_score": 72.69,
    "step_scores": {
      "step1": {
        "step_name": "准备阶段",
        "score": 66.49,
        "is_correct": false,
        "feedback": "准备阶段：需要改进"
      }
      // ... 其他步骤
    }
  }
}
```

### 2. 检查数据库

```sql
SELECT id, total_score, step_scores, feedback 
FROM training_records 
WHERE status = 'done' 
ORDER BY completed_at DESC 
LIMIT 1;
```

**预期结果**：
- `total_score`: 数值类型（如 72.69）
- `step_scores`: 有效的 JSON 对象
- `feedback`: 文本内容

### 3. 前端测试

访问训练页面：
```
https://117.72.44.96:5173/training
```

操作流程：
1. 点击"开始训练"
2. 等待几秒（模拟训练过程）
3. 点击"完成训练"
4. ✅ 应该成功跳转至报告页面

## 相关文件

### 修改的文件

1. **Training Service**
   - 文件：`backend/app/services/training_service.py`
   - 修改：第 148-175 行
   - 改动：添加 Decimal 转换逻辑

### 相关依赖

```
backend/app/services/scoring_service.py  # 生成 Decimal 数据
backend/app/repositories/training_repository.py  # 保存到数据库
backend/app/models/training_record.py  # 定义 JSON 字段
```

## 预防措施

### 最佳实践

1. **API 边界处进行类型转换**
   ```python
   # 在返回给客户端或保存到数据库前转换
   def serialize_for_api(data):
       return convert_decimal_to_float(data)
   ```

2. **统一数据类型规范**
   ```python
   # Schema 层明确指定类型
   class ScoreSchema(BaseModel):
       total_score: float  # 使用 float 而非 Decimal
       step_scores: dict
   ```

3. **添加类型检查测试**
   ```python
   def test_score_serialization():
       result = await service.generate_mock_score("fire_extinguisher")
       json.dumps(result)  # 应该能正常序列化
   ```

### 类似问题排查

如果遇到类似的序列化错误：

1. **检查数据类型**
   ```python
   print(type(data))  # 查看数据类型
   print(json.dumps(data, default=str))  # 尝试序列化
   ```

2. **常见不可序列化类型**
   - `Decimal` → 转换为 `float`
   - `datetime` → 转换为 ISO 字符串
   - `set` → 转换为 `list`
   - 自定义对象 → 实现 `__dict__` 或 `to_dict()`

3. **使用 Pydantic 自动处理**
   ```python
   from pydantic import BaseModel
   
   class ScoreResponse(BaseModel):
       total_score: float
       step_scores: dict
   
   # Pydantic 会自动处理类型转换
   response = ScoreResponse(**result)
   ```

## 总结

### 问题根源
- SQLAlchemy JSON 字段无法序列化 `Decimal` 类型

### 解决方案
- 在保存到数据库前，递归将所有 `Decimal` 转换为 `float`

### 影响范围
- ✅ 修复"完成训练"功能
- ✅ 评分数据可正常保存
- ✅ 前端可获取评分详情

### 后续优化
- 考虑在 Schema 层统一使用 `float`
- 添加序列化测试用例
- 文档化数据类型规范

---

**修复时间**：2026-03-12  
**修复状态**：✅ 已完成  
**测试状态**：待验证
