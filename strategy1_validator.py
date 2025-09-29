"""
策略1验证器 - 测试不同定义方案与已知信号的匹配度
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
from datetime import datetime

from data_loader import WindDataLoader
from metrics.strategy1_definitions import Strategy1Definitions


class Strategy1Validator:
    """策略1验证器"""
    
    def __init__(self):
        """初始化验证器"""
        self.data_loader = WindDataLoader()
        self.data = None
        self.known_signals = None
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
        
        # 添加ATR60
        self.data = self.data_loader.add_atr60(self.data)
        
        # 获取已知信号日期
        self.known_signals = self.data_loader.get_known_signals()
        
        # 过滤在数据范围内的信号
        data_start = pd.Timestamp(self.data.index.min())
        data_end = pd.Timestamp(self.data.index.max())
        self.known_signals = [
            signal for signal in self.known_signals 
            if data_start <= signal <= data_end
        ]
        
        print(f"数据加载完成: {len(self.data)}条记录")
        print(f"有效信号日期: {len(self.known_signals)}个")
        
    def validate_all_definitions(self) -> Dict:
        """
        验证所有定义方案
        
        Returns:
            验证结果字典
        """
        if self.data is None:
            raise ValueError("请先调用load_data()加载数据")
        
        print("开始验证各种定义方案...")
        
        # 创建策略定义实例
        strategy_defs = Strategy1Definitions(self.data)
        
        # 获取正确的策略信号
        all_signals = strategy_defs.get_strategy_signals()
        
        # 创建已知信号的布尔序列
        known_signal_series = pd.Series(False, index=self.data.index)
        for signal_timestamp in self.known_signals:
            # 尝试直接匹配timestamp
            if signal_timestamp in known_signal_series.index:
                known_signal_series[signal_timestamp] = True
            else:
                # 尝试转换为date匹配
                signal_date = signal_timestamp.date()
                matching_indices = [idx for idx in known_signal_series.index 
                                  if (hasattr(idx, 'date') and idx.date() == signal_date) or idx == signal_date]
                for idx in matching_indices:
                    known_signal_series[idx] = True
        
        # 验证每个定义
        results = {}
        for def_name, predicted_signals in all_signals.items():
            # 确保信号序列与数据对齐
            if len(predicted_signals) != len(known_signal_series):
                print(f"警告: {def_name}信号长度不匹配，跳过验证")
                continue
            
            # 计算匹配指标
            metrics = self._calculate_metrics(known_signal_series, predicted_signals)
            results[def_name] = {
                'predicted_signals': predicted_signals,
                'metrics': metrics
            }
            
            print(f"\n{def_name}:")
            print(f"  命中率: {metrics['hit_rate']:.1%}")
            print(f"  精确率: {metrics['precision']:.1%}")
            print(f"  召回率: {metrics['recall']:.1%}")
            print(f"  F1分数: {metrics['f1_score']:.3f}")
            print(f"  总信号数: {metrics['total_signals']}")
        
        self.results = results
        return results
    
    def _calculate_metrics(self, known_signals: pd.Series, predicted_signals: pd.Series) -> Dict:
        """
        计算验证指标
        
        Args:
            known_signals: 已知信号（真实标签）
            predicted_signals: 预测信号
            
        Returns:
            指标字典
        """
        # 基本统计
        true_positives = (known_signals & predicted_signals).sum()
        false_positives = (~known_signals & predicted_signals).sum()
        false_negatives = (known_signals & ~predicted_signals).sum()
        true_negatives = (~known_signals & ~predicted_signals).sum()
        
        # 计算指标
        total_known = known_signals.sum()
        total_predicted = predicted_signals.sum()
        
        hit_rate = true_positives / total_known if total_known > 0 else 0
        precision = true_positives / total_predicted if total_predicted > 0 else 0
        recall = hit_rate  # 召回率就是命中率
        
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'true_positives': int(true_positives),
            'false_positives': int(false_positives),
            'false_negatives': int(false_negatives),
            'true_negatives': int(true_negatives),
            'hit_rate': hit_rate,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'total_known': int(total_known),
            'total_signals': int(total_predicted)
        }
    
    def get_best_definition(self) -> Tuple[str, Dict]:
        """
        获取最佳定义方案
        
        Returns:
            (最佳方案名称, 最佳方案结果)
        """
        if not self.results:
            raise ValueError("请先调用validate_all_definitions()进行验证")
        
        # 按F1分数排序
        best_def = max(self.results.items(), key=lambda x: x[1]['metrics']['f1_score'])
        
        return best_def[0], best_def[1]
    
    def analyze_signal_dates(self, definition_name: str = None) -> pd.DataFrame:
        """
        分析信号日期的详细情况
        
        Args:
            definition_name: 要分析的定义名称，如果为None则分析最佳定义
            
        Returns:
            信号分析结果DataFrame
        """
        if not self.results:
            raise ValueError("请先调用validate_all_definitions()进行验证")
        
        if definition_name is None:
            definition_name, _ = self.get_best_definition()
        
        if definition_name not in self.results:
            raise ValueError(f"未找到定义: {definition_name}")
        
        predicted_signals = self.results[definition_name]['predicted_signals']
        
        # 创建分析结果
        analysis_data = []
        
        # 分析已知信号日期
        for known_timestamp in self.known_signals:
            known_date = known_timestamp.date()  # 转换为date类型
            if known_date in predicted_signals.index:
                predicted = predicted_signals[known_date]
                status = "命中" if predicted else "遗漏"
            else:
                status = "超出数据范围"
            
            analysis_data.append({
                'date': known_date,
                'type': '已知信号',
                'predicted': predicted if known_date in predicted_signals.index else False,
                'status': status
            })
        
        # 分析预测的信号日期（但不在已知信号中）
        predicted_dates = predicted_signals[predicted_signals].index
        known_dates_set = {ts.date() for ts in self.known_signals}  # 转换为date集合
        for pred_date in predicted_dates:
            if pred_date not in known_dates_set:
                analysis_data.append({
                    'date': pred_date,
                    'type': '额外信号',
                    'predicted': True,
                    'status': '新增'
                })
        
        df = pd.DataFrame(analysis_data)
        df = df.sort_values('date')
        
        return df
    
    def generate_summary_report(self) -> str:
        """
        生成总结报告
        
        Returns:
            报告字符串
        """
        if not self.results:
            return "尚未进行验证，请先调用validate_all_definitions()"
        
        report = ["=" * 60]
        report.append("策略1定义方案验证报告")
        report.append("=" * 60)
        start_date = self.data.index[0]
        end_date = self.data.index[-1]
        if hasattr(start_date, 'date'):
            start_date = start_date.date()
        if hasattr(end_date, 'date'):
            end_date = end_date.date()
        report.append(f"数据范围: {start_date} 到 {end_date}")
        report.append(f"已知信号数量: {len(self.known_signals)}")
        report.append("")
        
        # 按F1分数排序显示结果
        sorted_results = sorted(self.results.items(), 
                              key=lambda x: x[1]['metrics']['f1_score'], 
                              reverse=True)
        
        report.append("各方案验证结果（按F1分数排序）:")
        report.append("-" * 60)
        
        for i, (def_name, result) in enumerate(sorted_results, 1):
            metrics = result['metrics']
            report.append(f"{i}. {def_name}")
            report.append(f"   命中率: {metrics['hit_rate']:.1%} ({metrics['true_positives']}/{metrics['total_known']})")
            report.append(f"   精确率: {metrics['precision']:.1%}")
            report.append(f"   F1分数: {metrics['f1_score']:.3f}")
            report.append(f"   总信号: {metrics['total_signals']}")
            report.append("")
        
        # 最佳方案详细分析
        best_name, best_result = self.get_best_definition()
        report.append(f"最佳方案: {best_name}")
        report.append("-" * 30)
        
        best_metrics = best_result['metrics']
        report.append(f"命中信号: {best_metrics['true_positives']}")
        report.append(f"遗漏信号: {best_metrics['false_negatives']}")
        report.append(f"错误信号: {best_metrics['false_positives']}")
        report.append(f"F1分数: {best_metrics['f1_score']:.3f}")
        
        return "\n".join(report)


def main():
    """主函数 - 运行完整的验证流程"""
    print("开始策略1定义方案验证...")
    
    # 创建验证器
    validator = Strategy1Validator()
    
    # 加载数据
    validator.load_data(start_date="2013-01-01", end_date="2025-04-30")
    
    # 验证所有定义
    results = validator.validate_all_definitions()
    
    # 生成报告
    print("\n" + "="*80)
    report = validator.generate_summary_report()
    print(report)
    
    # 分析最佳方案的信号日期
    best_name, _ = validator.get_best_definition()
    signal_analysis = validator.analyze_signal_dates(best_name)
    
    print(f"\n{best_name} 信号日期分析:")
    print(signal_analysis.to_string(index=False))
    
    return validator, results


if __name__ == "__main__":
    validator, results = main()