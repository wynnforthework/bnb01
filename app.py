from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import json
from datetime import datetime, timedelta

from backend.trading_engine import TradingEngine
from backend.binance_client import BinanceClient
from backend.database import DatabaseManager
from config.config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
trading_engine = None
binance_client = BinanceClient()
db_manager = DatabaseManager()

@app.route('/')
def index():
    return render_template('index.html')

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
    if trading_engine:
        portfolio = trading_engine.get_portfolio_status()
        return jsonify({
            'success': True,
            'data': portfolio
        })
    return jsonify({'success': False, 'message': '交易引擎未启动'})

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

@app.route('/api/market/<symbol>')
def get_market_data(symbol):
    """获取市场数据"""
    data = binance_client.get_klines(symbol=symbol, interval='1h', limit=100)
    if data is not None:
        return jsonify({
            'success': True,
            'data': data.to_dict('records')
        })
    return jsonify({'success': False, 'message': '获取市场数据失败'})

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
            # 获取实时数据
            if trading_engine:
                portfolio = trading_engine.get_portfolio_status()
                socketio.emit('portfolio_update', portfolio)
            
            # 获取最新交易
            recent_trades = db_manager.get_trades(limit=10)
            trade_data = []
            for trade in recent_trades:
                trade_data.append({
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'timestamp': trade.timestamp.isoformat(),
                    'profit_loss': trade.profit_loss
                })
            socketio.emit('trades_update', trade_data)
            
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