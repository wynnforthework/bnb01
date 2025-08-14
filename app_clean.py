from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import json
from datetime import datetime, timedelta

from backend.trading_engine import TradingEngine
from backend.binance_client import BinanceClient
from backend.database import DatabaseManager
from backend.data_collector import DataCollector
from backend.risk_manager import RiskManager
from backend.backtesting import BacktestEngine
from strategies.ma_strategy import MovingAverageStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.ml_strategy import MLStrategy
from config.config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
trading_engine = None
futures_trading_engine = None

# 初始化现货交易引擎（用于策略列表显示）
def initialize_spot_engine():
    """初始化现货交易引擎"""
    global trading_engine
    if trading_engine is None:
        try:
            print("初始化现货交易引擎...")
            trading_engine = TradingEngine(trading_mode='SPOT')
            print(f"现货交易引擎初始化成功，策略数量: {len(trading_engine.strategies)}")
        except Exception as e:
            print(f"初始化现货交易引擎失败: {e}")

# 初始化合约交易引擎（用于策略列表显示）
def initialize_futures_engine():
    """初始化合约交易引擎"""
    global futures_trading_engine
    if futures_trading_engine is None:
        try:
            print("初始化合约交易引擎...")
            futures_trading_engine = TradingEngine(trading_mode='FUTURES', leverage=10)
            print(f"合约交易引擎初始化成功，策略数量: {len(futures_trading_engine.strategies)}")
        except Exception as e:
            print(f"初始化合约交易引擎失败: {e}")

# 在应用启动时初始化
try:
    initialize_spot_engine()
    initialize_futures_engine()
except Exception as e:
    print(f"应用启动时初始化引擎失败: {e}")

# 使用客户端管理器避免重复初始化
from backend.client_manager import client_manager
binance_client = client_manager.get_spot_client()
futures_client = client_manager.get_futures_client()

db_manager = DatabaseManager()
data_collector = DataCollector()
risk_manager = RiskManager()
backtest_engine = BacktestEngine()

@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/futures')
# def futures():
#     return render_template('futures.html')

@app.route('/api/account')
def get_account():
    """获取账户信息"""
    account_info = binance_client.get_account_info()
    if account_info:
        balances = []
        for balance in account_info['balances']:
            free = float(balance['free'])
            locked = float(balance['locked'])
            if free > 0 or locked > 0:
                balances.append({
                    'asset': balance['asset'],
                    'free': free,
                    'locked': locked,
                    'total': free + locked
                })
        return jsonify({
            'success': True,
            'balances': balances
        })
    return jsonify({'success': False, 'message': '获取账户信息失败'})

