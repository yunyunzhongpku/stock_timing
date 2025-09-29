# 股指择时策略系统

## 项目概述

本项目实现基于中证全指和申万一级行业数据的股指择时策略系统，包含三种经典的技术形态识别策略，支持单独回测和组合回测分析。

可以使用WIND咨询API。

## 策略详情

### 策略1：下跌反弹形态（含ATR修正）

**核心逻辑**：
- 识别市场下跌超过阈值后的反弹信号
- 下跌过程中小幅回弹不超过反弹阈值则认为下跌趋势未变
- 根据ATR60动态调整阈值参数

**ATR修正规则**：
```python
if ATR60 < 1%:
    correction_factor = sqrt(ATR60 / 1%)  # 缩小阈值
elif ATR60 > 2%:
    correction_factor = sqrt(ATR60 / 2%)  # 放大阈值  
else:
    correction_factor = 1.0               # 阈值不变

adjusted_decline_threshold = -5% * correction_factor
adjusted_rebound_threshold = 0.5% * correction_factor
```

### 策略2：顶部切换形态

**核心逻辑**：
- 基于申万一级行业52周新高数据识别市场顶部切换
- 双重条件筛选：新高行业数量大幅减少 + 指数下跌超过ATR60

**信号确认条件**：
```python
condition1 = (前一日新高行业数 >= 3) AND (当日新高行业数 <= 前一日新高行业数 - 3)
condition2 = 当日中证全指跌幅 <= -ATR60
signal = condition1 AND condition2
```

### 策略3：三角形突破

**核心逻辑**：
- 识别指数极度收敛后的突破行情
- 三重条件判断：收敛 + 突破 + 区间收窄

**信号确认条件**：
```python
convergence = 前5日每日涨跌幅绝对值 <= 1%
breakout = 突破日涨跌幅绝对值 > 1%
以5日内最高价和5日内最低价构建震荡区间，5日内最高价和最低价所构建的震荡区间处于收缩状态，即该通道宽度在收窄（怎么定义？）
signal = convergence AND breakout AND narrowing
```

**价格区间收窄定义**：
```python
def is_price_range_narrowing_5days(prices, current_idx, narrowing_ratio=0.8):
    # 当前5日区间宽度
    current_5d = prices[current_idx-4:current_idx+1]
    current_width = (current_5d.max() - current_5d.min()) / current_5d.mean()
    
    # 前5日区间宽度  
    prev_5d = prices[current_idx-9:current_idx-4]
    prev_width = (prev_5d.max() - prev_5d.min()) / prev_5d.mean()
    
    return current_width < prev_width * narrowing_ratio
```
