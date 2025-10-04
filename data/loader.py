"""
数据加载模块
Data Loader Module

支持多数据源，优先使用WindPy，回退到演示数据
"""

import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime

try:
    from WindPy import w
    WIND_AVAILABLE = True
except ImportError:
    WIND_AVAILABLE = False


class DataLoader:
    """
    通用数据加载器

    支持：
    - WindPy API（优先）
    - 演示数据（回退）
    """

    def __init__(self, auto_connect: bool = True):
        """
        初始化数据加载器

        Args:
            auto_connect: 是否自动连接Wind API
        """
        self.connected = False

        if WIND_AVAILABLE and auto_connect:
            try:
                w.start()
                self.connected = True
                print("Wind API连接成功")
            except Exception as e:
                print(f"Wind API连接失败: {e}")
                self.connected = False
        elif not WIND_AVAILABLE:
            print("Warning: WindPy未安装，将使用演示数据")

    def load_ohlc_data(self,
                       ticker: str,
                       start_date: str,
                       end_date: Optional[str] = None) -> pd.DataFrame:
        """
        加载OHLC价格数据

        Args:
            ticker: 股票/指数代码，例如'000985.CSI'（中证全指）
            start_date: 开始日期，格式'YYYY-MM-DD'
            end_date: 结束日期，格式'YYYY-MM-DD'，默认为今天

        Returns:
            pd.DataFrame: 包含['open', 'high', 'low', 'close', 'volume', 'amt']的数据框
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # 尝试从Wind获取数据
        if self.connected:
            try:
                data = self._load_from_wind(ticker, start_date, end_date)
                print(f"成功获取{len(data)}条{ticker}数据")
                return data
            except Exception as e:
                print(f"获取Wind数据失败: {e}，使用演示数据")

        # 回退到演示数据
        print(f"使用演示数据模拟{ticker}")
        return self._generate_demo_data(start_date, end_date)

    def _load_from_wind(self,
                       ticker: str,
                       start_date: str,
                       end_date: str) -> pd.DataFrame:
        """
        从Wind API加载数据

        Args:
            ticker: Wind代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: OHLC数据
        """
        fields = "open,high,low,close,volume,amt"
        result = w.wsd(ticker, fields, start_date, end_date)

        if result.ErrorCode != 0:
            raise Exception(f"Wind API错误: {result.Data}")

        # 转换为DataFrame
        df = pd.DataFrame(
            result.Data,
            columns=result.Times,
            index=fields.split(",")
        ).T

        df.index.name = 'trade_date'

        # 转换为数值类型
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 删除缺失值
        df = df.dropna()

        return df

    def _generate_demo_data(self,
                           start_date: str,
                           end_date: str) -> pd.DataFrame:
        """
        生成演示数据

        基于真实市场特征的随机数据，包含：
        - 随机波动
        - 趋势成分
        - 极端事件
        - 合理的OHLC关系

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            pd.DataFrame: 模拟的OHLC数据
        """
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        dates = pd.bdate_range(start=start, end=end)

        n_days = len(dates)
        np.random.seed(42)

        # 1. 基础收益：正态分布 + 趋势 + 波动率变化
        returns = np.random.normal(0.0005, 0.015, n_days)

        # 2. 波动率制度切换
        volatility_regime = np.random.choice(
            [0.8, 1.2, 2.0],
            n_days,
            p=[0.7, 0.2, 0.1]
        )
        returns *= volatility_regime

        # 3. 趋势成分（周期性）
        trend = np.sin(np.arange(n_days) * 2 * np.pi / 252) * 0.002
        returns += trend

        # 4. 极端事件（2%概率）
        extreme_events = np.random.choice([0, 1], n_days, p=[0.98, 0.02])
        extreme_returns = np.random.normal(-0.05, 0.02, n_days)
        returns = np.where(extreme_events, extreme_returns, returns)

        # 5. 计算收盘价
        base_price = 4000.0
        close_prices = base_price * np.exp(np.cumsum(returns))

        # 6. 计算开盘价（含跳空）
        gap_returns = np.random.normal(0, 0.002, n_days)
        open_prices = np.roll(close_prices, 1) * (1 + gap_returns)
        open_prices[0] = close_prices[0]

        # 7. 计算高低价（基于日内波动）
        high_low_range = np.abs(returns) * 0.6 + 0.003

        high_prices = np.maximum(open_prices, close_prices) * (
            1 + high_low_range * np.random.uniform(0.2, 1.0, n_days)
        )
        low_prices = np.minimum(open_prices, close_prices) * (
            1 - high_low_range * np.random.uniform(0.2, 1.0, n_days)
        )

        # 8. 计算成交量和成交额
        base_volume = 1e8
        volume = base_volume * (
            1 + np.abs(returns) * 5 + np.random.normal(0, 0.3, n_days)
        )
        volume = np.maximum(volume, base_volume * 0.1)

        amt = volume * close_prices * np.random.uniform(0.8, 1.2, n_days)

        # 9. 构建DataFrame
        df = pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volume,
            'amt': amt,
        }, index=dates)

        df.index.name = 'trade_date'

        # 10. 确保OHLC关系正确
        df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
        df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)

        print(f"生成了{len(df)}条模拟数据，时间范围: "
              f"{df.index[0].date()} 到 {df.index[-1].date()}")

        return df

    def close(self):
        """关闭Wind连接"""
        if WIND_AVAILABLE and self.connected:
            try:
                w.stop()
                print("Wind API连接已关闭")
            except Exception:
                pass


def load_csi_all_index(start_date: str = "2013-01-01",
                       end_date: Optional[str] = None) -> pd.DataFrame:
    """
    便捷函数：加载中证全指(000985.CSI)数据

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        pd.DataFrame: OHLC数据
    """
    loader = DataLoader()
    data = loader.load_ohlc_data("000985.CSI", start_date, end_date)
    loader.close()
    return data
