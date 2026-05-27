# Seed Inventory

这个文件是唯一的 seed 汇总表，用来做查重、看当前进度、判断下一步还缺哪些数据。新增规则前先搜索这里；不要再维护第二份 seed 总表。

## 状态约定

- `done`: 规则已抽象，脚本已实现，并有可验证输出。
- `todo`: 候选规则，尚未实现或尚未验证。
- `blocked`: 规则来源、渲染方式或验证器还不清楚。

## 难度字段

- `Build`: seed 的生成/验证实现复杂度，不等于题目推理难度。取值：`low` / `medium` / `high`。
- `Reasoning Max`: 这个 seed 可稳定生成的 VQA 推理难度上限。取值：`low` / `medium` / `high` / `very_high`。
- 优先选择 `Build` 可控但 `Reasoning Max` 高的 seed。

## 汇总表

| Seed ID | 名称 | 状态 | Build | Reasoning Max | Reasoning | Visual | Rule | 来源 | 脚本/输出 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `cube_roll_vqa_1` | 立方体滚动方位 | `done` | `medium` | `high` | `spatial`, `simulation` | `grid_board` | `explicit_text_prompt` | 合成 / 状态机 | `cube_roll_vqa_pipeline.py` | 网格路径 + 立方体朝向；可增加长路径提高难度。 |
| `dodger_vqa_v1` | Dodger 碰撞躲避 | `done` | `low` | `high` | `simulation` | `scene_objects` | `explicit_text_prompt` | `original/批次 5-0521.md`; Invent with Python Dodger | `generator/dodger_vqa_generator.py`; `generated/dodger_vqa_v1/` | 网格化动作场景；可做多步安全规划和威胁排序。 |
| `flip_blocks_1` | 翻转方块 / Bloxorz | `done` | `medium` | `very_high` | `spatial`, `game_rule_planning` | `grid_board` | `explicit_text_prompt` | `original/0519-rules批次4.md` | `flip_blocks_1_pipeline.py` | 2 格长方体翻滚与目标规划；适合多步搜索题。 |
| `memory_puzzle_v1` | Memory Puzzle 记忆配对 | `done` | `low` | `medium` | `deductive` | `grid_board` | `explicit_text_prompt` | `original/批次 5-0521.md`; Invent with Python Memory Puzzle | `generator/memory_puzzle_vqa_generator.py`; `generated/memory_puzzle_v1/` | 翻开卡片的形状+颜色配对；可做匹配判断和可见配对计数。 |
| `spongebob_cube_vqa_1` | 海绵宝宝立方体 VQA | `done` | `medium` | `high` | `spatial` | `scene_objects` | `explicit_text_prompt` | 合成 | `spongebob_cube_vqa_pipeline.py` | 3D 物体朝向判断；可用更长路径提高推理步数。 |
| `maze` | 多层迷宫 | `todo` | `medium` | `high` | `algorithmic`, `game_rule_planning` | `grid_board` | `explicit_text_prompt` | `original/Seeds-Generator_Summary.csv` | 待定 | 可做 BFS/DFS、最短路、可达性。 |
| `raven` | 瑞文矩阵补全 | `todo` | `high` | `very_high` | `inductive` | `grid_board` | `visual_demonstration` | `original/Seeds-Generator_Summary.csv` | 待定 | 视觉规律归纳；生成和验证器设计成本高。 |
| `ca_forward` | 元胞自动机前向预测 | `todo` | `low` | `high` | `simulation` | `grid_board` | `explicit_text_prompt` | `original/Seeds-Generator_Summary.csv` | 待定 | 多时间步状态演化，工程可控。 |
| `logic_grid` | 视觉逻辑网格 | `todo` | `medium` | `high` | `constraint_satisfaction` | `table_matrix` | `explicit_text_prompt` | `original/Seeds-Generator_Summary.csv` | 待定 | 静态约束求解。 |
| `graph_coloring` | 平面图 K 着色 | `todo` | `medium` | `high` | `constraint_satisfaction` | `node_link_graph` | `explicit_text_prompt` | `original/Seeds-Generator_Summary.csv` | 待定 | 图节点颜色约束。 |
| `ortho_projection` | 正交投影 | `todo` | `medium` | `high` | `spatial` | `3d_projection` | `explicit_text_prompt` | `original/Seeds-Generator_Summary.csv` | 待定 | 3D 到多视图投影。 |
| `sokoban_v1` | Sokoban 推箱子 | `done` | `low` | `medium` | `simulation` | `grid_board` | `explicit_text_prompt` | `original/批次 5-0521.md` | `generator/sokoban_vqa_generator.py`; `generated/sokoban_v1/` | 随机生成的简单墙体/目标/箱子分布，用于局部合法性和计数。 |
| `othello_v1` | Othello 黑白棋 | `done` | `low` | `high` | `game_rule_planning` | `grid_board` | `explicit_text_prompt` | `original/批次 5-0521.md` | `generator/othello_vqa_generator.py`; `generated/othello_v1/` | 判断黑白棋翻转落子合法性和翻转数量。 |
| `flood_it_v1` | Flood It 色彩填充 | `done` | `medium` | `high` | `algorithmic` | `grid_board` | `explicit_text_prompt` | `original/批次 5-0521.md` | `generator/flood_it_vqa_generator.py`; `generated/flood_it_v1/` | 识别连通块，计算改变颜色后新增的方块数量。 |
| `connect_four_v1` | Connect Four 四子棋 | `done` | `low` | `medium` | `game_rule_planning` | `grid_board` | `explicit_text_prompt` | `original/批次 5-0521.md` | `generator/connect_four_vqa_generator.py`; `generated/connect_four_v1/` | 模拟落子重力和获胜/封堵判断。 |
| `bejeweled_v1` | Bejeweled 三消 | `done` | `low` | `medium` | `algorithmic` | `grid_board` | `explicit_text_prompt` | `original/批次 5-0521.md` | `generator/bejeweled_vqa_generator.py`; `generated/bejeweled_v1/` | 交换相邻宝石并计算消除数量。 |
| `pipe_dream_v1` | Pipe Dream 管道连通 | `done` | `medium` | `high` | `algorithmic` | `grid_board` | `explicit_text_prompt` | `original/批次 5-0521.md` | `generator/pipe_dream_vqa_generator.py`; `generated/pipe_dream_v1/` | 网格连通性判断。 |

## 新增规则时怎么填

1. 先按 `Seed ID`、中文名、来源文件搜索本表，确认没有重复。
2. 如果只是换皮但推理内核和验证器一样，在原行备注里加变体，不新建 seed。
3. 如果需要独立生成脚本或独立验证器，新增一行，状态先写 `todo`。
4. 数据生成并验证后，把状态改成 `done`，补上脚本和输出目录。
5. 同时填写 `Build` 和 `Reasoning Max`，避免把工程复杂度和 VQA 推理难度混在一起。

复现命令优先看每个输出目录下的 `manifest.json` 里的 `reproduce_command` 字段。
