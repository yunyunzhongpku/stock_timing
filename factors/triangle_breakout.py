"""
因子：三角形突破形态
Triangle Breakout Pattern Factor

基于收敛+突破+区间收窄的三重条件判断
适用于任何OHLC价格数据
"""

import numpy as np
import pandas as pd
from typing import Dict


def _is_converging_triangle(data: pd.DataFrame,
                            current_idx: int,
                            narrowing_ratio: float = 0.8) -> bool:
    """
    辅助函数：判断是否形成收敛三角形

    Args:
        data: OHLC数据，必须包含'high'和'low'列
        current_idx: 当前日期索引
        narrowing_ratio: 收窄比例阈值，默认0.8（收窄20%）

    Returns:
        bool: 是否形成收敛形态
    """
    if current_idx < 4:
        return False

    # 取最近5日的高低价
    highs = data['high'].iloc[current_idx-4:current_idx+1]
    lows = data['low'].iloc[current_idx-4:current_idx+1]

    if len(highs) < 5 or len(lows) < 5:
        return False

    # 最近两日的区间 vs 前三日的区间
    recent_range = max(highs.iloc[-2:]) - min(lows.iloc[-2:])
    earlier_range = max(highs.iloc[:-2]) - min(lows.iloc[:-2])

    # 避免除零错误
    if earlier_range <= 0:
        return False

    return recent_range < earlier_range * narrowing_ratio


def generate_signals(data: pd.DataFrame,
                     convergence_threshold: float = 0.01,
                     breakout_threshold: float = 0.01,
                     narrowing_ratio: float = 0.8) -> pd.Series:
    """
    三角形突破因子：生成交易信号

    三个核心条件（全部满足才触发信号）：
    1. 前5日收敛：每日涨跌幅绝对值 <= convergence_threshold
    2. 当日突破：涨跌幅绝对值 > breakout_threshold
    3. 区间收窄：最近2日区间 < 前3日区间 * narrowing_ratio

    Args:
        data: OHLC价格数据，必须包含['open', 'high', 'low', 'close']列
        convergence_threshold: 收敛阈值，默认0.01（1%）
        breakout_threshold: 突破阈值，默认0.01（1%）
        narrowing_ratio: 收窄比例，默认0.8（收窄20%）

    Returns:
        pd.Series: 信号序列，True表示信号触发，索引与data一致

    Example:
        >>> data = load_ohlc_data('000985.CSI', '2013-01-01', '2025-04-30')
        >>> signals = generate_signals(data, convergence_threshold=0.01,
        ...                           breakout_threshold=0.01,
        ...                           narrowing_ratio=0.8)
        >>> signal_dates = signals[signals == True].index.tolist()
    """
    # 输入验证
    required_cols = ['open', 'high', 'low', 'close']
    for col in required_cols:
        if col not in data.columns:
            raise ValueError(f"数据必须包含列: {col}")

    # 初始化信号序列
    signals = pd.Series(False, index=data.index)

    # 计算日收益率
    daily_return = data['close'].pct_change()

    # 从第10天开始（需要足够的历史数据）
    for i in range(9, len(data)):
        try:
            # 条件1：前5日收敛 (第i-5到第i-1日)
            convergence_period = daily_return.iloc[i-5:i]
            convergence = all(abs(convergence_period) <= convergence_threshold)

            # 条件2：当日突破
            current_return = daily_return.iloc[i]
            breakout = abs(current_return) > breakout_threshold

            # 条件3：区间收窄（使用前一日判断形态）
            narrowing = _is_converging_triangle(data, i-1, narrowing_ratio)

            # 综合信号：三个条件都满足
            signals.iloc[i] = (convergence and breakout and narrowing
                             and not pd.isna(current_return))

        except Exception:
            # 处理异常情况，继续下一次循环
            continue

    return signals


def get_signal_direction(data: pd.DataFrame, signals: pd.Series) -> pd.Series:
    """
    获取信号方向（做多/做空）

    Args:
        data: OHLC价格数据
        signals: 信号序列

    Returns:
        pd.Series: 信号方向，'up'表示向上突破(做多)，'down'表示向下突破(做空)
    """
    daily_return = data['close'].pct_change()
    directions = pd.Series('', index=data.index)

    for date in signals[signals == True].index:
        ret = daily_return.loc[date]
        directions.loc[date] = 'up' if ret > 0 else 'down'

    return directions


# 预设参数配置
PRESET_PARAMS = {
    'basic': {
        'convergence_threshold': 0.01,   # 1%
        'breakout_threshold': 0.01,      # 1%
        'narrowing_ratio': 0.8,          # 收窄20%
        'description': '基础版本：最直观的参数，无调参嫌疑'
    },
    'strict': {
        'convergence_threshold': 0.008,  # 0.8%
        'breakout_threshold': 0.015,     # 1.5%
        'narrowing_ratio': 0.7,          # 收窄30%
        'description': '严格版本：更小的收敛阈值，更大的突破要求'
    },
    'loose': {
        'convergence_threshold': 0.012,  # 1.2%
        'breakout_threshold': 0.008,     # 0.8%
        'narrowing_ratio': 0.85,         # 收窄15%
        'description': '宽松版本：更宽松的条件，信号更多'
    }
}


def generate_signals_preset(data: pd.DataFrame, preset: str = 'basic') -> pd.Series:
    """
    使用预设参数生成信号

    Args:
        data: OHLC价格数据
        preset: 预设参数名称，可选'basic', 'strict', 'loose'

    Returns:
        pd.Series: 信号序列
    """
    if preset not in PRESET_PARAMS:
        raise ValueError(f"未知的预设参数: {preset}. 可选: {list(PRESET_PARAMS.keys())}")

    params = PRESET_PARAMS[preset]
    return generate_signals(
        data,
        convergence_threshold=params['convergence_threshold'],
        breakout_threshold=params['breakout_threshold'],
        narrowing_ratio=params['narrowing_ratio']
    )
