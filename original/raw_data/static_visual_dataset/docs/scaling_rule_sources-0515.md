# Scaling Rule Sources for Static Visual VQA

目标：只收集“可规则化、可自己用 Python 批量生成 VQA”的题型来源和规则族；不优先使用已有 generator，也不直接采集受版权保护的原题。

和当前 `docs/data_summary-0515.md` 的对应关系：

- `规律补全`：矩阵/RPM、几何类比、图形序列、Bongard 概念归纳
- `六图分类`：Bongard、属性分类、相同/不同规则
- `三维空间`：折纸、立方体展开、三视图、心理旋转、积木/拼装、Tangram
- `路径与计量`：pencil puzzles、迷宫/路径、图表/坐标、几何测量
- `类比与逻辑映射`：几何类比、符号映射、matchstick、figure weights、机械推理

---

## 1. 最值得优先做的规则族

| 优先级 | 规则族 | 可生成内容 | 为什么适合 scaling | 主要来源 |
| --- | --- | --- | --- | --- |
| P0 | RPM / 矩阵规律 | 2x2/3x3 矩阵补全，多选或直接生成答案 | 属性和变换可组合，天然可控难度 | Raven/PGM/RPM 论文与综述 |
| P0 | Bongard / 六图分类 | 左右两组或 6 图二分类，问共同规则/哪张不属于 | 规则集合很大，图片简单，答案可验证 | Foundalis / Bongard 问题 |
| P0 | Pencil puzzle 规则 | Akari/Hashi/Slitherlink/Nurikabe/Battleships/Tents 等 | 规则明确，可用求解器验证唯一解，适合大量 VQA 模板 | Nikoli/Janko/Conceptis/GMPuzzles |
| P0 | 空间折叠与展开 | 折纸打孔/裁切、cube net、三视图、截面 | 和现有 `三维空间` 高度对齐，规则可参数化 | PFP/GamiBench/3DSRBench/空间能力测试 |
| P1 | 图表/科学图推理 | bar/line/pie/scatter，最大最小、趋势、差值、比例、交叉点 | Matplotlib 低成本生成，QA 自动可验 | FigureQA/DVQA/PlotQA/ChartQA |
| P1 | 机械推理图 | 齿轮、滑轮、杠杆、天平、液压、简单电路 | 图形简单但推理链明确，可用公式或图算法求解 | Bennett/LogicVista/mechanical reasoning |
| P1 | Matchstick / 七段数码管 | 移动/添加/删除 1-2 根火柴使等式成立 | 状态空间小，答案可枚举验证 | MathSticks / matchstick puzzle 规则 |
| P1 | 几何类比 | A:B::C:?，旋转/镜像/缩放/颜色/拓扑变换 | 和矩阵题互补，可做单步/多步映射 | geometric analogy papers |
| P2 | Tangram / 拼装覆盖 | 给轮廓和部件，问能否拼成、缺哪个、面积/位置关系 | 可用 exact polygon 坐标验证，但实现略重 | TangramPuzzle |
| P2 | Block design / 积木拼图 | 彩色方块拼图、正交投影、可见块计数 | 和空间题强相关，Python 3D/2D 投影可生成 | block design / 3D spatial sources |

---

## 2. RPM / 矩阵规律

**规则语法**

- 属性：shape/type、color/fill、size、number、position、orientation、line style、texture。
- 行列关系：progression、XOR/OR/AND、addition/subtraction、permutation、cyclic shift、reflection、rotation、superposition、disappearance。
- 难度控制：
  - 单属性单规则：颜色轮换、数量 +1、旋转 90 度。
  - 多属性单规则：数量 + 颜色同时变化。
  - 多规则组合：行方向一个规则、列方向另一个规则。
  - 干扰项：只满足局部相似、不满足全局一致。

**可做 VQA 模板**

- “选择能补全问号的图形。”
- “第三行第三列应该有几个圆？”
- “缺失格子的颜色/方向/数量是什么？”
- “哪一个候选项同时满足行和列的规律？”

