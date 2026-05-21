# Game Scaling Rule Candidates

目标：补充一些 game 类规则来源，用于自己写 Python 批量生成静态 VQA。这里优先选“局面可以静态渲染、规则可程序验证、和 `docs/data_summary-0515.md` 已有条目重复较少”的游戏。

不优先放入：`Sokoban/maze/sliding-tile/Atari/Rubik's cube`，因为现有文档里已有 `VR-Bench`、`AlphaMaze`、`iVISPAR`、`Gym-V`、`CubeVLM` 等相关条目。

## 推荐候选表

| 优先级 | Game / 规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | Connect Four / 四子棋 | 低 | 7x6 竖棋盘，红黄棋子受重力落子 | 哪列是合法落子；落子后谁赢；是否已有四连；找立即获胜/防守列 | 用二维数组表示棋盘；合法列为未满列；落子后扫描横/竖/斜四连；可用小深度 minimax 生成战术题 | MathWorld: https://mathworld.wolfram.com/Connect-Four.html；Hasbro rules: https://instructions.hasbro.com/en-gb/instruction/the-classic-game-of-connect-4 |
| P0 | Reversi / Othello | 低 | 8x8 黑白棋盘 | 哪些位置是合法落子；某步会翻转几个子；落子后棋盘变成什么；当前比分 | 检查 8 个方向是否夹住对方棋子；翻转列表可精确计算；随机合法对局采样局面 | Reversi rules: https://documentation.help/Reversi-Rules/rules.htm；US Othello rules PDF: https://usothello.org/misc/USOA_Tourn_Rules.pdf |
| P0 | Gomoku / Five-in-a-row | 低 | 15x15 或更小棋盘，黑白棋子 | 谁已经五连；下一步哪里能赢；哪里需要堵；有几个活三/活四 | 棋盘扫描连续线段；可先做无禁手版本，后续再加 Renju 禁手 | Rules overview: https://en.wikipedia.org/wiki/Gomoku |
| P0 | Hex | 低 | 六边形网格，两色棋子，双方连接对边 | 哪方已经连通；某步是否完成连接；哪块是关键桥；候选落子是否合法 | 把格子看成图节点；同色邻接并查集/BFS 判断是否连接两条边 | Hex rules overview: https://en.wikipedia.org/wiki/Hex_%28board_game%29 |
| P0 | SET-like card game | 低 | 12 张卡，每张有颜色/形状/数量/填充属性 | 三张是否成 set；缺哪张；一屏中有几个 set；哪张参与最多 set | 每张卡是属性向量；每维满足 all-same 或 all-different；穷举三元组验证 | SET rules: https://brilliant.org/wiki/set-game/；overview: https://en.wikipedia.org/wiki/Set_%28card_game%29 |
| P1 | Mastermind | 低 | 多行颜色猜测 + 黑/白反馈钉 | 哪个候选密码满足所有反馈；还剩几个可能密码；下一猜反馈是什么 | 枚举所有颜色序列；按 exact-position 和 color-only 反馈过滤候选 | Rules overview: https://en.wikipedia.org/wiki/Mastermind_%28board_game%29 |
| P1 | Dots and Boxes | 低 | 点阵、已画边、已完成方格归属 | 当前玩家能否完成盒子；某步得几分；哪些边是安全边；游戏比分 | 网格边集合；每条候选边检查新闭合方格数量；可生成 endgame chain 题 | Rules overview: https://en.wikipedia.org/wiki/Dots_and_boxes |
| P1 | Mancala / Kalah | 低 | 两排坑位 + 两个得分仓，坑内石子数 | 走某坑后石子如何分布；是否获得额外回合；是否触发 capture；当前得分 | 数组模拟 sowing；最后一粒位置决定 extra turn/capture；适合数值+视觉结合 | Kalah rules: https://mancala.fandom.com/wiki/Kalah；overview: https://en.wikipedia.org/wiki/Kalah |
| P1 | Blokus-like polyomino placement | 中 | 方格棋盘、彩色多连方块、剩余块 | 哪个位置可放；是否只角接触不边接触；最多还能放几个格；哪个候选非法 | 多连方块坐标 + 旋转/翻转；检测越界、重叠、角接触、边接触 | Blokus rules: https://officialgamerules.org/game-rules/blokus/；overview: https://en.wikipedia.org/wiki/Blokus |
| P1 | Peg Solitaire | 低 | 十字/三角棋盘，有孔和棋子 | 哪些跳跃合法；跳一步后局面；最少剩几个；当前是否无路可走 | 图上跳跃规则：起点有子、中间有子、终点空；BFS/DFS 可生成可解局面 | Rules overview: https://en.wikipedia.org/wiki/Peg_solitaire |
| P1 | Lights Out | 低 | 方格灯阵，亮/灭状态 | 按某格后哪些灯改变；最少几步全灭；哪个按钮必须按 | 状态是 bitset；按键为自身+邻居 XOR；线性代数或 BFS 解 | Rules overview: https://en.wikipedia.org/wiki/Lights_Out_%28game%29 |
| P1 | Ricochet Robots | 低-中 | 网格墙、多个机器人、目标格 | 某机器人沿方向会停在哪；几步可到目标；哪条路径最短 | 预计算滑行到墙/机器人前的位置；BFS 搜索多机器人状态 | Rules overview: https://en.wikipedia.org/wiki/Ricochet_Robots |
| P2 | Pipe / Net / Plumber | 低 | 方格管道块，每块可旋转 | 哪些块需旋转；旋转后是否全连通；水从入口到哪个出口 | 每块有连接方向 bitmask；旋转变换；图连通验证 | Pipes rules: https://logicpuzzles.ca/games/pipes |
| P2 | 2048 | 低 | 4x4 数字方块局面 | 向某方向滑动后的局面；合并后最大块；哪个方向得分最高 | 数组模拟滑动压缩和相同数合并；可固定不生成随机新块来做可验证题 | Rules overview: https://en.wikipedia.org/wiki/2048_%28video_game%29 |
| P2 | Tetris board state | 中 | 10x20 堆叠棋盘 + 当前方块 | 当前方块能否放在某列/旋转；放下后消几行；哪列高度最高 | 网格碰撞检测；旋转模板；hard drop 后清行和高度统计 | Tetris guideline overview: https://tetris.wiki/Tetris_Guideline |
| P2 | Khet / laser maze-like optics | 低 | 网格、镜子、激光源、目标 | 激光路径到哪里；哪个镜子被击中；旋转哪个镜子能命中目标 | 光线按方向逐格传播；镜子反射表；遇阻/出界/命中即停止 | Khet overview: https://en.wikipedia.org/wiki/Khet_%28game%29 |

