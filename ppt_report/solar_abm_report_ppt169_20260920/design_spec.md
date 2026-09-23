<!-- ppt-master-schema: design-spec/v1 -->
# 德国光伏政策组合 ABM 复现与 LLM 增强 - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | 德国光伏政策组合 ABM：复现与 LLM 增强汇报 |
| Canvas Format | PPT 16:9 (1280×720) |
| Page Count | 14 |
| Primary Language | zh-CN |
| Target Audience | 课题组内部与导师/评审：已了解论文与「复现 + LLM 增强」的总目标，关心复现忠诚度、结果是否可信、剩余风险 |
| Communication Intent | 先讲清系统怎么搭、复现到什么程度、LLM 接在哪里；再用结果证明主线成立；然后主动暴露两处已知偏差与根因；最后对齐下一步优先级与投入（汇报与问责在前，决策对齐在后） |
| Desired Audience Outcome | 听完能独立判断「哪部分结论可信、哪部分是已知偏差」，并就对下一步做校准、扩主体规模还是接成熟 Agent 框架形成一致意见 |
| Core Message / Ask / Action | 论文的两阶段采用 + 双因子经验曲线主线已忠实落地，LLM 增强也端到端跑通；政策—扩散—降本的整体形态与文献一致（组件成本 26 年降约 86%），但绝对量级与国外成本存在两处已定位、可解释的偏差 |
| Delivery Context | 主要：演讲者主导的 15–20 分钟进度汇报（现场或线上，可现场演示代码与结果图）；次要：会后作为可自行阅读的存档材料，需要不依赖讲解也能看懂关键结论 |
| Artifact Afterlife | 项目进度存档与下一阶段任务对齐的依据；后续可复用于向导师/评审复述结论，也可作为论文或结题材料的素材来源 |
| Reading Mode | balanced |
| Content Strategy | balanced default：可重组叙事与页面结构，事实、数字与结论不越出仓库内记录（请读我.txt、系统说明.md、model_specification.md、测试记录.txt、analysis/metrics.py 输出） |
| Design Style | 证据型编辑设计：briefing 式中立叙述 + pyramid 式收尾，editorial × data-journalism 的版式与数据纪律 |
| Formula Policy | text-only |
| AI Image Acquisition Path | not applicable |
| Generation Mode | continuous |
| Spec Refinement | disabled |
| Speaker Notes | enabled — workflow default (proactive speaker notes true) |
| Custom Animations | disabled — workflow default (proactive custom animations false) |
| Narration Audio | disabled — workflow default (proactive narration audio false) |
| Created Date | 2026-09-20 |

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Format | PPT 16:9 |
| Dimensions | 1280 × 720 |
| viewBox | `0 0 1280 720` |
| Margins | 上 56 / 下 56 / 左右 72 |
| Content Area | 1136 × 608 |

## III. Visual Theme

### Theme Style

- **Mode**: custom
- **Mode References**: briefing, pyramid
- **Mode Behavior**: 主体采用 briefing 的中立叙述——主题式标题、同级条目等重、按"项目/系统/机制/接入/结果/偏差/进度/下一步"分区，方便会后浏览与检索；末三页切换到 pyramid 的结论先行：先给"两处偏差已定位、优先级建议是校准"，再展开证据与取舍，收束到一次明确的优先级选择。
- **Visual style**: custom
- **Visual Style References**: editorial, data-journalism
- **Visual style Behavior**: 以 editorial 的杂志式层级为主干——细线分隔代替卡片、非对称分栏、页眉 kicker + 主张式标题 + 引言层级的字号梯度，圆角近乎为零、阴影仅在真有浮动元素时出现；数据页吸收 data-journalism 的多栏微图与脚注纪律：每个数字都带单位与来源行，表格与图表紧贴其解读文字而不是居中孤立，空白用于分栏节奏而非装饰。
- **Theme**: 纸面研究报告——暖白纸底、深墨蓝主色、砖红作唯一强调色，青绿只用于第二数据系列
- **Tone**: 克制、可核对、不辩护；把"已知偏差"当作资产而非软肋