**来源**

- Raven Progressive Matrices 是非语言抽象推理测试，常见形式是带缺失格的 2x2/3x3/更多矩阵，并从候选项选择补全图形：https://en.wikipedia.org/wiki/Raven%27s_Progressive_Matrices
- RPM 规则通常作用在 number、position、type/shape、size、color 等属性上：https://www.emergentmind.com/topics/raven-s-progressive-matrices-rpm
- PGM / RAVEN 相关自动出题文献可作为规则拆解参考，但这里不直接复用 generator：https://arxiv.org/abs/2003.11608
- 综述：Deep Learning Methods for Abstract Visual Reasoning: A Survey on Raven's Progressive Matrices：https://arxiv.org/abs/2201.12382

---

## 3. Bongard / 六图分类

**规则语法**

- 输入：两组图，每组 6 张；或 6 张图要求二分类。
- 正例/负例规则：
  - 几何属性：有闭合区域、凸/凹、对称、相交、包含、接触。
  - 关系属性：一个对象在另一个内部、所有线段平行、两个形状相切。
  - 数量属性：正例有奇数个对象，负例有偶数个对象。
  - 拓扑属性：连通分量数、洞数、交叉数、端点数。
  - 组合属性：正例满足 “红色三角形在圆内且数量为 2”。

**可做 VQA 模板**

- “左边图形共同满足什么规则？”
- “下面哪张图属于左边这一组？”
- “把 6 张图按隐藏规则分成两组。”
- “哪张图和其他图不属于同一类？”

**来源**

- Foundalis 的 Bongard problem 页面，核心形式是两组各 6 个黑白方框，目标是找左右两边视觉模式差异：https://www.foundalis.com/res/diss_research.html
- Quanta 对 Bongard 问题的概述：左边 6 个例子满足未知规则，右边 6 个不满足：https://www.quantamagazine.org/bongard-problems-and-scientific-discovery-20170608/
- Bongard problem 基本定义和相关工作：https://en.wikipedia.org/wiki/Bongard_problem

---

## 4. Pencil Puzzle 规则库

这类来源不一定给 generator，但给了稳定规则。适合自己实现：随机生成完整解 -> 删除线索 -> 用 solver 验证唯一解 -> 渲染成图片 -> 生成 VQA。

### 4.1 路径/连通类

| 类型 | 核心规则 | VQA 方向 | 来源 |
| --- | --- | --- | --- |
| Hashi / Bridges | 岛屿按数字连桥，桥横竖、不交叉，所有岛连通 | 哪些岛相连、总桥数、是否唯一、缺哪座桥 | https://arxiv.org/abs/1905.00973 |
| Slitherlink | 根据数字决定周围边数，形成单一闭合回路 | 某格周围几条线、是否在环上、闭环长度 | Nikoli/Janko/Conceptis |
| Numberlink / Arukone | 同数字端点配对，路径不交叉，覆盖或不覆盖全格 | 哪两个端点相连、某格属于哪条路径 | Nikoli/Janko |
| Masyu | 黑白圆约束直行/转弯，形成单环 | 下一步方向、哪个候选违反规则 | Nikoli/Janko |
| Yajilin | 箭头数字约束黑格数量，非黑格成单环 | 黑格位置、箭头可见数量、路径连通 | Nikoli/Janko |

### 4.2 涂格/分区类

| 类型 | 核心规则 | VQA 方向 | 来源 |
| --- | --- | --- | --- |
| Nurikabe | 数字岛大小固定，海连通，不能有 2x2 海 | 某格黑/白、岛大小、是否违反 2x2 | https://www.puzzlemix.com/Nurikabe |
| Akari / Light Up | 灯照亮行列，黑格数字约束邻灯数，灯互不照 | 哪格放灯、哪格被照亮、违反哪条规则 | Janko/Nikoli |
| Hitori | 删除数字使行列不重复，黑格不相邻，白格连通 | 哪些格涂黑、是否连通、重复消除 | Nikoli/Janko |
| Fillomino | 相同数字连块大小等于数字，相邻同大小块不可接触 | 某块大小、边界在哪里 | Nikoli/Janko |
| Shikaku | 分割矩形成含一个数字的区域，面积等于数字 | 区域面积、边界、某格属于哪个数字 | Nikoli/Janko |

