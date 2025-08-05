from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.config import Config

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # BUY/SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    strategy = Column(String(50))
    profit_loss = Column(Float, default=0.0)
    status = Column(String(20), default='FILLED')

class Position(Base):
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, unique=True)
    quantity = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Strategy(Base):
    __tablename__ = 'strategies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    symbol = Column(String(20), nullable=False)
    parameters = Column(String(500))  # JSON格式的参数
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)

class DatabaseManager:
    def __init__(self):
        self.config = Config()
        self.engine = create_engine(self.config.DATABASE_URL)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_trade(self, symbol, side, quantity, price, strategy=None, profit_loss=0.0):
        """添加交易记录"""
        trade = Trade(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            strategy=strategy,
            profit_loss=profit_loss
        )
        self.session.add(trade)
        self.session.commit()
        return trade
    
    def update_position(self, symbol, quantity, avg_price, current_price):
        """更新持仓"""
        position = self.session.query(Position).filter_by(symbol=symbol).first()
        if position:
            position.quantity = quantity
            position.avg_price = avg_price
            position.current_price = current_price
            position.unrealized_pnl = (current_price - avg_price) * quantity
            position.timestamp = datetime.utcnow()
        else:
            position = Position(
                symbol=symbol,
                quantity=quantity,
                avg_price=avg_price,
                current_price=current_price,
                unrealized_pnl=(current_price - avg_price) * quantity
            )
            self.session.add(position)
        self.session.commit()
        return position
    
    def get_positions(self):
        """获取所有持仓"""
        return self.session.query(Position).all()
    
    def get_trades(self, limit=100):
        """获取交易历史"""
        return self.session.query(Trade).order_by(Trade.timestamp.desc()).limit(limit).all()
    
    def get_strategy_performance(self, strategy_name):
        """获取策略表现"""
        trades = self.session.query(Trade).filter_by(strategy=strategy_name).all()
        if not trades:
            return None
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.profit_loss > 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        total_pnl = sum(t.profit_loss for t in trades)
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl': total_pnl / total_trades if total_trades > 0 else 0
        }