import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Binance API配置
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')
    BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'True').lower() == 'true'
    
    # 数据库配置
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///trading.db')
    
    # Redis配置
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # 交易配置
    DEFAULT_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT']
    DEFAULT_TIMEFRAME = '1h'
    MAX_POSITION_SIZE = 0.1  # 最大仓位比例
    STOP_LOSS_PERCENT = 0.02  # 止损比例
    TAKE_PROFIT_PERCENT = 0.05  # 止盈比例
    
    # 风险管理
    MAX_DAILY_LOSS = 0.05  # 最大日损失比例
    MAX_DRAWDOWN = 0.15  # 最大回撤比例
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'