@app.route('/api/portfolio')
def get_portfolio():
    """获取投资组合"""
    global trading_engine
    try:
        if trading_engine is None:
            trading_engine = TradingEngine()
        
        portfolio = trading_engine.get_portfolio_status()
        return jsonify({
            'success': True,
            'data': portfolio
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取投资组合失败: {str(e)}'})

@app.route('/api/trades')
def get_trades():
    """获取交易历史"""
    trades = db_manager.get_trades(limit=100)
    trade_list = []
    for trade in trades:
        trade_list.append({
            'id': trade.id,
            'symbol': trade.symbol,
            'side': trade.side,
            'quantity': trade.quantity,
            'price': trade.price,
            'timestamp': trade.timestamp.isoformat(),
            'strategy': trade.strategy,
            'profit_loss': trade.profit_loss
        })
    return jsonify({
        'success': True,
        'trades': trade_list
    })

@app.route('/api/trading/start', methods=['POST'])
def start_trading():
    """启动交易"""
    global trading_engine
    try:
        if trading_engine is None:
            trading_engine = TradingEngine()
        
        if not trading_engine.is_running:
            trading_thread = threading.Thread(target=trading_engine.start_trading)
            trading_thread.daemon = True
            trading_thread.start()
            return jsonify({'success': True, 'message': '交易已启动'})
        else:
            return jsonify({'success': False, 'message': '交易已在运行中'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动失败: {str(e)}'})

@app.route('/api/trading/stop', methods=['POST'])
def stop_trading():
    """停止交易"""
    global trading_engine
    if trading_engine and trading_engine.is_running:
        trading_engine.stop_trading()
        return jsonify({'success': True, 'message': '交易已停止'})
    return jsonify({'success': False, 'message': '交易未在运行'})

@app.route('/api/trading/status')
def get_trading_status():
    """获取交易状态"""
    global trading_engine
    is_running = trading_engine.is_running if trading_engine else False
    return jsonify({
        'success': True,
        'is_running': is_running
    })

# ========== 合约交易API端点 ==========

@app.route('/api/futures/account')
def get_futures_account():
    """获取合约账户信息"""
    try:
        account_balance = futures_client.get_account_balance()
        if account_balance:
            return jsonify({
                'success': True,
                'data': {
                    'totalWalletBalance': account_balance['totalWalletBalance'],
                    'totalUnrealizedProfit': account_balance['totalUnrealizedProfit'],
                    'totalMarginBalance': account_balance['totalMarginBalance'],
                    'totalPositionInitialMargin': account_balance['totalPositionInitialMargin'],
                    'totalOpenOrderInitialMargin': account_balance['totalOpenOrderInitialMargin'],
                    'availableBalance': account_balance['availableBalance'],
                    'maxWithdrawAmount': account_balance['maxWithdrawAmount'],
                    'assets': account_balance['assets']
                }
            })
        else:
            return jsonify({'success': False, 'message': '获取合约账户信息失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取合约账户信息失败: {str(e)}'})

@app.route('/api/futures/positions')
def get_futures_positions():
    """获取合约持仓"""
    try:
        positions = futures_client.get_positions()
        positions_data = []
        
        for pos in positions:
            # Calculate percentage if not provided by API
            percentage = 0
            if 'percentage' in pos:
                percentage = float(pos['percentage'])
            else:
                # Calculate percentage based on entry price and mark price
                entry_price = float(pos['entryPrice'])
                mark_price = float(pos['markPrice'])
                if entry_price > 0:
                    percentage = ((mark_price - entry_price) / entry_price) * 100
                    if float(pos['positionAmt']) < 0:  # Short position
                        percentage = -percentage
            
            positions_data.append({
                'symbol': pos['symbol'],
                'positionAmt': float(pos['positionAmt']),
                'entryPrice': float(pos['entryPrice']),
                'markPrice': float(pos['markPrice']),
                'unRealizedProfit': float(pos['unRealizedProfit']),
                'percentage': percentage,
                'positionSide': pos['positionSide'],
                'marginType': pos['marginType'],
                'isolatedMargin': float(pos['isolatedMargin']),
                'leverage': pos['leverage']
            })
        
        return jsonify({
            'success': True,
            'positions': positions_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取合约持仓失败: {str(e)}'})

@app.route('/api/futures/trading/start', methods=['POST'])
def start_futures_trading():
    """启动合约交易"""
    global futures_trading_engine
    try:
        data = request.get_json()
        leverage = data.get('leverage', 10)
        symbols = data.get('symbols', ['BTCUSDT', 'ETHUSDT'])
        
        if futures_trading_engine is None:
            futures_trading_engine = TradingEngine(trading_mode='FUTURES', leverage=leverage)
        
        if not futures_trading_engine.is_running:
            trading_thread = threading.Thread(target=futures_trading_engine.start_trading)
            trading_thread.daemon = True
            trading_thread.start()
            return jsonify({
                'success': True, 
                'message': f'合约交易已启动，杠杆: {leverage}x，币种: {", ".join(symbols)}'
            })
        else:
            return jsonify({'success': False, 'message': '合约交易已在运行中'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动合约交易失败: {str(e)}'})

@app.route('/api/futures/trading/stop', methods=['POST'])
def stop_futures_trading():
    """停止合约交易"""
    global futures_trading_engine
    if futures_trading_engine and futures_trading_engine.is_running:
        futures_trading_engine.stop_trading()
        return jsonify({'success': True, 'message': '合约交易已停止'})
    return jsonify({'success': False, 'message': '合约交易未在运行'})

@app.route('/api/futures/trading/status')
def get_futures_trading_status():
    """获取合约交易状态"""
    global futures_trading_engine
    is_running = futures_trading_engine.is_running if futures_trading_engine else False
    leverage = futures_trading_engine.leverage if futures_trading_engine else 10
    strategies_count = len(futures_trading_engine.strategies) if futures_trading_engine else 0
    
    status = 'RUNNING' if is_running else 'STOPPED'
    
    return jsonify({
        'success': True,
        'status': status,
        'is_running': is_running,
        'leverage': leverage,
        'strategies_count': strategies_count,
        'trading_mode': 'FUTURES'
    })

@app.route('/api/futures/leverage/set', methods=['POST'])
def set_futures_leverage():
    """设置合约杠杆"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'BTCUSDT')
        leverage = data.get('leverage', 10)
        
        result = futures_client.set_leverage(symbol, leverage)
        if result:
            return jsonify({
                'success': True,
                'message': f'{symbol} 杠杆设置为 {leverage}x'
            })
        else:
            return jsonify({'success': False, 'message': '杠杆设置失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'设置杠杆失败: {str(e)}'})

@app.route('/api/futures/order/place', methods=['POST'])
def place_futures_order():
    """下合约订单"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'BTCUSDT')
        side = data.get('side', 'BUY')
        quantity = float(data.get('quantity', 0.001))
        order_type = data.get('order_type', 'MARKET')
        price = data.get('price', None)
        leverage = data.get('leverage', 10)
        position_side = data.get('position_side', 'LONG')
        
        if order_type == 'LIMIT' and not price:
            return jsonify({'success': False, 'message': '限价单必须指定价格'})
        
        order = futures_client.place_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            leverage=leverage,
            position_side=position_side
        )
        
        if order:
            return jsonify({
                'success': True,
                'message': '合约订单下单成功',
                'order_id': order.get('orderId', 'N/A'),
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': order.get('price', 'MARKET')
            })
        else:
            return jsonify({'success': False, 'message': '合约订单下单失败'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'下单失败: {str(e)}'})

@app.route('/api/futures/market/<symbol>')
def get_futures_market_data(symbol):
    """获取合约市场数据"""
    try:
        # 获取基础价格信息
        current_price = futures_client.get_ticker_price(symbol)
        
        # 获取标记价格信息
        mark_price_info = futures_client.get_mark_price(symbol)
        
        # 获取资金费率
        funding_rate = futures_client.get_funding_rate(symbol)
        
        # 获取K线数据
        klines = futures_client.get_klines(symbol, '1h', 24)
        
        market_data = {
            'symbol': symbol,
            'currentPrice': current_price,
            'markPrice': mark_price_info['markPrice'] if mark_price_info else current_price,
            'indexPrice': mark_price_info['indexPrice'] if mark_price_info else current_price,
            'fundingRate': funding_rate['fundingRate'] if funding_rate else 0,
            'nextFundingTime': mark_price_info['nextFundingTime'] if mark_price_info else None,
            'klines': klines.to_dict('records') if not klines.empty else []
        }
        
        return jsonify({
            'success': True,
            'data': market_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取合约市场数据失败: {str(e)}'})

@app.route('/api/futures/position/close', methods=['POST'])
def close_futures_position():
    """平仓"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'BTCUSDT')
        position_side = data.get('position_side', 'BOTH')
        
        result = futures_client.close_position(symbol, position_side)
        if result:
            return jsonify({
                'success': True,
                'message': f'{symbol} 持仓已平仓',
                'order_id': result.get('orderId', 'N/A')
            })
        else:
            return jsonify({'success': False, 'message': '平仓失败或无持仓'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'平仓失败: {str(e)}'})

@app.route('/api/futures/trades')
def get_futures_trades():
    """获取合约交易历史"""
    try:
        trades = db_manager.get_trades(limit=100)
        futures_trades = []
        
        for trade in trades:
            # 检查是否是合约交易记录
            # 方法1: 检查策略名称是否包含FUTURES
            # 方法2: 检查交易记录是否有trading_mode字段
            # 方法3: 检查是否是合约交易引擎产生的记录
            is_futures_trade = (
                'FUTURES' in str(trade.strategy) or 
                hasattr(trade, 'trading_mode') or
                '合约' in str(trade.strategy) or
                trade.strategy in ['MovingAverageStrategy', 'RSIStrategy', 'MLStrategy']  # 这些策略在合约模式下也会使用
            )
            
            if is_futures_trade:
                futures_trades.append({
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'timestamp': trade.timestamp.isoformat(),
                    'strategy': trade.strategy,
                    'profit_loss': trade.profit_loss,
                    'type': 'FUTURES'
                })
        
        return jsonify({
            'success': True,
            'trades': futures_trades
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取合约交易历史失败: {str(e)}'})

@app.route('/api/futures/strategies/list')
def get_futures_strategies():
    """获取合约策略列表"""
    global futures_trading_engine
    try:
        if futures_trading_engine is None:
            return jsonify({
                'success': True,
                'strategies': []
            })
        
        strategies_info = []
        for name, strategy in futures_trading_engine.strategies.items():
            strategies_info.append({
                'name': name,
                'symbol': strategy.symbol,
                'type': strategy.__class__.__name__,
                'position': strategy.position,
                'entry_price': strategy.entry_price,
                'parameters': strategy.parameters,
                'leverage': futures_trading_engine.leverage
            })
        
        return jsonify({
            'success': True,
            'strategies': strategies_info
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取合约策略列表失败: {str(e)}'})

# 创建models目录
import os
if not os.path.exists('models'):
    os.makedirs('models')

@socketio.on('connect')
def handle_connect():
    print('客户端已连接')
    emit('connected', {'data': '连接成功'})

@socketio.on('disconnect')
def handle_disconnect():
    print('客户端已断开连接')

def broadcast_updates():
    """广播实时更新"""
    while True:
        try:
            # 获取现货实时数据
            if trading_engine:
                portfolio = trading_engine.get_portfolio_status()
                socketio.emit('portfolio_update', portfolio)
            
            # 获取合约实时数据
            if futures_trading_engine:
                futures_portfolio = futures_trading_engine.get_portfolio_status()
                socketio.emit('futures_portfolio_update', futures_portfolio)
            
            # 获取最新交易
            recent_trades = db_manager.get_trades(limit=10)
            trade_data = []
            futures_trade_data = []
            
            for trade in recent_trades:
                trade_info = {
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'timestamp': trade.timestamp.isoformat(),
                    'profit_loss': trade.profit_loss
                }
                
                # 区分现货和合约交易
                if 'FUTURES' in str(trade.strategy):
                    futures_trade_data.append(trade_info)
                else:
                    trade_data.append(trade_info)
            
            socketio.emit('trades_update', trade_data)
            socketio.emit('futures_trades_update', futures_trade_data)
            
            socketio.sleep(5)  # 每5秒更新一次
        except Exception as e:
            print(f"广播更新错误: {e}")
            socketio.sleep(10)

if __name__ == '__main__':
    # 启动实时更新线程
    update_thread = threading.Thread(target=broadcast_updates)
    update_thread.daemon = True
    update_thread.start()
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)