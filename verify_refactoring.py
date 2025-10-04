"""
验证脚本：确保重构后的代码与原始版本产生一致的结果
Verification Script: Ensure refactored code produces identical results

测试内容：
1. Strategy3 (三角形突破) 信号生成
2. 回测分析结果对比
"""

import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入旧版本代码
from data_loader import WindDataLoader
from metrics.strategy3_definitions import Strategy3Definitions

# 导入新版本代码
from data.loader import DataLoader
from factors.triangle_breakout import generate_signals
from backtest.signal_analyzer import analyze_signals
from config import get_strategy_parameters, get_holding_periods


def compare_dataframes(df1, df2, name: str, tolerance: float = 1e-6):
    """
    比较两个DataFrame是否相同

    Args:
        df1: 第一个DataFrame
        df2: 第二个DataFrame
        name: 数据名称
        tolerance: 数值容差

    Returns:
        bool: 是否相同
    """
    print(f"\n检查 {name}...")

    # 检查形状
    if df1.shape != df2.shape:
        print(f"  [FAIL] 形状不一致: {df1.shape} vs {df2.shape}")
        return False

    # 检查索引
    if not df1.index.equals(df2.index):
        print(f"  [FAIL] 索引不一致")
        return False

    # 检查列名
    if not all(df1.columns == df2.columns):
        print(f"  [FAIL] 列名不一致")
        return False

    # 检查数值
    try:
        pd.testing.assert_frame_equal(df1, df2, atol=tolerance, rtol=tolerance)
        print(f"  [OK] 完全一致")
        return True
    except AssertionError as e:
        print(f"  [FAIL] 数值不一致: {e}")
        return False


def compare_series(s1, s2, name: str):
    """比较两个Series是否相同"""
    print(f"\n检查 {name}...")

    # 检查长度
    if len(s1) != len(s2):
        print(f"  [FAIL] 长度不一致: {len(s1)} vs {len(s2)}")
        return False

    # 检查索引
    if not s1.index.equals(s2.index):
        print(f"  [FAIL] 索引不一致")
        return False

    # 检查值
    try:
        pd.testing.assert_series_equal(s1, s2)
        print(f"  [OK] 完全一致")
        return True
    except AssertionError as e:
        print(f"  [FAIL] 值不一致: {e}")
        # 打印详细差异
        diff_mask = (s1 != s2)
        if diff_mask.any():
            print(f"  差异位置数量: {diff_mask.sum()}")
            diff_indices = s1.index[diff_mask]
            if len(diff_indices) <= 10:
                print(f"  差异位置: {diff_indices.tolist()}")
        return False


def verify_strategy3_signals():
    """验证Strategy3信号生成"""
    print("\n" + "="*100)
    print("验证 Strategy3 (三角形突破) 信号生成")
    print("="*100)

    # 加载数据（使用相同的数据源）
    print("\n加载数据...")
    loader = WindDataLoader()
    data = loader.get_csi_all_data("2013-01-01", "2025-04-30")

    # 处理日期显示（兼容datetime.date和Timestamp）
    start_date = data.index[0] if hasattr(data.index[0], 'date') else data.index[0]
    end_date = data.index[-1] if hasattr(data.index[-1], 'date') else data.index[-1]
    if hasattr(start_date, 'date'):
        start_date = start_date.date()
    if hasattr(end_date, 'date'):
        end_date = end_date.date()

    print(f"数据范围: {start_date} 到 {end_date}")
    print(f"数据量: {len(data)} 条")

    # ===== 旧版本 =====
    print("\n使用旧版本代码生成信号...")
    strategy_old = Strategy3Definitions(data)
    signals_old_dict = strategy_old.get_strategy_signals()
    signals_old = signals_old_dict['triangle_breakout_basic']

    signal_dates_old = signals_old[signals_old == True].index.tolist()
    print(f"旧版本找到 {len(signal_dates_old)} 个信号")

    # ===== 新版本 =====
    print("\n使用新版本代码生成信号...")
    params = get_strategy_parameters('triangle_breakout', preset='basic')
    signals_new = generate_signals(
        data,
        convergence_threshold=params['convergence_threshold'],
        breakout_threshold=params['breakout_threshold'],
        narrowing_ratio=params['narrowing_ratio']
    )

    signal_dates_new = signals_new[signals_new == True].index.tolist()
    print(f"新版本找到 {len(signal_dates_new)} 个信号")

    # ===== 对比 =====
    print("\n" + "="*100)
    print("对比结果")
    print("="*100)

    # 对比信号序列
    result = compare_series(signals_old, signals_new, "信号序列")

    # 对比信号日期列表
    if signal_dates_old == signal_dates_new:
        print("\n信号日期列表: [OK] 完全一致")
    else:
        print("\n信号日期列表: [FAIL] 不一致")
        only_in_old = set(signal_dates_old) - set(signal_dates_new)
        only_in_new = set(signal_dates_new) - set(signal_dates_old)
        if only_in_old:
            print(f"  仅在旧版本: {only_in_old}")
        if only_in_new:
            print(f"  仅在新版本: {only_in_new}")

    return result


