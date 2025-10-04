"""
回测分析器
Signal Backtest Analyzer

通用的信号回测分析工具，支持：
- 固定持有期收益分析
- 统计显著性检验
- 双向交易（做多/做空）
- 时间分割分析（训练期/测试期）
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Any, Dict, List, Tuple, Optional


def analyze_signals(data: pd.DataFrame,
                    signals: pd.Series,
                    holding_periods: List[int] = [1, 5, 10, 20, 40],
                    direction: str = 'bidirectional') -> Dict:
    """
    分析信号触发后的收益表现

    Args:
        data: OHLC价格数据，必须包含'close'列
        signals: 信号序列，True表示信号触发
        holding_periods: 持有期列表，例如[1, 5, 10, 20, 40]表示分析1日、5日...后的收益
        direction: 交易方向
            - 'long': 只做多（所有信号都买入）
            - 'short': 只做空（所有信号都卖出）
            - 'bidirectional': 双向交易（根据信号当日涨跌判断方向）

    Returns:
        包含收益统计的字典，格式为：
        {
            'performance_results': [...],  # 每个信号的详细收益
            'stats_summary': {...}         # 汇总统计
        }
    """
    if 'close' not in data.columns:
        raise ValueError("数据必须包含'close'列")

    # 获取所有信号日期
    signal_dates = signals[signals == True].index.tolist()

    if len(signal_dates) == 0:
        return {
            'performance_results': [],
            'stats_summary': {},
            'error': '没有找到任何信号'
        }

    # 分析每个信号后的收益
    performance_results = []

    for signal_date in signal_dates:
        try:
            # 定位信号日期
            idx_arr = data.index.get_indexer([signal_date])
            if idx_arr.size == 0 or idx_arr[0] == -1:
                continue
            signal_idx = int(idx_arr[0])

            # 确保有足够的后续数据
            max_period = max(holding_periods)
            if signal_idx + max_period >= len(data):
                continue

            # 计算收益
            base_price = data['close'].iloc[signal_idx]
            future_prices = data['close'].iloc[signal_idx:signal_idx + max_period + 1]

            # 判断信号方向
            if direction == 'bidirectional':
                signal_return = data['close'].pct_change().iloc[signal_idx]
                trade_direction = 'up' if signal_return > 0 else 'down'
            elif direction == 'long':
                trade_direction = 'up'
            else:  # short
                trade_direction = 'down'

            # 计算原始价格变化（用于可视化）
            price_returns = (future_prices / base_price - 1) * 100

            # 计算交易收益（考虑做多/做空）
            if trade_direction == 'up':
                # 做多：价格上涨为正收益
                trading_returns = (future_prices / base_price - 1) * 100
            else:
                # 做空：价格下跌为正收益
                trading_returns = (base_price / future_prices - 1) * 100

            # 记录各持有期的收益
            result = {
                'signal_date': signal_date,
                'base_price': base_price,
                'direction': trade_direction
            }

            # 添加各持有期收益
            for period in holding_periods:
                if period < len(trading_returns):
                    result[f'day_{period}_return'] = trading_returns.iloc[period]
                else:
                    result[f'day_{period}_return'] = np.nan

            # 添加序列数据（用于绘图）
            result['price_returns_series'] = price_returns.iloc[1:max_period+1].values if len(price_returns) > max_period else None
            result['trading_returns_series'] = trading_returns.iloc[1:max_period+1].values if len(trading_returns) > max_period else None

            performance_results.append(result)

        except Exception as e:
            print(f"处理信号 {signal_date} 时出错: {e}")
            continue

    if not performance_results:
        return {
            'performance_results': [],
            'stats_summary': {},
            'error': '没有足够的数据进行分析'
        }

    # 计算统计指标
    stats_summary = _calculate_statistics(performance_results, holding_periods)

    return {
        'performance_results': performance_results,
        'stats_summary': stats_summary,
        'total_signals': len(performance_results),
        'holding_periods': holding_periods
    }


def _calculate_statistics(performance_results: List[Dict],
                          holding_periods: List[int]) -> Dict:
    """
    计算统计指标

    Args:
        performance_results: 信号表现结果列表
        holding_periods: 持有期列表

    Returns:
        统计汇总字典
    """
    stats_summary = {}

    for period in holding_periods:
        period_key = f'day_{period}_return'
        period_name = f'{period}日'

        # 提取该持有期的所有收益
        returns_list = [r[period_key] for r in performance_results if not np.isnan(r[period_key])]

        if not returns_list:
            continue

        # 计算统计量
        mean_return = np.mean(returns_list)
        median_return = np.median(returns_list)
        std_return = np.std(returns_list)
        positive_ratio = sum(r > 0 for r in returns_list) / len(returns_list) * 100

        # t检验：检验平均收益是否显著大于0
        res_any: Any = stats.ttest_1samp(returns_list, 0)
        t_stat = float(getattr(res_any, 'statistic', res_any[0]))
        p_value = float(getattr(res_any, 'pvalue', res_any[1]))

        stats_summary[period_name] = {
            '样本数量': len(returns_list),
            '平均收益': mean_return,
            '中位收益': median_return,
            '标准差': std_return,
            '胜率': positive_ratio,
            't统计量': t_stat,
            'p值': p_value,
            '显著性': 'yes' if p_value < 0.05 else 'no'
        }

    return stats_summary


def analyze_signals_with_time_split(data: pd.DataFrame,
                                    signals: pd.Series,
                                    split_date: str,
                                    holding_periods: List[int] = [1, 5, 10, 20, 40],
                                    direction: str = 'bidirectional') -> Tuple[Dict, Dict]:
    """
    分析信号，按时间分割为训练期和测试期

    Args:
        data: OHLC价格数据
        signals: 信号序列
        split_date: 分割日期，例如'2022-01-01'
        holding_periods: 持有期列表
        direction: 交易方向

    Returns:
        (训练期结果, 测试期结果)
    """
    # 分割信号
    split_date_pd = pd.Timestamp(split_date)
    signal_dates = signals[signals == True].index.tolist()

    in_sample_signals = pd.Series(False, index=data.index)
    out_sample_signals = pd.Series(False, index=data.index)

    for date in signal_dates:
        if pd.Timestamp(date) < split_date_pd:
            in_sample_signals.loc[date] = True
        else:
            out_sample_signals.loc[date] = True

    # 分别分析
    in_sample_results = analyze_signals(
        data, in_sample_signals, holding_periods, direction
    )
    out_sample_results = analyze_signals(
        data, out_sample_signals, holding_periods, direction
    )

    return in_sample_results, out_sample_results


def get_signal_direction(data: pd.DataFrame, signals: pd.Series) -> pd.Series:
    """
    获取每个信号的交易方向

    Args:
        data: OHLC价格数据
        signals: 信号序列

    Returns:
        方向序列，'up'表示做多，'down'表示做空
    """
    daily_return = data['close'].pct_change()
    directions = pd.Series('', index=data.index)

    for date in signals[signals == True].index:
        ret = daily_return.loc[date]
        directions.loc[date] = 'up' if ret > 0 else 'down'

    return directions


def print_analysis_summary(analysis_results: Dict, title: str = "信号分析结果"):
    """
    打印分析结果摘要

    Args:
        analysis_results: analyze_signals返回的结果
        title: 标题
    """
    print("\n" + "="*100)
    print(title)
    print("="*100)

    if 'error' in analysis_results:
        print(f"错误: {analysis_results['error']}")
        return

    print(f"\n总信号数: {analysis_results['total_signals']}")

    stats_summary = analysis_results.get('stats_summary', {})
    if not stats_summary:
        print("没有统计数据")
        return

    print("\n持有期收益统计:")
    print("-" * 100)
    print(f"{'持有期':<8} {'样本数':<8} {'平均收益':<12} {'中位收益':<12} {'胜率':<10} "
          f"{'t统计量':<12} {'p值':<12} {'显著性':<8}")
    print("-" * 100)

    for period_name, stats in stats_summary.items():
        sig = "是" if stats['显著性'] == 'yes' else "否"
        print(f"{period_name:<8} {stats['样本数量']:<8} {stats['平均收益']:>10.2f}% "
              f"{stats['中位收益']:>10.2f}% {stats['胜率']:>8.1f}% "
              f"{stats['t统计量']:>10.3f} {stats['p值']:>10.4f} {sig:<8}")