### Color Scheme

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #F7F5F0 | 页面底色，暖白纸面 |
| Secondary background | #EDE8DF | 表头、参数区、KPI 块的浅底 |
| Primary | #16233A | 标题、正文强调、图表主线、深色分区块 |
| Accent | #C0562B | 唯一强调色：关键数字、结论线、当前状态标记；呼应光伏的暖色 |
| Secondary accent | #2E6F6A | 第二数据系列（国外/对照）、次级标记 |
| Body text | #35322C | 正文文字，与底色对比度 > 10:1 |

## IV. Typography System

### Font Plan

| Role | Character (Reference) | Primary | English if non-English | Fallback tail |
| --- | --- | --- | --- | --- |
| Title | 无衬线黑体，稳重无装饰 | Microsoft YaHei | Georgia | Microsoft YaHei, Georgia, serif |
| Body | 同族无衬线，字面清晰 | Microsoft YaHei | Segoe UI | Microsoft YaHei, Segoe UI, sans-serif |
| Data | 等宽数字，便于对齐与核对 | Consolas | Consolas | Consolas, Microsoft YaHei, monospace |

- **Role rationale**: 增加 Data 角色，用于 KPI 数字、参数表、检查点与代码片段——本套 14 页中数字密集且需要纵向对齐，等宽数字可显著提升可核对性。
- **Title stack**: `Georgia, "Microsoft YaHei", "PingFang SC", serif`
- **Body stack**: `"Microsoft YaHei", "Segoe UI", system-ui, sans-serif`
- **Data stack**: `Consolas, "Microsoft YaHei", monospace`

### Font Size Hierarchy

| Purpose | Anchor Size (px) |
| --- | ---: |
| Body | 24 |
| Title | 42 |
| Subtitle | 32 |
| Annotation | 18 |
| Footnote | 16 |
| Display | 64 |

## V. Layout Principles

### Page Structure

- **Header area**: 顶部 96px 内：左侧 kicker（章节/页码线索，Annotation 字号），其下为标题；标题与正文之间一条 hairline 规则（Primary 12% 不透明度）
- **Content area**: 中段自由分栏；数据页默认"图/表 + 解读文字"双栏，文字栏不少于 380px，图表不居中孤立
- **Footer area**: 底部 40px 内：左侧来源/口径说明，右侧页码，均为 Footnote 字号，Primary 60% 不透明度

### Spacing Specification

| Element | Current Project |
| --- | --- |
| Safe margin | 72px |
| Content block gap | 32px |
| Icon-text gap | 12px |

## VI. Icon Usage Specification

- **Primary bundled library**: tabler-outline
- **Stroke Width**: 2

| Icon Path | Suitable Scenarios |
| --- | --- |
| tabler-outline/sun | 光伏主题、封面与章节标记 |
| tabler-outline/target | 目标、采用决策阈值 |
| tabler-outline/route | 五步调度、流程顺序 |
| tabler-outline/binary-tree | 两阶段决策、分叉逻辑 |
| tabler-outline/users | 采用者主体与人群构成 |
| tabler-outline/building-factory | 制造商主体与产能 |
| tabler-outline/trending-down | 成本下降、经验曲线 |
| tabler-outline/chart-line | 结果图表、指标页 |
| tabler-outline/robot | LLM 主体决策 |
| tabler-outline/code | 代码结构、模块划分 |
| tabler-outline/database | 历史数据、知识存量 |
| tabler-outline/checklist | 测试与验证状态 |
| tabler-outline/alert-triangle | 已知偏差与风险 |
| tabler-outline/circle-check | 已完成项、通过项 |
| tabler-outline/clock | 时间步、运行耗时 |
| tabler-outline/file-text | 文档、记录、来源 |

## VII. Visualization Reference List

