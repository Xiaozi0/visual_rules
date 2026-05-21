# Datasets Rule Summary

这个文档只做一件事：把 `datasets/` 里的三份数据源压成便于派任务的 rule/domain 摘要。

不追求学术定义，只按“是否像同一类 generator 工作”来整理。

---

## 1. VisuLogic-Train

路径：`datasets/VisuLogic-Train/visulogic_train_solution.jsonl`

说明：

- 文件里没有显式 `domain/subcategory` 字段
- 以下是根据 `question + solution` 归纳出来的可用 domain
- 这份数据最适合优先派任务，因为重复模板很多

### V1. 规律补全

- 含义：根据图形序列或矩阵中的变化规律，补全问号位置
- 代表题型：`id=00000`
- 常见规则：旋转、平移、黑白交替、数量变化、位置变化
- 是否高频：是
- 是否与其他数据集重合：是，和 `VisualPuzzles` 的 `inductive`、SMART 的 `pattern` 有重合

### V2. 六图分类

- 含义：把 6 个图形按共同属性分成两组
- 代表题型：`id=00005`
- 常见规则：对称性、面积比例、开闭性、黑白面积、线段数、闭合区域数
- 是否高频：是
- 是否与其他数据集重合：是，和 `VisualPuzzles` 的一部分 `inductive` 重合

### V3. 三维折叠与展开

- 含义：二维展开图与三维立体之间互相对应
- 代表题型：`id=00009`
- 常见规则：相邻面、对面、朝向、折叠后面关系
- 是否高频：中高
- 是否与其他数据集重合：是，和 `VisualPuzzles spatial`、`SMART spatial` 重合

### V4. 三维视图与投影

- 含义：判断某个三维物体从某方向看会得到什么视图，或哪个视图不可能
- 代表题型：`id=00013`
- 常见规则：前后左右视图、遮挡、可见面、投影一致性
- 是否高频：中
- 是否与其他数据集重合：是，和 `VisualPuzzles spatial`、`SMART spatial` 重合

### V5. 截面与切割

- 含义：判断立体被切开后的截面，或根据切割关系反推结构
- 代表题型：`id=00007`
- 常见规则：切面形状、顶点穿过关系、空洞结构、切后组合关系
- 是否高频：中
- 是否与其他数据集重合：是，和 `VisualPuzzles spatial/deductive` 重合

### V6. 空间拼装与折纸裁切

- 含义：若干部件能否拼成立体，或者折纸、裁切后展开会得到什么
- 代表题型：`id=00039`, `id=00069`
- 常见规则：部件配准、体块守恒、折叠后裁切、展开还原
- 是否高频：中低
- 是否与其他数据集重合：部分重合，主要和 `SMART spatial`、`VisualPuzzles deductive/spatial` 重合

### VisuLogic 派工建议

- 第一组：`V1 规律补全`
- 第二组：`V2 六图分类`
- 第三组：`V3/V4/V5/V6` 三维空间相关题一起处理

---

## 2. VisualPuzzles

路径：`datasets/VisualPuzzles/visualpuzzles_data.jsonl`

说明：

- 这份数据自带 5 个 category
- 但它们更像 benchmark 的“推理方式标签”，不完全等于 generator 的 rule family
- 派任务时建议做一层转译

### P1. inductive

- 代表题型：`id=1`
- 典型形式：六图分类、图形规律发现
- 更适合转成的任务类型：
  - 图形规律补全
  - 六图分类
- 与其他数据集重合：和 `VisuLogic V1/V2` 高度重合

### P2. spatial

- 代表题型：`id=3`
- 典型形式：迷宫、立体、折叠、视图、可见性
- 更适合转成的任务类型：
  - 路径/迷宫
  - 三维折叠与展开
  - 三维视图与投影
  - 截面/空间结构
- 与其他数据集重合：和 `VisuLogic V3/V4/V5/V6`、`SMART spatial/path` 重合

### P3. deductive

- 代表题型：`id=4`
- 典型形式：积木组合、编码映射、叠片/逻辑约束
- 更适合转成的任务类型：
  - 空间拼装
  - 显式规则推断
  - 编码/映射
- 与其他数据集重合：和 `VisuLogic` 的空间拼装类、`SMART logic/algebra` 部分重合

### P4. analogical

