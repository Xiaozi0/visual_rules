## 数据说明
该代码仓库收集了有关vision reasoning 论文以及论文中数据taxonomy（分类）、设计原则、示例、子类别描述和统计分布，这是抽象“seed规则”的最佳来源。

并采用LLM将规则抽象化，然后通过LLM/代码scaling up，以生成更多的规则和数据。

## 文件结构
vendor/：包含了从论文中开源代码。
datasets/：包含了从论文中开源数据。
rules/：包含了从论文中抽象出的规则。
records/：包含了从论文中抽象出的规则的记录。
tmps/：暂时不用看

## 目前支持
### 数据/论文
- [VisuLogic](https://github.com/VisuLogic-Benchmark/VisuLogic-Train)（训练集 5000+ rules）  
Paper: [arXiv:2504.15279](https://arxiv.org/pdf/2504.15279.pdf).  
项目页: https://visulogic-benchmark.github.io/VisuLogic/  
核心规则：6大domains + 23 subcategories（Quantitative/Spatial/Positional/Attribute/Stylistic/Other）。论文中有分布图、具体子类示例（如数量增减、折叠展开、旋转平移、对称性、风格变换等）。强调视觉中心、难以语言化。

- [VisualPuzzles](https://github.com/neulab/VisualPuzzles)  (1168 diverse puzzles
)
Paper: [arXiv:2504.10342](https://arxiv.org/pdf/2504.10342.pdf)   
核心规则：5大reasoning categories（Algorithmic / Analogical / Deductive / Inductive / Spatial），每类有Easy/Medium/Hard难度标注。大量来自公务员考试逻辑题视觉化翻译。设计原则：最小化领域知识，只用图像+问题+常识。

这里的题目比较复杂，有些是human场景的，有一些没有问答形式，比较适合视觉推理的多样性和复杂性研究。

- [SMART](https://github.com/merlresearch/SMART) (101 rules)  
Paper: arXiv:2212.09993  
核心规则：101个独特root puzzles，每个可程序化augment到~2000实例。混合8类基础技能（计数、算术、逻辑、代数、空间、模式、路径、测量）。每个puzzle有核心算法 + 参数化变体（外观、问题表述、答案）。

