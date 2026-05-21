# Visual Scaling VQA Data Format Specification

This document defines the standard format for VQA (Visual Question Answering) data within the project. It extends the basic `Simple-MMEval` schema (`media` + `messages` + `id`) with rich metadata for classification, tracking, and reproducibility.

## 1. File Structure

Data is stored as a JSON array or preferably as **JSONL** (JSON Lines) for large-scale efficiency.

```json
{
  "id": "vqa_cube_roll_001_seed42",
  "media": ["images/00001.png"],
  "messages": [
    {
      "role": "user",
      "question": "<image> Starting from the blue start square, roll the cube following the arrows (Up, Right, Down). Which face is on top at the end?",
      "answer": "A",
      "options": {"A": "Face", "B": "Pants", "C": "Shirt", "D": "Back"},
      "choices": ["A", "B", "C", "D"],
      "hint": "Pay attention to the spatial orientation changes as the cube rolls."
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
      "seed_description": "Grid 5x5, path length 3, starting at [2,0].",
      "generator": "cube_roll_vqa_pipeline.py"
    },
    "gt": {
      "answer": "A",
      "answer_text": "Face",
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

## 2. Field Definitions

### Core Fields (Simple-MMEval Compatible)
- **`id`**: (string) Globally unique identifier. Suggested format: `{task}_{index}_seed{seed}`.
- **`media`**: (list[string]) Relative paths to image files.
- **`messages`**: (list[dict]) Conversation turns.
  - `role`: "user" or "assistant".
  - `question`: The prompt text. Use `<image>` placeholders for image interleaving.
  - `answer`: Set to `""` in training data or the correct answer in ground truth.
  - `options` / `choices`: Required for multiple-choice evaluation.

### Metadata Fields

#### **A. `classification` (Taxonomy)**
- **`domain`**: The broader subject area (e.g., `logic_puzzles`, `math`, `physics`).
- **`task`**: The specific name of the puzzle or task (e.g., `cube_orientation`, `maze_pathfinding`).
- **`reasoning_type`**: The core reasoning kernel required (see `classification.md`).
- **`visual_type`**: The primary visual modality (e.g., `grid_board`, `node_link_graph`).
- **`rule_delivery_mode`**: How rules are delivered (e.g., `implicit_zero_shot`, `explicit_text_prompt`).

#### **B. `provenance` (Ancestry)**
- **`source`**: URL or reference to the original seed, rule, or logic.
- **`method`**: Generation methodology (e.g., `deterministic_algorithm`, `llm_synthetic`, `hybrid_simulation`).
- **`seed`**: The random seed used for this instance (if applicable).
- **`seed_description`**: Textual description of what the seed or parameters define.
- **`generator`**: The script name or version that produced this data.

#### **C. `gt` (Ground Truth)**
- **`answer`**: The shorthand canonical answer (e.g., "A").
- **`answer_text`**: The full-text answer.
- **`validator`**: Configuration for automated evaluation (e.g., `exact_match`).

#### **D. `instance` (Specific Attributes)**
- **`difficulty`**: Qualitative difficulty level (`easy`, `medium`, `hard`).
- **`complexity_score`**: Numerical value representing task complexity (e.g., 0.0 to 1.0).
- **`raw_state`**: Internal generator state/parameters for debugging or reconstruction.