| Page | Family | Template | Usage |
| --- | --- | --- | --- |
| P07 | table | templates/tables/metric_table.svg | 经验曲线参数对照（截距与两个 β 斜率、对应学习率） |
| P11 | table | templates/tables/metric_table.svg | 结果关键指标与年度采用检查点 |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| results.png | 1800×1200 | 1.50 (3:2) | 仿真结果四联图：累计装机、组件成本、累计采用者、政策与价格信号 | Chart screenshot | 整幅横置于页面左侧 62% 宽度，右侧 38% 放四条解读；图下留一行运行条件脚注 | no-crop | user | Existing | 项目 312-tick 公式模式运行输出（seed=42，合成数据），位于仓库根目录 results.png | n/a | local |

## IX. Content Outline

### Part 1: 项目与系统

#### Slide 01 - 封面

- **Audience move**: 只知道"在复现一篇论文" → 立刻抓住"复现已落地、LLM 已接入、两处偏差已定位"三件事
- **Layout**: editorial 首屏：左侧 58% 放标题组（kicker + 主标题 + 副标题），右侧 42% 放三个纵向排列的超大数字，数字下各一行小注；页面下缘一条贯穿全宽的 hairline 规则，规则下方是仓库名与日期
- **Title**: 德国光伏政策组合 ABM：复现与 LLM 增强
- **Core message**: 论文模型已复现到可运行、可验证，LLM 增强已端到端跑通，两处偏差已被定位
- **Content**: kicker "进度汇报 / 2026-09"；主标题如上；副标题"复现 Nuñez-Jimenez et al. (2022) 德国 1991–2016 光伏政策组合模型，并让制造商与采用者的决策接入 LLM"；三个钩子数字（Data 字体）：`50/500` 累计采用、`0.6 MW` 累计装机、`−85.9%` 国内组件成本降幅，小注分别为"10%，真实约 7%""1:1000 缩比下的量级""2.833 → 0.399 €/W"；下缘：`solar-abm-replication` · 2026-09-20
- **Native shape suggestion**: hairline 贯穿线用单条直线；三个数字块用无边框文本分组，不加卡片底

#### Slide 02 - 汇报结构

- **Audience move**: 不知道接下来会听到什么 → 清楚 14 页的三段结构与时间分配
- **Layout**: 左侧竖向编号列表（五个分组，编号用 Data 字体），右侧 45% 留白只放一句话导语；不用卡片网格
- **Title**: 汇报结构
- **Core message**: 全部内容分五段：系统怎么搭 → 机制是什么 → LLM 接在哪里 → 结果说了什么 → 偏差与下一步
- **Content**: 01 项目与系统（P03–P05，约 4 分钟）｜02 复现的三个核心机制（P06–P08，约 5 分钟）｜03 LLM 增强接在哪里（P09，约 2 分钟）｜04 结果与验证（P10–P11，约 4 分钟）｜05 偏差、进度与下一步（P12–P14，约 4 分钟）。右侧导语："前两段讲我们造了什么，后三段讲它算出了什么、哪里还不能信、下一步做什么。"

#### Slide 03 - 背景：论文问题与两条主线

- **Audience move**: 记得"要复现论文"但不确定边界 → 明确论文的问题、复现范围与第二条增量主线
- **Layout**: 上三分之一放问题陈述（大字号一段话），下三分之二左右分栏：左栏"主线一 · 模型复现"，右栏"主线二 · LLM 增强"，两栏之间一条竖向 hairline；每栏顶部一个图标（sun / robot）
- **Title**: 论文问的是政策组合怎么推动扩散；我们做的是复现，再加一层 LLM
- **Core message**: 复现是可信度基线，LLM 增强是增量实验
- **Content**: 问题陈述："技术推动（政府研发投入）与需求拉动（上网电价补贴 FiT）如何共同塑造德国光伏 1991–2016 的扩散轨迹。" 左栏：复现 Nuñez-Jimenez et al., 2022, *Research Policy* 的补充材料模型；三类主体（采用者/制造商/安装商）+ 宏观观察者；312 个月；进度 **~95%**。右栏：让制造商与采用者的决策改由 LLM 完成；带记忆、工具调用与结构化校验；失败自动回退公式；进度 **~75%**。