- 代表题型：`id=6`
- 典型形式：类比关系、图形或符号映射迁移
- 更适合转成的任务类型：
  - 类比映射
  - 符号/图形变换迁移
- 与其他数据集重合：和 `SMART algebra/logic` 有部分重合

### P5. algorithmic

- 代表题型：`id=9`
- 典型形式：长度比较、路径收益、数值条件、局部搜索
- 更适合转成的任务类型：
  - 路径/搜索
  - 计数/测量
  - 条件优化
- 与其他数据集重合：和 `SMART counting/math/measure/path` 重合较多

### VisualPuzzles 派工建议

- 不建议按原始 5 个标签直接派
- 建议转成这 4 个工作包：
  - `规律与分类`
  - `三维空间`
  - `路径与计量`
  - `类比与规则映射`

---

## 3. SMART-101

路径：`datasets/smart/SMART101-release-v1/puzzle_type_info.csv`

说明：

- 这份数据自带 9 个 `type`
- 它已经比 VisualPuzzles 更接近规则类型
- 适合直接按类型归并，再看和其他数据集是否重复

### S1. path

- 代表题型：`puzzle_id=1`
- 含义：路径追踪、连通关系、顺着连接找目标
- 与其他数据集重合：和 `VisualPuzzles spatial/algorithmic` 重合

### S2. counting

- 代表题型：`puzzle_id=2`
- 含义：按形状、边数、对象种类做计数
- 与其他数据集重合：和 `VisualPuzzles algorithmic` 部分重合

### S3. math

- 代表题型：`puzzle_id=6`
- 含义：数值关系、算式约束、候选数填充
- 与其他数据集重合：和 `VisualPuzzles algorithmic` 部分重合

### S4. algebra

- 代表题型：`puzzle_id=7`
- 含义：交换规则、比例关系、变量式推断
- 与其他数据集重合：和 `VisualPuzzles analogical/deductive` 部分重合

### S5. spatial

- 代表题型：`puzzle_id=17`
- 含义：折纸、切割、空间结构、视图
- 与其他数据集重合：和 `VisuLogic V3/V4/V5/V6` 高度重合

### S6. order

- 代表题型：`puzzle_id=18`
- 含义：顺序恢复、堆叠顺序、先后约束
- 与其他数据集重合：和 `VisualPuzzles deductive`、部分 `logic` 类题重合

### S7. measure

- 代表题型：`puzzle_id=20`
- 含义：长度、面积、尺寸测量
- 与其他数据集重合：和 `VisualPuzzles algorithmic` 部分重合

### S8. logic

- 代表题型：`puzzle_id=40`
- 含义：条件排除、最少补全、唯一可行结构
- 与其他数据集重合：和 `VisualPuzzles deductive` 重合

### S9. pattern

- 代表题型：`puzzle_id=77`
- 含义：颜色反转、局部图形规律、模式匹配
- 与其他数据集重合：和 `VisuLogic V1`、`VisualPuzzles inductive` 高度重合

### SMART 派工建议

- 第一组：`pattern + logic + order`
- 第二组：`spatial`
- 第三组：`counting + math + measure`
- 第四组：`path`
- 第五组：`algebra`

---

## 4. 合并后的派工视角

如果你的目标是“避免多人抽到其实相同的题型”，那三份数据可以先合成下面 5 个总工作包：

### G1. 规律补全

- 来源：
  - VisuLogic `V1`
  - VisualPuzzles `inductive` 的一部分
  - SMART `pattern`

### G2. 六图分类

- 来源：
  - VisuLogic `V2`
  - VisualPuzzles `inductive` 的一部分

### G3. 三维空间

- 来源：
  - VisuLogic `V3/V4/V5/V6`
  - VisualPuzzles `spatial` 和部分 `deductive`
  - SMART `spatial`

### G4. 路径与计量

- 来源：
  - VisualPuzzles `algorithmic/spatial`
  - SMART `path/counting/math/measure`

### G5. 类比与逻辑映射

- 来源：
  - VisualPuzzles `analogical/deductive`
  - SMART `algebra/logic/order`

---

## 5. 最短建议

如果你现在就要派任务，可以直接这样分：

1. 一个人负责 `规律补全`
2. 一个人负责 `六图分类`
3. 一个人负责 `三维空间`
4. 一个人负责 `路径与计量`
5. 一个人负责 `类比与逻辑映射`

这样比按论文分更不容易重复。
