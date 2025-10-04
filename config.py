"""
配置文件
Configuration Module

统一管理策略参数和分析设置
"""

from typing import Dict, List


# ===== 数据配置 =====
DATA_CONFIG = {
    # 默认标的
    'default_ticker': '000985.CSI',  # 中证全指
    'default_start_date': '2013-01-01',
    'default_end_date': None,  # None表示使用今天
}


# ===== 策略1: 下跌反弹 (已停止) =====
STRATEGY1_CONFIG = {
    'name': 'decline_rebound',
    'display_name': '下跌反弹形态',
    'status': 'discontinued',

    'parameters': {
        'lookback_days': 20,  # 回看天数
    },

    'note': '此策略已于2025-10-04停止开发，仅供学习参考'
}


# ===== 策略3: 三角形突破 =====
STRATEGY3_CONFIG = {
    'name': 'triangle_breakout',
    'display_name': '三角形突破',
    'status': 'active',

    # 预设参数配置
    'presets': {
        'basic': {
            'convergence_threshold': 0.01,   # 1%
            'breakout_threshold': 0.01,      # 1%
            'narrowing_ratio': 0.8,          # 收窄20%
            'description': '基础版本：最直观的参数，无调参嫌疑'
        },
        'strict': {
            'convergence_threshold': 0.008,  # 0.8%
            'breakout_threshold': 0.015,     # 1.5%
            'narrowing_ratio': 0.7,          # 收窄30%
            'description': '严格版本：更小的收敛阈值，更大的突破要求'
        },
        'loose': {
            'convergence_threshold': 0.012,  # 1.2%
            'breakout_threshold': 0.008,     # 0.8%
            'narrowing_ratio': 0.85,         # 收窄15%
            'description': '宽松版本：更宽松的条件，信号更多'
        }
    },

    # 默认使用基础版本
    'default_preset': 'basic'
}


# ===== 回测配置 =====
BACKTEST_CONFIG = {
    # 持有期设置
    'holding_periods': [1, 5, 10, 20, 40],  # 固定持有期（交易日）

    # 交易方向
    'direction': 'bidirectional',  # 'long', 'short', 'bidirectional'

    # 时间分割
    'time_split': {
        'enabled': True,
        'split_date': '2022-01-01',  # 训练期/测试期分割点
        'train_period_name': '训练期(2013-2021)',
        'test_period_name': '测试期(2022-2025)'
    },

    # 显著性检验
    'significance_level': 0.05,  # p值阈值
}


# ===== 指标配置 =====
INDICATOR_CONFIG = {
    'atr': {
        'window': 60,  # ATR窗口期
        'base_decline': -0.05,  # 基础下跌阈值 (-5%)
        'base_rebound': 0.005,  # 基础反弹阈值 (+0.5%)
    }
}


# ===== 输出配置 =====
OUTPUT_CONFIG = {
    # 输出目录
    'output_dir': 'outputs',

    # 图表设置
    'figure_dpi': 300,
    'figure_size': (18, 14),

    # 文件命名模式
    'filename_pattern': '{strategy_name}_{analysis_type}_{timestamp}.png'
}


# ===== 便捷函数 =====

def get_strategy_config(strategy_name: str) -> Dict:
    """
    获取策略配置

    Args:
        strategy_name: 策略名称，'decline_rebound' 或 'triangle_breakout'

    Returns:
        策略配置字典
    """
    configs = {
        'decline_rebound': STRATEGY1_CONFIG,
        'triangle_breakout': STRATEGY3_CONFIG
    }

    if strategy_name not in configs:
        raise ValueError(f"未知策略: {strategy_name}. "
                        f"可用策略: {list(configs.keys())}")

    return configs[strategy_name]


def get_strategy_parameters(strategy_name: str, preset: str = None) -> Dict:
    """
    获取策略参数

    Args:
        strategy_name: 策略名称
        preset: 预设名称（仅用于triangle_breakout），None表示使用默认

    Returns:
        参数字典
    """
    config = get_strategy_config(strategy_name)

    if strategy_name == 'triangle_breakout':
        # 三角形突破：使用预设参数
        preset = preset or config['default_preset']

        if preset not in config['presets']:
            raise ValueError(f"未知预设: {preset}. "
                           f"可用预设: {list(config['presets'].keys())}")

        return config['presets'][preset]

    elif strategy_name == 'decline_rebound':
        # 下跌反弹：直接返回参数
        return config['parameters']

    else:
        raise ValueError(f"未知策略: {strategy_name}")


def get_holding_periods() -> List[int]:
    """获取持有期列表"""
    return BACKTEST_CONFIG['holding_periods']


def get_time_split_date() -> str:
    """获取时间分割日期"""
    return BACKTEST_CONFIG['time_split']['split_date']


# ===== 配置验证 =====

def validate_config():
    """验证配置的完整性和一致性"""
    issues = []

    # 检查策略配置
    for strategy_name in ['decline_rebound', 'triangle_breakout']:
        try:
            config = get_strategy_config(strategy_name)

            # 检查必需字段
            required_fields = ['name', 'display_name', 'status']
            for field in required_fields:
                if field not in config:
                    issues.append(f"{strategy_name} 缺少字段: {field}")

        except Exception as e:
            issues.append(f"{strategy_name} 配置错误: {e}")

    # 检查回测配置
    if not BACKTEST_CONFIG['holding_periods']:
        issues.append("holding_periods 不能为空")

    if BACKTEST_CONFIG['direction'] not in ['long', 'short', 'bidirectional']:
        issues.append(f"无效的交易方向: {BACKTEST_CONFIG['direction']}")

    # 输出结果
    if issues:
        print("配置验证失败:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("配置验证通过")
        return True


if __name__ == '__main__':
    # 验证配置
    validate_config()

    # 打印配置摘要
    print("\n" + "="*80)
    print("策略配置摘要")
    print("="*80)

    for strategy in ['decline_rebound', 'triangle_breakout']:
        config = get_strategy_config(strategy)
        print(f"\n{config['display_name']} ({strategy}):")
        print(f"  状态: {config['status']}")

        if strategy == 'triangle_breakout':
            print(f"  预设参数:")
            for preset_name, preset_config in config['presets'].items():
                print(f"    - {preset_name}: {preset_config['description']}")
        else:
            print(f"  参数: {config['parameters']}")

    print(f"\n回测设置:")
    print(f"  持有期: {BACKTEST_CONFIG['holding_periods']}")
    print(f"  交易方向: {BACKTEST_CONFIG['direction']}")
    print(f"  时间分割: {BACKTEST_CONFIG['time_split']['split_date']}")
