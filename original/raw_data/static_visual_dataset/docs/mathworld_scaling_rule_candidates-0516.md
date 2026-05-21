# MathWorld Scaling Rule Candidates - Collected

目标：专门从 Wolfram MathWorld 中筛选可静态渲染、可用 Python 生成和自动验证的规则型 VQA scaling 候选。表格格式沿用 `docs/scaling_rule_candidates_all-0516.md`。

筛选标准：

- 来源尽量只使用 MathWorld 条目。
- 可以静态渲染成图像、棋盘、网格、图、几何构型或数表。
- 答案可以用公式、枚举、图算法、线性代数、约束求解、几何计算或状态搜索自动验证。
- 对已经高度重复的方向保留但标注重复度，方便后续取舍。

---

## 1. 图论、路径与网络结构

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Eulerian Path / 一笔画图 | 低 | 无向图、桥图、城市/岛屿连接图、边高亮 | 是否存在一笔画；从哪个点开始可走完所有边；添加/删除哪条边后可一笔画 | 用 NetworkX 统计连通性和奇度顶点数；生成满足 0 或 2 个奇点的图；可枚举一条 Euler trail | 给定 7 个节点 10 条边，问能否从 A 出发每条边恰走一次 | [MathWorld: Eulerian Path](https://mathworld.wolfram.com/EulerianPath.html) |
| Hamiltonian Path / Hamiltonian Cycle | 低-中 | 一般图、网格图、立体骨架图、候选访问序列 | 某序列是否访问每点一次；是否形成 Hamiltonian cycle；缺失下一点是哪一个 | 小规模图用回溯/bitmask DP；候选序列直接验证顶点唯一性和相邻边存在 | 给出一个 12 点图和访问序列，问是否为 Hamiltonian path | [MathWorld: Hamiltonian Path](https://mathworld.wolfram.com/HamiltonianPath.html)；[MathWorld: Hamiltonian Cycle](https://mathworld.wolfram.com/HamiltonianCycle.html) |
| Icosian Game / 十二面体 Hamiltonian 游戏 | 低 | 十二面体图、20 点 pegboard、局部路径高亮 | 路径是否已经重复点；下一步哪些点合法；是否能闭合成 Hamiltonian cycle | 固定 dodecahedral graph；用 DFS/DP 验证路径扩展和闭合；可从完整解中截断生成题 | 图上已有 16 个访问点，问哪个候选点能继续保持合法 | [MathWorld: Icosian Game](https://mathworld.wolfram.com/IcosianGame.html) |
| Graph Path / 最短路径与简单路径 | 中 | 节点-边图、带权图、迷宫抽象图 | 两点间是否连通；最短路径长度；某条路径是否合法；有几条长度 k 路径 | BFS/Dijkstra/枚举简单路径；随机图控制路径唯一性或多解数量 | 从 S 到 T 的最短路径经过几个节点 | [MathWorld: Graph Path](https://mathworld.wolfram.com/GraphPath.html) |
| Grid Graph / 方格图路径 | 中 | m x n 方格点阵、障碍边、路径涂色 | 两点最短路；环数量；是否二分图；Hamiltonian path 是否可能 | 构造 `P_m x P_n` 图；BFS、二分染色、回溯或 DP 验证；障碍可由删边生成 | 在 5x6 网格中，问红色路径是否走到每个格点一次 | [MathWorld: Grid Graph](https://mathworld.wolfram.com/GridGraph.html) |
| Maze / 迷宫 | 高 | 方格迷宫、圆形迷宫、入口出口 | 哪条路线能到出口；最少转弯数；死胡同数量；某堵墙移除后是否连通 | 生成 spanning tree maze 或带环迷宫；BFS/DFS 验证路径、距离和连通性 | 从入口到出口最少需要走几步 | [MathWorld: Maze](https://mathworld.wolfram.com/Maze.html) |
| Vertex Coloring / 图着色 | 低 | 平面图、一般图、节点颜色候选 | 当前着色是否合法；最少需要几色；哪个节点颜色冲突 | 对小图用回溯/ILP 求 chromatic number；候选着色检查边两端颜色 | 图中蓝色方案是否是合法 3-coloring | [MathWorld: Vertex Coloring](https://mathworld.wolfram.com/VertexColoring.html) |
| Map Coloring / 地图着色 | 低 | 区域地图、平面划分、邻接图 | 相邻区域是否冲突；最少颜色数；某区域可用哪些颜色 | 随机生成 planar graph 或 Voronoi 区域邻接图；图着色验证 | 给定部分着色地图，问区域 R 还能用哪些颜色 | [MathWorld: Map Coloring](https://mathworld.wolfram.com/MapColoring.html) |
| Clique / 团检测 | 低 | 图中节点集高亮、社交网络样式图 | 高亮节点是否两两相连；最大 clique 大小；补哪条边形成 clique | 穷举小规模节点子集；Bron-Kerbosch 求最大 clique；生成唯一最大团 | 图中红色 5 个点是否构成 clique | [MathWorld: Clique](https://mathworld.wolfram.com/Clique.html) |
| Graceful Graph / 优美标号 | 低 | 图节点数字标签、边差值标注 | 标号是否 graceful；哪条边差值重复；缺失节点标签是多少 | 对边计算绝对差；检查节点标签唯一、边标签覆盖 1..m；可回溯生成题 | 给定 6 条边的树标号，问是否为 graceful labeling | [MathWorld: Graceful Graph](https://mathworld.wolfram.com/GracefulGraph.html) |
| Dominating Set / 控制集 | 低 | 图节点、被覆盖节点阴影、高亮控制点 | 高亮集合是否 domination set；最少控制点数；哪个节点未被覆盖 | 小图枚举节点子集；验证每个节点在集合中或邻接集合；可用 ILP | 红色节点能否覆盖整张图 | [MathWorld: Domination Number](https://mathworld.wolfram.com/DominationNumber.html) |
| Spanning Tree / 生成树 | 低 | 连通图、候选边集合高亮 | 高亮边是否形成生成树；删哪条边仍连通；有几个环 | 用并查集检测连通和无环；边数应为 n-1；可用 Kirchhoff 矩阵树定理计数小图 | 图中蓝色边是否连接全部节点且没有环 | [MathWorld: Spanning Tree](https://mathworld.wolfram.com/SpanningTree.html) |
| Planar Graph / 平面图判定 | 低 | 节点连线图、交叉边图、平面嵌入候选 | 是否平面；哪个边交叉可重画；是否含 K5/K3,3 结构 | 小图用 planarity test；几何绘制中可检测线段交叉；生成 planar/nonplanar 对照 | 这张图是否可以不交叉地画在平面上 | [MathWorld: Planar Graph](https://mathworld.wolfram.com/PlanarGraph.html) |
| Tree / 树结构 | 低 | 层级树、无根树、根节点高亮 | 是否为树；叶子数；两个节点距离；最近公共祖先 | 检查连通且边数 n-1；BFS 求距离；有根树预处理 LCA | 图中从节点 7 到节点 12 的路径长度是多少 | [MathWorld: Tree](https://mathworld.wolfram.com/Tree.html) |

---

## 2. 棋盘图、棋子移动与棋盘约束

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Knight Graph / 骑士图 | 低 | m x n 棋盘、骑士可达边、路径编号 | 某步是否为骑士移动；哪些格可达；路径是否为 knight's tour | 构造 `(±1,±2)` 移动图；验证路径邻接和覆盖；小棋盘 DFS 生成 tour 片段 | 从 c3 出发，下一步能否到 d5 | [MathWorld: Knight Graph](https://mathworld.wolfram.com/KnightGraph.html) |
| King Graph / 王图 | 低 | 棋盘格点、八邻域连边、王路径 | 某路径是否合法；最少王步数；哪些格一步可达；是否 Hamiltonian | 用 Chebyshev 距离验证一步移动；BFS 求最短路；障碍棋盘可做路径题 | 王从 A1 到 E4 最少几步 | [MathWorld: King Graph](https://mathworld.wolfram.com/KingGraph.html) |
| Queen Graph / 后图 | 中 | m x n 棋盘、后可攻击连线、棋子摆放 | 两个皇后是否互相攻击；给定摆放是否合法；最少颜色数/着色问题 | 同行/同列/同对角线判断；可转为 graph coloring 或 independent set | 图中 6 个皇后是否两两不攻击 | [MathWorld: Queen Graph](https://mathworld.wolfram.com/QueenGraph.html) |
| Queens Problem / n 皇后 | 中 | n x n 棋盘、皇后符号、候选落子 | 当前局面是否合法；还能放在哪些格；有几个解；补全一行皇后 | 回溯生成 n-queens 解；局部遮罩验证行列对角线冲突；可控制唯一补全 | 在 8x8 棋盘中，问第 6 行皇后应放哪一列 | [MathWorld: Queens Problem](https://mathworld.wolfram.com/QueensProblem.html) |
| Rook Graph / 车图与行列约束 | 低 | m x n 棋盘、车攻击线、矩阵格 | 两格是否同行同列；最少颜色数；Latin square 对应着色 | 构造 `K_m x K_n` rook graph；检查行列邻接；用着色生成 Latin square 题 | 哪些格与红色车在 rook graph 中相邻 | [MathWorld: Rook Graph](https://mathworld.wolfram.com/RookGraph.html) |
| Bishop Graph / 象图 | 低 | 棋盘、对角线连通分量、黑白格分组 | 两格是否同一 bishop component；某移动是否合法；是否连通 | 判断同色且同对角线移动；构造 bishop graph，按颜色分连通分量 | 白格上的象能否到达目标格 | [MathWorld: Bishop Graph](https://mathworld.wolfram.com/BishopGraph.html) |
| Rook Complement Graph / 非同行非同列关系 | 低 | m x n 棋盘、互不同行列连线 | 两格是否在补图相邻；高亮集合是否互相非同行列；匹配/排列题 | 对所有格 `(r,c)` 建图，边连接 `r1!=r2 and c1!=c2`；验证 clique/independent set | 红色格子集合是否任意两格都不同行不同列 | [MathWorld: Rook Complement Graph](https://mathworld.wolfram.com/RookComplementGraph.html) |
| Leaper Graph / 广义跳棋子 | 低 | 棋盘、固定跳跃向量、可达图 | 哪些格一步可达；路径是否合法；棋盘是否连通 | 给定 leaper 向量 `(a,b)`，生成八种符号变换移动；BFS/连通性验证 | 使用 (2,3)-leaper，从中心格能跳到哪些格 | [MathWorld: Leaper Graph](https://mathworld.wolfram.com/LeaperGraph.html) |
| Triangular Honeycomb Chess Graphs | 低 | 三角网格/六角棋盘、rook/bishop/queen/king 移动线 | 某移动是否合法；连通分量；最短步数；攻击关系 | 用 axial/triangular lattice 坐标建图；按方向集合生成边；BFS 验证 | 在三角蜂窝棋盘中，rook 从 A 到 B 需要几步 | [MathWorld: Triangular Honeycomb Rook Graph](https://mathworld.wolfram.com/TriangularHoneycombRookGraph.html) |
| Puz-Graph / 滑块置换图 | 中-高 | 小图上放编号棋子和一个空位、状态转移图 | 某移动是否合法；两个状态是否同连通分量；最短移动步数 | 状态为含空位的排列；沿底图边交换空位和相邻棋子；BFS 最短路 | 从左图状态到右图状态最少移动几次 | [MathWorld: Puz-Graph](https://mathworld.wolfram.com/Puz-Graph.html) |

---

## 3. 数表、填数与代数约束

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Magic Square / 幻方 | 中 | n x n 数字方阵、部分空格、行列对角线标注 | 是否为 magic square；缺失数是多少；magic constant；哪条线不满足 | 检查数字集合、行/列/对角线和；可由 Siamese method 或已知构造生成 | 3x3 方阵中缺失中心数，使所有线和相等 | [MathWorld: Magic Square](https://mathworld.wolfram.com/MagicSquare.html) |
| Duerer's Magic Square / Durer 幻方变体 | 低 | 4x4 幻方、象限/中心 2x2 高亮 | 哪些区域和为 34；哪个数字交换会破坏性质；补缺失格 | 固定 Duerer square 或同构变换；验证行列对角线、象限、中心块和 | 问高亮的四个角数字之和是否为 34 | [MathWorld: Duerer's Magic Square](https://mathworld.wolfram.com/DuerersMagicSquare.html) |
| Pandiagonal Magic Square / 泛对角幻方 | 低 | 带环绕对角线的方阵、对角线高亮 | 某条环绕对角线和；是否 pandiagonal；缺失数 | 用模索引计算 wraparound diagonal；候选方阵直接验证 | 高亮环绕对角线的和是否等于 magic constant | [MathWorld: Pandiagonal Magic Square](https://mathworld.wolfram.com/PandiagonalMagicSquare.html) |
| Multiplication Magic Square / 乘法幻方 | 低 | n x n 数字方阵、乘积标注 | 行列对角线乘积是否相等；缺失因子；最小乘积比较 | 用整数乘积或质因数向量验证；随机生成乘法一致方阵 | 缺失格填几能让三行乘积相同 | [MathWorld: Multiplication Magic Square](https://mathworld.wolfram.com/MultiplicationMagicSquare.html) |
| Prime Magic Square / 素数幻方 | 低 | 方阵中全为素数、空格和候选素数 | 是否全素且 magic；哪个候选能填入；magic constant | 素性测试 + 幻方和约束；用回溯或模板生成小阶题 | 哪个候选素数放入空格后仍为幻方 | [MathWorld: Prime Magic Square](https://mathworld.wolfram.com/PrimeMagicSquare.html) |
| Semimagic Square / 半幻方 | 低 | 方阵、只要求行列和 | 是否 semimagic；哪条对角线不满足 magic；行列缺失值 | 行列求和验证；对角线作为干扰项；可从 Latin/排列矩阵生成 | 该方阵是 magic square 还是只满足 semimagic | [MathWorld: Semimagic Square](https://mathworld.wolfram.com/SemimagicSquare.html) |
| Latin Square / 拉丁方 | 高 | n x n 符号/颜色/数字方阵、部分空格 | 某行列是否合法；缺失符号；是否 reduced Latin square；两个格能否同符号 | 检查每行每列是否为 1..n；用群表或随机置换生成；回溯补全 | 4x4 拉丁方中空格应填哪个颜色 | [MathWorld: Latin Square](https://mathworld.wolfram.com/LatinSquare.html) |
| Partial Latin Square / 局部符号集合拉丁方 | 低 | 每格有候选符号小列表、已填符号 | 哪个符号可填；是否违反局部候选或行列唯一性；是否可补全 | 每格有 allowed set；用 CSP/回溯验证唯一解；可生成比 Sudoku 更泛化的题 | 中心格只能从 {1,3,5} 选，问哪个选项合法 | [MathWorld: Partial Latin Square](https://mathworld.wolfram.com/PartialLatinSquare.html) |
| Euler Square / Graeco-Latin Square | 中 | 两套符号叠加方阵、颜色+形状组合 | 两个 Latin squares 是否正交；是否每个组合只出现一次；缺失组合 | 分别验证行列唯一；组合 pair 全局唯一；可用有限域构造 | 哪个颜色-形状组合应填入空格 | [MathWorld: Euler Square](https://mathworld.wolfram.com/EulerSquare.html) |
| Cryptarithmetic / 字母算式 | 低 | 竖式加减乘、字母替代数字、候选映射 | 哪个数字映射满足竖式；某字母是多少；是否唯一解 | 约束每字母唯一数字、首字母非零；按列进位回溯或 brute force | SEND + MORE = MONEY 中，问 M 是多少 | [MathWorld: Cryptarithmetic](https://mathworld.wolfram.com/Cryptarithmetic.html) |
| Alphametic / 有意义词语字母算式 | 低 | 单词竖式、主题词、字母表 | 映射是否有效；哪个选项为唯一解；进位位置判断 | 与 cryptarithmetic 相同，增加单词模板生成；可控制字母数不超过 10 | TWO + TWO = FOUR 中，哪个数字可对应 O | [MathWorld: Alphametic](https://mathworld.wolfram.com/Alphametic.html) |
| Skeleton Division / 骨架除法 | 低 | 长除法版式、星号/空格、部分数字 | 缺失数字；商是否正确；某一步乘积是否匹配 | 枚举被除数/除数/商；用长除法中间步骤约束过滤 | 长除法中第二个部分积应是多少 | [MathWorld: Skeleton Division](https://mathworld.wolfram.com/SkeletonDivision.html) |
| Talisman Square / 相邻差约束方阵 | 低 | 方阵、相邻格差值条件、候选填数 | 是否满足相邻差至少 k；哪个格冲突；补一个数字 | 检查横竖斜邻域绝对差；回溯生成满足条件的排列方阵 | 空格填 8 是否会和邻格差值太小 | [MathWorld: Talisman Square](https://mathworld.wolfram.com/TalismanSquare.html) |
| Magic Circle / 圆环幻数 | 低 | 圆周节点、弦/线组合、节点数字 | 每条直线和是否相等；缺失节点；magic constant | 固定 incidence hypergraph；验证每条线的和；回溯生成唯一补全 | 圆上哪个数字能让所有直线和相等 | [MathWorld: Magic Circles](https://mathworld.wolfram.com/MagicCircles.html) |

---

## 4. 拼块、铺砌、拆分与空间构型

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Polyomino / 多连方 | 中 | 方格拼块轮廓、旋转/翻转候选、编号格 | 该形状是几连方；两个形状是否等价；是否含洞；周长/面积 | 坐标集合标准化；旋转/翻转归一；连通性、洞、周长计算 | 两个 pentomino 是否只差旋转或翻转 | [MathWorld: Polyomino](https://mathworld.wolfram.com/Polyomino.html) |
| Polyomino Tiling / 多连方铺砌 | 中 | 棋盘区域、多块 polyomino、部分覆盖 | 某块能否放入；是否完整覆盖；最少/最多剩余格；候选铺法是否合法 | Exact cover/DLX 或回溯；检测重叠、越界、覆盖完整性 | 用 5 块 pentomino 能否铺满给定 5x5 缺口区域 | [MathWorld: Polyomino Tiling](https://mathworld.wolfram.com/PolyominoTiling.html) |
| Tetromino / 四连方 | 中 | Tetris-like 四连方、候选朝向、棋盘区域 | 形状名称；旋转后占哪些格；能否填入空洞；消行数 | 预定义 5/7/19 种 tetromino；旋转模板和碰撞检测 | 当前 L tetromino 旋转后会覆盖哪些格 | [MathWorld: Tetromino](https://mathworld.wolfram.com/Tetromino.html) |
| Pentomino / 五连方 | 中 | 12 种 pentomino、矩形区域、候选拼法 | 某块名称；是否能铺矩形；哪个候选位置非法；剩余空洞形状 | 12 个坐标模板；exact cover 验证；可用已知矩形尺寸生成题 | 哪个 pentomino 能填入右上角空洞 | [MathWorld: Pentomino](https://mathworld.wolfram.com/Pentomino.html) |
| T-Polyomino / T 型多连方 | 低 | T 形块、不同阶数、网格占格 | 阶数是多少；能否由若干 T-polyomino 铺满区域；旋转合法性 | 按阶数生成 T 形坐标；回溯铺砌；检查面积整除和覆盖 | 图中 T-polyomino 的 order 是几 | [MathWorld: T-Polyomino](https://mathworld.wolfram.com/T-Polyomino.html) |
| Polycube / 多立方体 | 中 | 体素块、三视图、候选 3D 形状 | 由几块小立方体组成；两个 polycube 是否同构；能否装箱 | 3D 坐标集合；24 种旋转归一；体素投影和装箱回溯 | 哪个 3D 候选与左侧三视图一致 | [MathWorld: Polycube](https://mathworld.wolfram.com/Polycube.html) |
| Soma Cube / Soma 立方 | 中 | 7 个 Soma pieces、3x3x3 目标体、候选放置 | 某块放置是否合法；缺失块是哪一块；是否填满 3x3x3 | 体素 exact cover；固定 7 件 Soma pieces；旋转枚举 | 最后一块应选哪个才能补成 3x3x3 立方 | [MathWorld: Soma Cube](https://mathworld.wolfram.com/SomaCube.html) |
| Slothouber-Graatsma Puzzle | 低 | 3x3x3 盒子、6 个 1x2x2 块和 3 个小立方 | 哪个块位置合法；空洞是否可填；是否完整装箱 | 3D exact cover；长方体块旋转；枚举装箱状态 | 还剩两个 1x1x1 空位，问当前装法是否可能完成 | [MathWorld: Slothouber-Graatsma Puzzle](https://mathworld.wolfram.com/Slothouber-GraatsmaPuzzle.html) |
| Conway Puzzle / 立方装箱 | 低 | 多块长方体/立方体拼成大立方 | 组件是否能放；当前局面是否可完成；缺失体素数 | 体素化块；exact cover/DFS；从完整解移除部分块生成题 | 哪个候选块能放入中央空腔 | [MathWorld: Conway Puzzle](https://mathworld.wolfram.com/ConwayPuzzle.html) |
| Cube Dissection / 立方体拆分 | 低 | 大立方切成若干块、爆炸图、体素图 | 这些块能否重组成立方；哪个切面面积最大；体积是否一致 | 体素或多面体布尔运算；体积守恒；装箱验证 | 图中 4 个部件总体积是否等于 3x3x3 立方 | [MathWorld: Cube Dissection](https://mathworld.wolfram.com/CubeDissection.html) |
| Dissection Puzzles / 平面拆分拼图 | 中 | 多边形分割、候选重排目标形 | 哪些碎片可拼成目标；面积是否相等；边长是否匹配 | 多边形面积、边长、角度；允许旋转/翻转；小规模 exact cover 或几何配准 | 这些碎片能否拼成右侧正方形 | [MathWorld: Dissection Puzzles](https://mathworld.wolfram.com/DissectionPuzzles.html) |
| T-Puzzle | 低 | T puzzle 四块/多块、目标轮廓、候选摆放 | 哪块应旋转；当前拼法是否重叠；能否组成 T 形 | 多边形刚体变换；碰撞检测和目标覆盖；可用离散化辅助验证 | 哪个选项把碎片放进 T 形轮廓且无重叠 | [MathWorld: T-Puzzle](https://mathworld.wolfram.com/T-Puzzle.html) |
| Tangram / 七巧板 | 高 | 七巧板碎片、目标剪影、候选摆放 | 哪块位置错误；是否完整覆盖剪影；面积比例 | 固定 7 块多边形；离散网格或多边形布尔验证；可生成 silhouette matching | 右侧摆法中哪一块超出了目标轮廓 | [MathWorld: Tangram](https://mathworld.wolfram.com/Tangram.html) |
| Rep-Tile / 自相似拼块 | 低 | 大形状由若干小相似形组成、缩放网格 | 缩放倍数；小块数量；是否为 rep-tile 分割 | 多边形相似变换；面积比等于块数；边界覆盖验证 | 该图是否把一个三角形分成 4 个相似三角形 | [MathWorld: Rep-Tile](https://mathworld.wolfram.com/Rep-Tile.html) |

---

## 5. 铺砌、蜂窝、packing 与 covering

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Tiling / 一般铺砌 | 中 | 平面 tile 图案、周期单元、缺失 tile | 哪块 tile 应填；是否周期；某 tile 的 corona 数量 | 规则 tile 坐标生成；检查邻接、覆盖、重复单元；可从周期 tiling 抽空 | 空白处应放哪种 tile 才能延续图案 | [MathWorld: Tiling](https://mathworld.wolfram.com/Tiling.html) |
| Tessellation / 正则与半正则镶嵌 | 低 | 正多边形铺面、顶点周围多边形序列 | 顶点配置；是否 regular/semiregular；缺失多边形边数 | 用角度和为 360 度验证；生成 3 regular 和 8 semiregular 图案 | 某顶点周围的配置是 3.6.3.6 还是 3.4.6.4 | [MathWorld: Tessellation](https://mathworld.wolfram.com/Tessellation.html) |
| Hexagon Tiling / 六边形铺砌 | 低 | 正六边形网格、非正六边形周期铺砌、菱形填充六边形 | 哪些格相邻；路径距离；菱形铺法数量小例；缺失 tile | axial/cube 坐标生成 hex grid；邻接和距离公式；小区域 exact cover | 在六边形网格中，从 A 到 B 的最短步数 | [MathWorld: Hexagon Tiling](https://mathworld.wolfram.com/HexagonTiling.html) |
| Square Tiling / 方形铺砌 | 中 | 正方形网格、不同大小方块填矩形 | 是否无重叠覆盖；缺失方块边长；面积和 | 矩形 packing/exact cover；用扫描线检测重叠；面积和验证 | 空白矩形应用哪个边长的正方形填补 | [MathWorld: Square Tiling](https://mathworld.wolfram.com/SquareTiling.html) |
| Domino Tiling / 多米诺铺砌 | 高 | 黑白棋盘区域、2x1 domino 覆盖 | 是否可铺；某摆法是否合法；铺法数小例；黑白格数量必要条件 | 二分图完美匹配或 DP；棋盘染色快速判定；exact cover 验证候选 | 去掉两个同色角的棋盘能否用 domino 铺满 | [MathWorld: Domino Tiling](https://mathworld.wolfram.com/DominoTiling.html) |
| Penrose Tiles / 非周期铺砌 | 低 | kite/dart 或 rhombus tiles、匹配规则标记 | 哪个 tile 可接在边上；局部匹配是否违反规则；图案是否可扩展 | 用 edge colors/arrows 作为约束；局部 CSP；substitution rules 生成 patches | 哪个候选菱形能接在红色箭头边旁 | [MathWorld: Penrose Tiles](https://mathworld.wolfram.com/PenroseTiles.html) |
| Wang Tile / 边色方块铺砌 | 低 | 方块 tile 四边颜色、网格空格 | 哪个 tile 可放；是否所有相邻边匹配；有几种补全 | 每个 tile 为四元组颜色；CSP/回溯；局部唯一解生成 | 空白格上方为红、左方为蓝，应选哪个 tile | [MathWorld: Wang Tile](https://mathworld.wolfram.com/WangTile.html) |
| Circle Packing / 圆 packing | 低 | 容器内多个圆、相切图、圆心标注 | 是否重叠；哪些圆相切；packing density；最大可放半径 | 计算圆心距离与半径和；面积密度；优化或采样生成非重叠布局 | 图中圆 A 和圆 B 是否相切 | [MathWorld: Circle Packing](https://mathworld.wolfram.com/CirclePacking.html) |
| Rigid Circle Packing / 稳定圆 packing | 低 | 圆接触网络、可移动圆高亮 | 哪个圆可移动；接触图是否刚性局部条件；相切邻居数量 | 建 contact graph；局部用约束或几何自由度近似判断；生成简单稳定/不稳定例 | 哪个圆没有被邻居固定住 | [MathWorld: Rigid Circle Packing](https://mathworld.wolfram.com/RigidCirclePacking.html) |
| Circle Covering / 圆覆盖 | 低 | 平面区域、多个重叠圆、未覆盖点 | 某点是否被覆盖；区域是否全覆盖；最少还需几个圆 | 点采样 + 精确圆覆盖判断；小区域可用网格验证；生成可视化覆盖漏洞 | 黑点是否落在任一圆内 | [MathWorld: Circle Covering](https://mathworld.wolfram.com/CircleCovering.html) |
| Sphere Packing / 球 packing | 中 | 3D 球堆、投影视图、接触网络 | 哪些球相切；层数；投影中遮挡关系；packing density | 3D 坐标距离验证；投影渲染；固定 FCC/HCP 小块生成 | 中心球接触了几个球 | [MathWorld: Sphere Packing](https://mathworld.wolfram.com/SpherePacking.html) |
| Kissing Number / 接吻数 | 低 | 中心圆/球与周围圆/球接触图 | 中心对象接触数量；哪个对象不相切；维度对应数值 | 2D/3D 坐标距离验证；计数与中心距离等于半径和的邻居 | 图中有几个圆与中心圆相切 | [MathWorld: Kissing Number](https://mathworld.wolfram.com/KissingNumber.html) |

---

## 6. 计算几何、平面构造与度量题

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Voronoi Diagram / Voronoi 图 | 低 | 点集、Voronoi 区域、查询点 | 查询点属于哪个站点；两区域是否相邻；边界由哪些点决定 | scipy.spatial.Voronoi 或半平面裁剪；最近点验证；邻接由 ridge_points 得到 | 黑点落在哪个 Voronoi cell 中 | [MathWorld: Voronoi Diagram](https://mathworld.wolfram.com/VoronoiDiagram.html) |
| Delaunay Triangulation / Delaunay 三角剖分 | 低 | 点集三角网、候选边、外接圆 | 哪条边是 Delaunay；某三角形是否合法；与 Voronoi 邻接关系 | scipy.spatial.Delaunay；空圆条件验证；随机点集避免共圆退化 | 红色边是否属于 Delaunay triangulation | [MathWorld: Delaunay Triangulation](https://mathworld.wolfram.com/DelaunayTriangulation.html) |
| Convex Hull / 凸包 | 低 | 平面点集、外壳多边形、高亮候选点 | 哪些点在凸包上；凸包面积；某点是否内部 | Graham scan/Monotonic chain；点在多边形内；shoelace 面积 | 哪个蓝点不是凸包顶点 | [MathWorld: Convex Hull](https://mathworld.wolfram.com/ConvexHull.html) |
| Triangulation / 多边形三角剖分 | 低 | 简单多边形、对角线、三角形区域 | 某条对角线是否合法；三角形数量；面积和是否匹配 | ear clipping 或 shapely triangulate；检查对角线在多边形内且不交叉 | 七边形三角剖分应有几个三角形 | [MathWorld: Triangulation](https://mathworld.wolfram.com/Triangulation.html) |
| Art Gallery Theorem / 多边形守卫 | 低 | 多边形房间、守卫点、可见区域阴影 | 几个守卫足够；某点是否被看见；哪个角未覆盖 | 多边形可见性计算；小 n 用三角剖分和 3-coloring 构造；采样验证覆盖 | 图中哪个区域没有被任一守卫看到 | [MathWorld: Art Gallery Theorem](https://mathworld.wolfram.com/ArtGalleryTheorem.html) |
| Point in Polygon / 点在多边形内 | 低 | 多边形、查询点、射线 | 点在内/外/边界；射线交点数；哪个点被包含 | ray casting 或 winding number；避免边界退化或单独标注 | 黑点是在多边形内部还是外部 | [MathWorld: Point in Polygon](https://mathworld.wolfram.com/PointinPolygon.html) |
| Polygon Area / 多边形面积 | 低 | 网格多边形、顶点坐标、三角分割 | 面积是多少；哪个多边形面积更大；Pick 定理小题 | shoelace formula；网格点可用 Pick theorem；自动渲染坐标 | 图中格点多边形面积是多少 | [MathWorld: Polygon Area](https://mathworld.wolfram.com/PolygonArea.html) |
| Pick's Theorem / 格点多边形 | 低 | 格点多边形、边界点/内部点标记 | 内部格点数；面积；边界点数；缺失点分类 | 计算 lattice polygon 面积和边界 gcd；用 `A = I + B/2 - 1` 验证 | 已知面积 12、边界点 10，问内部点几个 | [MathWorld: Pick's Theorem](https://mathworld.wolfram.com/PicksTheorem.html) |
| Euler Characteristic / 欧拉示性数 | 低 | 平面图、多面体网格、顶点边面标注 | V-E+F 是多少；是否满足凸多面体公式；缺失面数 | 计数 vertices/edges/faces；多面体/平面图拓扑验证 | 该多面体有 8 顶点 12 边，问面数是多少 | [MathWorld: Euler Characteristic](https://mathworld.wolfram.com/EulerCharacteristic.html) |
| Polyhedron / 多面体骨架 | 中 | 3D 多面体、展开图、顶点边面 | 顶点/边/面数量；哪个展开图可折叠；邻接面判断 | 用预定义 polyhedron mesh；投影渲染；图结构验证邻接 | 正十二面体每个面邻接几个面 | [MathWorld: Polyhedron](https://mathworld.wolfram.com/Polyhedron.html) |
| Platonic Solid / 柏拉图立体 | 中 | 五种正多面体、骨架图、面展开图 | 识别立体；面数/顶点数/边数；对偶是谁 | 固定五种 mesh 参数；欧拉公式和对偶映射验证 | 由 20 个三角形面组成的是哪种正多面体 | [MathWorld: Platonic Solid](https://mathworld.wolfram.com/PlatonicSolid.html) |
| Frustum / 截台体积 | 低 | 截锥/截棱锥、尺寸标注 | 体积/侧面积；哪个截面更大；高度缺失 | 公式计算；随机尺寸生成；图中标注参数 | 上底半径 2、下底半径 5、高 6 的截锥体积是多少 | [MathWorld: Frustum](https://mathworld.wolfram.com/Frustum.html) |

---

## 7. 数列、图案、自动机与视觉化规则

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Cellular Automaton / 元胞自动机 | 低 | 1D/2D 网格时间演化、初态和规则 | 下一行/下一代是什么；某格 t 步后状态；规则号识别 | 按邻域规则迭代 bit grid；固定随机 seed；答案直接模拟 | Rule 30 的下一行中第 5 格是黑还是白 | [MathWorld: Cellular Automaton](https://mathworld.wolfram.com/CellularAutomaton.html) |
| Elementary Cellular Automaton | 低 | 1D 二值 CA 三邻域、规则表、时空图 | 给定规则表求下一行；识别规则号；补缺失像素 | 8 个邻域到 bit 输出；规则号二进制编码；逐行模拟 | 规则 110 下，当前 001110 的下一行是什么 | [MathWorld: Elementary Cellular Automaton](https://mathworld.wolfram.com/ElementaryCellularAutomaton.html) |
| Game of Life / 生命游戏 | 中 | 二维黑白格、当前代和候选下一代 | 下一代某格状态；图案是否仍生命；几代后数量 | 按 8 邻域计数应用 Life 规则；模拟多步；可生成 oscillator/still life | 这个 blinker 下一代是横线还是竖线 | [MathWorld: Life](https://mathworld.wolfram.com/Life.html) |
| Pascal's Triangle / 杨辉三角 | 低 | 三角数表、缺失数字、模颜色图 | 缺失项；某行和；奇偶颜色模式；组合数位置 | 用 `C(n,k)` 公式或递推；模 p 着色；自动生成空格 | 第 7 行第 3 个数是多少 | [MathWorld: Pascal's Triangle](https://mathworld.wolfram.com/PascalsTriangle.html) |
| Ulam Spiral / 素数螺旋 | 低 | 数字方格螺旋、素数高亮、坐标标注 | 某格数字；某数字坐标；是否素数；高亮数列规律 | 生成方形螺旋映射；素性测试；可问坐标和数值互查 | 螺旋中数字 37 位于中心的哪个方向 | [MathWorld: Ulam Spiral](https://mathworld.wolfram.com/UlamSpiral.html) |
| Fibonacci Word / 斐波那契词 | 低 | 二值字符串/条纹递推图 | 下一段字符串；第 n 位字符；替换规则是否正确 | 字符串 morphism 迭代；直接索引或递推；渲染条纹 | 按 0->01, 1->0，第三次迭代结果是什么 | [MathWorld: Fibonacci Word](https://mathworld.wolfram.com/FibonacciWord.html) |
| Lindenmayer System / L-system | 低 | 迭代曲线、重写规则、候选下一步 | 下一代字符串；哪幅图是第 k 代；转角数量 | 字符串重写 + turtle graphics；验证 token counts 和渲染路径 | Koch 规则迭代两次后有几段线 | [MathWorld: Lindenmayer System](https://mathworld.wolfram.com/LindenmayerSystem.html) |
| Koch Snowflake / Koch 雪花 | 低 | 分形曲线迭代图、边段数量 | 第 n 代边数/周长；哪幅图是下一代；面积增长 | 递推 `segments=3*4^n`；turtle 生成；多边形面积公式 | 第 3 次迭代后共有多少条小线段 | [MathWorld: Koch Snowflake](https://mathworld.wolfram.com/KochSnowflake.html) |
| Sierpinski Sieve / Sierpinski 三角 | 低 | 三角递归图、缺失子三角、迭代阶数 | 黑/白区域数量；某子区域是否被移除；第几阶图 | 递归三角划分或 Pascal mod 2；坐标判断；计数公式 | 第 4 阶图中有多少个最小黑三角 | [MathWorld: Sierpinski Sieve](https://mathworld.wolfram.com/SierpinskiSieve.html) |
| Hilbert Curve / 空间填充曲线 | 低 | 方格中的递归路径、编号点、方向箭头 | 下一步方向；两编号点是否相邻；第 n 阶覆盖格数 | Hilbert index <-> xy 映射；路径邻接验证；递归绘制 | Hilbert 曲线第 12 步走向哪个方向 | [MathWorld: Hilbert Curve](https://mathworld.wolfram.com/HilbertCurve.html) |
| Dragon Curve / 龙曲线 | 低 | 折纸曲线、左右转序列、迭代图 | 下一次折叠序列；末端位置；哪幅图是第 k 阶 | 生成 turn sequence；turtle path；检测自交/端点 | 第 5 次迭代的最后一个转向是左还是右 | [MathWorld: Dragon Curve](https://mathworld.wolfram.com/DragonCurve.html) |
| Penrose Tiling Substitution / Penrose 递归图案 | 低 | 菱形/风筝飞镖替换步骤、局部 patch | 哪个子 tile 出现；下一阶 tile 数；边匹配是否正确 | substitution matrix 计数；几何替换渲染；边箭头约束验证 | 下一阶中胖菱形数量会变成多少 | [MathWorld: Penrose Tiles](https://mathworld.wolfram.com/PenroseTiles.html) |

---

## 8. 经典 puzzle 与状态搜索

| 候选规则族 | 和已有数据重复度 | 静态图形式 | 可生成的 VQA 类型 | Python 生成/验证思路 | 示例 | 规则来源 |
| --- | --- | --- | --- | --- | --- | --- |
| Tower of Hanoi / 汉诺塔 | 低 | 三柱圆盘、当前状态和目标状态 | 哪个移动合法；最少步数；下一步应移动哪盘；是否可在 k 步内到达 | 状态 tuple 表示每盘柱号；合法移动 BFS 或公式 `2^n-1`；从解路径采样 | 当前状态下，最小盘能移到哪根柱子 | [MathWorld: Tower of Hanoi](https://mathworld.wolfram.com/TowerofHanoi.html) |
| 15 Puzzle / 十五数码 | 高 | 4x4 滑块、空格、目标状态 | 哪些滑块可移动；是否可解；最少步数小局面；移动后状态 | 置换逆序奇偶性判可解；A*/IDA* 解小扰动状态；候选移动验证 | 当前空格旁边哪些数字可以滑入 | [MathWorld: 15 Puzzle](https://mathworld.wolfram.com/15Puzzle.html) |
| Baguenaudier / 九连环 | 低 | 环扣开关序列、二进制状态、步骤图 | 下一步合法操作；最少解开步数；某状态编号 | 用 Gray code/状态图模拟；合法翻转规则；BFS 验证 | 当前 01011 状态下哪个环能被翻转 | [MathWorld: Baguenaudier](https://mathworld.wolfram.com/Baguenaudier.html) |
| Tic-Tac-Toe Multiway / 井字棋多路状态 | 中 | 3x3 棋盘、game tree 小图、候选落子 | 当前谁赢；哪些落子合法；下一状态数；是否已经终局 | 枚举棋盘状态；胜线检测；生成 game tree 或 multiway graph | 轮到 X，哪个格落子后立即获胜 | [MathWorld: Multicomputation](https://mathworld.wolfram.com/Multicomputation.html) |
| Conway's Game of Life Patterns | 中 | still life/oscillator/glider 静态序列 | 该图案是静物还是振荡子；几代回到原样；下一代活细胞数 | Life 模拟并检测周期；固定 pattern 库；可自动渲染多帧为静态图 | 这个 5x5 图案两代后是否回到原样 | [MathWorld: Life](https://mathworld.wolfram.com/Life.html) |
| Theta-0 Graph Puzzle | 低 | 特定 puzzle graph、边/节点路径 | 能否从指定状态到目标；路径是否合法；图结构属性 | 将 puzzle 抽象为图搜索；按条目图结构固定生成；BFS 验证 | 从红点到蓝点是否存在不重复边路径 | [MathWorld: Theta-0 Graph](https://mathworld.wolfram.com/Theta-0Graph.html) |
| Caliban Puzzle | 低 | 棋盘/图形 puzzle 布局、候选移动 | 哪步合法；是否达到目标；最短步数小实例 | 若条目规则固定，可编码状态转移；BFS/DFS 自动验证 | 哪个选项是当前局面的合法下一步 | [MathWorld: Caliban Puzzle](https://mathworld.wolfram.com/CalibanPuzzle.html) |
| Diabolical Cube | 低 | 小立方体组合块、目标立方、候选装配 | 哪个部件位置合法；能否组成立方；缺失块 | 体素 exact cover；旋转枚举；固定 puzzle pieces | 哪个候选部件能填入剩余空间 | [MathWorld: Diabolical Cube](https://mathworld.wolfram.com/DiabolicalCube.html) |

---

## 9. 现阶段优先级备注

| 规则族 / 方向 | 建议 | 原因 |
| --- | --- | --- |
| 最值得优先补充 | Eulerian/Hamiltonian、棋盘图、Voronoi/Delaunay/Convex Hull、Magic/Latin/cryptarithmetic、circle packing、Wang/Penrose tiles | 与现有数据重复较低，视觉形式清楚，Python 验证直接，能形成大量参数化题 |
| 可作为中期扩展 | polyomino/pentomino/polyclube/Soma、dissection、Art Gallery、L-system/fractal | 生成和渲染成本稍高，但题型质量高，适合做中等难度 scaling |
| 需要谨慎避免重复 | Maze、15 Puzzle、Tangram、Domino Tiling、Sudoku-like Latin squares、Tower of Hanoi | 现有 benchmark 或总表已有近邻，除非设计出明显不同的视觉/推理切面 |
| 不太适合第一批 | 过深的数论条目、纯公式条目、大规模 NP-hard 最优题 | 静态图像信息量弱，或自动生成唯一答案成本高，容易变成文本数学题 |