#### Slide 04 - 系统架构：四类角色

- **Audience move**: 知道有"三类主体"但说不清各自职责 → 能说出每个角色做什么、有多少、彼此怎么相连
- **Layout**: 左侧 62% 为中心式架构图（native SVG）：中间"宏观环境"横条在上方提供外生信号，下方三个主体区块（采用者 / 安装商 / 制造商）以箭头串成需求—交付—降本回路，国内与国外用颜色区分；右侧 38% 逐行列出数量与关键参数
- **Title**: 四类角色，每个月走一遍同样的循环
- **Core message**: 采用者产生需求、安装商消化订单、制造商降本，宏观环境给出外生信号
- **Content**: 架构图节点与箭头：宏观环境（电价 / FiT / 媒体关注 / 研发强度 / 全球累计装机）→ 采用者；采用者（500 个，按 1:1000 缩比）产生需求 → 安装队列；安装商（国内 / 国外各 1）按产能交付并回馈 BOS 成本；制造商（国内 / 国外各 1）依据累计产量与知识存量降本，并把新价格回馈给采用者；国内与国外制造商之间有知识溢出箭头。右侧要点：采用者构成 住宅 81% / 工商业 18.5% / 电站 0.5%；系统规模按屋顶面积 × 0.15 kWp/m² 生成；制造商与安装商的主要参数（截距、β 斜率、加成率）全部来自论文 SI 表格。

#### Slide 05 - 五步调度

- **Audience move**: 不知道一个月里谁先谁后 → 记住固定的五步顺序及其因果
- **Layout**: 横向五段流程条贯穿页面中部（每段一个编号 + 名称 + 一行说明），段间用箭头连接；页面上方一条时间轴标注 1991 → 2016；下方一行脚注说明"顺序不可颠倒"的依据
- **Title**: 每个 tick（= 1 个月）严格按五步执行
- **Core message**: 顺序不可颠倒：宏观 → 采用者 → 安装商 → 制造商 → 推进
- **Content**: ① 更新宏观变量（读取当月电价、FiT、媒体关注度、研发强度、全球累计装机）；② 采用者决策（未安装者评估是否安装，产生新需求进入安装队列）；③ 安装商响应（按产能消化订单，调整用工与非组件成本）；④ 制造商技术更新（结算累计产量、更新知识存量、按经验曲线更新成本）；⑤ 时钟推进（记录装机量、就业、价格）。脚注：调度顺序按论文补充材料 §1.1.5 实现于 `model/solar_model.py`。

### Part 2: 复现的三个核心机制

#### Slide 06 - 采用决策：两阶段

- **Audience move**: 以为采用是一个公式算出来的 → 理解"先萌生念头、再算经济账"的两阶段结构
- **Layout**: 上下两阶段流程图。上段"阶段一 · 萌生念头"：一条加权求和式 + 一条 0.5 阈值标尺；下段"阶段二 · 经济与环境评估"：从阈值处分叉成两条路径（早期采用者直装 / 双 NPV 比较），右侧窄栏放阈值与溢价说明
- **Title**: 采用不是一次判断，而是两阶段
- **Core message**: 阶段一的门槛决定"想不想装"，阶段二的 NPV 决定"装不装、买谁的组件"
- **Content**: 阶段一（Eq. 2）`0.19·PE + 0.17·IN + 0.52·AW + 0.12·IRR > 0.5`；PE = 1 km 内已装邻居比例，IN = 当月光伏信息量，AW = 环境意识（N(0.5, 0.2)，赋值后恒定），IRR = 代表家庭内部收益率；权重来自 Table SI 11。阶段二：早期采用者（AW > 0.92 且为住宅用户）直接安装；其余主体分别计算国内与国外组件的 NPV，选择**非负且最大**者，平局偏好国内；国外组件额外承受 1.1% 折现溢价（Table SI 10）。右侧说明：IRR 由二分法求解；规模效应 SE = 1.1246 · S^−0.051；NPV 折现 20 年现金流，含自发自用省费、余电上网收入与运维成本。

