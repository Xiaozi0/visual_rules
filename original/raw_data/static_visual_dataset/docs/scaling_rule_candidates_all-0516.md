# Scaling Rule Candidates - Collected

目标：把当前搜集到的、相对不重复于 `docs/data_summary-0515.md` 的规则型静态 VQA scaling 候选整理在一起。这里不写优先级，只按规则/题型分类。

筛选标准：

- 可以静态渲染成图像。
- 可以自己用 Python 生成局面/图形/图表。
- 答案可以用规则、公式、枚举、图搜索、线性代数或模拟器自动验证。
- 尽量避开已有高重复方向：`RAVEN/RPM`、`Bongard/BPS`、`Nikoli/Janko/pencil puzzle` 大类、`STARE/cube net/tangram`、`Sokoban/maze/sliding-tile/Atari/Rubik's cube`。


---

## 2. 物理、机械与可验证量

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| 机械推理图 | 低 | 齿轮组、皮带、滑轮、杠杆、液压、电路开关 | 方向、速度比、省力倍数、平衡位置、灯泡亮灭、哪个系统可行 | 齿轮/皮带用图遍历判断方向；杠杆用力矩公式；滑轮用支撑绳段计数；电路用连通图 |  | [Mechanical Reasoning dataset](https://huggingface.co/datasets/grow-ai-like-a-child/mechanical-reasoning)；[paper](https://arxiv.org/abs/2410.00318) |
| Figure Weights / 天平图形重量 | 低 | 多个天平等式/不等式、图形砝码、候选补全 | 哪个选项平衡；某图形重量；哪个更重；最少需要几个图形 | 随机采样整数权重，生成线性等式/不等式；用线性方程或枚举验证唯一答案 |  | [WAIS Figure Weights](https://en.wikipedia.org/wiki/Wechsler_Adult_Intelligence_Scale)；[CORE Figure Weights](https://cognitivemetrics.com/test/CORE/FW) |
| 可验证物理量图 | 低 | 斜面、弹簧、浮力、碰撞前后、容器液面 | 哪个物体受力大；液面高度；弹簧伸长；速度/能量比较 | 限定到高中公式级别；底层参数随机采样；答案用公式计算，图像只负责呈现参数 |  | [QuantiPhy](https://quantiphy.stanford.edu/) |

---

## 3. 符号、属性与约束推理

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Matchstick / 七段数码管 | 低 | 火柴数字、运算符、错误等式、几何火柴图 | 移动/添加/删除几根使等式成立；问哪根应移动；问是否有解/有几个解 | 七段数码管状态枚举；操作距离为 1/2/3；用表达式求值或几何连通/方块计数验证 |  | [MathSticks](https://arxiv.org/abs/2510.00483)；[通用规则](https://en.wikipedia.org/wiki/Matchstick_puzzle) |
| SET-like 属性卡片 | 低 | 12 张卡，每张有颜色/形状/数量/填充属性 | 三张是否成 set；找缺失卡；一屏中有几个 set；哪张参与最多 set | 每张卡是属性向量；每维满足 all-same 或 all-different；穷举三元组验证 |  | [SET rules](https://brilliant.org/wiki/set-game/)；[overview](https://en.wikipedia.org/wiki/Set_%28card_game%29) |
| Mastermind / 颜色密码反馈 | 低 | 多行颜色猜测 + 黑/白反馈钉 | 哪个候选密码满足所有反馈；还剩几个可能密码；下一猜反馈是什么 | 枚举所有颜色序列；按 exact-position 和 color-only 反馈过滤候选 |  | [Rules](https://en.wikipedia.org/wiki/Mastermind_%28board_game%29)；[complexity](https://arxiv.org/abs/1207.0773) |
| 视觉逻辑场景 / Description Logic | 低-中 | 简单 2D 或 3D 场景：物体、属性、关系、区域 | all/exists/not/and/or、计数约束、包含关系、多跳关系 | 自己生成场景图和渲染；答案由一阶逻辑/描述逻辑查询得到；可避免真实图像依赖 |  | [LoRA VQA](https://lora-vqa.github.io/) |

---

## 4. 棋盘连接与落子游戏

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Connect Four / 四子棋 | 低 | 7x6 竖棋盘，红黄棋子受重力落子 | 哪列是合法落子；落子后谁赢；是否已有四连；找立即获胜/防守列 | 用二维数组表示棋盘；合法列为未满列；落子后扫描横/竖/斜四连；可用小深度 minimax 生成战术题 |  | [MathWorld](https://mathworld.wolfram.com/Connect-Four.html)；[Hasbro rules](https://instructions.hasbro.com/en-gb/instruction/the-classic-game-of-connect-4) |
| Reversi / Othello | 低 | 8x8 黑白棋盘 | 哪些位置是合法落子；某步会翻转几个子；落子后棋盘变成什么；当前比分 | 检查 8 个方向是否夹住对方棋子；翻转列表可精确计算；随机合法对局采样局面 |  | [Reversi rules](https://documentation.help/Reversi-Rules/rules.htm)；[US Othello rules](https://usothello.org/misc/USOA_Tourn_Rules.pdf) |
| Gomoku / Five-in-a-row | 低 | 15x15 或更小棋盘，黑白棋子 | 谁已经五连；下一步哪里能赢；哪里需要堵；有几个活三/活四 | 棋盘扫描连续线段；可先做无禁手版本，后续再加 Renju 禁手 |  | [Gomoku](https://en.wikipedia.org/wiki/Gomoku) |
| Hex | 低 | 六边形网格，两色棋子，双方连接对边 | 哪方已经连通；某步是否完成连接；哪块是关键桥；候选落子是否合法 | 把格子看成图节点；同色邻接并查集/BFS 判断是否连接两条边 |  | [Hex](https://en.wikipedia.org/wiki/Hex_%28board_game%29) |
| Dots and Boxes | 低 | 点阵、已画边、已完成方格归属 | 当前玩家能否完成盒子；某步得几分；哪些边是安全边；游戏比分 | 网格边集合；每条候选边检查新闭合方格数量；可生成 endgame chain 题 |  | [Dots and Boxes](https://en.wikipedia.org/wiki/Dots_and_boxes) |

---

## 5. 放置、拼块与空间构型

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Block design / 彩色积木拼图 | 中 | 2x2/3x3/4x4 目标图案、双色对角块、候选块朝向 | 最少块数、某块朝向、哪个候选能拼成目标、缺失区域 | 用方格/三角半格表示块面；枚举块朝向；验证拼接后像素/网格一致 |  | [Block Design](https://en.wikipedia.org/wiki/Block_design_test)；[Kohs](https://reference.jrank.org/psychology/Kohs_Block_Test.html) |
| 正交三视图/体素重建 | 中 | front/top/right 三视图、体素堆、候选 3D 结构 | 从三视图选可能结构；数隐藏方块；哪个视图不一致 | 随机生成体素集合；投影得到三视图；候选用投影一致性和最小/最大体素数验证 |  | [3ViewSense](https://arxiv.org/abs/2603.07751)；[mental rotation](https://en.wikipedia.org/wiki/Mental_rotation) |
| Blokus-like polyomino placement | 中 | 方格棋盘、彩色多连方块、剩余块 | 哪个位置可放；是否只角接触不边接触；最多还能放几个格；哪个候选非法 | 多连方块坐标 + 旋转/翻转；检测越界、重叠、角接触、边接触 |  | [Blokus rules](https://officialgamerules.org/game-rules/blokus/)；[overview](https://en.wikipedia.org/wiki/Blokus) |
| Tetris board state | 中 | 10x20 堆叠棋盘 + 当前方块 | 当前方块能否放在某列/旋转；放下后消几行；哪列高度最高 | 网格碰撞检测；旋转模板；hard drop 后清行和高度统计 |  | [Tetris Guideline](https://tetris.wiki/Tetris_Guideline) |

---

## 6. 状态转移与模拟类游戏

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Mancala / Kalah | 低 | 两排坑位 + 两个得分仓，坑内石子数 | 走某坑后石子如何分布；是否获得额外回合；是否触发 capture；当前得分 | 数组模拟 sowing；最后一粒位置决定 extra turn/capture；适合数值+视觉结合 |  | [Kalah rules](https://mancala.fandom.com/wiki/Kalah)；[overview](https://en.wikipedia.org/wiki/Kalah) |
| Tower of Hanoi 静态状态 | 低 | 三根柱子、不同大小圆盘、当前状态/目标状态 | 下一步合法移动、最少步数、当前是否有效、目标能否在 k 步内到达 | 状态用 tuple 表示；合法移动图搜索；最短路/BFS 或公式验证 |  | [Tower of Hanoi](https://mathworld.wolfram.com/TowerofHanoi.html) |
| Peg Solitaire | 低 | 十字/三角棋盘，有孔和棋子 | 哪些跳跃合法；跳一步后局面；最少剩几个；当前是否无路可走 | 图上跳跃规则：起点有子、中间有子、终点空；BFS/DFS 可生成可解局面 |  | [Peg Solitaire](https://en.wikipedia.org/wiki/Peg_solitaire) |
| Lights Out | 低 | 方格灯阵，亮/灭状态 | 按某格后哪些灯改变；最少几步全灭；哪个按钮必须按 | 状态是 bitset；按键为自身+邻居 XOR；线性代数或 BFS 解 |  | [Lights Out](https://en.wikipedia.org/wiki/Lights_Out_%28game%29) |
| 2048 | 低 | 4x4 数字方块局面 | 向某方向滑动后的局面；合并后最大块；哪个方向得分最高 | 数组模拟滑动压缩和相同数合并；可固定不生成随机新块来做可验证题 |  | [2048](https://en.wikipedia.org/wiki/2048_%28video_game%29) |

---

## 7. 路径、管道与光线传播

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Rush Hour / 滑块交通 | 低-中 | 6x6 网格、不同长度车辆、出口 | 哪辆车可动；最少几步出车；某移动是否合法 | 网格状态 + BFS/A*；先从解路径反向扰动生成可解状态；静态图渲染 |  | [Rush Hour](https://en.wikipedia.org/wiki/Rush_Hour_%28puzzle%29) |
| Ricochet Robots | 低-中 | 网格墙、多个机器人、目标格 | 某机器人沿方向会停在哪；几步可到目标；哪条路径最短 | 预计算滑行到墙/机器人前的位置；BFS 搜索多机器人状态 |  | [Ricochet Robots](https://en.wikipedia.org/wiki/Ricochet_Robots) |
| Pipe / Net / Plumber | 低 | 方格管道块，每块可旋转 | 哪些块需旋转；旋转后是否全连通；水从入口到哪个出口 | 每块有连接方向 bitmask；旋转变换；图连通验证 |  | [Pipe puzzle](https://logicpuzzles.ca/games/pipes) |
| Khet / laser maze-like optics | 低 | 网格、镜子、激光源、目标 | 激光路径到哪里；哪个镜子被击中；旋转哪个镜子能命中目标 | 光线按方向逐格传播；镜子反射表；遇阻/出界/命中即停止 |  | [Khet](https://en.wikipedia.org/wiki/Khet_%28game%29) |

---

## 8. 当前不建议作为新增重点的高重复项

| 规则族 / game | 原因 | `data_summary-0515.md` 已有对应 |
| --- | --- | --- |
| RPM / Raven 矩阵 | 已有 RAVEN、I-RAVEN、raven-gen，重复高 | RAVEN / I-RAVEN / raven-gen |
| Bongard / 六图分类 | 已有 BPS 和 Bongard-LOGO，重复高 | BPS / Bongard-LOGO |
| Nikoli/Janko/pencil puzzle 大类 | 已有多条 puzzle 来源和 generator 来源，重复高 | pencil-puzzle-bench / grilops / Simon Tatham / janko.at / Nikoli |
| Cube net folding / Tangram | STARE 已明确包含，现有三维空间包也覆盖 | STARE / VisualPuzzles / VisuLogic / SMART |
| Sudoku/Nonogram/Kakuro 变体 | 已被 SynLogic、pencil-puzzle-bench、PuzzleMadness 等覆盖 | SynLogic / pencil-puzzle-bench / PuzzleMadness |
| 迷宫/路径基础题 | 已有 VR-Bench、AlphaMaze、VisualPuzzles、SMART、VGRP-Bench | VR-Bench / AlphaMaze / SMART / VGRP-Bench |
| Sokoban | VR-Bench 已覆盖推箱子 | VR-Bench |
| Sliding tile / 15 puzzle | iVISPAR 已覆盖 sliding-tile 空间规划 | iVISPAR |
| Atari / Mario / fighting games | 现有文档已有相关条目，且更偏动态 agent，不适合静态 VQA 起步 | Odysseus / Atari-GPT / fighting games |
| Rubik's Cube | CubeVLM 已覆盖 | CubeVLM |
