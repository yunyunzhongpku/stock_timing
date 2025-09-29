"""
信号触发后40个交易日收益分析
分析策略信号的预测效果和统计显著性
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
from data_loader import WindDataLoader
from metrics.strategy1_definitions import Strategy1Definitions

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def analyze_signal_performance():
    """分析信号触发后的表现"""
    
    print("开始分析信号触发后40个交易日的收益表现...")
    
    # 加载数据
    loader = WindDataLoader()
    data = loader.get_csi_all_data("2013-01-01", "2025-04-30")
    data = loader.add_atr60(data)
    
    # 获取策略信号
    strategy = Strategy1Definitions(data)
    signals = strategy.get_strategy_signals()['correct_decline_rebound']
    
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
            
            # 计算累计收益率
            returns = (future_prices / base_price - 1) * 100
            
            # 记录关键指标
            result = {
                'signal_date': signal_date,
                'base_price': base_price,
                'day_1_return': returns.iloc[1] if len(returns) > 1 else np.nan,
                'day_5_return': returns.iloc[5] if len(returns) > 5 else np.nan,
                'day_10_return': returns.iloc[10] if len(returns) > 10 else np.nan,
                'day_20_return': returns.iloc[20] if len(returns) > 20 else np.nan,
                'day_40_return': returns.iloc[40] if len(returns) > 40 else np.nan,
                'max_return_40d': returns.iloc[1:41].max() if len(returns) > 40 else np.nan,
                'min_return_40d': returns.iloc[1:41].min() if len(returns) > 40 else np.nan,
                'returns_series': returns.iloc[1:41].values if len(returns) > 40 else None
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
    
    # 提取各期收益
    day_1_returns = [r['day_1_return'] for r in performance_results if not np.isnan(r['day_1_return'])]
    day_5_returns = [r['day_5_return'] for r in performance_results if not np.isnan(r['day_5_return'])]
    day_10_returns = [r['day_10_return'] for r in performance_results if not np.isnan(r['day_10_return'])]
    day_20_returns = [r['day_20_return'] for r in performance_results if not np.isnan(r['day_20_return'])]
    day_40_returns = [r['day_40_return'] for r in performance_results if not np.isnan(r['day_40_return'])]
    max_returns = [r['max_return_40d'] for r in performance_results if not np.isnan(r['max_return_40d'])]
    
    stats_results = {}
    
    for period, returns_list in [
        ('1日', day_1_returns), ('5日', day_5_returns), 
        ('10日', day_10_returns), ('20日', day_20_returns), 
        ('40日', day_40_returns), ('40日内最高', max_returns)
    ]:
        if returns_list:
            mean_return = np.mean(returns_list)
            median_return = np.median(returns_list)
            std_return = np.std(returns_list)
            positive_ratio = sum(r > 0 for r in returns_list) / len(returns_list) * 100
            
            # t检验：检验平均收益是否显著大于0
            t_stat, p_value = stats.ttest_1samp(returns_list, 0)
            
            stats_results[period] = {
                '样本数量': len(returns_list),
                '平均收益': mean_return,
                '中位收益': median_return,
                '标准差': std_return,
                '正收益比例': positive_ratio,
                't统计量': t_stat,
                'p值': p_value,
                '显著性': 'yes' if p_value < 0.05 else 'no'
            }
    
    return stats_results

def create_performance_charts(performance_results, stats_results):
    """创建收益表现图表"""
    
    if not performance_results:
        print("没有数据可供绘图")
        return
    
    # 创建图表
    fig = plt.figure(figsize=(16, 12))
    
    # 1. 收益分布箱线图
    ax1 = plt.subplot(2, 3, 1)
    periods = ['1日', '5日', '10日', '20日', '40日']
    returns_data = []
    
    for period in periods:
        if period in stats_results:
            if period == '1日':
                returns_data.append([r['day_1_return'] for r in performance_results if not np.isnan(r['day_1_return'])])
            elif period == '5日':
                returns_data.append([r['day_5_return'] for r in performance_results if not np.isnan(r['day_5_return'])])
            elif period == '10日':
                returns_data.append([r['day_10_return'] for r in performance_results if not np.isnan(r['day_10_return'])])
            elif period == '20日':
                returns_data.append([r['day_20_return'] for r in performance_results if not np.isnan(r['day_20_return'])])
            elif period == '40日':
                returns_data.append([r['day_40_return'] for r in performance_results if not np.isnan(r['day_40_return'])])
    
    ax1.boxplot(returns_data, labels=periods)
    ax1.set_title('信号后收益分布箱线图')
    ax1.set_ylabel('收益率 (%)')
    ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7)
    ax1.grid(True, alpha=0.3)
    
    # 2. 平均收益柱状图
    ax2 = plt.subplot(2, 3, 2)
    periods_with_data = []
    mean_returns = []
    colors = []
    
    for period in periods:
        if period in stats_results:
            periods_with_data.append(period)
            mean_ret = stats_results[period]['平均收益']
            mean_returns.append(mean_ret)
            colors.append('green' if mean_ret > 0 else 'red')
    
    bars = ax2.bar(periods_with_data, mean_returns, color=colors, alpha=0.7)
    ax2.set_title('各期平均收益率')
    ax2.set_ylabel('平均收益率 (%)')
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.8)
    ax2.grid(True, alpha=0.3)
    
    # 添加数值标签
    for bar, value in zip(bars, mean_returns):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{value:.2f}%', ha='center', va='bottom')
    
    # 3. 正收益比例
    ax3 = plt.subplot(2, 3, 3)
    positive_ratios = [stats_results[period]['正收益比例'] for period in periods_with_data]
    bars = ax3.bar(periods_with_data, positive_ratios, color='blue', alpha=0.7)
    ax3.set_title('正收益信号比例')
    ax3.set_ylabel('正收益比例 (%)')
    ax3.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50%基准线')
    ax3.set_ylim(0, 100)
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # 添加数值标签
    for bar, value in zip(bars, positive_ratios):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{value:.1f}%', ha='center', va='bottom')
    
    # 4. 累计收益曲线（所有信号的平均）
    ax4 = plt.subplot(2, 3, 4)
    
    # 计算平均累计收益曲线
    valid_series = [r['returns_series'] for r in performance_results if r['returns_series'] is not None]
    if valid_series:
        avg_returns = np.mean(valid_series, axis=0)
        days = range(1, len(avg_returns) + 1)
        
        ax4.plot(days, avg_returns, 'b-', linewidth=2, label='平均累计收益')
        ax4.axhline(y=0, color='red', linestyle='--', alpha=0.7)
        ax4.set_title('信号后40日平均累计收益曲线')
        ax4.set_xlabel('交易日')
        ax4.set_ylabel('累计收益率 (%)')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
    
    # 5. 显著性测试结果
    ax5 = plt.subplot(2, 3, 5)
    ax5.axis('off')
    
    # 创建统计表格
    table_data = []
    for period in periods_with_data:
        if period in stats_results:
            s = stats_results[period]
            significance = '是' if s['显著性'] == 'yes' else '否'
            table_data.append([
                period,
                f"{s['平均收益']:.2f}%",
                f"{s['正收益比例']:.1f}%",
                f"{s['t统计量']:.2f}",
                f"{s['p值']:.4f}",
                significance
            ])
    
    table = ax5.table(cellText=table_data,
                     colLabels=['期间', '平均收益', '胜率', 't统计量', 'p值', '显著性'],
                     cellLoc='center',
                     loc='center',
                     colWidths=[0.1, 0.15, 0.15, 0.15, 0.15, 0.15])
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    ax5.set_title('统计显著性测试结果')
    
    # 6. 个别信号表现散点图
    ax6 = plt.subplot(2, 3, 6)
    
    signal_dates_plot = [pd.to_datetime(r['signal_date']) for r in performance_results if not np.isnan(r['day_20_return'])]
    day_20_returns_plot = [r['day_20_return'] for r in performance_results if not np.isnan(r['day_20_return'])]
    
    colors_scatter = ['green' if r > 0 else 'red' for r in day_20_returns_plot]
    ax6.scatter(signal_dates_plot, day_20_returns_plot, c=colors_scatter, alpha=0.7)
    ax6.axhline(y=0, color='black', linestyle='--', alpha=0.7)
    ax6.set_title('各信号20日收益表现')
    ax6.set_xlabel('信号日期')
    ax6.set_ylabel('20日收益率 (%)')
    ax6.grid(True, alpha=0.3)
    
    # 格式化x轴日期
    ax6.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax6.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax6.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # 保存图表
    output_file = 'strategy1_performance_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n图表已保存到: {output_file}")
    
    plt.show()

def print_summary_statistics(stats_results):
    """打印统计摘要"""
    
    print("\n" + "="*80)
    print("策略1信号后收益表现统计摘要")
    print("="*80)
    
    for period, stats in stats_results.items():
        print(f"\n[{period}后收益表现]:")
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

def main():
    """主函数"""
    
    # 分析信号表现
    performance_results = analyze_signal_performance()
    
    if not performance_results:
        print("没有足够的数据进行分析")
        return
    
    print(f"\n成功分析了 {len(performance_results)} 个信号的后续表现")
    
    # 计算统计指标
    stats_results = calculate_statistics(performance_results)
    
    # 打印统计摘要
    print_summary_statistics(stats_results)
    
    # 创建图表
    create_performance_charts(performance_results, stats_results)
    
    return performance_results, stats_results

if __name__ == "__main__":
    performance_results, stats_results = main()