def verify_strategy3_backtest():
    """验证Strategy3回测结果"""
    print("\n" + "="*100)
    print("验证 Strategy3 回测分析")
    print("="*100)

    # 这个测试比较简单：只要信号一致，回测结果应该也一致
    # 因为回测逻辑是新写的，没有对应的旧版本
    # 我们主要检查回测分析器是否能正常运行

    print("\n加载数据...")
    loader = WindDataLoader()
    data = loader.get_csi_all_data("2013-01-01", "2025-04-30")

    print("\n生成信号...")
    params = get_strategy_parameters('triangle_breakout', preset='basic')
    signals = generate_signals(
        data,
        convergence_threshold=params['convergence_threshold'],
        breakout_threshold=params['breakout_threshold'],
        narrowing_ratio=params['narrowing_ratio']
    )

    print(f"找到 {signals.sum()} 个信号")

    print("\n执行回测...")
    results = analyze_signals(
        data,
        signals,
        holding_periods=get_holding_periods(),
        direction='bidirectional'
    )

    # 检查结果结构
    print("\n检查回测结果结构...")
    required_keys = ['performance_results', 'stats_summary', 'total_signals', 'holding_periods']
    all_ok = True

    for key in required_keys:
        if key in results:
            print(f"  {key}: [OK]")
        else:
            print(f"  {key}: [FAIL] 缺失")
            all_ok = False

    # 检查统计摘要
    if 'stats_summary' in results:
        stats = results['stats_summary']
        print(f"\n统计摘要包含 {len(stats)} 个持有期")
        for period_name, period_stats in stats.items():
            print(f"  {period_name}: 样本数={period_stats['样本数量']}, "
                  f"平均收益={period_stats['平均收益']:.2f}%, "
                  f"显著性={period_stats['显著性']}")

    return all_ok


def main():
    """主函数"""
    print("\n" + "="*100)
    print("重构验证测试")
    print("="*100)
    print("\n测试重构后的代码是否与原始版本产生一致的结果")

    results = {}

    # 测试1: Strategy3 信号生成
    try:
        results['strategy3_signals'] = verify_strategy3_signals()
    except Exception as e:
        print(f"\n[ERROR] Strategy3信号生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['strategy3_signals'] = False

    # 测试2: Strategy3 回测
    try:
        results['strategy3_backtest'] = verify_strategy3_backtest()
    except Exception as e:
        print(f"\n[ERROR] Strategy3回测测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['strategy3_backtest'] = False

    # 总结
    print("\n" + "="*100)
    print("验证总结")
    print("="*100)

    all_passed = all(results.values())

    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")

    print("\n" + "="*100)
    if all_passed:
        print("[OK] 所有测试通过！重构成功！")
    else:
        print("[WARN] 部分测试失败，需要检查差异")
    print("="*100)

    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
