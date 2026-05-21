

# VQA Seed (规则/游戏) 分类体系与总结规范

本指南旨在为所有的 VQA 数据生成“种子（Seed）”建立标准化的分类和档案记录体系。一个“Seed”代表一种底层规则、一款经典游戏或一个认知任务。标准的分类有助于我们评估多模态大模型在不同维度的能力分布，并为强化学习（RL）提供结构化的环境接口。

## 一、 Seed 的三维分类依据 (The 3D Taxonomy)

在引入任何新的游戏或规则时，必须依据以下三个维度对其进行精准定位：

### 维度 1：推理内核 (Reasoning Type)
*解决该任务，模型需要调用哪种人类核心认知能力？*
- `algorithmic` (算法执行)：严格按步骤图遍历、寻路、排序。（例：迷宫寻路、排序网络）
- `deductive` (演绎推理)：由已知严格推导未知，排除法。（例：扫雷、数独逻辑推导）
- `inductive` (归纳发现)：从少量样本总结出隐藏的普遍规律。（例：ARC、找规律）
- `analogical` (类比映射)：A 与 B 的关系，映射到 C 与 D。（例：瑞文矩阵变体）
- `constraint_satisfaction` (约束求解)：满足所有静态限制条件。（例：图着色、N皇后）
- `spatial` (空间推理)：心理旋转、折叠、透视、3D拓扑。（例：翻转方块、立方体展开）
- `numerical` (数值计算)：数学运算、面积计算、代数方程。（例：24点、数织计算）
- `simulation` (状态演化)：推演确定性系统未来 N 步的状态。（例：生命游戏、沙元胞）
- `mechanical_physical` (物理/机械)：重力、碰撞、传动、杠杆。（例：齿轮转向、愤怒的小鸟）
- `game_rule_planning` (博弈/多步规划)：在动态对抗或目标导向中搜索最优解。（例：国际象棋、推箱子）

### 维度 2：视觉模态 (Visual Type)
*该任务的状态空间如何被渲染为图像（渲染引擎的选择依据）？*
- `grid_board`：基于离散格子的棋盘（推箱子、贪吃蛇、俄罗斯方块）。
- `table_matrix`：行列对齐的数据/文字表格（逻辑真值表）。
- `node_link_graph`：由节点和边组成的拓扑图（TSP问题、网络流）。
- `geometry_diagram`：2D矢量几何图形（多边形面积、相交判断）。
- `chart_plot`：带有坐标轴的统计图表。
- `diagram_flow`：带箭头的架构/时序流程图。
- `map_circuit`：现实意义的物理/电路连线图。
- `symbol_panel`：非网格化的纯符号/公式排列（火柴棍等式）。
- `3d_projection`：透视或正交的 3D 渲染（3D 迷宫、积木堆叠）。
- `scene_objects`：具象的日常物体或自然场景截图。

### 维度 3：规则交付 (Rule Delivery Mode)
*模型在做题前，如何得知游戏的玩法和目标？*
1. `implicit_zero_shot` (隐式先验)：只给图和问题，假定模型自带该游戏（如国际象棋）的知识先验。
2. `explicit_text_prompt` (显式文本)：在 Prompt 中用长文本详细写明游戏规则和物理设定。
3. `visual_demonstration` (视觉示例)：通过连续几帧的图像示例（Few-shot Demo）让模型自己悟出规则。

---

## 二、 常见游戏玩法的分类映射速查表

| 游戏/规则大类 | 典型游戏案例 | 推荐的 Reasoning Type | 推荐的 Visual Type |
| :--- | :--- | :--- | :--- |
| **迷宫与路径规划** | 迷宫 (Maze), 连线游戏 | `algorithmic` 或 `game_rule_planning` | `grid_board` |
| **状态机与棋盘动作** | 贪吃蛇, 俄罗斯方块, 吃豆人 | `simulation` 或 `game_rule_planning` | `grid_board` |
| **逻辑约束与数谜** | 数独, 扫雷, Nonogram | `constraint_satisfaction` | `grid_board` |
| **经典对抗棋类** | 国际象棋, 围棋, 五子棋 | `game_rule_planning` | `grid_board` |
| **物理抛物与弹射** | 打砖块, 愤怒的小鸟, 坦克大战 | `mechanical_physical` | `geometry_diagram` |
| **空间与几何翻转** | 翻转方块 (Bloxorz) | `spatial` | `3d_projection` |
| **匹配与消除** | 消除星星, 噗哟噗哟 | `simulation` 或 `game_rule_planning` | `grid_board` |
| **记忆与找规律** | 翻牌记忆, ARC, 找茬 | `inductive` | `grid_board` |

---

## 三、 标准 Seed 总结文档模板 (Seed Document Template)

```markdown
# Seed: [游戏/规则名称]

## 1. 基本信息
- **Seed ID**: `[如：sokoban_v1]`
- **来源/参考**: `[链接]`
- **核心玩法描述**: `[玩家目标描述]`

## 2. 三维分类标签
- **推理内核 (Reasoning Type)**: `[标签]` 
- **视觉表现 (Visual Type)**: `[标签]`
- **规则交付 (Rule Delivery)**: `[标签]`

## 3. VQA 任务设计 (Target QA Pairs)
1. **状态判定 (State)**: ...
2. **合法性验证 (Validation)**: ...
3. **多步推演 (Simulation)**: ...
4. **全局规划 (Planning)**: ...

## 4. 数据生成与渲染思路
- **底层数据结构**: ...
- **验证算法 (Ground Truth)**: ...
- **渲染方案**: ...

## 5. 难度分级 (Difficulty Scaling)
- **Level 1 (Easy)**: ...
- **Level 2 (Medium)**: ...
- **Level 3 (Hard)**: ...
```
