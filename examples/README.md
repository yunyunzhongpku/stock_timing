# 示例代码 Examples

本目录包含完整的使用示例，演示如何使用重构后的模块进行策略分析。

## 文件说明

### 1. `run_csi_all_index.py`
**完整示例：中证全指分析**

演示完整的策略分析流程：
- 数据加载
- 信号生成
- 回测分析
- 可视化
- 时间分割验证

**运行方式：**
```bash
python examples/run_csi_all_index.py
```

**输出：**
- 控制台：详细的分析报告
- `outputs/` 目录：生成的图表文件

---

### 2. `template_custom_asset.py`
**模板示例：自定义资产分析**

演示如何将策略因子应用到其他资产（股票、指数、期货等）。

**使用步骤：**

1. **修改配置**：编辑文件中的配置部分
   ```python
   TICKER = '000300.SH'      # 修改为你的资产代码
   ASSET_NAME = '沪深300'     # 修改为资产名称
   START_DATE = '2013-01-01'
   END_DATE = '2025-04-30'
   ```

2. **选择数据加载方式**：
   - 方法1：使用DataLoader（支持Wind）
   - 方法2：从CSV加载
   - 方法3：自定义数据源

3. **选择因子**：
   - `analyze_triangle_breakout()` - 三角形突破
   - `analyze_decline_rebound()` - 下跌反弹（已停止）

4. **运行分析**：
   ```bash
   python examples/template_custom_asset.py
   ```

---

## 快速开始

### 最简示例

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
results = analyze_signals(
    data,
    signals,
    holding_periods=get_holding_periods(),
    direction='bidirectional'
)

# 4. 打印结果
print_analysis_summary(results)
```

---

## 数据要求

所有策略因子都需要标准的OHLC数据格式：

| 列名 | 类型 | 说明 |
|------|------|------|
| `open` | float | 开盘价 |
| `high` | float | 最高价 |
| `low` | float | 最低价 |
| `close` | float | 收盘价 |
| `volume` | float | 成交量（可选） |

数据索引必须是日期类型（`pd.DatetimeIndex`）。

---

## 进阶用法

### 1. 参数对比

对比不同参数版本的表现：

```python
from config import STRATEGY3_CONFIG

for preset_name in STRATEGY3_CONFIG['presets'].keys():
    params = get_strategy_parameters('triangle_breakout', preset=preset_name)
    signals = generate_signals(data, **params)
    results = analyze_signals(data, signals)
    print_analysis_summary(results, title=f"参数版本: {preset_name}")
```

### 2. 时间分割验证

评估out-of-sample表现：

```python
from backtest.signal_analyzer import analyze_signals_with_time_split
from backtest.visualizer import print_time_split_summary

in_sample, out_sample = analyze_signals_with_time_split(
    data,
    signals,
    split_date='2022-01-01',
    holding_periods=[1, 5, 10, 20, 40],
    direction='bidirectional'
)

print_time_split_summary(in_sample, out_sample, key_period='20日')
```

### 3. 自定义可视化

```python
from backtest.visualizer import plot_signal_performance
import matplotlib.pyplot as plt

fig = plot_signal_performance(
    results,
    title="我的策略表现",
    output_path="outputs/my_strategy.png",
    figsize=(20, 16)
)

plt.show()  # 显示图表
```

---

## 常见问题

**Q: 如何加载自己的CSV数据？**

A: 在`template_custom_asset.py`中使用方法2：
```python
data = pd.read_csv('your_data.csv', index_col='date', parse_dates=True)
data = data[['open', 'high', 'low', 'close']]
```

**Q: 如何只做单向交易？**

A: 修改`direction`参数：
```python
# 只做多
results = analyze_signals(data, signals, direction='long')

# 只做空
results = analyze_signals(data, signals, direction='short')
```

**Q: 如何修改持有期？**

A: 直接传入自定义列表：
```python
results = analyze_signals(
    data,
    signals,
    holding_periods=[1, 3, 7, 14, 30]  # 自定义持有期
)
```

---

## 输出说明

### 控制台输出

```
================================================================================
策略分析结果
================================================================================

总信号数: 52

持有期收益统计:
--------------------------------------------------------------------------------
持有期   样本数   平均收益      中位收益      胜率        t统计量      p值          显著性
--------------------------------------------------------------------------------
1日      52       0.12%        0.08%       53.8%      0.234       0.8156      否
5日      52       0.45%        0.32%       57.7%      0.987       0.3284      否
10日     52       0.89%        0.67%       61.5%      1.345       0.1845      否
20日     52       1.96%        1.45%       65.4%      2.456       0.0165      是
40日     52       3.42%        2.78%       69.2%      3.123       0.0028      是
```

### 图表输出

`outputs/` 目录下生成PNG文件，包含6个子图：
1. 收益分布箱线图
2. 平均收益柱状图
3. 胜率柱状图
4. 累计收益曲线（分做多/做空）
5. 统计显著性表格
6. 信号时间分布散点图

---

## 相关文档

- 项目README: `../README.md`
- 因子研究总结: `../docs/FACTOR_RESEARCH_SUMMARY.md`
- 配置文件: `../config.py`

---

*最后更新: 2025-10-04*