#### Slide 07 - 成本演化：双因子经验曲线

- **Audience move**: 以为降本只靠规模化生产 → 理解"干中学"和"研究中学"是两个独立驱动
- **Layout**: 左栏 52% 放公式与一条示意折线（native SVG，展示成本随累计产量与知识存量双驱动下降的形态）；右栏 48% 放参数对照表（metric_table）
- **Title**: 组件成本由"干中学"与"研究中学"共同驱动
- **Core message**: 国内靠研发、国外靠规模，两条曲线因此明显分岔
- **Content**: 公式（大字居中）：`MC = α · (CP / CP₀)^β_LBD · (KS / KS₀)^β_LBR`；参数对照表：截距 α 国内 2.882 / 国外 2.448 / 非组件 3.354（€/W）；β_LBD 干中学 −0.074 / −0.448 / −0.155；β_LBR 研究中学 −0.814 / −0.074 / —；对应学习率 5.0% / 26.7% / 43.1% / 5.0% / 10.2%；学习率换算 `β = log₂(1 − LR)`；知识存量按永续盘存更新 `KS_t = (1 − δ)·KS_{t−1} + R&D_t`，δ ≈ 0.874%/月（≈10%/年）。脚注：参数取自论文 Table SI 53。
- **Visualization**: 示意折线为定性表达不计入数据图；参数表 `ec-params=yes`。**Native-ready**: `ec-params=yes`

#### Slide 08 - 渠道与劳动力

- **Audience move**: 认为安装环节只是执行末端 → 理解它如何形成负反馈、抑制过热
- **Layout**: 左侧 55% 为反馈回路图（native SVG 环形，三个节点：订单积压 / 用工规模 / BOS 报价，箭头带正负号）；右侧 45% 三条要点逐条展开
- **Title**: 安装商既是缓冲器，也是降温阀
- **Core message**: 订单积压推高用工与非组件成本，反过来抑制安装速度，形成自我降温
- **Content**: 要点一 订单队列：采用决策先进入待安装队列，再按安装商产能逐月消化，因此"决定装"与"实际装"之间存在时滞。要点二 用工调整：积压超过阈值就招人、低于阈值就裁员，且有就业下限。要点三 报价机制：BOS 成本随"积压 / 人手"比上升，安装商在供不应求时提价，形成负反馈。附注：非组件成本走单因子经验曲线，β = −0.155（学习率 10.2%）；实现于 `submodels/labor_market.py`。

### Part 3: LLM 增强

#### Slide 09 - LLM 接在哪里

- **Audience move**: 不确定 LLM 是否真的参与了决策 → 清楚接入点、能力清单与回退边界
- **Layout**: 左右两栏对照（制造商 / 采用者），每栏顶部图标 + 触发频率 + 输出字段；页面下缘一条横向"回退链"：LLM 调用 → 校验 → 失败则公式，用箭头串起
- **Title**: LLM 只接管两类主体的决策，且始终有公式兜底
- **Core message**: 制造商每月决策、采用者按 5% 抽样决策；任何失败都回退公式，仿真永不停摆
- **Content**: 左栏 制造商（每次 2 个，每月一次）：输出 `expand / maintain / reduce`、变动幅度（0–0.5）、研发方向（效率 / 降本 / 无），经 Pydantic 校验。右栏 采用者（每月从未决策者中随机抽 5%）：输出是否安装、置信度、主因（经济 / 环保 / 社会 / 政策）。共有能力：滚动 6 轮对话记忆；function calling 工具（市场行情、邻居采用率、静态回收期、自身产能与库存）；`asyncio.gather` 并发；最多 3 轮工具循环。回退链：网络错误 / 返回非 JSON / 校验失败 → 制造商退回经验曲线公式、采用者退回两阶段公式。附注：因 OpenAI 端点不可达改用 DeepSeek（deepseek-chat，OpenAI 兼容）；已修复"返回内容被散文与代码围栏包裹导致全部静默回退"的缺陷（`extract_json_object`），冒烟测试确认 0 回退。

