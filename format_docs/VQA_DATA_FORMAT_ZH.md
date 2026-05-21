# Visual Scaling VQA 数据格式规范

本文档定义了项目中 VQA（视觉问答）数据的标准格式。它扩展了基础的 `Simple-MMEval` 模式（`media` + `messages` + `id`），并增加了丰富的元数据，用于分类、追踪和可复现性。

## 1. 文件结构

数据以 JSON 数组形式存储，在大规模应用中推荐使用 **JSONL** (JSON Lines) 格式以提高读取效率。

```json
{
  "id": "vqa_cube_roll_001_seed42",
  "media": ["images/00001.png"],
  "messages": [
    {
      "role": "user",
      "question": "<image> 从蓝色起点方块开始，按图中箭头路径依次翻滚（上、右、下）。最后哪个面朝上？",
      "answer": "A",
      "options": {"A": "脸", "B": "裤子", "C": "衣服", "D": "背面"},
      "choices": ["A", "B", "C", "D"],
      "hint": "注意立方体翻滚时的空间朝向变化。"
    }
  ],
  "metadata": {
    "classification": {
      "domain": "logic_puzzles",
      "task": "cube_orientation",
      "reasoning_type": "spatial",
      "visual_type": "grid_board",
      "rule_delivery_mode": "explicit_text_prompt"
    },
    "provenance": {
      "source": "https://github.com/example/cube-puzzles",
      "method": "deterministic_physics_sim",
      "seed": 42,
      "seed_description": "网格 5x5, 路径长度 3, 起点 [2,0]。",
      "generator": "cube_roll_vqa_pipeline.py"
    },
    "gt": {
      "answer": "A",
      "answer_text": "脸",
      "answer_type": "multiple_choice",
      "validator": {
        "kind": "exact_match",
        "solution": "A"
      }
    },
    "instance": {
      "difficulty": "medium",
      "complexity_score": 0.6,
      "tags": ["cube-rolling", "spongebob", "path-following"],
      "raw_state": {
        "grid_size": [5, 5],
        "path": ["U", "R", "D"],
        "start_orientation": "..."
      }
    }
  }
}
```

## 2. 字段定义

### 核心字段 (兼容 Simple-MMEval)
- **`id`**: (string) 全局唯一标识符。建议格式：`{task}_{index}_seed{seed}`。
- **`media`**: (list[string]) 图像文件的相对路径。
- **`messages`**: (list[dict]) 对话轮次。
  - `role`: "user" 或 "assistant"。
  - `question`: 提示词文本。使用 `<image>` 占位符进行图像交织。
  - `answer`: 在训练数据中设为 `""`，在真值数据中设为正确答案。
  - `options` / `choices`: 选择题评估所必需。

### 元数据字段 (Metadata)

#### **A. `classification` (分类体系)**
- **`domain`**: 更广泛的学科领域（如 `logic_puzzles`, `math`, `physics`）。
- **`task`**: 谜题或任务的具体名称（如 `cube_orientation`, `maze_pathfinding`）。
- **`reasoning_type`**: 核心推理内核（参考 `classification.md`）。
- **`visual_type`**: 主要视觉模态（如 `grid_board`, `node_link_graph`）。
- **`rule_delivery_mode`**: 规则交付方式（如 `implicit_zero_shot`, `explicit_text_prompt`）。

#### **B. `provenance` (溯源信息)**
- **`source`**: 原始种子、规则或逻辑的 URL 或参考引用。
- **`method`**: 生成方法（如 `deterministic_algorithm`, `llm_synthetic`, `hybrid_simulation`）。
- **`seed`**: 用于该实例的随机种子（如果适用）。
- **`seed_description`**: 种子或参数定义内容的文本描述。
- **`generator`**: 产生该数据的脚本名称或版本。

#### **C. `gt` (地面真值)**
- **`answer`**: 规范答案的简写（如 "A"）。
- **`answer_text`**: 完整文本答案。
- **`validator`**: 自动评估的配置（如 `exact_match`）。

#### **D. `instance` (实例属性)**
- **`difficulty`**: 定性难度等级（`easy`, `medium`, `hard`）。
- **`complexity_score`**: 代表任务复杂度的数值（如 0.0 到 1.0）。
- **`raw_state`**: 用于调试或重建的内部生成器状态/参数。


