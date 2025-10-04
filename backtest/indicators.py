"""
技术指标计算模块
Technical Indicators Module

包含ATR等常用技术指标的计算
"""

import numpy as np
import pandas as pd
from typing import Union, Tuple


def calculate_true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """
    计算真实波动率（True Range）

    TR = max(high - low, abs(high - prev_close), abs(low - prev_close))

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列

    Returns:
        真实波动率序列
    """
    if len(high) != len(low) or len(high) != len(close):
        raise ValueError("价格序列长度必须相等")

    # 前一日收盘价
    prev_close = close.shift(1)

    # 计算三个候选值
    hl = high - low
    hc = (high - prev_close).abs()
    lc = (low - prev_close).abs()

    # 取最大值作为真实波动率
    tr = pd.DataFrame({'hl': hl, 'hc': hc, 'lc': lc}).max(axis=1)

    return tr


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                 window: int = 60) -> pd.Series:
    """
    计算平均真实波动率（Average True Range）

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        window: 平均窗口期，默认60日

    Returns:
        ATR序列（相对值，已除以收盘价）
    """
    # 计算真实波动率
    tr = calculate_true_range(high, low, close)

    # 计算简单移动平均
    atr_abs = tr.rolling(window=window, min_periods=window).mean()

    # 转换为相对ATR（ATR / 收盘价）
    atr_relative = atr_abs / close

    return atr_relative


def get_atr_correction_factor(atr60: Union[float, pd.Series]) -> Union[float, pd.Series]:
    """
    根据ATR60计算修正因子

    修正规则：
    - ATR60 < 1%: correction = sqrt(ATR60 / 1%)  # 缩小阈值
    - ATR60 > 2%: correction = sqrt(ATR60 / 2%)  # 放大阈值
    - 1% <= ATR60 <= 2%: correction = 1.0       # 阈值不变

    Args:
        atr60: ATR60值或序列

    Returns:
        修正因子
    """
    if isinstance(atr60, pd.Series):
        correction = pd.Series(index=atr60.index, dtype=float)

        # ATR < 1%
        mask_low = atr60 < 0.01
        correction[mask_low] = np.sqrt(atr60[mask_low] / 0.01)

        # ATR > 2%
        mask_high = atr60 > 0.02
        correction[mask_high] = np.sqrt(atr60[mask_high] / 0.02)

        # 1% <= ATR <= 2%
        mask_normal = (atr60 >= 0.01) & (atr60 <= 0.02)
        correction[mask_normal] = 1.0

        return correction
    else:
        # 单个值处理
        if atr60 < 0.01:
            return np.sqrt(atr60 / 0.01)
        elif atr60 > 0.02:
            return np.sqrt(atr60 / 0.02)
        else:
            return 1.0


def get_adjusted_thresholds(atr60: Union[float, pd.Series],
                           base_decline: float = -0.05,
                           base_rebound: float = 0.005) -> Tuple[Union[float, pd.Series], Union[float, pd.Series]]:
    """
    获取ATR调整后的阈值

    Args:
        atr60: ATR60值或序列
        base_decline: 基础下跌阈值，默认-5%
        base_rebound: 基础反弹阈值，默认0.5%

    Returns:
        (调整后的下跌阈值, 调整后的反弹阈值)
    """
    correction = get_atr_correction_factor(atr60)

    adjusted_decline = base_decline * correction
    adjusted_rebound = base_rebound * correction

    return adjusted_decline, adjusted_rebound
