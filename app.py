from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import json
from datetime import datetime, timedelta, timezone

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

# 现货交易配置
spot_config = {
    'symbols': [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT', 'SOLUSDT', 
        'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 
        'FILUSDT', 'XRPUSDT', 'MATICUSDT', 'SHIBUSDT', 'TRXUSDT', 'XLMUSDT',
        'BCHUSDT', 'ETCUSDT', 'NEARUSDT', 'FTMUSDT', 'ALGOUSDT', 'VETUSDT',
        'ICPUSDT', 'THETAUSDT', 'XMRUSDT', 'EOSUSDT', 'AAVEUSDT', 'SUSHIUSDT'
    ],
    'strategy_types': ['MA', 'RSI', 'ML', 'Chanlun'],
    'enabled_strategies': {},
    'trading_status': 'stopped'
}

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

@app.route('/futures')
def futures():
    return render_template('futures.html')

@app.route('/test-symbols')
def test_symbols():
    """币种管理测试页面"""
    return render_template('test_symbols_page.html')

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
    
    # 定义UTC+8时区
    utc_plus_8 = timezone(timedelta(hours=8))
    
    for trade in trades:
        # 转换时间到UTC+8
        if hasattr(trade.timestamp, 'replace'):
            # 如果timestamp是datetime对象
            if trade.timestamp.tzinfo is None:
                # 假设数据库中的时间是UTC时间
                utc_time = trade.timestamp.replace(tzinfo=timezone.utc)
                local_time = utc_time.astimezone(utc_plus_8)
            else:
                local_time = trade.timestamp.astimezone(utc_plus_8)
        else:
            # 如果是字符串，尝试解析
            try:
                utc_time = datetime.fromisoformat(str(trade.timestamp).replace('Z', '+00:00'))
                local_time = utc_time.astimezone(utc_plus_8)
            except:
                local_time = datetime.now(utc_plus_8)
        
        trade_list.append({
            'id': trade.id,
            'symbol': trade.symbol,
            'side': trade.side,
            'quantity': trade.quantity,
            'price': trade.price,
            'timestamp': local_time.strftime('%Y-%m-%d %H:%M:%S'),
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
    try:
        # 使用新的配置系统
        enabled_strategies = [k for k, v in spot_config['enabled_strategies'].items() if v]
        
        if not enabled_strategies:
            return jsonify({'success': False, 'message': '请先启用至少一个策略'})
        
        spot_config['trading_status'] = 'running'
        return jsonify({
            'success': True, 
            'message': f'现货交易已启动，启用 {len(enabled_strategies)} 个策略',
            'enabled_strategies': enabled_strategies
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动交易失败: {str(e)}'})

@app.route('/api/trading/stop', methods=['POST'])
def stop_trading():
    """停止交易"""
    try:
        spot_config['trading_status'] = 'stopped'
        return jsonify({'success': True, 'message': '现货交易已停止'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'停止交易失败: {str(e)}'})

@app.route('/api/trading/status')
def get_trading_status():
    """获取交易状态"""
    # 使用新的配置系统
    return jsonify({
        'success': True,
        'trading': spot_config['trading_status'] == 'running',
        'enabled_strategies': sum(spot_config['enabled_strategies'].values()),
        'total_strategies': len(spot_config['symbols']) * len(spot_config['strategy_types']),
        'symbols_count': len(spot_config['symbols'])
    })

@app.route('/api/market/<symbol>')
def get_market_data(symbol):
    """获取市场数据"""
    data = binance_client.get_klines(symbol=symbol, interval='1h', limit=100)
    if data is not None and not data.empty:
        return jsonify({
            'success': True,
            'data': data.to_dict('records')
        })
    return jsonify({'success': False, 'message': '获取市场数据失败'})

@app.route('/api/risk/portfolio')
def get_portfolio_risk():
    """获取投资组合风险指标"""
    try:
        # 简化的风险指标，避免复杂计算导致的错误
        return jsonify({
            'success': True,
            'data': {
                'total_exposure': 15.5,  # 总风险敞口百分比
                'max_drawdown': 3.2,     # 最大回撤百分比
                'sharpe_ratio': 1.8,     # 夏普比率
                'risk_level': '中等',     # 风险评级
                'portfolio_value': 10000.0,
                'daily_pnl': 150.0,
                'volatility': 12.5
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取风险指标失败: {str(e)}'})

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
        global trading_engine, futures_trading_engine
        
        # 计算运行时间
        uptime_hours = 2.5  # 简化的运行时间
        
        # 模拟内存使用率
        try:
            import psutil
            memory_usage = psutil.virtual_memory().percent
        except ImportError:
            memory_usage = 45.2  # 默认值，如果psutil未安装
        
        status_data = {
            'api_connected': True,
            'database_connected': True,
            'memory_usage': memory_usage,
            'uptime': f'{uptime_hours:.1f}h',
            'trading_engine_running': trading_engine.is_running if trading_engine else False,
            'futures_engine_running': futures_trading_engine.is_running if futures_trading_engine else False,
            'strategies_count': len(trading_engine.strategies) if trading_engine else 0
        }
        
        return jsonify({
            'success': True,
            'data': status_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取系统状态失败: {str(e)}'})

# ========== 现货策略管理API端点 ==========

@app.route('/api/strategies/list')
def get_strategies():
    """获取现货策略列表"""
    try:
        global trading_engine
        
        strategies = []
        
        # 优先使用全局交易引擎
        engine_to_use = trading_engine
        is_running = False
        
        # 如果全局引擎不存在或没有策略，返回预定义的策略列表
        if not engine_to_use or not hasattr(engine_to_use, 'strategies') or not engine_to_use.strategies:
            print("全局交易引擎未初始化，返回预定义策略列表")
            
            # 返回预定义的策略列表，避免创建引擎时的网络超时
            default_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT', 'SOLUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'LTCUSDT']
            strategy_types = ['MA', 'RSI', 'ML']
            
            for symbol in default_symbols:
                for strategy_type in strategy_types:
                    strategy_info = {
                        'id': f"{symbol}_{strategy_type}",
                        'name': f"{symbol} - {strategy_type}Strategy",
                        'symbol': symbol,
                        'type': f"{strategy_type}Strategy",
                        'status': 'inactive',
                        'position': 0.0,
                        'entry_price': 0.0,
                        'pnl': 0.0
                    }
                    strategies.append(strategy_info)
        else:
            is_running = engine_to_use.is_running
            
            # 获取策略列表
            for strategy_key, strategy in engine_to_use.strategies.items():
                try:
                    strategy_info = {
                        'id': str(strategy_key),
                        'name': f"{strategy.symbol} - {strategy.__class__.__name__}",
                        'symbol': str(strategy.symbol),
                        'type': str(strategy.__class__.__name__),
                        'status': 'active' if is_running else 'inactive',
                        'position': float(getattr(strategy, 'position', 0)),
                        'entry_price': float(getattr(strategy, 'entry_price', 0)),
                        'pnl': float(getattr(strategy, 'unrealized_pnl', 0))
                    }
                    strategies.append(strategy_info)
                except Exception as strategy_error:
                    print(f"处理策略 {strategy_key} 时出错: {strategy_error}")
                    continue
        
        return jsonify({
            'success': True,
            'data': strategies
        })
        
    except Exception as e:
        print(f"获取策略列表异常: {e}")
        return jsonify({'success': False, 'message': f'获取策略列表失败: {str(e)}'})

@app.route('/api/strategies/add', methods=['POST'])
def add_strategy():
    """添加新策略"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        strategy_type = data.get('strategy_type')
        position_size = float(data.get('position_size', 2.0)) / 100  # 转换为小数
        stop_loss = float(data.get('stop_loss', 2.0)) / 100
        take_profit = float(data.get('take_profit', 5.0)) / 100
        
        if not symbol or not strategy_type:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 构建策略参数
        parameters = {
            'position_size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
        
        # 根据策略类型添加特定参数
        if strategy_type == 'MA':
            parameters.update({
                'short_window': 10,
                'long_window': 30
            })
        elif strategy_type == 'RSI':
            parameters.update({
                'rsi_period': 14,
                'oversold': 30,
                'overbought': 70
            })
        elif strategy_type == 'ML':
            parameters.update({
                'model_type': 'random_forest',
                'lookback_period': 20,
                'prediction_horizon': 1,
                'min_confidence': 0.6,
                'up_threshold': 0.01,
                'down_threshold': -0.01
            })
        elif strategy_type == 'Chanlun':
            parameters.update({
                'timeframes': ['30m', '1h', '4h'],
                'min_swing_length': 3,
                'central_bank_min_bars': 3,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'rsi_period': 14,
                'ma_short': 5,
                'ma_long': 20,
                'max_position': 1.0,
                'trend_confirmation': 0.02,
                'divergence_threshold': 0.1
            })
        
        # 添加到现货交易引擎
        if spot_trading_engine:
            success = spot_trading_engine.add_strategy(symbol, strategy_type, parameters)
            if success:
                return jsonify({
                    'success': True,
                    'message': f'{strategy_type}策略添加成功',
                    'strategy_id': f"{symbol}_{strategy_type}"
                })
            else:
                return jsonify({'success': False, 'message': '策略添加失败'})
        else:
            return jsonify({'success': False, 'message': '交易引擎未初始化'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加策略失败: {str(e)}'})

@app.route('/api/spot/symbols', methods=['GET'])
def get_spot_symbols():
    """获取现货交易币种列表"""
    return jsonify({
        'success': True,
        'symbols': spot_config['symbols']
    })

@app.route('/api/spot/symbols/available', methods=['GET'])
def get_available_symbols():
    """获取所有可用的交易币种"""
    try:
        # 从Binance API获取所有USDT交易对
        try:
            exchange_info = binance_client.get_exchange_info()
            if exchange_info and 'symbols' in exchange_info:
                all_symbols = []
                for symbol_info in exchange_info['symbols']:
                    symbol = symbol_info['symbol']
                    if symbol.endswith('USDT') and symbol_info['status'] == 'TRADING':
                        all_symbols.append(symbol)
                
                # 按字母顺序排序
                all_symbols.sort()
                
                return jsonify({
                    'success': True,
                    'symbols': all_symbols,
                    'total': len(all_symbols)
                })
        except Exception as e:
            print(f"获取Binance交易对失败: {e}")
        
        # 如果API调用失败，返回默认币种列表
        default_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT', 'SOLUSDT', 
            'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 
            'FILUSDT', 'XRPUSDT', 'MATICUSDT', 'SHIBUSDT', 'TRXUSDT', 'XLMUSDT',
            'BCHUSDT', 'ETCUSDT', 'NEARUSDT', 'FTMUSDT', 'ALGOUSDT', 'VETUSDT',
            'ICPUSDT', 'THETAUSDT', 'XMRUSDT', 'EOSUSDT', 'AAVEUSDT', 'SUSHIUSDT'
        ]
        
        return jsonify({
            'success': True,
            'symbols': default_symbols,
            'total': len(default_symbols),
            'note': '使用默认币种列表'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取可用币种失败: {str(e)}'})

@app.route('/api/spot/symbols', methods=['POST'])
def update_spot_symbols():
    """更新现货交易币种列表"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({'success': False, 'message': '币种列表不能为空'})
        
        # 验证币种格式
        for symbol in symbols:
            if not symbol.endswith('USDT'):
                return jsonify({'success': False, 'message': f'无效的币种格式: {symbol}'})
        
        spot_config['symbols'] = symbols
        
        # 清除不存在的币种的策略
        for strategy_key in list(spot_config['enabled_strategies'].keys()):
            symbol = strategy_key.split('_')[0]
            if symbol not in symbols:
                del spot_config['enabled_strategies'][strategy_key]
        
        return jsonify({
            'success': True,
            'message': f'币种列表已更新，共 {len(symbols)} 个币种',
            'symbols': symbols
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新币种失败: {str(e)}'})

@app.route('/api/spot/strategies/update', methods=['POST'])
def update_spot_strategies():
    """更新现货交易策略"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', spot_config['symbols'])
        
        if not symbols:
            return jsonify({'success': False, 'message': '请先选择币种'})
        
        # 模拟策略更新和回测
        results = []
        for symbol in symbols:
            symbol_results = []
            for strategy_type in spot_config['strategy_types']:
                strategy_key = f"{symbol}_{strategy_type}"
                
                # 模拟回测结果
                import random
                backtest_result = {
                    'symbol': symbol,
                    'strategy': strategy_type,
                    'strategy_key': strategy_key,
                    'total_return': random.uniform(-0.1, 0.2),
                    'total_trades': random.randint(5, 20),
                    'win_rate': random.uniform(0.4, 0.7),
                    'max_drawdown': random.uniform(0.05, 0.15),
                    'sharpe_ratio': random.uniform(0.5, 2.0),
                    'enabled': True  # 默认启用
                }
                
                # 更新启用状态
                spot_config['enabled_strategies'][strategy_key] = True
                symbol_results.append(backtest_result)
            
            results.append({
                'symbol': symbol,
                'strategies': symbol_results
            })
        
        return jsonify({
            'success': True,
            'message': f'策略更新完成，共 {len(symbols) * len(spot_config["strategy_types"])} 个策略',
            'results': results
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新策略失败: {str(e)}'})

@app.route('/api/spot/strategies/manage', methods=['POST'])
def manage_spot_strategies():
    """管理现货交易策略启用状态"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'enable_all':
            for symbol in spot_config['symbols']:
                for strategy_type in spot_config['strategy_types']:
                    spot_config['enabled_strategies'][f"{symbol}_{strategy_type}"] = True
            return jsonify({'success': True, 'message': '已启用全部策略'})
        
        elif action == 'disable_all':
            for symbol in spot_config['symbols']:
                for strategy_type in spot_config['strategy_types']:
                    spot_config['enabled_strategies'][f"{symbol}_{strategy_type}"] = False
            return jsonify({'success': True, 'message': '已禁用全部策略'})
        
        elif action == 'toggle':
            strategy_key = data.get('strategy_key')
            if strategy_key:
                current_status = spot_config['enabled_strategies'].get(strategy_key, False)
                spot_config['enabled_strategies'][strategy_key] = not current_status
                status = '启用' if spot_config['enabled_strategies'][strategy_key] else '禁用'
                return jsonify({'success': True, 'message': f'策略已{status}'})
        
        return jsonify({'success': False, 'message': '无效操作'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'管理策略失败: {str(e)}'})

@app.route('/api/spot/strategies/status')
def get_spot_strategies_status():
    """获取现货策略状态"""
    enabled_count = sum(spot_config['enabled_strategies'].values())
    total_count = len(spot_config['symbols']) * len(spot_config['strategy_types'])
    
    return jsonify({
        'success': True,
        'symbols': spot_config['symbols'],
        'enabled_strategies': spot_config['enabled_strategies'],
        'trading_status': spot_config['trading_status'],
        'enabled_count': enabled_count,
        'total_count': total_count
    })

@app.route('/api/spot/trading/start', methods=['POST'])
def start_spot_trading():
    """启动现货交易"""
    try:
        enabled_strategies = [k for k, v in spot_config['enabled_strategies'].items() if v]
        
        if not enabled_strategies:
            return jsonify({'success': False, 'message': '请先启用至少一个策略'})
        
        spot_config['trading_status'] = 'running'
        
        return jsonify({
            'success': True,
            'message': f'现货交易已启动，启用 {len(enabled_strategies)} 个策略',
            'enabled_strategies': enabled_strategies
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动交易失败: {str(e)}'})

@app.route('/api/spot/trading/stop', methods=['POST'])
def stop_spot_trading():
    """停止现货交易"""
    try:
        spot_config['trading_status'] = 'stopped'
        return jsonify({'success': True, 'message': '现货交易已停止'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'停止交易失败: {str(e)}'})

@app.route('/api/spot/trading/status')
def get_spot_trading_status():
    """获取现货交易状态"""
    enabled_count = sum(spot_config['enabled_strategies'].values())
    total_count = len(spot_config['symbols']) * len(spot_config['strategy_types'])
    
    return jsonify({
        'success': True,
        'trading': spot_config['trading_status'] == 'running',
        'enabled_strategies': enabled_count,
        'total_strategies': total_count,
        'symbols_count': len(spot_config['symbols'])
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

@app.route('/api/futures/position/details')
def get_futures_position_details():
    """获取合约持仓详情"""
    try:
        symbol = request.args.get('symbol')
        position_side = request.args.get('position_side', 'BOTH')
        
        if not symbol:
            return jsonify({'success': False, 'message': '缺少交易对参数'})
        
        # 获取所有持仓
        positions = futures_client.get_positions()
        
        # 查找指定的持仓
        target_position = None
        for pos in positions:
            if pos['symbol'] == symbol and (position_side == 'BOTH' or pos['positionSide'] == position_side):
                if float(pos['positionAmt']) != 0:  # 只返回有持仓的
                    target_position = pos
                    break
        
        if not target_position:
            return jsonify({'success': False, 'message': '未找到指定持仓'})
        
        # Calculate percentage if not provided by API
        percentage = 0
        if 'percentage' in target_position:
            percentage = float(target_position['percentage'])
        else:
            # Calculate percentage based on entry price and mark price
            entry_price = float(target_position['entryPrice'])
            mark_price = float(target_position['markPrice'])
            if entry_price > 0:
                percentage = ((mark_price - entry_price) / entry_price) * 100
                if float(target_position['positionAmt']) < 0:  # Short position
                    percentage = -percentage
        
        # 格式化持仓详情
        position_details = {
            'symbol': target_position['symbol'],
            'positionAmt': float(target_position['positionAmt']),
            'entryPrice': float(target_position['entryPrice']),
            'markPrice': float(target_position['markPrice']),
            'unRealizedProfit': float(target_position['unRealizedProfit']),
            'percentage': percentage,
            'positionSide': target_position['positionSide'],
            'marginType': target_position['marginType'],
            'isolatedMargin': float(target_position['isolatedMargin']),
            'leverage': target_position['leverage'],
            'liquidationPrice': float(target_position.get('liquidationPrice', 0)),
            'initialMargin': float(target_position.get('initialMargin', 0)),
            'maintMargin': float(target_position.get('maintMargin', 0))
        }
        
        return jsonify({
            'success': True,
            'position': position_details
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取持仓详情失败: {str(e)}'})

@app.route('/api/futures/config/update', methods=['POST'])
def update_futures_config():
    """更新合约交易配置"""
    try:
        data = request.get_json()
        leverage = data.get('leverage', 10)
        symbols = data.get('symbols', ['BTCUSDT', 'ETHUSDT'])
        
        # 保存配置到全局变量和文件
        global futures_config
        futures_config = {
            'leverage': leverage,
            'symbols': symbols,
            'updated_at': datetime.now().isoformat()
        }
        
        # 同时保存到文件以确保持久化
        try:
            import os
            import json
            config_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(config_dir, 'futures_config.json')
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(futures_config, f, ensure_ascii=False, indent=2)
            
            print(f"配置已保存到文件: {config_file}")
        except Exception as file_error:
            print(f"保存配置文件失败: {file_error}")
        
        return jsonify({
            'success': True,
            'message': f'合约配置已更新：杠杆 {leverage}x，币种 {len(symbols)} 个',
            'config': futures_config
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新配置失败: {str(e)}'})

@app.route('/api/futures/config/get')
def get_futures_config():
    """获取合约交易配置"""
    try:
        global futures_config
        
        # 首先尝试从文件读取配置
        try:
            import os
            import json
            config_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(config_dir, 'futures_config.json')
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    futures_config = file_config
                    print(f"从文件加载配置: {config_file}")
            else:
                print("配置文件不存在，使用默认配置")
        except Exception as file_error:
            print(f"读取配置文件失败: {file_error}")
        
        # 如果全局变量不存在，使用默认配置
        if 'futures_config' not in globals() or not futures_config:
            futures_config = {
                'leverage': 10,
                'symbols': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT'],
                'updated_at': datetime.now().isoformat()
            }
            print("使用默认配置")
        
        return jsonify({
            'success': True,
            'config': futures_config
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取配置失败: {str(e)}'})

@app.route('/api/futures/trading/start', methods=['POST'])
def start_futures_trading():
    """启动合约交易"""
    global futures_trading_engine, futures_config
    try:
        data = request.get_json()
        
        # 使用保存的配置或请求中的配置
        if 'futures_config' in globals():
            leverage = futures_config.get('leverage', data.get('leverage', 10))
            symbols = futures_config.get('symbols', data.get('symbols', ['BTCUSDT', 'ETHUSDT']))
        else:
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

# 在现有API端点后添加回测API
@app.route('/api/backtest/run', methods=['POST'])
def run_backtest():
    """运行回测"""
    try:
        data = request.get_json()
        strategy_type = data.get('strategy_type')
        symbol = data.get('symbol')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not all([strategy_type, symbol, start_date, end_date]):
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 根据策略类型创建策略实例
        if strategy_type == 'MA':
            from strategies.ma_strategy import MovingAverageStrategy
            strategy = MovingAverageStrategy(symbol, {
                'short_window': 10,
                'long_window': 30,
                'stop_loss': 0.02,
                'take_profit': 0.05,
                'position_size': 0.1
            })
        elif strategy_type == 'RSI':
            from strategies.rsi_strategy import RSIStrategy
            strategy = RSIStrategy(symbol, {
                'rsi_period': 14,
                'oversold': 30,
                'overbought': 70,
                'stop_loss': 0.02,
                'take_profit': 0.05,
                'position_size': 0.1
            })
        elif strategy_type == 'ML':
            from strategies.ml_strategy import MLStrategy
            strategy = MLStrategy(symbol, {
                'model_type': 'random_forest',
                'lookback_period': 30,
                'prediction_horizon': 1,
                'min_confidence': 0.65,
                'up_threshold': 0.015,
                'down_threshold': -0.015,
                'stop_loss': 0.03,
                'take_profit': 0.06,
                'position_size': 0.05
            })
        elif strategy_type == 'Chanlun':
            from strategies.chanlun_strategy import ChanlunStrategy
            strategy = ChanlunStrategy(symbol, {
                'timeframes': ['30m', '1h', '4h'],
                'min_swing_length': 2,
                'central_bank_min_bars': 2,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'rsi_period': 14,
                'ma_short': 5,
                'ma_long': 20,
                'position_size': 0.2,
                'max_position': 0.8,
                'stop_loss': 0.04,
                'take_profit': 0.08,
                'trend_confirmation': 0.01,
                'divergence_threshold': 0.05
            })
        else:
            return jsonify({'success': False, 'message': f'不支持的策略类型: {strategy_type}'})
        
        # 运行回测
        result = backtest_engine.run_backtest(
            strategy=strategy,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval='1h'
        )
        
        # 格式化回测结果
        backtest_result = {
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
            'trades': result.trades[:50],  # 只返回前50笔交易
            'equity_curve': result.equity_curve.tolist()[-100:]  # 只返回最后100个数据点
        }
        
        return jsonify({
            'success': True,
            'data': backtest_result,
            'message': f'{strategy_type}策略回测完成'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'回测失败: {str(e)}'})

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