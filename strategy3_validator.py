"""
策略3验证器 - 三角形突破信号识别和基础验证
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
from datetime import datetime

from data_loader import WindDataLoader
from metrics.strategy3_definitions import Strategy3Definitions

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class Strategy3Validator:
    """策略3验证器"""
    
    def __init__(self):
        """初始化验证器"""
        self.data_loader = WindDataLoader()
        self.data = None
        self.results = {}
        
    def load_data(self, start_date: str = "2013-01-01", end_date: str = "2025-04-30"):
        """
        加载数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        """
        print(f"正在加载数据: {start_date} 到 {end_date}")
        
        # 获取OHLC数据
        self.data = self.data_loader.get_csi_all_data(start_date, end_date)
        
        print(f"数据加载完成: {len(self.data)}条记录")
        print(f"数据日期范围: {self.data.index[0]} 到 {self.data.index[-1]}")
        
    def validate_all_strategies(self) -> Dict:
        """
        验证所有策略3定义方案
        
        Returns:
            验证结果字典
        """
        if self.data is None:
            raise ValueError("请先调用load_data()加载数据")
        
        print("开始运行策略3算法...")
        
        # 创建策略定义实例
        strategy_defs = Strategy3Definitions(self.data)
        
        # 获取所有策略信号
        all_signals = strategy_defs.get_strategy_signals()
        
        # 获取信号汇总统计
        signal_summary = strategy_defs.get_signal_summary()
        
        results = {}
        for strategy_name, signals in all_signals.items():
            signal_dates = signals[signals == True].index.tolist()
            
            # 基础统计
            total_signals = len(signal_dates)
            trading_days = len(self.data)
            signal_frequency = total_signals / trading_days * 100 if trading_days > 0 else 0
            
            # 年度分布
            yearly_distribution = self._analyze_yearly_distribution(signal_dates)
            
            # 月度分布
            monthly_distribution = self._analyze_monthly_distribution(signal_dates)
            
            # 市场环境分析
            market_analysis = self._analyze_market_environment(signal_dates)
            
            results[strategy_name] = {
                'signals': signals,
                'signal_dates': signal_dates,
                'total_signals': total_signals,
                'signal_frequency': signal_frequency,  # 信号频率（%）
                'avg_signals_per_year': signal_summary[strategy_name]['avg_signals_per_year'],
                'yearly_distribution': yearly_distribution,
                'monthly_distribution': monthly_distribution,
                'market_analysis': market_analysis
            }
            
            print(f"\\n{strategy_name}:")
            print(f"  总信号数: {total_signals}")
            print(f"  信号频率: {signal_frequency:.3f}%")
            print(f"  年均信号: {signal_summary[strategy_name]['avg_signals_per_year']:.1f}个")
            if signal_dates:
                print(f"  首个信号: {signal_dates[0].strftime('%Y-%m-%d')}")
                print(f"  最后信号: {signal_dates[-1].strftime('%Y-%m-%d')}")
        
        self.results = results
        return results
    
    def _analyze_yearly_distribution(self, signal_dates: List) -> Dict:
        """分析信号的年度分布"""
        if not signal_dates:
            return {}
        
        yearly_counts = {}
        for date in signal_dates:
            year = date.year
            yearly_counts[year] = yearly_counts.get(year, 0) + 1
        
        return yearly_counts
    
    def _analyze_monthly_distribution(self, signal_dates: List) -> Dict:
        """分析信号的月度分布"""
        if not signal_dates:
            return {}
        
        monthly_counts = {}
        for date in signal_dates:
            month = date.month
            monthly_counts[month] = monthly_counts.get(month, 0) + 1
        
        return monthly_counts
    
    def _analyze_market_environment(self, signal_dates: List) -> Dict:
        """分析信号触发时的市场环境"""
        if not signal_dates:
            return {}
        
        market_conditions = {
            'avg_close_price': [],
            'avg_volatility': [],
            'avg_volume_ratio': []  # 如果有成交量数据
        }
        
        for date in signal_dates:
            try:
                date_idx = self.data.index.get_loc(date)
                
                # 当日收盘价
                close_price = self.data['close'].iloc[date_idx]
                market_conditions['avg_close_price'].append(close_price)
                
                # 前5日波动率
                if date_idx >= 5:
                    recent_returns = self.data['close'].pct_change().iloc[date_idx-4:date_idx+1]
                    volatility = recent_returns.std()
                    market_conditions['avg_volatility'].append(volatility)
                
            except (KeyError, IndexError):
                continue
        
        # 计算平均值
        analysis = {}
        for key, values in market_conditions.items():
            if values:
                analysis[key] = np.mean(values)
        
        return analysis
    
    def get_best_strategy(self) -> Tuple[str, Dict]:
        """
        获取最佳策略（基于信号数量和分布的合理性）
        
        Returns:
            (最佳策略名称, 最佳策略结果)
        """
        if not self.results:
            raise ValueError("请先调用validate_all_strategies()进行验证")
        
        # 评分机制：平衡信号数量和分布合理性
        best_score = -1
        best_strategy = None
        
        for strategy_name, result in self.results.items():
            total_signals = result['total_signals']
            avg_per_year = result['avg_signals_per_year']
            
            # 评分：希望每年有适量信号（5-20个较理想）
            if 5 <= avg_per_year <= 20:
                frequency_score = 1.0
            elif avg_per_year < 5:
                frequency_score = avg_per_year / 5.0
            else:
                frequency_score = max(0.5, 20 / avg_per_year)
            
            # 总体评分
            total_score = frequency_score * min(1.0, total_signals / 50)  # 希望至少有一定数量的信号
            
            if total_score > best_score:
                best_score = total_score
                best_strategy = (strategy_name, result)
        
        return best_strategy
    
    def analyze_signal_characteristics(self, strategy_name: str = None) -> pd.DataFrame:
        """
        分析信号特征
        
        Args:
            strategy_name: 要分析的策略名称，如果为None则分析最佳策略
            
        Returns:
            信号特征分析结果DataFrame
        """
        if not self.results:
            raise ValueError("请先调用validate_all_strategies()进行验证")
        
        if strategy_name is None:
            strategy_name, _ = self.get_best_strategy()
        
        if strategy_name not in self.results:
            raise ValueError(f"未找到策略: {strategy_name}")
        
        signal_dates = self.results[strategy_name]['signal_dates']
        
        # 分析每个信号的特征
        analysis_data = []
        
        for date in signal_dates:
            try:
                date_idx = self.data.index.get_loc(date)
                
                # 基本信息
                close_price = self.data['close'].iloc[date_idx]
                daily_return = self.data['close'].pct_change().iloc[date_idx]
                
                # 前5日区间特征
                if date_idx >= 4:
                    recent_5d = self.data.iloc[date_idx-4:date_idx+1]
                    range_width = (recent_5d['high'].max() - recent_5d['low'].min()) / recent_5d['close'].mean()
                    
                    analysis_data.append({
                        'date': date,
                        'close_price': close_price,
                        'daily_return': daily_return,
                        'range_width': range_width,
                        'breakout_direction': 'up' if daily_return > 0 else 'down',
                        'year': date.year,
                        'month': date.month,
                        'weekday': date.weekday()  # 0=周一, 6=周日
                    })
            except (KeyError, IndexError):
                continue
        
        if analysis_data:
            df = pd.DataFrame(analysis_data)
            return df
        else:
            return pd.DataFrame()
    
    def generate_validation_report(self) -> str:
        """
        生成验证报告
        
        Returns:
            报告字符串
        """
        if not self.results:
            return "尚未进行验证，请先调用validate_all_strategies()"
        
        report = ["=" * 80]
        report.append("策略3：三角形突破验证报告")
        report.append("=" * 80)
        
        # 数据概况
        start_date = self.data.index[0].strftime('%Y-%m-%d')
        end_date = self.data.index[-1].strftime('%Y-%m-%d')
        report.append(f"数据范围: {start_date} 到 {end_date}")
        report.append(f"总交易日数: {len(self.data)}")
        report.append("")
        
        # 各策略结果
        report.append("各策略方案结果:")
        report.append("-" * 60)
        
        for i, (strategy_name, result) in enumerate(self.results.items(), 1):
            report.append(f"{i}. {strategy_name}")
            report.append(f"   总信号数: {result['total_signals']}")
            report.append(f"   信号频率: {result['signal_frequency']:.3f}%")
            report.append(f"   年均信号: {result['avg_signals_per_year']:.1f}个")
            
            # 年度分布
            yearly_dist = result['yearly_distribution']
            if yearly_dist:
                years = sorted(yearly_dist.keys())
                year_summary = ", ".join([f"{year}:{yearly_dist[year]}个" for year in years[-5:]])  # 最近5年
                report.append(f"   最近分布: {year_summary}")
            
            report.append("")
        
        # 最佳策略详细分析
        best_name, best_result = self.get_best_strategy()
        report.append(f"推荐策略: {best_name}")
        report.append("-" * 40)
        report.append(f"总信号数: {best_result['total_signals']}")
        report.append(f"平均每年: {best_result['avg_signals_per_year']:.1f}个信号")
        
        # 月度分布分析
        monthly_dist = best_result['monthly_distribution']
        if monthly_dist:
            months = ['1月', '2月', '3月', '4月', '5月', '6月', 
                     '7月', '8月', '9月', '10月', '11月', '12月']
            report.append(f"月度分布:")
            for month, name in enumerate(months, 1):
                count = monthly_dist.get(month, 0)
                if count > 0:
                    report.append(f"   {name}: {count}个")
        
        return "\\n".join(report)
    
    def create_signal_visualization(self, strategy_name: str = None) -> None:
        """
        创建信号可视化图表
        
        Args:
            strategy_name: 要可视化的策略名称
        """
        if not self.results:
            print("请先运行验证")
            return
        
        if strategy_name is None:
            strategy_name, _ = self.get_best_strategy()
        
        signal_dates = self.results[strategy_name]['signal_dates']
        signal_data = self.analyze_signal_characteristics(strategy_name)
        
        if signal_data.empty:
            print("没有信号数据可供可视化")
            return
        
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'策略3：{strategy_name} 信号分析', fontsize=16)
        
        # 1. 年度分布
        ax1 = axes[0, 0]
        yearly_counts = signal_data['year'].value_counts().sort_index()
        ax1.bar(yearly_counts.index, yearly_counts.values, alpha=0.7, color='blue')
        ax1.set_title('信号年度分布')
        ax1.set_xlabel('年份')
        ax1.set_ylabel('信号数量')
        ax1.grid(True, alpha=0.3)
        
        # 2. 月度分布
        ax2 = axes[0, 1]
        monthly_counts = signal_data['month'].value_counts().sort_index()
        month_names = ['1月', '2月', '3月', '4月', '5月', '6月',
                      '7月', '8月', '9月', '10月', '11月', '12月']
        ax2.bar(monthly_counts.index, monthly_counts.values, alpha=0.7, color='green')
        ax2.set_title('信号月度分布')
        ax2.set_xlabel('月份')
        ax2.set_ylabel('信号数量')
        ax2.set_xticks(range(1, 13))
        ax2.grid(True, alpha=0.3)
        
        # 3. 突破方向分布
        ax3 = axes[1, 0]
        direction_counts = signal_data['breakout_direction'].value_counts()
        colors = ['red' if direction == 'down' else 'green' for direction in direction_counts.index]
        ax3.pie(direction_counts.values, labels=[f'{dir}突破' for dir in direction_counts.index],
               autopct='%1.1f%%', colors=colors)
        ax3.set_title('突破方向分布')
        
        # 4. 收益分布
        ax4 = axes[1, 1]
        returns = signal_data['daily_return'] * 100  # 转为百分比
        ax4.hist(returns, bins=20, alpha=0.7, color='orange', edgecolor='black')
        ax4.axvline(x=0, color='red', linestyle='--', alpha=0.7, label='零线')
        ax4.set_title('信号日收益分布')
        ax4.set_xlabel('日收益率 (%)')
        ax4.set_ylabel('频次')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图表
        output_file = f'strategy3_{strategy_name}_validation.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\\n图表已保存到: {output_file}")
        
        plt.show()


def main():
    """主函数 - 运行完整的策略3验证流程"""
    print("开始策略3三角形突破验证...")
    
    # 创建验证器
    validator = Strategy3Validator()
    
    # 加载数据
    validator.load_data(start_date="2013-01-01", end_date="2025-04-30")
    
    # 验证所有策略定义
    results = validator.validate_all_strategies()
    
    # 生成验证报告
    print("\\n" + "="*80)
    report = validator.generate_validation_report()
    print(report)
    
    # 分析最佳策略的信号特征
    best_name, _ = validator.get_best_strategy()
    signal_analysis = validator.analyze_signal_characteristics(best_name)
    
    if not signal_analysis.empty:
        print(f"\\n{best_name} 信号特征分析:")
        print(f"信号总数: {len(signal_analysis)}")
        print(f"上涨突破: {len(signal_analysis[signal_analysis['breakout_direction']=='up'])}个")
        print(f"下跌突破: {len(signal_analysis[signal_analysis['breakout_direction']=='down'])}个")
        print(f"平均突破幅度: {signal_analysis['daily_return'].abs().mean()*100:.2f}%")
        
        # 显示前10个信号的详细信息
        print("\\n前10个信号详情:")
        print(signal_analysis[['date', 'daily_return', 'breakout_direction', 'range_width']].head(10).to_string(index=False))
    
    # 创建可视化图表
    validator.create_signal_visualization(best_name)
    
    return validator, results


if __name__ == "__main__":
    validator, results = main()