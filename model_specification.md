# Model Specification: Germany's Solar PV Policy Mix ABM

本文件根据论文《Beyond innovation and deployment: Modeling the impact of technology-push and demand-pull policies in Germany's solar policy mix》的补充材料（Supplementary Information）编译，旨在为多主体模型（ABM）的计算机复现提供核心变量定义、系统调度流程以及底层数学公式。

---

## 1. Section 1.1.3: 主体状态变量定义 (State Variables)

模型包含四大核心实体：观察者（全局环境）、采用者（市场需求端）、制造商（技术供应端）和安装商（渠道端）。以下是各实体的关键状态变量定义：

### 1.1 观察者/全局变量 (Observer / Global Variables)
* `tick / time-step`: 当前模拟步长，单位：月 (Month)，总计 312 步 (1991–2016)。
* `electricity-price-h`: 住宅用户零售电价 (Euro/kWh)。
* `electricity-price-c`: 商业用户零售电价 (Euro/kWh).
* `fit-tariff-h`: 住宅级光伏并网补贴（Feed-in Tariff）率 (Euro/kWh)。
* `fit-tariff-c`: 商业级光伏并网补贴（Feed-in Tariff）率 (Euro/kWh)。
* `media-coverage`: 当月媒体关于光伏的报道总量（流动的社会公共信息）。
* `tech-push-level`: 政府研发（R&D）技术推动政策的资金强度评级 (1–5)。

### 1.2 采用者主体 (Adopter Agents)
* `agent-id`: 唯一识别码。
* `adopter-type`: 类别枚举：`Household` (住宅用户) 或 `Commercial` (商业用户)。
* `location`: 二维空间坐标 `(x, y)`，位于 10×10 km 的德国地理网格中。
* `roof-size`: 可安装光伏的有效屋顶面积 ($m^2$)。
* `electricity-demand`: 月度基准用电需求 (kWh)。
* `awareness-env` ($\text{Env}$): 环境保护意识，取值范围 $[0, 1]$，服从不均匀分布。
* `discount-rate` ($r$): 财务投资折现率，住宅用户通常高于商业用户。
* `is-adopted`: 布尔值，标记是否已经安装光伏系统。
* `attitude` ($A$): 投资态度（结合环境与经济效益评估）。
* `social-norm` ($SN$): 主观规范（受邻里效应驱动）。
* `pbc`: 知觉行为控制（受市场成熟度与申请便利度驱动）。
* `intention` ($I$): 最终购买意愿，取值范围 $[0, 1]$。

### 1.3 制造企业主体 (Manufacturer Agents)
* `manufacturer-id`: 唯一识别码。
* `region`: 类别枚举：`Domestic` (德国本土) 或 `Foreign` (海外，如中国)。
* `capacity`: 当前光伏组件生产产能 (MW/月)。
* `module-efficiency`: 组件光电转化效率 (%)。
* `production-cost` ($MC$): 制造单位瓦数光伏组件的底线成本 (Euro/W)。
* `knowledge-stock` ($KS$): 企业自身的研发知识存量，由历年 R&D 投入累积。
* `cumulative-production` ($CP$): 企业自成立以来的累计组件产量（用于计算“干中学”效应）。

### 1.4 安装商主体 (Installer Agents)
* `installer-id`: 唯一识别码。
* `employees`: 当前雇佣的劳动力/安装工数量。
* `bos-cost` ($BOS$): 非组件平衡系统成本，包括支架、逆变器及人工造价 (Euro/W)。
* `order-backlog`: 当前积压、未完工的光伏安装订单量 (MW)。

---

## 2. Section 1.1.5: 系统调度与时序逻辑 (Process Overview and Scheduling)

模型以 **1个月** 为一个 Tick。在每个时间步内，系统内部必须严格按照以下顺序串行执行更新，严禁颠倒：

1.  **更新宏观环境 (`update-macro-variables`)**：
    * 读取历史实证数据，更新本月的 `electricity-price`、`fit-tariff` 和 `media-coverage`。
2.  **采用者决策循环 (`ask adopters [ evaluate-and-adopt ]`)**：
    * 所有 `is-adopted = false` 的采用者根据当前的电价、补贴和组件市场价，执行**计划行为理论（TPB）**子模型，更新 `intention`。
    * 若意愿突破阈值，则向本地安装商下单，更新 `is-adopted = true`。
3.  **安装商市场响应 (`ask installers [ manage-orders ]`)**：
    * 收集当月新订单，更新 `order-backlog`。
    * 根据订单积压状况，决定下个月是雇佣还是解雇员工（调整 `employees`）。
    * 根据劳动力成本和供需关系更新其服务报价（`bos-cost`）。
4.  **制造商技术更新 (`ask manufacturers [ produce-and-learn ]`)**：
    * 结算当月全球与本土的总出货量，更新各自的 `cumulative-production`。
    * 根据政府政策投入更新 `knowledge-stock`。
    * 应用**双因子经验曲线**更新下个月的组件出厂成本 `production-cost`。
