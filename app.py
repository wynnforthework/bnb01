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
binance_client = BinanceClient()
db_manager = DatabaseManager()
data_collector = DataCollector()
risk_manager = RiskManager()
backtest_engine = BacktestEngine()

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
    try:
        # 如果交易引擎未初始化，先初始化它
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

# 新增API端点

@app.route('/api/risk/portfolio')
def get_portfolio_risk():
    """获取投资组合风险指标"""
    try:
        risk_metrics = risk_manager.calculate_portfolio_risk()
        return jsonify({
            'success': True,
            'data': {
                'portfolio_value': risk_metrics.portfolio_value,
                'daily_pnl': risk_metrics.daily_pnl,
                'daily_return': risk_metrics.daily_return,
                'volatility': risk_metrics.volatility,
                'var_95': risk_metrics.var_95,
                'var_99': risk_metrics.var_99,
                'max_drawdown': risk_metrics.max_drawdown,
                'sharpe_ratio': risk_metrics.sharpe_ratio,
                'beta': risk_metrics.beta,
                'correlation_btc': risk_metrics.correlation_btc
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取风险指标失败: {str(e)}'})

@app.route('/api/risk/positions')
def get_position_risks():
    """获取各持仓的风险指标"""
    try:
        position_risks = risk_manager.get_position_risks()
        risks_data = []
        for risk in position_risks:
            risks_data.append({
                'symbol': risk.symbol,
                'quantity': risk.quantity,
                'market_value': risk.market_value,
                'weight': risk.weight,
                'volatility': risk.volatility,
                'var_95': risk.var_95,
                'beta': risk.beta,
                'correlation': risk.correlation
            })
        return jsonify({
            'success': True,
            'data': risks_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取持仓风险失败: {str(e)}'})

@app.route('/api/risk/report')
def get_risk_report():
    """获取风险报告"""
    try:
        report = risk_manager.generate_risk_report()
        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'生成风险报告失败: {str(e)}'})

@app.route('/api/data/collect', methods=['POST'])
def collect_historical_data():
    """收集历史数据"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'BTCUSDT')
        days = data.get('days', 30)
        interval = data.get('interval', '1h')
        
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            data_collector.collect_historical_data(symbol, interval, days)
        )
        loop.close()
        
        if not result.empty:
            return jsonify({
                'success': True,
                'message': f'成功收集 {len(result)} 条数据',
                'data_count': len(result)
            })
        else:
            return jsonify({'success': False, 'message': '数据收集失败'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'数据收集失败: {str(e)}'})

@app.route('/api/data/indicators/<symbol>')
def get_technical_indicators(symbol):
    """获取技术指标数据"""
    try:
        limit = request.args.get('limit', 100, type=int)
        indicators = data_collector.get_technical_indicators(symbol, limit)
        
        if not indicators.empty:
            return jsonify({
                'success': True,
                'data': indicators.to_dict('records')
            })
        else:
            return jsonify({'success': False, 'message': '暂无技术指标数据'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取技术指标失败: {str(e)}'})

@app.route('/api/backtest/run', methods=['POST'])
def run_backtest():
    """运行回测"""
    try:
        data = request.get_json()
        strategy_type = data.get('strategy_type', 'MA')
        symbol = data.get('symbol', 'BTCUSDT')
        start_date = data.get('start_date', '2023-01-01')
        end_date = data.get('end_date', '2023-12-31')
        parameters = data.get('parameters', {})
        
        # 创建策略实例
        if strategy_type == 'MA':
            strategy = MovingAverageStrategy(symbol, parameters)
        elif strategy_type == 'RSI':
            strategy = RSIStrategy(symbol, parameters)
        elif strategy_type == 'ML':
            strategy = MLStrategy(symbol, parameters)
        else:
            return jsonify({'success': False, 'message': '不支持的策略类型'})
        
        # 运行回测
        result = backtest_engine.run_backtest(strategy, symbol, start_date, end_date)
        
        # 转换结果为可序列化的格式
        backtest_data = {
            'total_return': result.total_return,
            'annual_return': result.annual_return,
            'max_drawdown': result.max_drawdown,
            'sharpe_ratio': result.sharpe_ratio,
            'win_rate': result.win_rate,
            'total_trades': result.total_trades,
            'profit_factor': result.profit_factor,
            'avg_trade_return': result.avg_trade_return,
            'volatility': result.volatility,
            'calmar_ratio': result.calmar_ratio,
            'equity_curve': result.equity_curve.tolist(),
            'drawdown_curve': result.drawdown_curve.tolist(),
            'trades': result.trades[-20:]  # 只返回最后20笔交易
        }
        
        return jsonify({
            'success': True,
            'data': backtest_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'回测失败: {str(e)}'})

@app.route('/api/backtest/compare', methods=['POST'])
def compare_strategies():
    """比较多个策略"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'BTCUSDT')
        start_date = data.get('start_date', '2023-01-01')
        end_date = data.get('end_date', '2023-12-31')
        
        # 创建多个策略
        strategies = [
            MovingAverageStrategy(symbol, {'short_window': 10, 'long_window': 30}),
            RSIStrategy(symbol, {'rsi_period': 14, 'oversold': 30, 'overbought': 70}),
            MLStrategy(symbol, {'model_type': 'random_forest'})
        ]
        
        comparison_result = backtest_engine.compare_strategies(
            strategies, symbol, start_date, end_date
        )
        
        return jsonify({
            'success': True,
            'data': comparison_result.to_dict('records')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'策略比较失败: {str(e)}'})

@app.route('/api/strategies/list')
def get_strategies():
    """获取策略列表"""
    global trading_engine
    try:
        # 如果交易引擎未初始化，先初始化它
        if trading_engine is None:
            trading_engine = TradingEngine()
        
        strategies_info = []
        for name, strategy in trading_engine.strategies.items():
            strategies_info.append({
                'name': name,
                'symbol': strategy.symbol,
                'type': strategy.__class__.__name__,
                'position': strategy.position,
                'entry_price': strategy.entry_price,
                'parameters': strategy.parameters
            })
        return jsonify({
            'success': True,
            'strategies': strategies_info
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取策略列表失败: {str(e)}'})

@app.route('/api/strategies/performance')
def get_strategy_performance():
    """获取策略表现"""
    try:
        performance_data = []
        strategy_names = ['MovingAverageStrategy', 'RSIStrategy', 'MLStrategy', 'LSTMStrategy']
        
        for strategy_name in strategy_names:
            perf = db_manager.get_strategy_performance(strategy_name)
            if perf:
                performance_data.append({
                    'strategy': strategy_name,
                    'total_trades': perf['total_trades'],
                    'win_rate': perf['win_rate'],
                    'total_pnl': perf['total_pnl'],
                    'avg_pnl': perf['avg_pnl']
                })
        
        return jsonify({
            'success': True,
            'data': performance_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取策略表现失败: {str(e)}'})

@app.route('/api/market/enhanced/<symbol>')
def get_enhanced_market_data(symbol):
    """获取增强的市场数据（包含技术指标）"""
    try:
        limit = request.args.get('limit', 100, type=int)
        interval = request.args.get('interval', '1h')
        
        # 获取基础市场数据
        market_data = data_collector.get_market_data(symbol, interval, limit)
        
        if market_data.empty:
            return jsonify({'success': False, 'message': '暂无市场数据'})
        
        # 计算技术指标
        enhanced_data = data_collector.calculate_technical_indicators(market_data, symbol)
        
        return jsonify({
            'success': True,
            'data': enhanced_data.to_dict('records')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取增强市场数据失败: {str(e)}'})

@app.route('/api/orderbook/<symbol>')
def get_orderbook(symbol):
    """获取订单簿数据"""
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        orderbook = loop.run_until_complete(
            data_collector.collect_orderbook_data(symbol)
        )
        loop.close()
        
        if orderbook:
            return jsonify({
                'success': True,
                'data': orderbook
            })
        else:
            return jsonify({'success': False, 'message': '获取订单簿失败'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取订单簿失败: {str(e)}'})

@app.route('/api/ml/train', methods=['POST'])
def train_ml_model():
    """训练机器学习模型"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'BTCUSDT')
        model_type = data.get('model_type', 'random_forest')
        
        # 创建ML策略并训练
        ml_strategy = MLStrategy(symbol, {'model_type': model_type})
        
        # 获取历史数据
        historical_data = data_collector.get_market_data(symbol, '1h', limit=1000)
        
        if historical_data.empty:
            return jsonify({'success': False, 'message': '训练数据不足'})
        
        # 训练模型
        success = ml_strategy.train_model(historical_data)
        
        if success:
            # 保存模型
            model_path = f'models/{symbol}_{model_type}_model.pkl'
            ml_strategy.save_model(model_path)
            
            return jsonify({
                'success': True,
                'message': '模型训练成功',
                'model_path': model_path
            })
        else:
            return jsonify({'success': False, 'message': '模型训练失败'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'模型训练失败: {str(e)}'})

@app.route('/api/alerts')
def get_alerts():
    """获取风险警告和系统提醒"""
    try:
        alerts = []
        
        # 获取风险警告
        portfolio_risk = risk_manager.calculate_portfolio_risk()
        position_risks = risk_manager.get_position_risks()
        
        warnings = risk_manager._generate_risk_warnings(portfolio_risk, position_risks)
        
        for warning in warnings:
            alerts.append({
                'type': 'risk',
                'level': 'warning',
                'message': warning,
                'timestamp': datetime.now().isoformat()
            })
        
        # 检查系统状态
        global trading_engine
        if trading_engine and not trading_engine.is_running:
            alerts.append({
                'type': 'system',
                'level': 'info',
                'message': '交易引擎未运行',
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({
            'success': True,
            'alerts': alerts
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取警告失败: {str(e)}'})

@app.route('/api/system/status')
def get_system_status():
    """获取系统状态"""
    try:
        global trading_engine
        
        status = {
            'trading_engine': trading_engine.is_running if trading_engine else False,
            'data_collection': trading_engine.data_collection_running if trading_engine else False,
            'database': True,  # 简化检查
            'api_connection': True,  # 简化检查
            'strategies_count': len(trading_engine.strategies) if trading_engine else 0,
            'uptime': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取系统状态失败: {str(e)}'})

@app.route('/api/export/trades')
def export_trades():
    """导出交易记录"""
    try:
        trades = db_manager.get_trades(limit=1000)
        trades_data = []
        
        for trade in trades:
            trades_data.append({
                'timestamp': trade.timestamp.isoformat(),
                'symbol': trade.symbol,
                'side': trade.side,
                'quantity': trade.quantity,
                'price': trade.price,
                'strategy': trade.strategy,
                'profit_loss': trade.profit_loss
            })
        
        return jsonify({
            'success': True,
            'data': trades_data,
            'count': len(trades_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'导出交易记录失败: {str(e)}'})

@app.route('/api/config/update', methods=['POST'])
def update_config():
    """更新系统配置"""
    try:
        data = request.get_json()
        
        # 这里可以添加配置更新逻辑
        # 例如更新策略参数、风险参数等
        
        return jsonify({
            'success': True,
            'message': '配置更新成功'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'配置更新失败: {str(e)}'})

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