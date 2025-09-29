"""
策略3信号日期对比分析 - 纯对比，不调整策略
"""

import pandas as pd
from datetime import datetime
from data_loader import WindDataLoader
from metrics.strategy3_definitions import Strategy3Definitions

def extract_strategy3_signals():
    """提取策略3识别的所有信号日期"""
    
    # 加载数据
    loader = WindDataLoader()
    data = loader.get_csi_all_data("2013-01-01", "2025-04-30")
    
    # 获取策略3信号
    strategy = Strategy3Definitions(data)
    all_signals = strategy.get_strategy_signals()
    
    # 提取推荐策略的信号
    signals = all_signals['triangle_breakout_loose']
    signal_dates = signals[signals == True].index.tolist()
    
    # 获取突破方向
    daily_return = data['close'].pct_change()
    signal_details = []
    
    for date in signal_dates:
        try:
            date_idx = data.index.get_loc(date)
            signal_return = daily_return.iloc[date_idx]
            direction = 'up' if signal_return > 0 else 'down'
            
            signal_details.append({
                'date': date,
                'date_str': date.strftime('%Y%m%d'),
                'direction': direction,
                'return_pct': signal_return * 100
            })
        except:
            continue
    
    return signal_details

def parse_reference_dates(ref_dates_str):
    """解析参考日期"""
    dates = []
    for date_str in ref_dates_str.strip().split('\n'):
        date_str = date_str.strip()
        if len(date_str) == 8:  # YYYYMMDD格式
            try:
                date = datetime.strptime(date_str, '%Y%m%d')
                dates.append({
                    'date': date,
                    'date_str': date_str,
                    'type': 'reference'
                })
            except:
                continue
    return dates

def compare_signals(strategy3_signals, reference_dates):
    """对比两组信号"""
    
    # 转换为日期字符串集合便于比较
    strategy3_dates = {s['date_str'] for s in strategy3_signals}
    strategy3_up_dates = {s['date_str'] for s in strategy3_signals if s['direction'] == 'up'}
    strategy3_down_dates = {s['date_str'] for s in strategy3_signals if s['direction'] == 'down'}
    reference_date_strs = {r['date_str'] for r in reference_dates}
    
    # 精确匹配
    exact_matches = strategy3_dates & reference_date_strs
    exact_matches_up = strategy3_up_dates & reference_date_strs
    exact_matches_down = strategy3_down_dates & reference_date_strs
    
    # 近似匹配（±1-3天）
    def find_nearby_matches(ref_dates, strategy_dates, tolerance_days=3):
        nearby_matches = []
        for ref_date_str in ref_dates:
            ref_date = datetime.strptime(ref_date_str, '%Y%m%d')
            
            for strategy_signal in strategy3_signals:
                strategy_date = strategy_signal['date']
                if hasattr(strategy_date, 'date'):
                    strategy_date = strategy_date.date()
                if hasattr(ref_date, 'date'):
                    ref_date_only = ref_date.date()
                else:
                    ref_date_only = ref_date
                days_diff = abs((strategy_date - ref_date_only).days)
                
                if 1 <= days_diff <= tolerance_days:
                    nearby_matches.append({
                        'ref_date': ref_date_str,
                        'strategy_date': strategy_signal['date_str'],
                        'days_diff': days_diff,
                        'direction': strategy_signal['direction']
                    })
                    break
        return nearby_matches
    
    nearby_matches = find_nearby_matches(reference_date_strs, strategy3_signals)
    
    # 未匹配的参考日期
    unmatched_references = reference_date_strs - strategy3_dates
    nearby_ref_dates = {m['ref_date'] for m in nearby_matches}
    truly_unmatched = unmatched_references - nearby_ref_dates
    
    # 策略3额外的信号
    extra_strategy3 = strategy3_dates - reference_date_strs
    
    return {
        'exact_matches': exact_matches,
        'exact_matches_up': exact_matches_up,
        'exact_matches_down': exact_matches_down,
        'nearby_matches': nearby_matches,
        'unmatched_references': truly_unmatched,
        'extra_strategy3': extra_strategy3,
        'statistics': {
            'total_reference': len(reference_dates),
            'total_strategy3': len(strategy3_signals),
            'strategy3_up': len(strategy3_up_dates),
            'strategy3_down': len(strategy3_down_dates),
            'exact_match_count': len(exact_matches),
            'exact_match_rate': len(exact_matches) / len(reference_dates) * 100,
            'nearby_match_count': len(nearby_matches),
            'total_hit_rate': (len(exact_matches) + len(nearby_matches)) / len(reference_dates) * 100
        }
    }