5.  **时钟推进 (`tick`)**：
    * 推进到下个月，记录全局装机容量、就业人口以及行业平均价格。

---

## 3. Section 1.3.3: 底层核心子模型与数学公式 (Sub-models & Equations)

### 3.1 采用者购买意愿公式（计划行为理论 TPB）
每个采用者的采用意愿 $I$ 由投资态度（$A$）、主观规范（邻里效应 $SN$）和知觉行为控制（$PBC$）加权决定：
$$I = w_{att} \cdot A + w_{sn} \cdot SN + w_{pbc} \cdot PBC$$

*标定权重 (Table SI 11)：$w_{att} = 0.55$, $w_{sn} = 0.30$, $w_{pbc} = 0.15$。*

#### 3.1.1 投资态度公式 ($A$)
投资态度结合了环境意识与经济驱动：
$$A = w_{env} \cdot \text{Env} + w_{eco} \cdot \text{Eco}$$

* **极高环境意识跳过机制**：若 $\text{Env} > \Theta_{env}$（阈值为 0.92，论文 Table SI 标定值，范围 [0.88, 1]），主体直接令 $A = 1.0$，跳过复杂的经济效益（NPV）评估。
* **经济态度效益评价 ($\text{Eco}$)**：由归一化后的净现值（NPV）决定：
    $$\text{Eco} = \frac{1}{1 + e^{-\gamma \cdot NPV_{norm}}}$$

#### 3.1.2 财务净现值公式 ($NPV$)
采用者评估在 20 年（240个月）的系统寿命期内，光伏所能带来的现金流折现：
$$NPV = \sum_{t=1}^{240} \frac{CF_t}{(1 + r)^t} - I_0$$
* $I_0$：光伏系统总初始投资 $= (\text{组件价格} + BOS\text{成本}) \cdot \text{系统容量}$。
* $CF_t$：第 $t$ 个月的现金流 $= \text{自发自用省下的电费} + \text{余电上网获得的 FiT 补贴} - \text{运维成本}$。
* $r$：个体的财务折现率 `discount-rate`。

#### 3.1.3 主观规范与邻里效应公式 ($SN$)
受空间地理位置影响，统计主体所在格点方圆 1 公里（或模型设定的邻里半径 $R$）内已经安装光伏的邻居比例：
$$SN = \frac{\text{Radius内已安装光伏的主体数量}}{\text{Radius内所有的主体总数}}$$

---

### 3.2 制造端组件成本技术学习曲线（双因子经验曲线）
光伏组件成本的下降由全球累计生产经验（干中学）和研发知识存量（研究中学）双驱动。本土和海外制造商制造组件的底线成本 $MC_t$ 计算如下（论文 Equation 24，Table SI 53 标定）：
$$MC_t = \alpha \cdot \left( \frac{CP_t}{CP_0} \right)^{\beta_{LBD}} \cdot \left( \frac{KS_t}{KS_0} \right)^{\beta_{LBR}}$$

* $CP_t$: 当期累积产量（Cumulative Production）。
* $KS_t$: 当期研发知识存量（Knowledge Stock）。
* $\alpha$: 截距（成本 €/W），国内 2.882、国外 2.448、非组件 3.354。
* $\beta_{LBD}$: 干中学 log-log 斜率，国内 −0.074、国外 −0.448（对应学习率 5.0% / 26.7%）。
* $\beta_{LBR}$: 研究中学 log-log 斜率，国内 −0.814、国外 −0.074（对应学习率 43.1% / 5.0%）。

学习率 $LR$（成本随驱动变量每翻一番下降的比例）与斜率 $\beta$ 的换算：
$$\beta = \log_2(1 - LR) = \frac{\ln(1 - LR)}{\ln 2}$$

非组件（BOS）单因子经验曲线（Equation 22）：$\alpha_I = 3.354$、$\beta_I = -0.155$（学习率 10.2%）。

研发知识存量 $KS_t$ 的永续盘存动态更新公式：
$$KS_t = (1 - \delta) \cdot KS_{t-1} + R\&D_t$$
* $\delta$: 知识折旧率（0.8742%/月，≈ 10%/年，Table SI 53）。
* $R\&D_t$: 当期研发资金（政府 GERD + 企业 BERD，含知识溢出）。

---

### 3.3 安装商渠道与劳动力动力学模型
安装商的非组件成本 $BOS_t$ 很大程度上取决于本地安装工的供需短缺程度。

#### 3.3.1 劳动力扩充与裁员决策
安装商根据当前的订单积压月数来动态调整员工数量。如果积压的订单需要超过 $\tau_{max}$ 个月才能干完，则触发扩招；反之若无工可开，则触发裁员：
$$\Delta \text{Employees} = \alpha \cdot \left( \frac{\text{order-backlog}}{\text{当前月完工能力}} - \tau_{target} \right)$$
* $\alpha$: 劳动力市场调整灵敏度系数。