### 4.3 放置/计数类

| 类型 | 核心规则 | VQA 方向 | 来源 |
| --- | --- | --- | --- |
| Battleships | 舰队水平/垂直放置，不接触，行列计数约束 | 某格是否有船、船长度、行列剩余数 | https://www.conceptispuzzles.com/index.aspx?uri=puzzle%2Fbattleships%2Frules |
| Tents | 每棵树配一个帐篷，帐篷不相邻，行列计数 | 哪棵树配哪个帐篷、行列剩余 | Janko/Nikoli |
| Star Battle | 每行/列/区域固定星数，星不相邻 | 某格能否放星、区域星数 | GMPuzzles/Janko |
| Minesweeper | 数字表示邻域雷数 | 某格是否雷、周围雷数、下一步安全格 | 通用规则，可自实现 |
| Skyscrapers | 行列排列数字，边缘线索表示可见楼数 | 某格高度、从某方向可见几个 | Nikoli/Janko |

### 4.4 数值约束类

| 类型 | 核心规则 | VQA 方向 | 来源 |
| --- | --- | --- | --- |
| Kakuro | 横竖连续白格和等于线索，数字不重复 | 某格数字、某段和、候选排除 | Conceptis/Nikoli |
| Futoshiki | 拉丁方 + 大小不等式 | 某格数字、哪条不等式限制 | Nikoli/Janko |
| KenKen / Calcudoku | 拉丁方 + 区域运算结果 | 区域缺数、运算符、候选验证 | 通用规则 |
| Killer Sudoku | Sudoku + cage sum | cage 和、候选组合、某格值 | Nikoli/PuzzleMadness |

**规则来源入口**

- Nikoli puzzle list，每个 puzzle 页面有 basic rules：https://www.nikoli.com/en/puzzles/
- Janko puzzle catalog，覆盖大量 puzzle types 和规则页：https://www.janko.at/Raetsel/Uebersicht.htm
- Conceptis Battleships 规则示例：https://www.conceptispuzzles.com/index.aspx?uri=puzzle%2Fbattleships%2Frules
- GMPuzzles / The Art of Puzzles，适合作为 puzzle type 和规则变体索引：https://www.gmpuzzles.com/

---

## 5. 三维空间：折叠、视图、旋转、截面

**规则语法**

- 折纸/打孔：折叠序列、孔/切口坐标、展开后的对称复制。
- Cube net：面邻接、对面、边共享、折叠后朝向。
- 三视图/投影：给 front/top/right，问可能的 3D 体素结构或某方向视图。
- 心理旋转：同一 3D 物体经旋转 vs 镜像；可问是否相同、旋转角、候选图。
- 截面：平面切立方体/圆柱/多面体，问截面形状或边数。
- Block design：用双色/四色方块拼目标图，问最少块数、某块朝向、是否可拼。

**可做 VQA 模板**

- “纸展开后孔的位置在哪里？”
- “哪个立方体能由该展开图折成？”
- “从右侧看会得到哪个视图？”
- “A 和 B 是同一个物体旋转后得到的吗？”
- “这个切面是什么形状？”

**来源**

- Paper Folding Puzzles benchmark，面向折纸空间推理：https://ojs.aaai.org/index.php/AAAI/article/view/38364
- GamiBench，origami folding tasks，用于 2D-to-3D planning：https://arxiv.org/abs/2512.22207
- 3DSRBench，将空间推理分为 height/orientation/location/multi-object 等问题类型：https://arxiv.org/abs/2412.07825
- Mental rotation 任务常见规则：比较两个 3D 对象是否为旋转等价或镜像：https://en.wikipedia.org/wiki/Mental_rotation
- Block design 是空间可视化/拼装类任务，可改写成纯图像 VQA：https://en.wikipedia.org/wiki/Block_design_test

