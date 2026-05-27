# VQA Seed 工作流

把 rules 变成可生成、可验证、可复用的 VQA seed。规则来源可以是图、图文规则、纯文本、源码、网页或已有数据表。

核心原则：

- 未经人工确认的 seed 不能标记为 `done`。
- 失败或有歧义的样例不能进入最终 JSONL。
- 优先做 `Build` 可控但 `Reasoning Max` 高的 seed。

关键文档：

- 查重与状态：`format_docs/SEED_INVENTORY.md`
- VQA 格式：`format_docs/VQA_DATA_FORMAT.md`
- 分类标签：`format_docs/classification.md`

## 1. 从 Rules 到 Seed

1. 记录来源路径或 URL。
2. 抽象最小规则：对象、状态变量、动作、状态转移、答案判定。
3. 查 `SEED_INVENTORY.md`，按名称、规则、推理类型、视觉类型查重。
4. 评估两个难度：
   - `Build`: 生成器和验证器实现复杂度，`low` / `medium` / `high`。
   - `Reasoning Max`: 可稳定生成的 VQA 推理难度上限，`low` / `medium` / `high` / `very_high`。
5. 如果只是换皮，在已有 seed 备注里加变体；如果需要新验证器或新推理核心，新增 seed。

## 2. 设计 VQA

每个题型必须满足：

- 图像可见：答案依赖的状态必须画出来，不能依赖隐藏变量。
- 规则清楚：题干说明必要规则，例如箭头、移动步长、碰撞规则。
- 答案唯一：不能多解，不能靠主观判断。
- 图像干净：图片里不要写题目、答案或解释性文字；
- 可验证：答案能从 `raw_state` 用 Python 重新算出。

提高推理难度的手段：

- 增加推理步数。
- 增加对象数量。
- 增加碰撞、阻挡、连锁、同时运动等交互。
- 组合多个判断，例如碰撞 + 最短路 + 时间优先级。
- 让候选答案接近，但不能产生歧义。

单条 VQA 的 `metadata.instance` 建议记录：

- `difficulty`
- `complexity_score`
- `reasoning_depth`
- `visual_load`

## 3. 生成器与输出

生成器放在：

```text
generator/<seed_id>_generator.py
```

第三方源码、规则快照或素材放在：

```text
vendor/<seed_id>/
```

输出目录：

```text
generated/<seed_id>/
  images/
  vis_scaling_simple_mm.jsonl
  rules.jsonl
  quality_report.json
  manifest.json
```

生成器至少记录：

- `VERSION`
- 来源路径或 URL
- 随机种子
- 规则版本
- 题型列表
- 自动验证器

输出格式必须符合 `VQA_DATA_FORMAT.md`，分类字段参考 `classification.md`。

## 4. 校验

自动校验至少包括：

- JSON / JSONL 可解析。
- 图片存在且可打开。
- 图片尺寸符合设计，优先正方形。
- `messages[0].answer == metadata.gt.answer`。
- 答案可由 `metadata.instance.raw_state` 重新计算。
- 答案唯一，无越界、初始冲突、遮挡和文字泄漏。

失败样例处理：

1. 定位问题属于规则、渲染、题干、验证器还是 metadata。
2. 修生成器，不手工改单条 JSON 掩盖问题。
3. 重新生成样例和 `quality_report.json`。
4. 重新人工确认。
5. 旧失败样例不能保留在最终 JSONL 中。

## 5. 人工确认与归档

先生成 2 条样例给人工确认。确认前：

- 可以写生成器和输出临时样例。
- 可以在 `SEED_INVENTORY.md` 登记为 `todo` 或 `blocked`。
- 不能标记为 `done`。
- 不能扩大生成数量。

人工确认通过后：

1. 更新 `SEED_INVENTORY.md`。
2. 状态改为 `done`。
3. 补全 `Build`、`Reasoning Max`、分类、来源、脚本/输出和备注。
4. 保留复现命令。

扩量只在 2 条样例通过后进行。

## 6. 生成流程

### 第一步
```text
要求：根据一直的规则进行 VQA 生成。VQA 格式参考 @format_docs/VQA_DATA_FORMAT.md，分类参考 @format_docs/classification.md。

需要处理的内容：把 @<rules_source> 里面的 <seed_name> 变成可以获得的 VQA，并生成 2 个 VQA 给我验证。

生成方式：
1. 首先抽象出题目的规则。
2. 先查 @format_docs/SEED_INVENTORY.md，判断是否重复，并评估 Build 与 Reasoning Max。
3. 分析如何生成视觉 VQA，图片尽量是正方形。
4. 设计如何渲染图像，图像要符合规则，不能把题目写上去。
5. @generator 放生成 VQA 的脚本。
6. @vendor 可以放原始源码、规则快照或第三方资料。
7. 输出要符合 @format_docs/VQA_DATA_FORMAT.md，并用 Python verifier 校验答案。
8. 生成后先不要归纳 seed，等我人工确认样例质量。
```

### 第二步：人工确认后

```text
这个数据可以。请把这个 seed 归纳到 @format_docs/SEED_INVENTORY.md，并提供以后复现生成的命令。
```

示例命令：

```bash
python3 generator/<seed_id>_generator.py --count 2 --seed 20260521 --out-dir generated/<seed_id>
python3 generator/<seed_id>_generator.py --count 1000 --seed 20260521 --out-dir generated/<seed_id>
```