#### 3.3.2 渠道成本动态报价
$$BOS_t = BOS_{base} \cdot \left( 1 + \beta \cdot \frac{\text{order-backlog}}{\text{Employees}_t} \right)$$
* 当订单激增、人手不足时，安装商会提高非组件溢价（$BOS_t$ 上升），形成市场降温的负反馈调节。

---

## 附录 A（2026-08-13 从论文 DOCX 补充材料提取）：采用决策的真实两阶段模型

> 本节纠正上文 §3.1 的简化版 TPB。论文实际的采用决策是**两阶段**过程，
> 上文把两个阶段合并成了单一 TPB 公式，与原文不符。以下内容从
> `1-s2.0-S0048733322001093-mmc1.docx` 的 OMML 公式与 Table 33/36/38/53 提取。

### 阶段一：萌生念头（Ideation，Equation 2）

主体在当月"萌生安装念头"当且仅当四个变量的加权和超过固定阈值 **0.5**：

$$k_{peers}\cdot PE_{i,t} + k_{info}\cdot IN_t + k_{awareness}\cdot AW_i + k_{attractive}\cdot IRR_t > 0.5$$

其中：
* $PE_{i,t}$：peer effects = 1 km 内已装邻居比例（Table 5：半径 **1 km**）
* $IN_t$：available information = 当月 PV 新闻/媒体信息量（随 PV 扩散变化）
* $AW_i$：environmental awareness = $N(0.5, 0.2)$，赋值后**恒定不变**
* $IRR_t$：economic attractiveness = 德国平均家庭 PV 投资的内部收益率

权重（Table 36 标定，3 个标定 + 第 4 个线性依赖，和 = 1）：
$$k_{awareness},\ k_{info},\ k_{attractive},\ k_{peers} = 0.52,\ 0.17,\ 0.12,\ 0.19$$
映射已确认：校准参数清单（OMML）列出 k_awareness、k_info、k_attractive 三个标定权重，
k_peers 为线性依赖项；正文敏感度分析明确"information weight = 0.17"。故
awareness=0.52、info=0.17、attractive=0.12、peers=0.19（peers = 1 − 0.52 − 0.17 − 0.12）。

### 阶段二：经济与环境意识评估（NPV 双选，Equations 3-5）

只有"萌生念头"的主体进入此阶段：
* **早期采用者**（$AW > \Theta_{env} = 0.92$ 且 residential）→ 直接安装
* 其余：分别计算 domestic / foreign 两个 NPV，选**非负且最大**者（平局偏好 domestic）

NPV（$y = 0..20$ 年，FiT 合同 20 年）：
$$NPV^d_{i,t} = -I^d_{i,t} + \sum_{y=0}^{20}\frac{AC_{i,t} - O\&M^d_{i,t} + FITR_{i,t}}{(1+r_t+D_i)^y} \ge 0$$
$$NPV^f_{i,t} = -I^f_{i,t} + \sum_{y=0}^{20}\frac{AC_{i,t} - O\&M^f_{i,t} + FITR_{i,t}}{(1+r_t+D_i+D^f_i)^y} \ge 0$$
$$D^f_i = D_i + R^f$$

关键子公式（Equations 6-10）：
* 投资 $I = S_i \cdot P_t \cdot SE_i$（系统大小 × 系统价格 × 规模效应）
* 规模效应 $SE_i = 1.1246 \cdot S_i^{-0.051}$（$S_i \ge 1$ kWp）；否则 $SE_i = 1.2$
* 自发自用省费 $AC_{i,t} = SC_i \cdot EG_i \cdot EP_{i,t}$
* 余电上网收入 $FITR_{i,t} = (1-SC_i) \cdot EG_i \cdot FIT_t$
* 发电量 $EG_i = SUN_i \cdot S_i \cdot PR \cdot PF_i$（$PR = 0.85$，$PF \sim N(0.9, 0.2)$）

### 与当前代码的差异（采用子模型已重写为两阶段，2026-08-13）

| 项目 | 论文 | 当前代码 |
|------|------|----------|
| 决策结构 | 两阶段（ideation 阈值 0.5 → NPV 双选） | ✅ 两阶段（submodels/adoption.py） |
| 邻居半径 | 1 km | 10 km（500 主体缩比的补偿，刻意偏离） |
| 环境意识 | 恒定 N(0.5,0.2) | ✅ 恒定（不再随媒体演化） |
| 早期采用者 | env>0.92 且 residential | ✅ env>0.92 且 residential（自然涌现，无种子 hack） |
| 经济评估 | IRR（ideation）+ NPV 双选（阶段二） | ✅ IRR（代表家庭）+ NPV 双选 |
| 环境意识阈值 | 0.92 | ✅ 0.92 |

> 说明：采用子模型已按论文两阶段重写。剩余主要偏离为邻居半径（1 km→10 km，
> 因 500 主体在 100×100 km 网格中 1 km 内平均仅 0.16 邻居，peer 效应无法启动）；
> 以及 IRR 用固定代表家庭（4 kWp、30% 自用）近似论文"平均德国家庭"。信息量 IN_t
> 采用 Table SI 15 的 logistic 拟合（新文章数 vs 世界累计装机），环境意识恒定。