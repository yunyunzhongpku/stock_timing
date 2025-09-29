"""
策略3：三角形突破信号触发后40个交易日收益分析
分析策略信号的预测效果和统计显著性
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
from data_loader import WindDataLoader
from metrics.strategy3_definitions import Strategy3Definitions

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def analyze_signal_performance(strategy_name: str = 'triangle_breakout_loose'):
    """分析指定策略的信号触发后表现"""
    
    print(f"开始分析{strategy_name}信号触发后40个交易日的收益表现...")
    
    # 加载数据
    loader = WindDataLoader()
    data = loader.get_csi_all_data("2013-01-01", "2025-04-30")
    
    # 获取策略信号
    strategy = Strategy3Definitions(data)
    all_signals = strategy.get_strategy_signals()
    
    if strategy_name not in all_signals:
        raise ValueError(f"策略名称 '{strategy_name}' 不存在")
    
    signals = all_signals[strategy_name]
    
    # 获取所有信号日期
    signal_dates = signals[signals == True].index.tolist()
    print(f"找到 {len(signal_dates)} 个信号日期")
    
    # 分析每个信号后40个交易日的收益
    performance_results = []
    
    for signal_date in signal_dates:
        try:
            signal_idx = data.index.get_loc(signal_date)
            
            # 确保有足够的后续数据
            if signal_idx + 40 >= len(data):
                print(f"跳过 {signal_date}: 后续数据不足40个交易日")
                continue
            
            # 计算40个交易日的收益
            base_price = data['close'].iloc[signal_idx]
            future_prices = data['close'].iloc[signal_idx:signal_idx+41]  # 包含信号日
            
            # 获取信号特征
            signal_return = data['close'].pct_change().iloc[signal_idx]
            breakout_direction = 'up' if signal_return > 0 else 'down'
            
            # 计算两套收益率：1) 原始价格变化 2) 交易收益
            # 原始价格变化（用于累计收益曲线图）
            price_returns = (future_prices / base_price - 1) * 100
            
            # 交易收益（用于统计分析）
            if breakout_direction == 'up':
                # 向上突破 → 做多 → 价格上涨为正收益
                trading_returns = (future_prices / base_price - 1) * 100
            else:
                # 向下突破 → 做空 → 价格下跌为正收益
                trading_returns = (base_price / future_prices - 1) * 100
            
            # 记录关键指标
            result = {
                'signal_date': signal_date,
                'base_price': base_price,
                'signal_return': signal_return * 100,  # 信号日收益
                'breakout_direction': breakout_direction,
                # 交易收益（用于大部分统计分析）
                'day_1_return': trading_returns.iloc[1] if len(trading_returns) > 1 else np.nan,
                'day_5_return': trading_returns.iloc[5] if len(trading_returns) > 5 else np.nan,
                'day_10_return': trading_returns.iloc[10] if len(trading_returns) > 10 else np.nan,
                'day_20_return': trading_returns.iloc[20] if len(trading_returns) > 20 else np.nan,
                'day_40_return': trading_returns.iloc[40] if len(trading_returns) > 40 else np.nan,
                'max_return_40d': trading_returns.iloc[1:41].max() if len(trading_returns) > 40 else np.nan,
                'min_return_40d': trading_returns.iloc[1:41].min() if len(trading_returns) > 40 else np.nan,
                # 原始价格变化序列（专门用于累计收益曲线图）
                'price_returns_series': price_returns.iloc[1:41].values if len(price_returns) > 40 else None,
                # 交易收益序列（用于其他分析）
                'trading_returns_series': trading_returns.iloc[1:41].values if len(trading_returns) > 40 else None
            }
            
            performance_results.append(result)
            
        except Exception as e:
            print(f"处理信号 {signal_date} 时出错: {e}")
            continue
    
    return performance_results

def calculate_statistics(performance_results):
    """计算统计指标"""
    
    if not performance_results:
        return {}
    
    # 分别分析上涨突破和下跌突破
    up_results = [r for r in performance_results if r['breakout_direction'] == 'up']
    down_results = [r for r in performance_results if r['breakout_direction'] == 'down']
    
    def calc_period_stats(results, period_key):
        """计算某个期间的统计指标"""
        returns_list = [r[period_key] for r in results if not np.isnan(r[period_key])]
        
        if not returns_list:
            return None
            
        mean_return = np.mean(returns_list)
        median_return = np.median(returns_list)
        std_return = np.std(returns_list)
        positive_ratio = sum(r > 0 for r in returns_list) / len(returns_list) * 100
        
        # t检验：检验平均收益是否显著大于0
        t_stat, p_value = stats.ttest_1samp(returns_list, 0)
        
        return {
            '样本数量': len(returns_list),
            '平均收益': mean_return,
            '中位收益': median_return,
            '标准差': std_return,
            '正收益比例': positive_ratio,
            't统计量': t_stat,
            'p值': p_value,
            '显著性': 'yes' if p_value < 0.05 else 'no'
        }
    
    stats_results = {}
    
    # 整体统计
    for period in ['day_1_return', 'day_5_return', 'day_10_return', 'day_20_return', 'day_40_return', 'max_return_40d']:
        period_name = {
            'day_1_return': '1日',
            'day_5_return': '5日', 
            'day_10_return': '10日',
            'day_20_return': '20日',
            'day_40_return': '40日',
            'max_return_40d': '40日内最高'
        }[period]
        
        stats_results[f'{period_name}后收益'] = calc_period_stats(performance_results, period)
    
    # 分方向统计
    stats_results['上涨突破统计'] = {}
    stats_results['下跌突破统计'] = {}
    
    for period in ['day_1_return', 'day_5_return', 'day_10_return', 'day_20_return', 'day_40_return', 'max_return_40d']:
        period_name = {
            'day_1_return': '1日',
            'day_5_return': '5日',
            'day_10_return': '10日', 
            'day_20_return': '20日',
            'day_40_return': '40日',
            'max_return_40d': '40日内最高'
        }[period]
        
        stats_results['上涨突破统计'][f'{period_name}后收益'] = calc_period_stats(up_results, period)
        stats_results['下跌突破统计'][f'{period_name}后收益'] = calc_period_stats(down_results, period)
    
    return stats_results

def create_performance_charts(performance_results, stats_results, strategy_name):
    """创建收益表现图表"""
    
    if not performance_results:
        print("没有数据可供绘图")
        return
    
    # 创建图表
    fig = plt.figure(figsize=(18, 14))
    
    # 准备数据
    periods = ['1日', '5日', '10日', '20日', '40日']
    
    # 1. 整体收益分布箱线图
    ax1 = plt.subplot(2, 3, 1)
    returns_data = []
    
    for period in periods:
        period_key = {
            '1日': 'day_1_return',
            '5日': 'day_5_return', 
            '10日': 'day_10_return',
            '20日': 'day_20_return',
            '40日': 'day_40_return'
        }[period]
        
        returns_data.append([r[period_key] for r in performance_results if not np.isnan(r[period_key])])
    
    ax1.boxplot(returns_data, labels=periods)
    ax1.set_title('三角形突破后收益分布')
    ax1.set_ylabel('收益率 (%)')
    ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7)
    ax1.grid(True, alpha=0.3)
    
    # 2. 平均收益柱状图
    ax2 = plt.subplot(2, 3, 2)
    mean_returns = []
    colors = []
    
    for period in periods:
        key = f'{period}后收益'
        if key in stats_results and stats_results[key]:
            mean_ret = stats_results[key]['平均收益']
            mean_returns.append(mean_ret)
            colors.append('green' if mean_ret > 0 else 'red')
        else:
            mean_returns.append(0)
            colors.append('gray')
    
    bars = ax2.bar(periods, mean_returns, color=colors, alpha=0.7)
    ax2.set_title('各期平均收益率')
    ax2.set_ylabel('平均收益率 (%)')
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.8)
    ax2.grid(True, alpha=0.3)
    
    # 添加数值标签
    for bar, value in zip(bars, mean_returns):
        if value != 0:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{value:.2f}%', ha='center', va='bottom')
    
    # 3. 正收益比例
    ax3 = plt.subplot(2, 3, 3)
    positive_ratios = []
    
    for period in periods:
        key = f'{period}后收益'
        if key in stats_results and stats_results[key]:
            positive_ratios.append(stats_results[key]['正收益比例'])
        else:
            positive_ratios.append(0)
    
    bars = ax3.bar(periods, positive_ratios, color='blue', alpha=0.7)
    ax3.set_title('正收益信号比例')
    ax3.set_ylabel('正收益比例 (%)')
    ax3.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50%基准线')
    ax3.set_ylim(0, 100)
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # 添加数值标签
    for bar, value in zip(bars, positive_ratios):
        if value != 0:
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{value:.1f}%', ha='center', va='bottom')
    
    # 4. 累计收益曲线（分方向 - 显示真实价格走势）
    ax4 = plt.subplot(2, 3, 4)
    
    up_results = [r for r in performance_results if r['breakout_direction'] == 'up' and r['price_returns_series'] is not None]
    down_results = [r for r in performance_results if r['breakout_direction'] == 'down' and r['price_returns_series'] is not None]
    
    if up_results:
        avg_up_returns = np.mean([r['price_returns_series'] for r in up_results], axis=0)
        days = range(1, len(avg_up_returns) + 1)
        ax4.plot(days, avg_up_returns, 'g-', linewidth=2, label=f'上涨突破(n={len(up_results)})')
    
    if down_results:
        avg_down_returns = np.mean([r['price_returns_series'] for r in down_results], axis=0)
        days = range(1, len(avg_down_returns) + 1)
        ax4.plot(days, avg_down_returns, 'r-', linewidth=2, label=f'下跌突破(n={len(down_results)})')
    
    ax4.axhline(y=0, color='black', linestyle='--', alpha=0.7)
    ax4.set_title('分方向平均价格变化曲线')
    ax4.set_xlabel('交易日')
    ax4.set_ylabel('价格变化率 (%)')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    # 5. 显著性测试结果表格
    ax5 = plt.subplot(2, 3, 5)
    ax5.axis('off')
    
    table_data = []
    for period in periods + ['40日内最高']:
        key = f'{period}后收益'
        if key in stats_results and stats_results[key]:
            s = stats_results[key]
            significance = '是' if s['显著性'] == 'yes' else '否'
            table_data.append([
                period,
                f"{s['平均收益']:.2f}%",
                f"{s['正收益比例']:.1f}%",
                f"{s['t统计量']:.2f}",
                f"{s['p值']:.4f}",
                significance
            ])
    
    if table_data:
        table = ax5.table(cellText=table_data,
                         colLabels=['期间', '平均收益', '胜率', 't统计量', 'p值', '显著性'],
                         cellLoc='center',
                         loc='center',
                         colWidths=[0.12, 0.15, 0.15, 0.15, 0.15, 0.12])
        
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.2)
    
    ax5.set_title('统计显著性测试结果')
    
    # 6. 信号时间分布散点图
    ax6 = plt.subplot(2, 3, 6)
    
    signal_dates_plot = [pd.to_datetime(r['signal_date']) for r in performance_results if not np.isnan(r['day_20_return'])]
    day_20_returns_plot = [r['day_20_return'] for r in performance_results if not np.isnan(r['day_20_return'])]
    directions = [r['breakout_direction'] for r in performance_results if not np.isnan(r['day_20_return'])]
    
    up_dates = [date for date, direction in zip(signal_dates_plot, directions) if direction == 'up']
    up_returns = [ret for ret, direction in zip(day_20_returns_plot, directions) if direction == 'up']
    down_dates = [date for date, direction in zip(signal_dates_plot, directions) if direction == 'down']
    down_returns = [ret for ret, direction in zip(day_20_returns_plot, directions) if direction == 'down']
    
    if up_dates:
        ax6.scatter(up_dates, up_returns, c='green', alpha=0.8, label='上涨突破(做多)', s=50, marker='o')  # 圆形
    if down_dates:
        ax6.scatter(down_dates, down_returns, c='red', alpha=0.8, label='下跌突破(做空)', s=50, marker='^')   # 三角形
    
    ax6.axhline(y=0, color='black', linestyle='--', alpha=0.7)
    ax6.set_title('各信号20日收益表现（分方向）')
    ax6.set_xlabel('信号日期')
    ax6.set_ylabel('20日收益率 (%)')
    ax6.grid(True, alpha=0.3)
    ax6.legend()
    
    # 格式化x轴日期
    ax6.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax6.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax6.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # 保存图表
    output_file = f'strategy3_{strategy_name}_performance_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\\n图表已保存到: {output_file}")
    
    plt.show()

def print_summary_statistics(stats_results, strategy_name):
    """打印统计摘要"""
    
    print("\\n" + "="*100)
    print(f"策略3：{strategy_name} 信号后收益表现统计摘要")
    print("="*100)
    
    # 整体表现
    print("\\n【整体表现分析】")
    print("-" * 50)
    
    for period_key in ['1日后收益', '5日后收益', '10日后收益', '20日后收益', '40日后收益', '40日内最高后收益']:
        if period_key in stats_results and stats_results[period_key]:
            stats = stats_results[period_key]
            print(f"\\n[{period_key.replace('后收益', '')}]:")
            print(f"   样本数量: {stats['样本数量']}")
            print(f"   平均收益: {stats['平均收益']:.2f}%")
            print(f"   中位收益: {stats['中位收益']:.2f}%")
            print(f"   收益标准差: {stats['标准差']:.2f}%")
            print(f"   正收益比例: {stats['正收益比例']:.1f}%")
            print(f"   t统计量: {stats['t统计量']:.3f}")
            print(f"   p值: {stats['p值']:.4f}")
            significance_text = "是" if stats['显著性'] == 'yes' else "否"
            print(f"   统计显著性(p<0.05): {significance_text}")
            
            # 判断表现
            if stats['平均收益'] > 0 and stats['显著性'] == 'yes':
                print(f"   >>> 表现: 显著正收益")
            elif stats['平均收益'] > 0:
                print(f"   >> 表现: 正收益但不显著") 
            else:
                print(f"   > 表现: 负收益")
    
    # 分方向分析
    print("\\n【分方向对比分析】")
    print("-" * 50)
    
    directions = ['上涨突破统计', '下跌突破统计']
    direction_names = ['上涨突破', '下跌突破']
    
    for direction, name in zip(directions, direction_names):
        if direction in stats_results:
            print(f"\\n{name}:")
            
            # 只显示关键期间
            key_periods = ['20日后收益', '40日内最高后收益']
            for period_key in key_periods:
                if period_key in stats_results[direction] and stats_results[direction][period_key]:
                    stats = stats_results[direction][period_key]
                    significance = "显著" if stats['显著性'] == 'yes' else "不显著"
                    print(f"   {period_key}: {stats['平均收益']:.2f}%, 胜率{stats['正收益比例']:.1f}%, {significance}")

def main(strategy_name: str = 'triangle_breakout_loose'):
    """主函数"""
    
    # 分析信号表现
    performance_results = analyze_signal_performance(strategy_name)
    
    if not performance_results:
        print("没有足够的数据进行分析")
        return
    
    print(f"\\n成功分析了 {len(performance_results)} 个信号的后续表现")
    
    # 计算统计指标
    stats_results = calculate_statistics(performance_results)
    
    # 打印统计摘要
    print_summary_statistics(stats_results, strategy_name)
    
    # 创建图表
    create_performance_charts(performance_results, stats_results, strategy_name)
    
    return performance_results, stats_results

if __name__ == "__main__":
    performance_results, stats_results = main()