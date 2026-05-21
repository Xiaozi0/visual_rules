# Visual Scaling VQA 数据格式规范

本规范定义了 Visual Question Answering (VQA) 任务的数据存储格式，严格遵循 `Simple-MMEval` 的基础协议（`media` + `messages` + `id`），并扩展了 `metadata` 字段以支持复杂的溯源、分类和调试需求。

## 核心数据结构

数据推荐以 **JSONL** (JSON Lines) 格式存储，确保大规模数据的读取效率。

```json
{
  "id": "vqa_counting_001_seed42",
  "media": ["images/vqa_counting_001.png"],
  "messages": [
    {
      "role": "user",
      "question": "<image> 在图中共有多少个红色的圆形？直接返回数字即可。",
      "answer": "",
      "options": {"A": "3", "B": "4", "C": "5", "D": "6"},
      "choices": ["A", "B", "C", "D"],
      "hint": "注意重叠的部分也需要计算在内。"
    }
  ],
  "metadata": {
    "dataset": {
      "category": "counting",
      "sub_category": "geometric_overlap",
      "source": "programmatic_gen",
      "method": "procedural_graphics_v1"
    },
    "provenance": {
      "seed": 42,
      "seed_description": "随机生成 3-7 个圆形，颜色随机分布，确保至少有两处重叠。",
      "rule_source": "rules/counting/rules_v1.md",
      "generator_version": "0.1.0"
    },
    "gt": {
      "answer": "A",
      "answer_text": "3",
      "answer_type": "multiple_choice",
      "validator": {
        "kind": "exact_match",
        "solution": "A"
      }
    },
    "instance": {
      "difficulty": "easy",
      "complexity": 2,
      "raw_state": {
        "shapes": [{"type": "circle", "color": "red", "pos": [10, 10]}, "..."]
      }
    }
  }
}
```

---

## 字段详解

### 1. 顶层必需字段 (Simple-MMEval 兼容)

- **`id`**: (string) 全局唯一标识符。建议包含数据集类型、索引或种子信息。
- **`media`**: (list[string]) 本地图片路径列表。路径相对于推理时指定的 `--img_dir`。
- **`messages`**: (list[dict]) 对话序列。
  - `question`: 必须包含 `<image>` 占位符。
  - `options` / `choices`: 选择题必备。
  - `answer`: 默认为 `""`，推理框架会将其填充为模型输出。

### 2. `metadata` 分类建议

为了方便后续的性能分析（如按分类看准确率），`metadata` 建议采用以下四层结构：

#### **A. `dataset` (分类与归属)**
- `category`: 顶级任务类型（如 `counting`, `logic`, `spatial`, `math`）。
- `sub_category`: 细分任务（如 `analog_clock`, `nested_rectangles`）。
- `source`: 数据来源标识（如 `synthetic_v1`, `manually_annotated`）。
- `method`: 生成或获取的具体方法（如 `rule_based`, `stable_diffusion_inpaint`）。

#### **B. `provenance` (溯源与种子)**
- `seed`: (int/string) 生成该样本所用的随机种子。
- `seed_description`: **[关键]** 对种子的文字描述。例如：“该种子用于控制背景噪声水平”或“定义了时钟的时针和分针初始角度”。
- `rule_source`: 引用的规则文件路径，方便追溯逻辑修改。

#### **C. `gt` (地面真值)**
- `answer`: 供模型评估的标准答案（如 "A"）。
- `answer_type`: `multiple_choice`, `open_ended`, `exact_number` 等。
- `validator`: 评估时使用的验证器配置。

#### **D. `instance` (实例属性)**
- `difficulty`: 难度等级。
- `complexity`: 复杂度评分（如物体数量、遮挡等级）。
- `raw_state`: 生成该题目时的原始参数（如坐标、颜色值），用于后期 Debug 或重建场景。

---

## 路径约定

在执行推理脚本时：
```bash
python mmeval/run.py --img_dir ./data/vqa_project/images --infile ./data/vqa_project/data.jsonl ...
```
JSON 中的 `media` 字段应写为 `["vqa_counting_001.png"]`，系统会自动拼接为 `./data/vqa_project/images/vqa_counting_001.png`。
