"""
因子：下跌反弹形态 [已停止]
Decline Rebound Pattern Factor [DISCONTINUED]

⚠️ 警告：此策略已于2025-10-04停止开发
原因：验证方法存在根本性问题（in-sample测试、验证数据可能循环论证）
保留原因：作为量化策略开发的教学案例，展示如何保持科学诚实性

详见：docs/FACTOR_RESEARCH_SUMMARY.md

基于ATR动态阈值的下跌反弹识别
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, NamedTuple
from backtest.indicators import calculate_atr, get_adjusted_thresholds


class TrendResult(NamedTuple):
    """下行反弹趋势分析结果"""
    is_valid: bool          # 是否为有效的下行反弹
    ends_today: bool        # 反弹是否在当天结束
    bottom_price: float     # 反弹底部价格
    bottom_idx: int         # 反弹底部位置
    high_price: float       # 反弹起点高点
    high_idx: int           # 反弹起点位置


def _trace_decline_trend(close: pd.Series,
                         atr60: pd.Series,
                         high_idx: int,
                         current_idx: int,
                         current_rebound_threshold: float) -> TrendResult:
    """
    辅助函数：从指定高点追踪完整的下行反弹

    关键逻辑：
    - 从高点开始，每天检查
    - 记录过程中的最低点作为反弹底部
    - 当某天反弹超过阈值时，认为反弹结束
    - 只有反弹在current_idx这一天结束才返回有效结果

    Args:
        close: 收盘价序列
        atr60: ATR60序列
        high_idx: 反弹起点（高点）
        current_idx: 当前要判断的日期
        current_rebound_threshold: 当日的反弹阈值

    Returns:
        反弹分析结果
    """
    if high_idx >= current_idx:
        return TrendResult(False, False, 0, 0, 0, 0)

    high_price = close.iloc[high_idx]
    bottom_price = high_price
    bottom_idx = high_idx

    # 从高点后一天开始追踪
    for i in range(high_idx + 1, current_idx + 1):
        current_price = close.iloc[i]
        prev_price = close.iloc[i-1]

        # 更新反弹底部
        if current_price < bottom_price:
            bottom_price = current_price
            bottom_idx = i

        # 计算当日相对前日的涨幅
        daily_return = (current_price - prev_price) / prev_price

        # 获取当日的反弹阈值（每天调整）
        day_atr = atr60.iloc[i]
        if pd.isna(day_atr):
            continue

        _, day_rebound_threshold = get_adjusted_thresholds(day_atr)

        # 检查是否反弹结束（涨幅超过当日阈值）
        if daily_return >= day_rebound_threshold:
            # 只有在current_idx这一天反弹结束才认为是有效信号
            ends_today = (i == current_idx)

            # 确保确实是下行反弹
            overall_decline = (bottom_price - high_price) / high_price
            if overall_decline >= 0:  # 没有实际下跌
                return TrendResult(False, False, 0, 0, 0, 0)

            return TrendResult(
                is_valid=True,
                ends_today=ends_today,
                bottom_price=bottom_price,
                bottom_idx=bottom_idx,
                high_price=high_price,
                high_idx=high_idx
            )

    # 如果到了current_idx还没反弹结束，返回无效
    return TrendResult(False, False, 0, 0, 0, 0)


def _has_signal_between(triggered_signals: List[int],
                        high_idx: int,
                        current_idx: int) -> bool:
    """
    辅助函数：检查高点到当前点之间是否存在其他信号

    Args:
        triggered_signals: 已触发信号的位置列表
        high_idx: 高点位置
        current_idx: 当前位置

    Returns:
        是否存在其他信号
    """
    for signal_idx in triggered_signals:
        if high_idx < signal_idx < current_idx:
            return True
    return False


def generate_signals(data: pd.DataFrame,
                    lookback_days: int = 20) -> pd.Series:
    """
    下跌反弹因子：生成交易信号 [已停止]

    ⚠️ 此策略已停止开发，仅供参考

    逻辑：
    1. 从20日内寻找高点
    2. 追踪高点后的下跌和反弹过程
    3. 当反弹结束（单日涨幅超过ATR调整后的阈值）时触发信号
    4. 要求总跌幅达到-5%（ATR调整），反弹幅度达到0.5%（ATR调整）

    Args:
        data: OHLC价格数据，必须包含['high', 'low', 'close']列
        lookback_days: 回看天数，用于寻找高点，默认20日

    Returns:
        pd.Series: 信号序列，True表示信号触发，索引与data一致

    Note:
        此函数需要data中包含'atr60'列，如果没有会自动计算
    """
    # 输入验证
    required_cols = ['high', 'low', 'close']
    for col in required_cols:
        if col not in data.columns:
            raise ValueError(f"数据必须包含列: {col}")

    # 计算或获取ATR60
    if 'atr60' in data.columns:
        atr60 = data['atr60'].copy()
    else:
        atr60 = calculate_atr(data['high'], data['low'], data['close'], window=60)

    close = data['close'].copy()

    signals = pd.Series(False, index=close.index)
    triggered_signals: List[int] = []  # 记录已触发的信号位置

    for i in range(lookback_days, len(close)):
        current_price = close.iloc[i]

        # 获取当日ATR调整后的阈值
        current_atr = atr60.iloc[i]
        if pd.isna(current_atr):
            continue
        decline_threshold, rebound_threshold = get_adjusted_thresholds(current_atr)

        # 1. 寻找回看窗口内的所有可能高点
        lookback_start = max(0, i - lookback_days)

        # 遍历回看窗口内的每个可能高点
        for high_candidate_idx in range(lookback_start, i):
            high_price = close.iloc[high_candidate_idx]

            # 2. 从该高点追踪下行反弹
            trend_result = _trace_decline_trend(
                close, atr60, high_candidate_idx, i, rebound_threshold
            )

            # 3. 检查是否为有效信号
            if trend_result.is_valid and trend_result.ends_today:
                # 计算整个反弹的总跌幅（高点到低点）
                total_decline = (trend_result.bottom_price - trend_result.high_price) / trend_result.high_price

                # 计算从反弹底部到当前的反弹幅度
                rebound_from_bottom = (current_price - trend_result.bottom_price) / trend_result.bottom_price

                # 检查条件
                decline_ok = total_decline <= decline_threshold
                rebound_ok = rebound_from_bottom >= rebound_threshold

                # 确保高点到当前点之间没有其他信号
                no_signal_between = not _has_signal_between(
                    triggered_signals, trend_result.high_idx, i
                )

                if decline_ok and rebound_ok and no_signal_between:
                    signals.iloc[i] = True
                    triggered_signals.append(i)
                    break  # 找到一个有效信号就停止，避免重复

    return signals


# ⚠️ 停止原因说明
DISCONTINUATION_REASON = """
策略1（下跌反弹）停止开发原因：

1. 验证方法存在根本性问题
   - 所有验证均为in-sample（样本内）测试
   - 验证数据可能存在循环论证
   - 缺乏真正的out-of-sample验证

2. 核心指标不可操作
   - "40日内最高收益"是马后炮指标
   - 实盘无法精准抓住最高点
   - 需要事后才能确定

3. 固定持有期不显著
   - 1日、5日、10日、20日、40日收益均不显著
   - 只有"最高收益"显著，这是循环论证

4. 补充离场机制会过拟合
   - 设计止盈/止损规则=新的参数优化
   - 在同一数据集上优化=过拟合陷阱

教训：
- 数据分割必须在开始就做对（训练/验证/测试）
- Out-of-sample验证是必须的，不是可选的
- 对"好结果"保持批判性怀疑
- 回测指标必须可操作
- 科学诚实比"成功"更重要

详见：docs/FACTOR_RESEARCH_SUMMARY.md
"""