## 最适合先做的 8 个

| 排名 | Game | 原因 |
| --- | --- | --- |
| 1 | Connect Four | 规则最短，渲染简单，合法性/胜负/一步战术都好验证 |
| 2 | Reversi / Othello | 翻转规则视觉性强，能产生多步但仍可精确验证的问题 |
| 3 | SET-like card game | 和已有 puzzle 重复少，属性组合可指数级扩展 |
| 4 | Gomoku | 可生成“找赢点/堵点/判断五连”，比棋类完整策略简单 |
| 5 | Hex | 连通性推理很清楚，适合补图搜索/拓扑连接类 |
| 6 | Mastermind | 静态图像简单，但逻辑约束强，适合候选筛选题 |
| 7 | Dots and Boxes | 边/闭合方格推理直观，适合局部计分和安全边问题 |
| 8 | Mancala / Kalah | 视觉上是数数和状态转移，适合做“模拟一步”类 VQA |

## 暂不建议优先做

| Game | 原因 |
| --- | --- |
| Chess / Go / Shogi | 规则或策略太重，容易变成专业引擎评测；如果做，只建议做非常局部的合法走法/吃子/连通气问题 |
| Sokoban | `VR-Bench` 已覆盖推箱子，重复高 |
| Maze / pathfinding game | `VR-Bench`、`AlphaMaze`、`VisualPuzzles`、`SMART` 已覆盖很多 |
| Sliding tile / 15 puzzle | `iVISPAR` 已覆盖 sliding-tile 空间规划 |
| Atari / Mario / fighting games | 现有文档已有 Odysseus、Atari-GPT、格斗游戏；且更偏动态 agent，不适合静态 VQA 起步 |
| Rubik's Cube | `CubeVLM` 已覆盖，且三维状态渲染和动作验证成本较高 |