### Part 4: 结果与验证

#### Slide 10 - 结果：四联图解读

- **Audience move**: 没看过运行结果 → 能读出"政策点燃 → 成本下降 → 补贴退坡后饱和"三条信息
- **Layout**: 左 62% 整幅放置 results.png（no-crop，按 3:2 原比例），右 38% 四条编号解读；图下方一行脚注写运行条件
- **Title**: 结果讲的是"政策点燃 → 成本下降 → 补贴退坡后饱和"
- **Core message**: 形态与文献叙事一致；绝对量级受缩比限制，不能直接对比真实装机
- **Content**: 图注：312 tick、seed=42、合成数据、公式模式。四条解读：① 左上 累计装机呈 S 形，1991–2000 几乎贴地，2004–2008 最陡，2008 年后走平，终点 0.6 MW；② 右上 组件生产成本 国内 2.833 → 0.399 €/W（−85.9%）、国外 2.444 → 0.084 €/W（−96.6%），2000 年后两条线明显分岔；③ 左下 累计采用者同样呈 S 形，终点 50/500 = 10%；④ 右下 FiT 2000 年上线（约 0.35），2004–2008 升到约 0.50，此后持续退坡，电价则从 0.14 缓升至 0.29 €/kWh。要点句："1991–1999 完全没有补贴，只有 6 户环境意识极高的住宅用户安装——采纳是被政策点燃的，不是自发的。"
- **Images**: results.png 整幅横置，不加裁切；右上角可用一条 accent 短规则指向"分岔点"，不覆盖图像内容

#### Slide 11 - 关键数字与年度检查点

- **Audience move**: 记得结论但记不住数字 → 拿到一份可核对、可复现的指标清单
- **Layout**: 上三分之一为四个 KPI 块（Secondary background 浅底，无边框），下三分之二左栏为年度检查点表（metric_table），右栏为累计采用的小折线示意 + 对照说明
- **Title**: 关键数字与年度检查点
- **Core message**: 采用 10%、成本降 86%、93 个测试通过——每一个都能复现
- **Content**: KPI 四块：`50 / 500` 累计采用户数（10%）｜`0.6 MW` 累计装机｜`−85.9%` 国内组件成本降幅｜`93` 单元测试通过。检查点表（年末累计采用户数）：1991 → 6；2000 → 8；2004 → 22；2008 → 50；2012 → 50；2016 → 50。右栏对照：真实德国住宅光伏采用率约 7%，本模型 10%，偏差约 3 个百分点，原因见下一页；运行开销：公式模式跑完 312 tick 约 12–15 秒（LLM 模式受 API 速率限制，需按 tick 节流）。
- **Visualization**: KPI 行与检查点表为文本网格，累计采用折线为值驱动小图。**Native-ready**: `result-kpis=yes; adoption-curve=yes`

### Part 5: 偏差、进度与下一步

#### Slide 12 - 两处已知偏差

- **Audience move**: 以为模型已经校准好了 → 明确哪两处数字不可信、根因是什么、修法是什么
- **Layout**: 左右两栏并列，每栏内统一的三段式（偏差 / 根因 / 修法），栏顶用 alert-triangle 图标 + 一行结论；页面下缘一条脚注链接到测试记录
- **Title**: 两处偏差已经定位，但都还没有修
- **Core message**: 采用率偏高源自缩比补偿；国外成本失真源自学习驱动量取错
- **Content**: 左栏 偏差一 · 采用率偏高：模型 10% vs 真实约 7%；根因：邻居半径用 10 km（论文为 1 km），是为 500 主体缩比做的补偿——1 km 半径下平均只有 0.16 个邻居，社会影响无法启动；修法：接入空间索引、把主体扩到 2 万后改回 1 km 并重新标定。右栏 偏差二 · 国外成本塌缩：模型 0.084 €/W vs 真实约 0.3 €/W；根因：学习驱动量用"全球累计装机"替代论文要求的"本区域累计产量"，且合成全球装机量级膨胀约 10 倍，叠加国外陡峭的干中学斜率（β = −0.448）后被放大；修法：修正全球装机量级，并为国外厂商引入外生区域产量序列。脚注：字面改回"自产累计产量"会反向失真（国外 2.24、国内 0.761 €/W），取舍分析见 `测试记录.txt` 第十三轮。

