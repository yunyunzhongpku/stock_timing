"""
策略1：下跌反弹形态的正确定义（完全重写版）
严格按照原始要求实现，修正所有概念性错误
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Optional, NamedTuple
from .atr import get_adjusted_thresholds


class TrendResult(NamedTuple):
    """下跌趋势分析结果"""
    is_valid: bool          # 是否为有效的下跌趋势
    ends_today: bool        # 趋势是否在当日结束
    bottom_price: float     # 趋势底部价格
    bottom_idx: int         # 趋势底部位置
    high_price: float       # 趋势起点高价
    high_idx: int           # 趋势起点位置


class Strategy1Definitions:
    """策略1的正确实现（完全重写版）"""
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化策略定义类
        
        Args:
            data: 包含OHLC数据的DataFrame，必须包含列：close, atr60
        """
        self.data = data.copy()
        required_cols = ['close', 'atr60']
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(f"数据必须包含列: {col}")
    
    def correct_decline_rebound_strategy(self, 
                                       lookback_days: int = 20) -> pd.Series:
        """
        完全正确的下跌反弹形态策略实现
        
        核心修正：
        1. 累计跌幅 = 从高点到趋势底部的跌幅（非高点到当前点）
        2. 反弹幅度 = 从趋势底部到当前点的反弹（非当日涨跌幅）
        3. 下跌趋势识别 = 逐日追踪，反弹超过阈值时趋势结束
        4. 信号触发 = 趋势结束当日，且满足跌幅和反弹条件
        
        Args:
            lookback_days: 回看天数，用于寻找高点
            
        Returns:
            信号序列（True表示信号日）
        """
        close = self.data['close'].copy()
        atr60 = self.data['atr60'].copy()
        
        signals = pd.Series(False, index=close.index)
        triggered_signals = []  # 记录已触发的信号位置
        
        for i in range(lookback_days, len(close)):
            current_price = close.iloc[i]
            
            # 获取当日ATR调整后的阈值
            current_atr = atr60.iloc[i]
            if pd.isna(current_atr):
                continue
            decline_threshold, rebound_threshold = get_adjusted_thresholds(current_atr)
            
            # 1. 寻找回看期内的所有可能高点
            lookback_start = max(0, i - lookback_days)
            
            # 遍历回看期内的每个可能高点
            for high_candidate_idx in range(lookback_start, i):
                high_price = close.iloc[high_candidate_idx]
                
                # 2. 从该高点追踪下跌趋势
                trend_result = self._trace_decline_trend(
                    close, atr60, high_candidate_idx, i, rebound_threshold
                )
                
                # 3. 检查是否为有效信号
                if trend_result.is_valid and trend_result.ends_today:
                    # 计算整个趋势的累计跌幅（高点到底部）
                    total_decline = (trend_result.bottom_price - trend_result.high_price) / trend_result.high_price
                    
                    # 计算从趋势底部到当前的反弹幅度
                    rebound_from_bottom = (current_price - trend_result.bottom_price) / trend_result.bottom_price
                    
                    # 检查条件
                    decline_ok = total_decline <= decline_threshold
                    rebound_ok = rebound_from_bottom >= rebound_threshold
                    
                    # 确保高点到当前点之间没有其他信号
                    no_signal_between = not self._has_signal_between(
                        triggered_signals, trend_result.high_idx, i
                    )
                    
                    if decline_ok and rebound_ok and no_signal_between:
                        signals.iloc[i] = True
                        triggered_signals.append(i)
                        break  # 找到一个有效信号就停止，避免重复
                        
        return signals
    
    def _trace_decline_trend(self, close: pd.Series, atr60: pd.Series, 
                           high_idx: int, current_idx: int, 
                           current_rebound_threshold: float) -> TrendResult:
        """
        从指定高点追踪完整的下跌趋势
        
        关键逻辑：
        - 从高点开始，逐日检查
        - 记录过程中的最低点作为趋势底部
        - 当某日反弹超过阈值时，认为趋势结束
        - 只有趋势在current_idx这一天结束才返回有效结果
        
        Args:
            close: 收盘价序列
            atr60: ATR60序列  
            high_idx: 趋势起点（高点）
            current_idx: 当前要判断的日期
            current_rebound_threshold: 当日的反弹阈值
            
        Returns:
            趋势分析结果
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
            
            # 更新趋势底部
            if current_price < bottom_price:
                bottom_price = current_price
                bottom_idx = i
            
            # 计算当日相对前日的涨跌幅
            daily_return = (current_price - prev_price) / prev_price
            
            # 获取当日的反弹阈值（每日动态调整）
            day_atr = atr60.iloc[i]
            if pd.isna(day_atr):
                continue
            
            _, day_rebound_threshold = get_adjusted_thresholds(day_atr)
            
            # 检查是否趋势结束（反弹超过当日阈值）
            if daily_return >= day_rebound_threshold:
                # 只有在current_idx这天趋势结束才认为是有效信号
                ends_today = (i == current_idx)
                
                # 确保整体确实是下跌趋势
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
        
        # 如果到了current_idx还没有趋势结束，返回无效
        return TrendResult(False, False, 0, 0, 0, 0)
    
    def _has_signal_between(self, triggered_signals: List[int], 
                          high_idx: int, current_idx: int) -> bool:
        """
        检查高点到当前点之间是否已有其他信号
        
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
    
    def get_strategy_signals(self, lookback_days: int = 20) -> dict:
        """
        获取策略信号
        
        Args:
            lookback_days: 回看天数
            
        Returns:
            包含策略信号的字典
        """
        return {
            'correct_decline_rebound': self.correct_decline_rebound_strategy(lookback_days)
        }
    
    def debug_signal_day(self, target_date, lookback_days: int = 20) -> dict:
        """
        调试特定日期的信号分析过程
        
        Args:
            target_date: 要调试的日期
            lookback_days: 回看天数
            
        Returns:
            调试信息字典
        """
        close = self.data['close']
        atr60 = self.data['atr60']
        
        try:
            target_idx = close.index.get_loc(target_date)
        except KeyError:
            return {"error": f"日期 {target_date} 不在数据范围内"}
        
        current_atr = atr60.iloc[target_idx]
        if pd.isna(current_atr):
            return {"error": f"日期 {target_date} 的ATR数据缺失"}
        
        decline_threshold, rebound_threshold = get_adjusted_thresholds(current_atr)
        
        debug_info = {
            "target_date": target_date,
            "current_price": close.iloc[target_idx],
            "current_atr": current_atr,
            "decline_threshold": decline_threshold,
            "rebound_threshold": rebound_threshold,
            "trends_found": []
        }
        
        # 分析所有可能的高点
        lookback_start = max(0, target_idx - lookback_days)
        for high_idx in range(lookback_start, target_idx):
            trend_result = self._trace_decline_trend(
                close, atr60, high_idx, target_idx, rebound_threshold
            )
            
            if trend_result.is_valid:
                total_decline = (trend_result.bottom_price - trend_result.high_price) / trend_result.high_price
                current_price = close.iloc[target_idx]
                rebound_from_bottom = (current_price - trend_result.bottom_price) / trend_result.bottom_price
                
                trend_info = {
                    "high_date": close.index[high_idx],
                    "high_price": trend_result.high_price,
                    "bottom_date": close.index[trend_result.bottom_idx], 
                    "bottom_price": trend_result.bottom_price,
                    "total_decline": total_decline,
                    "rebound_from_bottom": rebound_from_bottom,
                    "ends_today": trend_result.ends_today,
                    "decline_ok": total_decline <= decline_threshold,
                    "rebound_ok": rebound_from_bottom >= rebound_threshold
                }
                debug_info["trends_found"].append(trend_info)
        
        return debug_info