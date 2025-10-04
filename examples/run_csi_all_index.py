"""
完整示例：分析中证全指的三角形突破策略
Example: Complete Analysis of Triangle Breakout Strategy on CSI All Index

演示如何使用重构后的模块进行完整的策略分析，包括：
1. 数据加载
2. 信号生成
3. 回测分析
4. 可视化
5. 时间分割验证
"""

import sys
import os

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.loader import load_csi_all_index
from factors.triangle_breakout import generate_signals, get_signal_direction
from backtest.signal_analyzer import (
    analyze_signals,
    analyze_signals_with_time_split,
    print_analysis_summary
)
from backtest.visualizer import (
    plot_signal_performance,
    plot_time_split_comparison,
    print_time_split_summary
)
from config import (
    get_strategy_parameters,
    get_holding_periods,
    get_time_split_date,
    OUTPUT_CONFIG
)


def main():
    """主函数：完整分析流程"""

    print("\n" + "="*100)
    print("中证全指 - 三角形突破策略分析")
    print("="*100)

    # ===== 1. 加载数据 =====
    print("\n[1/5] 加载数据...")
    data = load_csi_all_index(start_date='2013-01-01', end_date='2025-04-30')
    print(f"数据范围: {data.index[0].date()} 到 {data.index[-1].date()}")
    print(f"总数据量: {len(data)} 个交易日")

    # ===== 2. 生成信号 =====
    print("\n[2/5] 生成交易信号...")

    # 使用基础版本参数（无调参嫌疑）
    params = get_strategy_parameters('triangle_breakout', preset='basic')
    print(f"参数设置: {params['description']}")
    print(f"  - 收敛阈值: {params['convergence_threshold']*100:.1f}%")
    print(f"  - 突破阈值: {params['breakout_threshold']*100:.1f}%")
    print(f"  - 收窄比例: {params['narrowing_ratio']}")

    signals = generate_signals(
        data,
        convergence_threshold=params['convergence_threshold'],
        breakout_threshold=params['breakout_threshold'],
        narrowing_ratio=params['narrowing_ratio']
    )

    signal_count = signals.sum()
    print(f"找到 {signal_count} 个信号")

    # 统计信号方向
    directions = get_signal_direction(data, signals)
    up_count = (directions == 'up').sum()
    down_count = (directions == 'down').sum()
    print(f"  - 向上突破（做多）: {up_count} 个")
    print(f"  - 向下突破（做空）: {down_count} 个")

    # ===== 3. 回测分析 =====
    print("\n[3/5] 回测分析...")

    holding_periods = get_holding_periods()
    print(f"持有期设置: {holding_periods}")

    # 全样本分析
    results = analyze_signals(
        data,
        signals,
        holding_periods=holding_periods,
        direction='bidirectional'  # 双向交易
    )

    # 打印分析结果
    print_analysis_summary(results, title="全样本分析结果")

    # ===== 4. 可视化 =====
    print("\n[4/5] 生成可视化图表...")

    output_dir = OUTPUT_CONFIG['output_dir']
    os.makedirs(output_dir, exist_ok=True)

    plot_signal_performance(
        results,
        title="三角形突破策略 - 全样本表现",
        output_path=f"{output_dir}/triangle_breakout_full_sample.png"
    )

    # ===== 5. 时间分割验证 =====
    print("\n[5/5] 时间分割验证...")

    split_date = get_time_split_date()
    print(f"分割日期: {split_date}")

    in_sample, out_sample = analyze_signals_with_time_split(
        data,
        signals,
        split_date=split_date,
        holding_periods=holding_periods,
        direction='bidirectional'
    )

    # 打印训练期/测试期结果
    print_analysis_summary(in_sample, title="训练期(2013-2021)分析结果")
    print_analysis_summary(out_sample, title="测试期(2022-2025)分析结果")

    # 打印对比摘要
    print_time_split_summary(in_sample, out_sample, key_period='20日')

    # 生成对比图表
    plot_time_split_comparison(
        in_sample,
        out_sample,
        title="三角形突破策略",
        output_dir=output_dir
    )

    # ===== 完成 =====
    print("\n" + "="*100)
    print("分析完成！")
    print(f"图表已保存到: {output_dir}/")
    print("="*100)


if __name__ == '__main__':
    main()