---

## 6. 图表和科学图规则

这类最适合低成本 scaling：直接用 `matplotlib` 生成图和底层表，再按模板出问答。

**规则语法**

- 图类型：vertical/horizontal bar、line、dot-line、pie、scatter、stacked bar、area。
- 单点读取：某类别值、某时间点值。
- 比较：最大/最小、A 是否大于 B、差值、比值、排名。
- 全局属性：median、range、trend、roughness、area under curve、交叉点、峰谷数量。
- 多步推理：先筛选再比较、跨系列差值、增长率、累计值。

**可做 VQA 模板**

- “哪个类别最大？”
- “A 和 B 的差是多少？”
- “哪条线在 x=5 后增长最快？”
- “两条曲线在哪里第一次相交？”
- “饼图中红色扇区占比是否超过蓝色两倍？”

**来源**

- FigureQA 使用 5 类常见图，并选了 15 类 relational question types，包括最大/最小、比较、median、roughness、AUC 等：https://www.microsoft.com/en-us/research/project/figureqa-dataset/
- DVQA 聚焦 bar chart QA，强调图内文字和答案随图变化：https://arxiv.org/abs/1801.08163
- PlotQA 包含 28.9M QA、224,377 plots，问题模板覆盖真实数值和复杂推理：https://iitmnlp.github.io/PlotQA/
- ChartQA 包含人工问题和增强问题，强调 chart 的视觉与逻辑推理：https://arxiv.org/abs/2203.10244

---

## 7. 机械推理和物理图

**规则语法**

- 齿轮：相邻啮合齿轮方向相反；奇偶个齿轮决定首尾方向；齿数决定角速度比。
- 皮带/链条：不交叉同向，交叉反向。
- 滑轮：支撑绳段数决定机械优势；固定滑轮只改变方向。
- 杠杆/天平：力矩平衡，`weight * distance` 相等。
- 液压：面积比放大力。
- 电路：串并联、开关通断、灯泡亮灭。

**可做 VQA 模板**

- “最后一个齿轮顺时针还是逆时针？”
- “哪个滑轮系统最省力？”
- “为了平衡杠杆，砝码应挂在哪个位置？”
- “闭合哪个开关会点亮灯泡 A？”

**来源**

- Mechanical reasoning tests 通常覆盖方向、速度、相对质量等物理/机械系统推理：https://www.iqtests.org/deductive-reasoning-tests/mechanical-deductive-reasoning
- 齿轮/皮带常见规则总结：https://www.jobtestprep.co.uk/mechanical-reasoning-study-guide
- Bennett Mechanical Comprehension Test 题型覆盖 pulleys/levers/gears/hydraulics/forces/electricity 等：https://www.practiceaptitudetests.com/bennett-mechanical-comprehension-tests/
- LogicVista 也把 mechanical reasoning 作为 visual logical reasoning 的一个能力项：https://logicvista.github.io/
- Probing Mechanical Reasoning in Large Vision Language Models 直接包含 gears/pulley/leverage/fluid mechanics 等认知实验题型：https://arxiv.org/abs/2410.00318

---

## 8. Matchstick / 七段数码管 / Figure Weights

### 8.1 Matchstick

**规则语法**

- 数字用七段数码管或火柴棍表示。
- 操作：移动/添加/删除 1-2 根。
- 目标：让等式成立，或让几何形状数量改变。
- 验证：枚举所有可达状态，检查算式或几何约束。

**来源**

- MathSticks benchmark：错误火柴等式，移动一根或两根，在守恒规则下修正等式：https://arxiv.org/abs/2510.00483
- Matchstick puzzle 常见形式包括 Roman numerals 或 seven-segment display 数字：https://en.wikipedia.org/wiki/Matchstick_puzzle
- iMatchstick 可作为规则和状态空间参考，不必复用其 solver：https://mario.studio/iMatchstick/