def print_comparison_report(comparison_result, strategy3_signals, reference_dates):
    """打印对比报告"""
    
    stats = comparison_result['statistics']
    
    print("="*80)
    print("策略3三角形突破信号 vs 参考日期对比分析")
    print("="*80)
    
    print(f"\\n【基本统计】")
    print(f"参考日期总数: {stats['total_reference']}个")
    print(f"策略3信号总数: {stats['total_strategy3']}个")
    print(f"  - 向上突破(做多): {stats['strategy3_up']}个")
    print(f"  - 向下突破(做空): {stats['strategy3_down']}个")
    
    print(f"\\n【匹配情况】")
    print(f"精确匹配: {stats['exact_match_count']}个 ({stats['exact_match_rate']:.1f}%)")
    print(f"  - 匹配的向上突破: {len(comparison_result['exact_matches_up'])}个")
    print(f"  - 匹配的向下突破: {len(comparison_result['exact_matches_down'])}个")
    print(f"近似匹配(±1-3天): {stats['nearby_match_count']}个")
    print(f"总命中率: {stats['total_hit_rate']:.1f}%")
    
    print(f"\\n【精确匹配的日期】")
    if comparison_result['exact_matches']:
        for date_str in sorted(comparison_result['exact_matches']):
            # 找到对应的信号详情
            signal_detail = next((s for s in strategy3_signals if s['date_str'] == date_str), None)
            direction_desc = "做多" if signal_detail['direction'] == 'up' else "做空"
            print(f"  {date_str}: {direction_desc} (突破{signal_detail['return_pct']:.2f}%)")
    else:
        print("  无精确匹配")
    
    print(f"\\n【近似匹配的日期】")
    if comparison_result['nearby_matches']:
        for match in comparison_result['nearby_matches']:
            direction_desc = "做多" if match['direction'] == 'up' else "做空"
            print(f"  参考{match['ref_date']} → 策略{match['strategy_date']} (相差{match['days_diff']}天, {direction_desc})")
    else:
        print("  无近似匹配")
    
    print(f"\\n【未匹配的参考日期】")
    if comparison_result['unmatched_references']:
        print(f"  共{len(comparison_result['unmatched_references'])}个:")
        for date_str in sorted(comparison_result['unmatched_references']):
            print(f"    {date_str}")
    else:
        print("  所有参考日期都被匹配到了！")
    
    print(f"\\n【策略3额外识别的信号】")
    print(f"  共{len(comparison_result['extra_strategy3'])}个 (策略3识别但不在参考列表中)")
    
    # 年度分布对比
    print(f"\\n【年度分布对比】")
    ref_by_year = {}
    strategy3_by_year = {}
    
    for ref in reference_dates:
        year = ref['date'].year
        ref_by_year[year] = ref_by_year.get(year, 0) + 1
    
    for signal in strategy3_signals:
        year = signal['date'].year
        strategy3_by_year[year] = strategy3_by_year.get(year, 0) + 1
    
    all_years = sorted(set(ref_by_year.keys()) | set(strategy3_by_year.keys()))
    print("年份\\t参考日期\\t策略3信号\\t匹配情况")
    print("-" * 50)
    
    for year in all_years:
        ref_count = ref_by_year.get(year, 0)
        strategy3_count = strategy3_by_year.get(year, 0)
        
        # 计算该年度的匹配数
        year_matches = 0
        for date_str in comparison_result['exact_matches']:
            if date_str.startswith(str(year)):
                year_matches += 1
        
        print(f"{year}\\t{ref_count}\\t\\t{strategy3_count}\\t\\t{year_matches}")

def main():
    """主函数"""
    
    # 参考日期（你提供的）
    reference_dates_str = """20130903
20141121
20160531
20160712
20161018
20180306
20180410
20180720
20190115
20191028
20191119
20191213
20200519
20201230
20210625
20211119
20220520
20230116
20230201
20230301
20240830
20250421
20250506
20250529
20250708
20250813"""
    
    print("正在提取策略3信号...")
    strategy3_signals = extract_strategy3_signals()
    
    print("正在解析参考日期...")
    reference_dates = parse_reference_dates(reference_dates_str)
    
    print("正在进行对比分析...")
    comparison_result = compare_signals(strategy3_signals, reference_dates)
    
    print_comparison_report(comparison_result, strategy3_signals, reference_dates)

if __name__ == "__main__":
    main()