"""
数据加载模块 - 使用Wind API获取中证全指数据
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
from datetime import datetime, timedelta

try:
    from WindPy import w
    WIND_AVAILABLE = True
except ImportError:
    WIND_AVAILABLE = False
    print("Warning: WindPy not available, will use demo data")


class WindDataLoader:
    """Wind API数据加载器"""
    
    def __init__(self):
        """初始化Wind连接"""
        self.connected = False
        if WIND_AVAILABLE:
            try:
                w.start()
                self.connected = True
                print("Wind API连接成功")
            except Exception as e:
                print(f"Wind API连接失败: {e}")
                self.connected = False
    
    def get_csi_all_data(self, 
                        start_date: str = "2013-01-01", 
                        end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取中证全指(000985.CSI)的OHLC数据
        
        Args:
            start_date: 开始日期，格式 "YYYY-MM-DD"
            end_date: 结束日期，格式 "YYYY-MM-DD"，默认为今天
            
        Returns:
            包含OHLC数据的DataFrame
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        if not self.connected:
            print("Wind API未连接，使用演示数据")
            return self._generate_demo_data(start_date, end_date)
        
        try:
            # 获取中证全指数据
            fields = "open,high,low,close,volume,amt"
            data = w.wsd("000985.CSI", fields, start_date, end_date)
            
            if data.ErrorCode != 0:
                raise Exception(f"Wind API错误: {data.Data}")
            
            # 转换为DataFrame
            df = pd.DataFrame(data.Data, columns=data.Times, index=fields.split(",")).T
            df.index.name = 'trade_date'
            
            # 数据类型转换
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 移除缺失值
            df = df.dropna()
            
            print(f"成功获取{len(df)}条中证全指数据")
            return df
            
        except Exception as e:
            print(f"获取Wind数据失败: {e}，使用演示数据")
            return self._generate_demo_data(start_date, end_date)
    
    def _generate_demo_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        生成演示用的模拟数据（基于真实市场特征）
        """
        print("生成模拟的中证全指数据用于测试...")
        
        # 创建日期范围（只包含工作日）
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        dates = pd.bdate_range(start=start, end=end)
        
        n_days = len(dates)
        np.random.seed(42)  # 固定随机种子保证可复现
        
        # 模拟价格走势（几何布朗运动 + 市场特征）
        returns = np.random.normal(0.0005, 0.015, n_days)  # 年化收益5%，波动15%
        
        # 添加一些市场特征
        # 1. 增加集群波动率
        volatility_regime = np.random.choice([0.8, 1.2, 2.0], n_days, p=[0.7, 0.2, 0.1])
        returns *= volatility_regime
        
        # 2. 添加趋势项
        trend = np.sin(np.arange(n_days) * 2 * np.pi / 252) * 0.002  # 年度周期
        returns += trend
        
        # 3. 模拟重大事件的极端收益
        extreme_events = np.random.choice([0, 1], n_days, p=[0.98, 0.02])
        extreme_returns = np.random.normal(-0.05, 0.02, n_days)
        returns = np.where(extreme_events, extreme_returns, returns)
        
        # 生成价格序列
        base_price = 4000.0  # 起始价格
        close_prices = base_price * np.exp(np.cumsum(returns))
        
        # 生成OHLC数据
        high_low_range = np.abs(returns) * 0.6 + 0.003  # 日内波动范围
        
        # Open价格（前一日close的小幅跳空）
        gap_returns = np.random.normal(0, 0.002, n_days)
        open_prices = np.roll(close_prices, 1) * (1 + gap_returns)
        open_prices[0] = close_prices[0]  # 第一天没有跳空
        
        # High和Low价格
        high_prices = np.maximum(open_prices, close_prices) * (1 + high_low_range * np.random.uniform(0.2, 1.0, n_days))
        low_prices = np.minimum(open_prices, close_prices) * (1 - high_low_range * np.random.uniform(0.2, 1.0, n_days))
        
        # 成交量和成交额
        base_volume = 1e8
        volume = base_volume * (1 + np.abs(returns) * 5 + np.random.normal(0, 0.3, n_days))
        volume = np.maximum(volume, base_volume * 0.1)  # 最小成交量
        
        amt = volume * close_prices * np.random.uniform(0.8, 1.2, n_days)
        
        # 创建DataFrame
        df = pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volume,
            'amt': amt
        }, index=dates)
        
        df.index.name = 'trade_date'
        
        # 确保OHLC关系正确
        df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
        df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
        
        print(f"生成了{len(df)}条模拟数据，时间范围: {df.index[0].date()} 到 {df.index[-1].date()}")
        
        return df
    
    def add_atr60(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        为数据添加ATR60指标
        
        Args:
            df: OHLC数据DataFrame
            
        Returns:
            添加ATR60列的DataFrame
        """
        from .metrics.atr import calculate_atr
        
        df_with_atr = df.copy()
        atr60 = calculate_atr(df['high'], df['low'], df['close'], window=60)
        df_with_atr['atr60'] = atr60
        
        return df_with_atr
    
    def get_known_signals(self) -> list:
        """
        获取已知的52个信号日期
        
        Returns:
            信号日期列表
        """
        signal_dates = [
            '20130319', '20130409', '20130614', '20130626', '20131030', '20131224',
            '20140114', '20140228', '20140429', '20150508', '20150630', '20150709',
            '20150729', '20150827', '20150916', '20160106', '20160114', '20160129',
            '20160301', '20160516', '20160802', '20170516', '20180212', '20180327',
            '20180531', '20180620', '20180807', '20181017', '20181128', '20181224',
            '20190430', '20190808', '20200204', '20200302', '20200320', '20200720',
            '20210301', '20210311', '20210729', '20220126', '20220310', '20220427',
            '20220906', '20220920', '20221012', '20221226', '20230428', '20231024',
            '20240123', '20240206', '20241014', '20241119', '20250107', '20250408'
        ]
        
        # 转换为datetime格式
        return [pd.to_datetime(date, format='%Y%m%d') for date in signal_dates]
    
    def close(self):
        """关闭Wind连接"""
        if WIND_AVAILABLE and self.connected:
            try:
                w.stop()
                print("Wind API连接已关闭")
            except:
                pass