# 股指择时策略系统

**项目简介**: 基于中证全指(000985.CSI)的股指择时因子库，采用模块化设计，易于扩展到其他资产。

**项目状态**: 2025-10-04 重构完成
- ✅ 策略3（三角形突破）：有效，可实战应用
- ❌ 策略1（下跌反弹）：已停止（详见文档）
- 📋 策略2（顶部切换）：规划中

---

## 🎯 核心特点

### 1. 科学诚实
- 对"好结果"保持批判性怀疑
- Out-of-sample验证（时间分割）
- 诚实报告测试期结果

### 2. 模块化设计
- **factors/**: 纯因子模块，易于复用
- **backtest/**: 通用回测工具
- **examples/**: 完整示例和模板

### 3. 可扩展性
- 新增因子只需实现`generate_signals()`
- 自动继承完整回测和可视化能力
- 支持任何OHLC数据源

---

## 📁 项目结构

```
Stock_Timing/
├── factors/                     # 策略因子模块
│   ├── triangle_breakout.py    # ✅ 三角形突破（有效）
│   └── decline_rebound.py      # ❌ 下跌反弹（已停止）
│
├── backtest/                    # 回测分析工具
│   ├── indicators.py           # 技术指标（ATR等）
│   ├── signal_analyzer.py      # 通用回测分析器
│   └── visualizer.py           # 标准化可视化
│
├── data/                        # 数据加载模块
│   └── loader.py               # 统一数据接口（Wind/演示数据）
│
├── examples/                    # 使用示例
│   ├── run_csi_all_index.py    # 完整分析示例
│   ├── template_custom_asset.py # 自定义资产模板
│   └── README.md               # 详细使用说明
│
├── docs/                        # 文档
│   └── FACTOR_RESEARCH_SUMMARY.md  # 完整研究总结
│
├── reports/                     # 历史报告（图表）
│   ├── strategy1/              # 策略1相关图表
│   └── strategy3/              # 策略3相关图表
│
├── config.py                    # 统一配置管理
├── verify_refactoring.py        # 重构验证脚本
├── data_loader.py               # 旧版数据加载器（待废弃）
└── requirements.txt             # 依赖包
```

---

## ⚡ 快速开始

### 最简示例（3行代码）

```python
from data.loader import load_csi_all_index
from factors.triangle_breakout import generate_signals
from backtest.signal_analyzer import analyze_signals, print_analysis_summary
from config import get_strategy_parameters, get_holding_periods

# 1. 加载数据
data = load_csi_all_index('2013-01-01', '2025-04-30')

# 2. 生成信号
params = get_strategy_parameters('triangle_breakout', preset='basic')
signals = generate_signals(data, **params)

# 3. 回测分析
results = analyze_signals(data, signals,
                         holding_periods=get_holding_periods(),
                         direction='bidirectional')

# 4. 打印结果
print_analysis_summary(results)
```

### 运行完整示例

```bash
# 安装依赖
pip install -r requirements.txt

# 运行中证全指分析（含时间分割验证）
python examples/run_csi_all_index.py

# 使用自定义资产（修改ticker后运行）
python examples/template_custom_asset.py

# 验证重构（确保与原始版本一致）
python verify_refactoring.py
```

---

## 📊 策略概览

### ✅ 策略3：三角形突破（有效）

**核心逻辑**: 收敛 + 突破 + 区间收窄的三重条件

```python
核心条件：
1. 前5日收敛：每日涨跌幅绝对值 <= 1%
2. 当日突破：涨跌幅绝对值 > 1%
3. 区间收窄：最近2日区间 < 前3日区间 * 0.8
```

**回测表现**（basic版本，2013-2025）:

| 持有期 | 平均收益 | 胜率 | p值 | 显著性 |
|--------|----------|------|------|--------|
| 20日 | **+1.96%** | **65.4%** | **0.0165** | **是** |
| 40日 | +2.01% | 63.5% | 0.0908 | 否 |

**时间分割验证**（2022-01-01分割）:
- 训练期（2013-2021）：38信号，20日+2.19%，p=0.0255 ✅
- 测试期（2022-2025）：14信号，20日+1.33%，p=0.3877 ⚠️

**结论**: 训练期显著，测试期样本量小未达显著性，**继续观察，谨慎应用**

---

### ❌ 策略1：下跌反弹（已停止）

**停止日期**: 2025-10-04
**停止原因**: 经批判性分析，发现验证方法存在根本性问题
- 所有验证均为in-sample测试
- 验证数据可能循环论证
- 核心指标"40日内最高收益"不可操作
- 补充离场机制会陷入过拟合陷阱

**教学价值**: 作为案例展示如何保持科学诚实，如何识别和避免方法论陷阱

**详见**: `docs/FACTOR_RESEARCH_SUMMARY.md` - 策略1完整停止决策记录

---

### 📋 策略2：顶部切换（规划中）

**思路**: 行业宽度骤降 + 指数同步走弱

**条件**:
- 行业宽度骤降：前一日新高行业数≥3 且当日减少≥3
- 指数同步走弱：当日中证全指跌幅 ≤ -ATR60

**状态**: 判定框架明确，尚未落地代码

---

## 🛠️ 核心技术

### ATR动态阈值纠偏

```python
if ATR60 < 1%:
    correction = sqrt(ATR60 / 1%)    # 低波动：缩小阈值
elif ATR60 > 2%:
    correction = sqrt(ATR60 / 2%)    # 高波动：放大阈值
else:
    correction = 1.0                 # 正常：不变

adjusted_decline = -5% * correction
adjusted_rebound = 0.5% * correction
```

### 双向交易逻辑

```python
if breakout_direction == 'up':
    # 向上突破 → 做多 → 价格上涨为正收益
    returns = (future_prices / base_price - 1) * 100
else:
    # 向下突破 → 做空 → 价格下跌为正收益
    returns = (base_price / future_prices - 1) * 100
```

---

## 📚 文档

### 核心文档
- **`docs/FACTOR_RESEARCH_SUMMARY.md`**: 完整研究总结
  - 策略1停止决策记录
  - 策略3完整回测结果
  - 核心教训和方法论
  - 重构说明

- **`examples/README.md`**: 详细使用指南
  - 快速开始
  - 完整示例
  - 自定义资产模板
  - 常见问题

- **`CLAUDE.md`**: 项目指导文档（给AI助手）

### 历史报告
- `reports/strategy1/`: 策略1图表（历史记录）
- `reports/strategy3/`: 策略3图表（历史记录）

---

## 🎓 核心教训

### 1. 验证方法论
- ✅ 数据分割必须在开始就做对
- ✅ Out-of-sample验证是必须的
- ✅ 对"好结果"保持批判性怀疑

### 2. 回测指标
- ✅ 使用可操作指标（固定持有期）
- ❌ 避免虚假指标（40日内最高）

### 3. 科学诚实
```
科学诚实 > 表面成功
及时止损 > 沉没成本
认识局限 > 盲目自信
```

---

## 🔧 扩展到其他资产

### 方法1：使用模板

1. 打开`examples/template_custom_asset.py`
2. 修改配置：
   ```python
   TICKER = '000300.SH'      # 改为你的资产代码
   ASSET_NAME = '沪深300'     # 改为资产名称
   ```
3. 运行：`python examples/template_custom_asset.py`

### 方法2：从CSV加载

```python
import pandas as pd
from factors.triangle_breakout import generate_signals

# 加载CSV数据
data = pd.read_csv('your_data.csv', index_col='date', parse_dates=True)
data = data[['open', 'high', 'low', 'close']]

# 生成信号
signals = generate_signals(data,
                          convergence_threshold=0.01,
                          breakout_threshold=0.01,
                          narrowing_ratio=0.8)
```

---

## ⚙️ 依赖环境

- **Python**: 3.11+
- **核心依赖**: pandas, numpy, matplotlib, scipy
- **可选依赖**: WindPy（真实数据）, pytest（测试）

**安装**:
```bash
pip install -r requirements.txt
```

---

## 🔬 验证与测试

### 重构验证

确保重构后代码与原始版本产生一致结果：

```bash
python verify_refactoring.py
```

**验证内容**:
- ✅ Strategy3信号生成：完全一致
- ✅ 回测分析：运行正常

---

## 📈 性能指标

### 策略3（三角形突破）

**信号频率**: 年均11个（2013-2025）
**方向分布**: 上破42%, 下破58%

**全样本表现**:
- 20日持有: +1.96%, 胜率65.4%, p=0.0165 ✅

**时间分割验证**:
- 训练期: +2.19%, p=0.0255 ✅
- 测试期: +1.33%, p=0.3877 ⚠️（样本量小）

---

## 🗺️ 路线图

### 高优先级
- [ ] 在其他市场/资产上测试策略3
- [ ] 开发策略2（顶部切换）
- [ ] 补充单元测试
- [ ] Wind数据CSV缓存

### 中优先级
- [ ] 轻量级回测引擎（含止盈止损）
- [ ] 信号质量评分系统
- [ ] 日志与告警规范

### 低优先级
- [ ] 多策略组合框架
- [ ] 实盘验证准备
- [ ] ruff/mypy代码质量工具

---

## 💡 贡献

本项目采用科学诚实原则：
- 诚实报告所有结果（好坏都接受）
- 严格的验证方法论
- 保持对"好结果"的批判性怀疑

如果您发现问题或有改进建议，欢迎提Issue。

---

## 📄 许可证

本项目用于研究和教学目的。使用本项目的策略进行实盘交易，风险自负。

---

## 🏆 成果总结

### 成功的部分
- ✅ 完整的模块化框架
- ✅ 严格的验证方法论
- ✅ 策略3（三角形突破）有效
- ✅ 完整的文档和示例

### 诚实的部分
- ❌ 策略1停止（方法论问题）
- ⚠️ 策略3测试期未达显著性
- 💡 保持科学诚实，继续观察

### 教学价值
- 展示完整的量化策略开发流程
- 展示如何识别和避免方法论陷阱
- 展示科学诚实的重要性

---

**最后更新**: 2025-10-04
**项目状态**: 重构完成，可用于研究和扩展

---

**核心价值观**:
> 在量化交易中，"不知道"比"错误的确定"更诚实。