#### Slide 13 - 当前进度与验证状态

- **Audience move**: 不确定哪些部分可以依赖 → 明确每个模块的完成度与验证手段
- **Layout**: 左右分栏：左栏为两条主线的完成度（横向进度条 + 百分比），右栏为验证清单（circle-check 图标逐项）；页面下缘放一行"已知代码债"
- **Title**: 主线一到 95%，主线二到 75%，93 个测试兜底
- **Core message**: 复现部分已经可以依赖；LLM 部分可用，但覆盖范围仍然有限
- **Content**: 左栏 模型复现 ~95%：三类主体定义、五步调度、两阶段采用、双因子经验曲线、劳动力市场、宏观环境（合成 + 真实历史）、历史数据加载、分析可视化全部落地。主线二 LLM 接入 ~75%：DeepSeek 接线、工具调用、对话记忆、并发、Pydantic 校验、确定性回退全部工作。右栏验证清单：93 个单元测试通过（约 0.8 秒）；312 tick 公式模式跑通；DeepSeek 三项能力实测（基础对话 / JSON 输出 / function calling）；LLM 回退缺陷已修复并冒烟验证 0 回退。下缘代码债：`config.py` 参数中心尚未接入主流程（参数仍硬编码在 `model/solar_model.py`）；`submodels/tpb.py` 为早期单阶段版本，现仅测试引用。
- **Visualization**: 完成度条为定性表达，不计入数据图；清单为文本网格。**Native-ready**: `progress-checklist=yes`

#### Slide 14 - 下一步

- **Audience move**: 认同现状但对优先级没有共识 → 在三条路径中选出一个优先项
- **Layout**: 三列等宽并列（同一形状、同一权重），每列顶部路径字母 + 名称，中部两到三行说明，底部一行"代价 / 收益"；页面下缘一条 accent 规则承载建议结论
- **Title**: 下一步有三个候选，建议先做校准
- **Core message**: 先修国外成本口径与邻居半径，再谈扩规模与接框架
- **Content**: 路径 A · 模型校准（建议优先）：修正全球累计装机量级与国外学习驱动量；逐图逐表对比论文输出；把采用率拉回 ~7%。代价低、直接决定现有结论的可信度。路径 B · 扩大主体规模：为邻居计算接入空间索引，主体从 500 扩到 2 万，邻居半径改回 1 km。代价中等、消除缩比假象，但需要重新标定。路径 C · 接入成熟 Agent 框架：引入 LangChain / AutoGen 做多步推理与更复杂的角色协作。代价高、收益偏探索性。建议结论（accent 规则上）：A → B → C；理由是先让数字可信，再让规模可信，最后才是能力上限。
- **Closing impact**: 收束句 "先让数字可信，再让规模可信，最后才谈能力上限" 与 accent 规则绑定，作为整场的落点

## X. Speaker Notes Requirements

- **Generation**: enabled
- **Filename**: match each SVG filename under `notes/`
- **Content**: 逐页中文讲稿，口语化但不失严谨；每页先给结论再给依据；公式页把符号逐个念清楚（例如"α 是截距，β_LBD 是干中学斜率"）；结果页按"装机—成本—采用—政策"顺序讲四个面板；偏差页必须点明"这是已知且已定位的偏差，不是没发现"；结束时给出 A → B → C 的优先级建议并邀请讨论
- **Total duration**: 15–20 分钟
- **Notes style**: conversational (正式但口语化)
- **Presentation purpose**: report and account 为主，兼顾 align（对齐下一步优先级）
