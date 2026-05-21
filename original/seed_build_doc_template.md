# Seed Build Doc Template

这个文档用于记录单个 `seed` 的规则抽象、验证方式、数据构造方案和实现进度。

目标不是一次写得很完整，而是保证后面继续做 generator、render、question template、批量生成时，不需要重新猜这条 seed 当时是怎么想的。

建议每个 seed 单独一个文档，文件名使用：

- `<seed_id>.md`

例如：

- `graph_isomorphism.md`
- `lights_out.md`
- `hex_connectivity.md`

主表里建议只存摘要字段，并额外记录：

- `doc_path`

---

## 推荐的主表最小字段

主表可以是 CSV / JSONL / Markdown 表格，建议至少包含：

- `seed_id`
- `name`
- `turn_type`
- `category`
- `rule`
- `difficulty_vars`
- `question_types`
- `verifier`
- `build_type`
- `build_status`
- `sources`
- `doc_path`
- `status`
- `duplicate_of`
- `notes`

其中：

- `turn_type`: `single_turn` / `multi_turn`
- `category`: `algorithm` / `arc` / `cognition` / `geometry` / `graphs` / `logic` / `puzzles` / `games` / `spatial` / `temporal`
- `build_type`: `upstream_generator` / `self_program` / `solver_based` / `llm_plus_verify` / `manual_pending`
- `build_status`: `not_started` / `drafted` / `implemented` / `verified` / `blocked`
- `status`: `candidate` / `canonical` / `done` / `drop`

---

## 单个 Seed 文档模板

下面这个模板用于记录单个 seed 的完整构造信息。

```md
# <seed_id>

## 1. Basic Info

- seed_id:
- name:
- turn_type:
- category:
- status:
- build_type:
- build_status:
- doc_owner:

## 2. Rule

### 2.1 Core rule
- 用一句话说明这个 seed 的核心规则。

### 2.2 Typical VQA forms
- 
- 
- 

### 2.3 Difficulty variables
- `<var_name>`: `<meaning>`
- `<var_name>`: `<meaning>`
- `<var_name>`: `<meaning>`

## 3. Sources

- `<source name>`: `<url>`
- `<source name>`: `<url>`

## 4. Verifier

### 4.1 Verification idea
- 一句话说明如何自动验证答案。

### 4.2 Verification method
- 类型:
- 具体方法:
  - 
  - 

### 4.3 Answer format
- boolean / count / choice / path / state / numeric / other

## 5. Build Plan

### 5.1 Build summary
- 一句话说明数据如何构造。

### 5.2 Instance construction pipeline
1. 
2. 
3. 
4. 
5. 
6. 

### 5.3 Rendering plan
- image form:
- key visual elements:
- options needed:
- output layout:

### 5.4 Question generation plan
- question templates:
  - 
  - 
- distractor plan:
  - 
  - 

## 6. Program Design

### 6.1 Input spec
- seed
- 
- 

### 6.2 Output spec
- image
- question
- answer
- metadata
- verification_trace

### 6.3 Metadata suggestion
- seed_id
- instance_id
- random_seed
- difficulty
- question_type
- answer
- source
- build_version

## 7. Risks

- visual ambiguity:
- multiple-solution risk:
- verifier edge cases:
- duplicate risk:

## 8. Dedup Note

- suspected_duplicate_of:
- difference_from_similar_seeds:
  - 
  - 

## 9. Implementation TODO

- [ ] abstract rule
- [ ] confirm difficulty vars
- [ ] confirm verifier
- [ ] design renderer
- [ ] design question templates
- [ ] write generator
- [ ] manual sample review
- [ ] automatic verification
- [ ] connect to main data format

## 10. Notes

- 
```

---

## 填写原则

### 1. 先短后长

第一次写时，只要先写清下面 6 件事：

- 规则是什么
- 属于哪个 category
- 难度变量是什么
- 怎么验证
- 怎么构造
- 来源是什么

其余内容可以后补。

### 2. 规则和构造要分开写

不要把：

- “这个任务在考什么”

和

- “这个任务怎么生成数据”

混在一起。

前者写在：

- `Core rule`

后者写在：

- `Build summary`
- `Instance construction pipeline`

### 3. 如果只是来源新增，不要重复建 seed

如果一个新来源只是和现有 seed 规则相同：

- 不新建 seed
- 只把来源补到已有 seed 的 `Sources`
- 或在主表中更新 `sources`

### 4. 如果生成方案变了，要补 build 信息

同一个 seed 可以有不同构造方案，但至少要在文档里记清：

- 当前采用哪一种
- 为什么这样做
- 是否已经实现

---

## 一个简短示例

```md
# graph_isomorphism

## 1. Basic Info

- seed_id: graph_isomorphism
- name: Graph Isomorphism
- turn_type: single_turn
- category: graphs
- status: canonical
- build_type: self_program
- build_status: drafted
- doc_owner: zixiao

## 2. Rule

### 2.1 Core rule
- Determine whether two rendered graphs are structurally identical.

### 2.2 Typical VQA forms
- Are these two graphs isomorphic?
- Which candidate graph matches the source graph?

### 2.3 Difficulty variables
- num_nodes: graph size
- edge_density: graph connectivity complexity
- layout_distortion: visual layout variation

## 3. Sources

- TACIT: https://github.com/danielxmed/tacit-benchmark
- Gym-V: https://github.com/ModalMinds/gym-v

## 4. Verifier

### 4.1 Verification idea
- Use an exact graph isomorphism check.

### 4.2 Verification method
- 类型: exact algorithm
- 具体方法:
  - build adjacency structure
  - run isomorphism solver

### 4.3 Answer format
- boolean

## 5. Build Plan

### 5.1 Build summary
- Randomly generate a graph, permute node identities, render two layouts, and verify with graph isomorphism.

### 5.2 Instance construction pipeline
1. sample a valid graph
2. create positive or negative pair
3. assign two different layouts
4. render node-link diagrams
5. generate question
6. compute answer with verifier

## 10. Notes

- Need to avoid trivial visual cues from layout symmetry.
```

---

## 推荐目录结构

如果后面要正式使用，建议逐步整理成：

```text
source_data/
  original/
    03.数据汇总-0515.md
    seed_build_doc_template.md
    seed_build_docs/
      graph_isomorphism.md
      lights_out.md
      hex_connectivity.md
```

这样：

- `03.数据汇总-0515.md` 负责收集候选
- `seed_build_docs/` 负责管理单个 seed 的详细构造
- 主表负责摘要、检索、去重状态
