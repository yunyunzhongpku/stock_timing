"""
模板示例：在自定义资产上测试因子
Template: Testing Factors on Custom Assets

演示如何将策略因子应用到其他资产（股票、指数、期货等）

使用步骤：
1. 准备OHLC数据
2. 选择因子
3. 生成信号
4. 回测分析
5. 可视化
"""

import sys
import os
import pandas as pd

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入必要模块
from data.loader import DataLoader
from factors.triangle_breakout import generate_signals as triangle_signals
from factors.decline_rebound import generate_signals as decline_signals
from backtest.signal_analyzer import analyze_signals, print_analysis_summary
from backtest.visualizer import plot_signal_performance
from backtest.indicators import calculate_atr
from config import get_strategy_parameters, get_holding_periods, OUTPUT_CONFIG


def load_your_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    加载你自己的数据

    方法1：使用DataLoader（支持Wind）
    方法2：从CSV加载
    方法3：从其他数据源加载

    Returns:
        pd.DataFrame: 必须包含['open', 'high', 'low', 'close']列
    """

    # ===== 方法1: 使用DataLoader =====
    loader = DataLoader()
    data = loader.load_ohlc_data(ticker, start_date, end_date)
    loader.close()
    return data

    # ===== 方法2: 从CSV加载 =====
    # data = pd.read_csv('your_data.csv', index_col='date', parse_dates=True)
    # return data[['open', 'high', 'low', 'close', 'volume']]

    # ===== 方法3: 从其他数据源 =====
    # 实现你自己的数据加载逻辑
    # ...


def analyze_triangle_breakout(data: pd.DataFrame, asset_name: str):
    """
    分析三角形突破因子

    Args:
        data: OHLC数据
        asset_name: 资产名称（用于标题）
    """
    print("\n" + "="*100)
    print(f"{asset_name} - 三角形突破因子分析")
    print("="*100)

    # 1. 获取参数
    params = get_strategy_parameters('triangle_breakout', preset='basic')
    print(f"使用参数: {params['description']}")

    # 2. 生成信号
    signals = triangle_signals(
        data,
        convergence_threshold=params['convergence_threshold'],
        breakout_threshold=params['breakout_threshold'],
        narrowing_ratio=params['narrowing_ratio']
    )

    signal_count = signals.sum()
    print(f"找到 {signal_count} 个信号")

    # 3. 回测分析
    results = analyze_signals(
        data,
        signals,
        holding_periods=get_holding_periods(),
        direction='bidirectional'  # 双向交易
    )

    # 4. 打印结果
    print_analysis_summary(results, title=f"{asset_name} - 三角形突破")

    # 5. 可视化
    output_dir = OUTPUT_CONFIG['output_dir']
    os.makedirs(output_dir, exist_ok=True)

    plot_signal_performance(
        results,
        title=f"{asset_name} - 三角形突破",
        output_path=f"{output_dir}/{asset_name}_triangle_breakout.png"
    )

    return results


def analyze_decline_rebound(data: pd.DataFrame, asset_name: str):
    """
    分析下跌反弹因子（已停止，仅供参考）

    Args:
        data: OHLC数据
        asset_name: 资产名称
    """
    print("\n" + "="*100)
    print(f"{asset_name} - 下跌反弹因子分析")
    print("="*100)
    print("⚠️ 注意：此因子已停止开发，仅供学习参考")

    # 1. 确保有ATR60
    if 'atr60' not in data.columns:
        data['atr60'] = calculate_atr(data['high'], data['low'], data['close'], window=60)

    # 2. 生成信号
    params = get_strategy_parameters('decline_rebound')
    signals = decline_signals(
        data,
        lookback_days=params['lookback_days']
    )

    signal_count = signals.sum()
    print(f"找到 {signal_count} 个信号")

    # 3. 回测分析
    results = analyze_signals(
        data,
        signals,
        holding_periods=get_holding_periods(),
        direction='bidirectional'
    )

    # 4. 打印结果
    print_analysis_summary(results, title=f"{asset_name} - 下跌反弹")

    return results


def main():
    """主函数：自定义资产分析示例"""

    # ===== 配置你的分析 =====
    TICKER = '000985.CSI'  # 修改为你的资产代码
    ASSET_NAME = '中证全指'  # 修改为资产名称
    START_DATE = '2013-01-01'
    END_DATE = '2025-04-30'

    # ===== 1. 加载数据 =====
    print("加载数据...")
    data = load_your_data(TICKER, START_DATE, END_DATE)
    print(f"数据范围: {data.index[0].date()} 到 {data.index[-1].date()}")
    print(f"总数据量: {len(data)} 个交易日")

    # ===== 2. 选择要分析的因子 =====

    # 分析三角形突破
    triangle_results = analyze_triangle_breakout(data, ASSET_NAME)

    # 如果需要，也可以分析下跌反弹（已停止）
    # decline_results = analyze_decline_rebound(data, ASSET_NAME)

    # ===== 3. 对比多个因子（可选）=====
    # 你可以在这里对比不同因子的表现
    # ...

    print("\n" + "="*100)
    print("分析完成！")
    print(f"图表已保存到: {OUTPUT_CONFIG['output_dir']}/")
    print("="*100)


if __name__ == '__main__':
    main()