### 8.2 Figure Weights / Balance Scale

**规则语法**

- 每种图形代表未知重量。
- 天平平衡表示线性等式，不平衡表示不等式。
- 问候选图形组合哪个能平衡、某图形重量、哪个更重。

**可做 VQA 模板**

- “哪一个选项能让右侧天平平衡？”
- “一个三角形等于几个圆？”
- “哪个物体更重？”

**来源**

- Figure Weights 类任务常被描述为通过视觉等式推断数量关系和 balance rules：https://www.reddit.com/r/AutismTranslated/comments/1rkp2ns/balancing_scales_test_during_assessment/

---

## 9. 几何类比和符号映射

**规则语法**

- A:B::C:?。
- 变换：平移、旋转、镜像、缩放、颜色替换、纹理替换、对象增删、层级包含变化。
- 结构映射：对象对应、关系对应、二阶关系，即 “A 到 B 的变化” 迁移到 C。
- 难度控制：单变换、多变换、变换顺序、干扰项相似度。

**可做 VQA 模板**

- “A 到 B 的变化应用到 C 后得到哪个图？”
- “哪一个候选和上方类比关系一致？”
- “图形 C 应该如何变化？”

**来源**

- Geometric analogy 研究常用多个候选项，并分析元素数量、变换数量对难度的影响：https://www.sciencedirect.com/science/article/pii/0160289684900096
- Lovett 等使用结构映射解决 geometric analogy problems，可作为符号化规则参考：https://pubmed.ncbi.nlm.nih.gov/21585502/
- Novick & Tversky 关于多变换几何类比中操作顺序的研究：https://www.tc.columbia.edu/faculty/bt2158/faculty-profile/files/orderingoperations_Thecaseofgeometricanalogies.pdf

---

## 10. Tangram / 拼装 / 多边形组合

**规则语法**

- 基元：三角形、正方形、平行四边形等多边形。
- 操作：平移、旋转、镜像、贴边、无重叠覆盖。
- 问题：能否覆盖目标轮廓、缺哪块、某块位置、面积/边界关系。
- 验证：用 exact polygon / grid rasterization 判断覆盖、重叠和边界一致。

**来源**

- TangramPuzzle 提出 Tangram Construction Expression，用精确坐标规格来降低视觉近似歧义：https://arxiv.org/abs/2601.16520
- Tangram benchmark 用于几何元素识别和视觉数学推理：https://arxiv.org/abs/2408.13854

---

## 11. 建议的落地顺序

1. `P0-RPM`：最快起量，和当前 `规律补全` 直接对齐。
2. `P0-Bongard`：补 `六图分类`，可大量生成概念归纳题。
3. `P0-Pencil`：优先挑 6-8 个规则最清楚的：Hashi、Battleships、Nurikabe、Akari、Skyscrapers、Shikaku、Slitherlink、Minesweeper。
4. `P0-Spatial`：先做 2D 折纸打孔、cube net、三视图体素，再做复杂 3D 渲染。
5. `P1-Chart`：作为低成本高规模补充，先做 bar/line/pie 的比较和数值推理。
6. `P1-Mechanical`：先做齿轮、皮带、杠杆、天平，避免一开始做真实物理仿真。
7. `P1-Matchstick/FigureWeights`：状态空间小，适合做可验证符号视觉题。

---

## 12. 不建议直接做的来源

- 直接抓 IQ/RPM 官方题、商业 aptitude test 题：版权风险高。只用公开论文/规则描述抽象规则。
- 直接抓 Nikoli/GMPuzzles/Janko 的具体题面：可以参考规则，不建议批量复制专家题。
- 已有完整 generator 的 benchmark：这次目标是搜集规则，不优先复用，例如 RAVEN/Bongard-LOGO/Reasoning Gym/Simon Tatham 等已有生成器体系。

