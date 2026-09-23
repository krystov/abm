<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- primary_language: zh-CN
- audience: 课题组内部与导师/评审，关心复现忠诚度、结果可信度与剩余风险
- objective: 讲清系统构成、复现程度与 LLM 接入位置，用结果证明主线成立，主动暴露两处已定位偏差，并让受众就对下一步（校准 / 扩规模 / 接框架）的优先级形成一致意见
- core_message: 两阶段采用与双因子经验曲线主线已忠实落地、LLM 增强已端到端跑通；政策—扩散—降本形态与文献一致，但绝对量级与国外成本存在两处已定位偏差
- consumption_mode: balanced

## mode
- mode: custom
- mode_references: briefing, pyramid
- mode_behavior: 主体走 briefing 的中立叙述：主题式标题、同级条目等重、按项目/系统/机制/接入/结果/偏差/进度/下一步分区，便于会后检索；末三页转 pyramid，结论先行，先给"两处偏差已定位、建议先做校准"，再展开证据与取舍，收束到一次明确的优先级选择。

## visual_style
- visual_style: custom
- visual_style_references: editorial, data-journalism
- visual_style_behavior: 以 editorial 的杂志式层级为主干——细线分隔代替卡片、非对称分栏、kicker 与主张式标题的字号梯度、圆角近乎为零、阴影仅用于真正的浮动元素；数据页吸收 data-journalism 的多栏微图与脚注纪律，每个数字都带单位与来源行，图表紧贴解读文字而不居中孤立，空白用于分栏节奏而非装饰。

## colors
- background: #F7F5F0
- secondary_bg: #EDE8DF
- primary: #16233A
- accent: #C0562B
- secondary_accent: #2E6F6A
- body_text: #35322C
- surface: #FFFFFF
- grid: #D8D2C6

## typography
- font_family: "Microsoft YaHei", "Segoe UI", system-ui, sans-serif
- title_family: Georgia, "Microsoft YaHei", "PingFang SC", serif
- body_family: "Microsoft YaHei", "Segoe UI", system-ui, sans-serif
- data_family: Consolas, "Microsoft YaHei", monospace
- body: 24
- title: 42
- subtitle: 32
- annotation: 18
- footnote: 16
- display: 64

## icons
- library: tabler-outline
- stroke_width: 2
- inventory: tabler-outline/sun, tabler-outline/target, tabler-outline/route, tabler-outline/binary-tree, tabler-outline/users, tabler-outline/building-factory, tabler-outline/trending-down, tabler-outline/chart-line, tabler-outline/robot, tabler-outline/code, tabler-outline/database, tabler-outline/checklist, tabler-outline/alert-triangle, tabler-outline/circle-check, tabler-outline/clock, tabler-outline/file-text

## page_rhythm
- P01: anchor
- P02: breathing
- P03: dense
- P04: dense
- P05: dense
- P06: dense
- P07: dense
- P08: breathing
- P09: dense
- P10: dense
- P11: dense
- P12: dense
- P13: breathing
- P14: anchor

## pptx_structure
- mode: flat

## images
- p10: images/results.png | source=user | pattern=整幅横置于页面左侧 62% 宽度，右侧 38% 放四条解读；图下留一行运行条件脚注 | crop=no-crop

## page_visualizations
- P07: table/metric_table
- P11: table/metric_table

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
