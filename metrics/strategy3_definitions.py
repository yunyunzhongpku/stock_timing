"""
策略3：三角形突破形态定义
基于收敛+突破+区间收窄的三重条件判断
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional


class Strategy3Definitions:
    """策略3：三角形突破形态的定义和实现"""
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化策略3定义类
        
        Args:
            data: 包含OHLC数据的DataFrame，必须包含列：open, high, low, close
        """
        self.data = data.copy()
        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(f"数据必须包含列: {col}")
    
    def is_converging_triangle_simple(self, current_idx: int, narrowing_ratio: float = 0.8) -> bool:
        """
        简单直接的收敛判断：看区间宽度是否在缩小
        
        Args:
            current_idx: 当前日期索引
            narrowing_ratio: 收窄比例阈值，默认0.8（收窄20%）
            
        Returns:
            bool: 是否形成收敛形态
        """
        if current_idx < 4:
            return False
        
        # 取最近5日的高低价
        highs = self.data['high'].iloc[current_idx-4:current_idx+1]
        lows = self.data['low'].iloc[current_idx-4:current_idx+1]
        
        if len(highs) < 5 or len(lows) < 5:
            return False
        
        # 最近两日的区间 vs 前三日的区间
        recent_range = max(highs.iloc[-2:]) - min(lows.iloc[-2:])
        earlier_range = max(highs.iloc[:-2]) - min(lows.iloc[:-2])
        
        # 避免除零错误
        if earlier_range <= 0:
            return False
            
        return recent_range < earlier_range * narrowing_ratio
    
    def triangle_breakout_strategy(self, 
                                  convergence_threshold: float = 0.01,
                                  breakout_threshold: float = 0.01,
                                  narrowing_ratio: float = 0.8) -> pd.Series:
        """
        三角形突破策略完整实现
        
        三个核心条件：
        1. 前5日收敛：每日涨跌幅绝对值 <= 1%
        2. 当日突破：涨跌幅绝对值 > 1%  
        3. 区间收窄：最近区间 < 前期区间 * 0.8
        
        Args:
            convergence_threshold: 收敛阈值，默认1%
            breakout_threshold: 突破阈值，默认1%
            narrowing_ratio: 收窄比例，默认0.8
            
        Returns:
            pd.Series: 信号序列，True表示信号触发
        """
        signals = pd.Series(False, index=self.data.index)
        
        # 计算日收益率
        daily_return = self.data['close'].pct_change()
        
        # 从第10天开始（需要足够的历史数据）
        for i in range(9, len(self.data)):
            try:
                # 条件1：前5日收敛 (第i-5到第i-1日)
                convergence_period = daily_return.iloc[i-5:i]
                convergence = all(abs(convergence_period) <= convergence_threshold)
                
                # 条件2：当日突破
                current_return = daily_return.iloc[i]
                breakout = abs(current_return) > breakout_threshold
                
                # 条件3：区间收窄（使用前一日判断形态）
                narrowing = self.is_converging_triangle_simple(i-1, narrowing_ratio)
                
                # 综合信号：三个条件都满足
                signals.iloc[i] = convergence and breakout and narrowing and not pd.isna(current_return)
                
            except Exception as e:
                # 处理异常情况，继续下一次循环
                continue
        
        return signals
    
    def get_strategy_signals(self) -> Dict[str, pd.Series]:
        """
        获取策略3的信号结果
        
        Returns:
            Dict[str, pd.Series]: 包含不同参数设置的信号结果
        """
        results = {}
        
        # 基础版本
        results['triangle_breakout_basic'] = self.triangle_breakout_strategy()
        
        # 严格版本（更小的阈值）
        results['triangle_breakout_strict'] = self.triangle_breakout_strategy(
            convergence_threshold=0.008,  # 0.8%
            breakout_threshold=0.015,     # 1.5%
            narrowing_ratio=0.7           # 收窄30%
        )
        
        # 宽松版本（更大的阈值）
        results['triangle_breakout_loose'] = self.triangle_breakout_strategy(
            convergence_threshold=0.012,  # 1.2%
            breakout_threshold=0.008,     # 0.8%
            narrowing_ratio=0.85          # 收窄15%
        )
        
        return results
    
    def analyze_convergence_patterns(self) -> pd.DataFrame:
        """
        分析收敛形态的分布情况
        
        Returns:
            pd.DataFrame: 收敛形态分析结果
        """
        analysis_data = []
        
        for i in range(9, len(self.data)):
            try:
                # 检查是否有收敛形态
                is_converging = self.is_converging_triangle_simple(i-1)
                
                if is_converging:
                    # 计算当前区间特征
                    highs = self.data['high'].iloc[i-4:i+1]
                    lows = self.data['low'].iloc[i-4:i+1]
                    
                    period_high = highs.max()
                    period_low = lows.min()
                    period_range = period_high - period_low
                    
                    # 记录形态特征
                    analysis_data.append({
                        'date': self.data.index[i],
                        'period_high': period_high,
                        'period_low': period_low,
                        'period_range': period_range,
                        'close_price': self.data['close'].iloc[i],
                        'daily_return': self.data['close'].pct_change().iloc[i]
                    })
                    
            except Exception:
                continue
        
        if analysis_data:
            return pd.DataFrame(analysis_data)
        else:
            return pd.DataFrame()
    
    def get_signal_summary(self) -> Dict:
        """
        获取信号汇总统计
        
        Returns:
            Dict: 信号统计结果
        """
        all_signals = self.get_strategy_signals()
        summary = {}
        
        for signal_name, signal_series in all_signals.items():
            signal_dates = signal_series[signal_series == True].index.tolist()
            
            summary[signal_name] = {
                'total_signals': len(signal_dates),
                'signal_dates': signal_dates,
                'avg_signals_per_year': len(signal_dates) / (len(self.data) / 252) if len(self.data) > 0 else 0,
                'first_signal': signal_dates[0] if signal_dates else None,
                'last_signal': signal_dates[-1] if signal_dates else None
            }
        
        return summary


def main():
    """测试策略3定义"""
    
    # 这里可以加载测试数据进行验证
    print("策略3定义模块已创建")
    print("包含的主要功能：")
    print("1. is_converging_triangle_simple() - 收敛形态判断")
    print("2. triangle_breakout_strategy() - 完整突破策略")
    print("3. get_strategy_signals() - 多参数版本对比")
    print("4. analyze_convergence_patterns() - 形态分析")
    print("5. get_signal_summary() - 信号汇总统计")


if __name__ == "__main__":
    main()