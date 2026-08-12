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

* **极高环境意识跳过机制**：若 $\text{Env} > \Theta_{env}$（阈值为 0.88），主体直接令 $A = 1.0$，跳过复杂的经济效益（NPV）评估。
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
光伏组件成本的下降由全球累计生产经验（干中学）和研发知识存量（研究中学）双驱动。本土和海外制造商制造组件的底线成本 $MC_t$ 计算如下：
$$MC_t = MC_0 \cdot \left( \frac{CP_t}{CP_0} \right)^{-b} \cdot \left( \frac{KS_t}{KS_0} \right)^{-c}$$

* $CP_t$: 当期累积产量（Cumulative Production）。
* $KS_t$: 当期研发知识存量（Knowledge Stock）。
* $b$: 学习演化指数（Learning-by-doing index），对应**产量每翻一番，成本下降约 18% - 20%**。
* $c$: 研究演化指数（Learning-by-searching index），对应研发资金转化为技术积淀的效率。

研发知识存量 $KS_t$ 的永续盘存动态更新公式：
$$KS_t = (1 - \delta) \cdot KS_{t-1} + R\&D_t$$
* $\delta$: 知识折旧率（通常设定为每年 10% 左右）。
* $R\&D_t$: 当期政府技术推动政策（Technology-push）注入的研发资金。

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