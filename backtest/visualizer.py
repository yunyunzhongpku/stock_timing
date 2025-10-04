"""
可视化工具
Visualization Toolkit

提供标准化的图表生成函数，用于回测结果展示
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import List, Dict, Optional

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


def plot_signal_performance(analysis_results: Dict,
                            title: str = "策略回测表现",
                            output_path: Optional[str] = None,
                            figsize: tuple = (18, 14)):
    """
    生成标准化的策略回测表现图表

    Args:
        analysis_results: analyze_signals返回的结果字典
        title: 图表主标题
        output_path: 输出路径，如None则不保存
        figsize: 图表尺寸

    Returns:
        matplotlib.figure.Figure对象
    """
    if 'error' in analysis_results:
        print(f"无法绘图: {analysis_results['error']}")
        return None

    performance_results = analysis_results['performance_results']
    stats_summary = analysis_results['stats_summary']

    if not performance_results:
        print("没有数据可供绘图")
        return None

    # 创建图表
    fig = plt.figure(figsize=figsize)
    fig.suptitle(title, fontsize=16, fontweight='bold')

    # 准备持有期列表
    periods = list(stats_summary.keys())

    # 1. 收益分布箱线图 (左上)
    ax1 = plt.subplot(2, 3, 1)
    _plot_return_boxplot(ax1, performance_results, periods, title)

    # 2. 平均收益柱状图 (中上)
    ax2 = plt.subplot(2, 3, 2)
    _plot_mean_returns(ax2, stats_summary, periods)

    # 3. 胜率柱状图 (右上)
    ax3 = plt.subplot(2, 3, 3)
    _plot_win_rates(ax3, stats_summary, periods)

    # 4. 累计收益曲线 (左下)
    ax4 = plt.subplot(2, 3, 4)
    _plot_cumulative_returns(ax4, performance_results, title)

    # 5. 统计显著性表格 (中下)
    ax5 = plt.subplot(2, 3, 5)
    _plot_significance_table(ax5, stats_summary, periods)

    # 6. 信号时间分布散点图 (右下)
    ax6 = plt.subplot(2, 3, 6)
    _plot_signal_scatter(ax6, performance_results)

    plt.tight_layout()

    # 保存图表
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {output_path}")

    return fig


def _plot_return_boxplot(ax, performance_results: List[Dict], periods: List[str], title: str):
    """绘制收益分布箱线图"""
    returns_data = []

    for period in periods:
        period_key = f'day_{period.replace("日", "")}_return'
        returns = [r.get(period_key) for r in performance_results if not pd.isna(r.get(period_key))]
        returns_data.append(returns)

    if returns_data:
        ax.boxplot(returns_data)
        ax.set_xticklabels(periods)
        ax.set_title('收益分布')
        ax.set_ylabel('收益率 (%)')
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.7)
        ax.grid(True, alpha=0.3)


def _plot_mean_returns(ax, stats_summary: Dict, periods: List[str]):
    """绘制平均收益柱状图"""
    mean_returns = []
    colors = []

    for period in periods:
        if period in stats_summary:
            mean_ret = stats_summary[period]['平均收益']
            mean_returns.append(mean_ret)
            colors.append('green' if mean_ret > 0 else 'red')
        else:
            mean_returns.append(0)
            colors.append('gray')

    bars = ax.bar(periods, mean_returns, color=colors, alpha=0.7)
    ax.set_title('各期平均收益率')
    ax.set_ylabel('平均收益率 (%)')
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.8)
    ax.grid(True, alpha=0.3)

    # 添加数值标签
    for bar, value in zip(bars, mean_returns):
        if value != 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                   f'{value:.2f}%', ha='center', va='bottom', fontsize=8)


def _plot_win_rates(ax, stats_summary: Dict, periods: List[str]):
    """绘制胜率柱状图"""
    win_rates = []

    for period in periods:
        if period in stats_summary:
            win_rates.append(stats_summary[period]['胜率'])
        else:
            win_rates.append(0)

    bars = ax.bar(periods, win_rates, color='blue', alpha=0.7)
    ax.set_title('正收益信号比例')
    ax.set_ylabel('正收益比例 (%)')
    ax.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50%基准线')
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    ax.legend()

    # 添加数值标签
    for bar, value in zip(bars, win_rates):
        if value > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   f'{value:.1f}%', ha='center', va='bottom', fontsize=8)


def _plot_cumulative_returns(ax, performance_results: List[Dict], title: str):
    """绘制累计收益曲线（分方向）"""
    # 检查是否有方向信息
    has_direction = 'direction' in performance_results[0] if performance_results else False

    if has_direction:
        # 双向交易展示
        up_results = [r for r in performance_results
                     if r.get('direction') == 'up' and r.get('trading_returns_series') is not None]
        down_results = [r for r in performance_results
                       if r.get('direction') == 'down' and r.get('trading_returns_series') is not None]

        if up_results:
            avg_up = np.mean([r['trading_returns_series'] for r in up_results], axis=0)
            days = range(1, len(avg_up) + 1)
            ax.plot(days, avg_up, 'g-', linewidth=2, label=f'做多(n={len(up_results)})')

        if down_results:
            avg_down = np.mean([r['trading_returns_series'] for r in down_results], axis=0)
            days = range(1, len(avg_down) + 1)
            ax.plot(days, avg_down, 'r-', linewidth=2, label=f'做空(n={len(down_results)})')
    else:
        # 单向交易展示
        valid_results = [r for r in performance_results
                        if r.get('trading_returns_series') is not None]

        if valid_results:
            avg_returns = np.mean([r['trading_returns_series'] for r in valid_results], axis=0)
            days = range(1, len(avg_returns) + 1)
            ax.plot(days, avg_returns, 'b-', linewidth=2, label=f'平均收益(n={len(valid_results)})')

    ax.axhline(y=0, color='black', linestyle='--', alpha=0.7)
    ax.set_title('平均累计收益曲线')
    ax.set_xlabel('交易日')
    ax.set_ylabel('收益率 (%)')
    ax.grid(True, alpha=0.3)
    ax.legend()


def _plot_significance_table(ax, stats_summary: Dict, periods: List[str]):
    """绘制统计显著性表格"""
    ax.axis('off')

    table_data = []
    for period in periods:
        if period in stats_summary:
            s = stats_summary[period]
            significance = '是' if s['显著性'] == 'yes' else '否'
            table_data.append([
                period,
                f"{s['平均收益']:.2f}%",
                f"{s['胜率']:.1f}%",
                f"{s['t统计量']:.2f}",
                f"{s['p值']:.4f}",
                significance
            ])

    if table_data:
        table = ax.table(cellText=table_data,
                        colLabels=['期间', '平均收益', '胜率', 't统计量', 'p值', '显著性'],
                        cellLoc='center',
                        loc='center',
                        colWidths=[0.12, 0.15, 0.15, 0.15, 0.15, 0.12])

        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.2)

    ax.set_title('统计显著性测试结果')


def _plot_signal_scatter(ax, performance_results: List[Dict]):
    """绘制信号时间分布散点图"""
    # 查找第一个有效的持有期字段（优先20日）
    sample_result = performance_results[0] if performance_results else {}

    # 确定用哪个持有期绘图
    period_key = None
    for key in ['day_20_return', 'day_10_return', 'day_5_return', 'day_1_return', 'day_40_return']:
        if key in sample_result:
            period_key = key
            break

    if not period_key:
        ax.text(0.5, 0.5, '无可用数据', ha='center', va='center', transform=ax.transAxes)
        return

    # 提取数据
    valid_data = [(pd.to_datetime(r['signal_date']), r[period_key], r.get('direction', 'unknown'))
                  for r in performance_results if not pd.isna(r.get(period_key))]

    if not valid_data:
        ax.text(0.5, 0.5, '无可用数据', ha='center', va='center', transform=ax.transAxes)
        return

    dates, returns, directions = zip(*valid_data)

    # 检查是否有方向信息
    has_direction = directions[0] != 'unknown'

    if has_direction:
        # 分方向绘制
        up_dates = [d for d, _, dir in valid_data if dir == 'up']
        up_returns = [r for _, r, dir in valid_data if dir == 'up']
        down_dates = [d for d, _, dir in valid_data if dir == 'down']
        down_returns = [r for _, r, dir in valid_data if dir == 'down']

        if up_dates:
            ax.scatter(up_dates, up_returns, c='green', alpha=0.8, label='做多', s=50, marker='o')
        if down_dates:
            ax.scatter(down_dates, down_returns, c='red', alpha=0.8, label='做空', s=50, marker='^')
    else:
        # 不分方向
        ax.scatter(dates, returns, c='blue', alpha=0.6, s=50)

    ax.axhline(y=0, color='black', linestyle='--', alpha=0.7)

    period_name = period_key.replace('day_', '').replace('_return', '日')
    ax.set_title(f'各信号{period_name}收益表现')
    ax.set_xlabel('信号日期')
    ax.set_ylabel(f'{period_name}收益率 (%)')
    ax.grid(True, alpha=0.3)

    if has_direction:
        ax.legend()

    # 格式化x轴日期
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)


def plot_time_split_comparison(in_sample_results: Dict,
                               out_sample_results: Dict,
                               title: str = "时间分割对比",
                               output_dir: str = "outputs"):
    """
    生成训练期/测试期对比图表

    Args:
        in_sample_results: 训练期结果
        out_sample_results: 测试期结果
        title: 图表主标题
        output_dir: 输出目录

    Returns:
        两个Figure对象: (in_sample_fig, out_sample_fig)
    """
    # 生成训练期图表
    in_sample_fig = plot_signal_performance(
        in_sample_results,
        title=f"{title} - 训练期",
        output_path=f"{output_dir}/{title}_训练期.png"
    )

    # 生成测试期图表
    out_sample_fig = plot_signal_performance(
        out_sample_results,
        title=f"{title} - 测试期",
        output_path=f"{output_dir}/{title}_测试期.png"
    )

    return in_sample_fig, out_sample_fig


def print_time_split_summary(in_sample_results: Dict,
                             out_sample_results: Dict,
                             key_period: str = '20日'):
    """
    打印时间分割对比摘要

    Args:
        in_sample_results: 训练期结果
        out_sample_results: 测试期结果
        key_period: 关键对比期间，默认20日
    """
    print("\n" + "="*100)
    print("时间分割对比摘要")
    print("="*100)

    in_stats = in_sample_results.get('stats_summary', {}).get(key_period, {})
    out_stats = out_sample_results.get('stats_summary', {}).get(key_period, {})

    if in_stats and out_stats:
        print(f"\n{key_period}持有期对比:")
        print("-" * 80)
        print(f"{'指标':<20} {'训练期':<25} {'测试期':<25}")
        print("-" * 80)
        print(f"{'样本数量':<20} {in_stats['样本数量']:<25} {out_stats['样本数量']:<25}")
        print(f"{'平均收益':<20} {in_stats['平均收益']:>10.2f}% {out_stats['平均收益']:>22.2f}%")
        print(f"{'胜率':<20} {in_stats['胜率']:>10.1f}% {out_stats['胜率']:>22.1f}%")
        print(f"{'p值':<20} {in_stats['p值']:>10.4f} {out_stats['p值']:>22.4f}")

        in_sig = "显著" if in_stats['显著性'] == 'yes' else "不显著"
        out_sig = "显著" if out_stats['显著性'] == 'yes' else "不显著"
        print(f"{'显著性':<20} {in_sig:<25} {out_sig:<25}")

        print("\n" + "="*100)
        print("结论:")
        print("="*100)

        if out_stats['显著性'] == 'yes':
            print("[OK] 策略在测试期(out-of-sample)仍然显著")
            print("[OK] 这证明策略具有真实的预测能力")
        else:
            print("[WARN] 策略在测试期(out-of-sample)不显著")
            print("[WARN] 可能存在过拟合，需要谨慎对待")
            print(f"[INFO] 测试期样本量: {out_stats['样本数量']}，可能样本量不足")
    else:
        print("无法进行对比，数据不完整")
