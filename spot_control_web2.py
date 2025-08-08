#!/usr/bin/env python3
"""
现货交易控制Web界面
"""

from flask import Flask, render_template, jsonify, request
import json
import os

app = Flask(__name__)

# 配置
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT', 'SOLUSDT', 'DOTUSDT', 'AVAXUSDT', 'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 'FILUSDT']
STRATEGIES = ['MA', 'RSI', 'ML', 'Chanlun']

# 全局状态
selected_symbols = []
enabled_strategies = {}
trading_status = 'stopped'

@app.route('/')
def index():
    """主页面"""
    return render_template('spot_control.html', 
                         symbols=SYMBOLS,
                         strategies=STRATEGIES,
                         selected_symbols=selected_symbols,
                         enabled_strategies=enabled_strategies,
                         trading_status=trading_status)

@app.route('/api/select_symbols', methods=['POST'])
def api_select_symbols():
    """选择币种API"""
    global selected_symbols
    data = request.get_json()
    selected_symbols = data.get('symbols', [])
    return jsonify({'success': True, 'message': f'已选择 {len(selected_symbols)} 个币种'})

@app.route('/api/update_strategies', methods=['POST'])
def api_update_strategies():
    """更新策略API"""
    global enabled_strategies
    
    if not selected_symbols:
        return jsonify({'success': False, 'message': '请先选择币种'})
    
    # 模拟策略更新和回测
    results = []
    for symbol in selected_symbols:
        symbol_results = []
        for strategy in STRATEGIES:
            strategy_key = f"{symbol}_{strategy}"
            
            # 模拟回测结果
            import random
            backtest_result = {
                'symbol': symbol,
                'strategy': strategy,
                'total_return': random.uniform(-0.1, 0.2),
                'total_trades': random.randint(5, 20),
                'win_rate': random.uniform(0.4, 0.7),
                'enabled': True
            }
            
            enabled_strategies[strategy_key] = True
            symbol_results.append(backtest_result)
        
        results.append({
            'symbol': symbol,
            'strategies': symbol_results
        })
    
    return jsonify({
        'success': True, 
        'message': f'策略更新完成，共 {len(selected_symbols) * len(STRATEGIES)} 个策略',
        'results': results
    })

@app.route('/api/manage_strategies', methods=['POST'])
def api_manage_strategies():
    """管理策略API"""
    global enabled_strategies
    data = request.get_json()
    action = data.get('action')
    
    if action == 'enable_all':
        for symbol in selected_symbols:
            for strategy in STRATEGIES:
                enabled_strategies[f"{symbol}_{strategy}"] = True
        return jsonify({'success': True, 'message': '已启用全部策略'})
    
    elif action == 'disable_all':
        for symbol in selected_symbols:
            for strategy in STRATEGIES:
                enabled_strategies[f"{symbol}_{strategy}"] = False
        return jsonify({'success': True, 'message': '已禁用全部策略'})
    
    elif action == 'toggle':
        strategy_key = data.get('strategy_key')
        if strategy_key:
            enabled_strategies[strategy_key] = not enabled_strategies.get(strategy_key, False)
            status = '启用' if enabled_strategies[strategy_key] else '禁用'
            return jsonify({'success': True, 'message': f'策略已{status}'})
    
    return jsonify({'success': False, 'message': '无效操作'})

@app.route('/api/start_trading', methods=['POST'])
def api_start_trading():
    """启动交易API"""
    global trading_status
    
    enabled = [k for k, v in enabled_strategies.items() if v]
    if not enabled:
        return jsonify({'success': False, 'message': '请先启用至少一个策略'})
    
    trading_status = 'running'
    return jsonify({
        'success': True, 
        'message': f'现货交易已启动，启用 {len(enabled)} 个策略',
        'enabled_strategies': enabled
    })

@app.route('/api/stop_trading', methods=['POST'])
def api_stop_trading():
    """停止交易API"""
    global trading_status
    trading_status = 'stopped'
    return jsonify({'success': True, 'message': '现货交易已停止'})

@app.route('/api/get_status')
def api_get_status():
    """获取状态API"""
    enabled_count = sum(enabled_strategies.values())
    total_count = len(selected_symbols) * len(STRATEGIES)
    
    return jsonify({
        'selected_symbols': selected_symbols,
        'enabled_strategies': enabled_strategies,
        'trading_status': trading_status,
        'enabled_count': enabled_count,
        'total_count': total_count
    })

if __name__ == '__main__':
    # 创建模板目录
    os.makedirs('templates', exist_ok=True)
    
    # 创建HTML模板
    html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>现货交易控制系统</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .card { margin-bottom: 20px; }
        .strategy-item { margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .enabled { background-color: #d4edda; border-color: #c3e6cb; }
        .disabled { background-color: #f8d7da; border-color: #f5c6cb; }
        .status-running { color: #28a745; }
        .status-stopped { color: #dc3545; }
        .backtest-result { font-size: 0.9em; color: #666; }
        .strategy-toggle { cursor: pointer; }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1 class="text-center mb-4">
            <i class="fas fa-chart-line"></i> 现货交易控制系统
        </h1>
        
        <!-- 状态栏 -->
        <div class="row mb-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-info-circle"></i> 系统状态</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3">
                                <strong>交易状态:</strong> 
                                <span id="trading-status" class="status-{{ trading_status }}">
                                    <i class="fas fa-{{ 'play' if trading_status == 'running' else 'stop' }}"></i>
                                    {{ '运行中' if trading_status == 'running' else '已停止' }}
                                </span>
                            </div>
                            <div class="col-md-3">
                                <strong>选择币种:</strong> <span id="selected-count">{{ selected_symbols|length }}</span> 个
                            </div>
                            <div class="col-md-3">
                                <strong>启用策略:</strong> <span id="enabled-count">{{ enabled_strategies.values()|sum }}</span> 个
                            </div>
                            <div class="col-md-3">
                                <strong>总策略:</strong> <span id="total-count">{{ (selected_symbols|length) * (strategies|length) }}</span> 个
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 主要功能 -->
        <div class="row">
            <!-- 左侧：币种选择 -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-coins"></i> 选择交易币种</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            {% for symbol in symbols %}
                            <div class="col-md-4 mb-2">
                                <div class="form-check">
                                    <input class="form-check-input symbol-checkbox" type="checkbox" 
                                           value="{{ symbol }}" id="symbol-{{ symbol }}"
                                           {% if symbol in selected_symbols %}checked{% endif %}>
                                    <label class="form-check-label" for="symbol-{{ symbol }}">
                                        {{ symbol }}
                                    </label>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                        <div class="mt-3">
                            <button class="btn btn-primary" onclick="selectAllSymbols()">
                                <i class="fas fa-check-double"></i> 全选
                            </button>
                            <button class="btn btn-secondary" onclick="clearAllSymbols()">
                                <i class="fas fa-times"></i> 清空
                            </button>
                            <button class="btn btn-success" onclick="saveSymbolSelection()">
                                <i class="fas fa-save"></i> 保存选择
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 右侧：策略管理 -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-cogs"></i> 策略管理</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <button class="btn btn-primary" onclick="updateStrategies()">
                                <i class="fas fa-sync"></i> 更新策略并回测
                            </button>
                        </div>
                        <div class="mb-3">
                            <button class="btn btn-success" onclick="enableAllStrategies()">
                                <i class="fas fa-check"></i> 启用全部
                            </button>
                            <button class="btn btn-danger" onclick="disableAllStrategies()">
                                <i class="fas fa-times"></i> 禁用全部
                            </button>
                        </div>
                        <div id="strategies-container">
                            <!-- 策略列表将在这里动态生成 -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 交易控制 -->
        <div class="row mt-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-play-circle"></i> 交易控制</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <button class="btn btn-success btn-lg w-100" onclick="startTrading()">
                                    <i class="fas fa-play"></i> 启动交易
                                </button>
                            </div>
                            <div class="col-md-4">
                                <button class="btn btn-danger btn-lg w-100" onclick="stopTrading()">
                                    <i class="fas fa-stop"></i> 停止交易
                                </button>
                            </div>
                            <div class="col-md-4">
                                <button class="btn btn-warning btn-lg w-100" onclick="restartTrading()">
                                    <i class="fas fa-redo"></i> 重启交易
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 消息提示 -->
        <div id="message-container" class="position-fixed top-0 end-0 p-3" style="z-index: 1050;"></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // 全局变量
        let selectedSymbols = {{ selected_symbols|tojson }};
        let enabledStrategies = {{ enabled_strategies|tojson }};
        let tradingStatus = '{{ trading_status }}';
        
        // 显示消息
        function showMessage(message, type = 'info') {
            const container = document.getElementById('message-container');
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} alert-dismissible fade show`;
            alert.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            container.appendChild(alert);
            
            // 自动消失
            setTimeout(() => {
                alert.remove();
            }, 5000);
        }
        
        // 选择币种
        function selectAllSymbols() {
            document.querySelectorAll('.symbol-checkbox').forEach(checkbox => {
                checkbox.checked = true;
            });
        }
        
        function clearAllSymbols() {
            document.querySelectorAll('.symbol-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
        }
        
        function saveSymbolSelection() {
            const selected = Array.from(document.querySelectorAll('.symbol-checkbox:checked'))
                                .map(checkbox => checkbox.value);
            
            fetch('/api/select_symbols', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({symbols: selected})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    selectedSymbols = selected;
                    updateStatus();
                    showMessage(data.message, 'success');
                } else {
                    showMessage(data.message, 'danger');
                }
            })
            .catch(error => {
                showMessage('保存失败: ' + error.message, 'danger');
            });
        }
        
        // 策略管理
        function updateStrategies() {
            if (selectedSymbols.length === 0) {
                showMessage('请先选择币种', 'warning');
                return;
            }
            
            fetch('/api/update_strategies', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    enabledStrategies = {};
                    data.results.forEach(symbolResult => {
                        symbolResult.strategies.forEach(strategy => {
                            const key = `${strategy.symbol}_${strategy.strategy}`;
                            enabledStrategies[key] = strategy.enabled;
                        });
                    });
                    updateStrategiesDisplay();
                    updateStatus();
                    showMessage(data.message, 'success');
                } else {
                    showMessage(data.message, 'danger');
                }
            })
            .catch(error => {
                showMessage('更新失败: ' + error.message, 'danger');
            });
        }
        
        function enableAllStrategies() {
            fetch('/api/manage_strategies', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'enable_all'})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    selectedSymbols.forEach(symbol => {
                        ['MA', 'RSI', 'ML', 'Chanlun'].forEach(strategy => {
                            enabledStrategies[`${symbol}_${strategy}`] = true;
                        });
                    });
                    updateStrategiesDisplay();
                    updateStatus();
                    showMessage(data.message, 'success');
                } else {
                    showMessage(data.message, 'danger');
                }
            });
        }
        
        function disableAllStrategies() {
            fetch('/api/manage_strategies', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'disable_all'})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    selectedSymbols.forEach(symbol => {
                        ['MA', 'RSI', 'ML', 'Chanlun'].forEach(strategy => {
                            enabledStrategies[`${symbol}_${strategy}`] = false;
                        });
                    });
                    updateStrategiesDisplay();
                    updateStatus();
                    showMessage(data.message, 'success');
                } else {
                    showMessage(data.message, 'danger');
                }
            });
        }
        
        function toggleStrategy(strategyKey) {
            fetch('/api/manage_strategies', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'toggle', strategy_key: strategyKey})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    enabledStrategies[strategyKey] = !enabledStrategies[strategyKey];
                    updateStrategiesDisplay();
                    updateStatus();
                    showMessage(data.message, 'success');
                } else {
                    showMessage(data.message, 'danger');
                }
            });
        }
        
        function updateStrategiesDisplay() {
            const container = document.getElementById('strategies-container');
            container.innerHTML = '';
            
            selectedSymbols.forEach(symbol => {
                const symbolDiv = document.createElement('div');
                symbolDiv.className = 'mb-3';
                symbolDiv.innerHTML = `<h6>${symbol}</h6>`;
                
                ['MA', 'RSI', 'ML', 'Chanlun'].forEach(strategy => {
                    const key = `${symbol}_${strategy}`;
                    const enabled = enabledStrategies[key] || false;
                    const strategyDiv = document.createElement('div');
                    strategyDiv.className = `strategy-item ${enabled ? 'enabled' : 'disabled'} strategy-toggle`;
                    strategyDiv.onclick = () => toggleStrategy(key);
                    strategyDiv.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <span>${strategy}</span>
                            <span class="badge ${enabled ? 'bg-success' : 'bg-secondary'}">
                                ${enabled ? '启用' : '禁用'}
                            </span>
                        </div>
                    `;
                    symbolDiv.appendChild(strategyDiv);
                });
                
                container.appendChild(symbolDiv);
            });
        }
        
        // 交易控制
        function startTrading() {
            fetch('/api/start_trading', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    tradingStatus = 'running';
                    updateStatus();
                    showMessage(data.message, 'success');
                } else {
                    showMessage(data.message, 'danger');
                }
            });
        }
        
        function stopTrading() {
            fetch('/api/stop_trading', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'}
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    tradingStatus = 'stopped';
                    updateStatus();
                    showMessage(data.message, 'success');
                } else {
                    showMessage(data.message, 'danger');
                }
            });
        }
        
        function restartTrading() {
            stopTrading();
            setTimeout(() => {
                startTrading();
            }, 1000);
        }
        
        // 更新状态显示
        function updateStatus() {
            const enabledCount = Object.values(enabledStrategies).filter(v => v).length;
            const totalCount = selectedSymbols.length * 4;
            
            document.getElementById('selected-count').textContent = selectedSymbols.length;
            document.getElementById('enabled-count').textContent = enabledCount;
            document.getElementById('total-count').textContent = totalCount;
            
            const statusElement = document.getElementById('trading-status');
            statusElement.className = `status-${tradingStatus}`;
            statusElement.innerHTML = `
                <i class="fas fa-${tradingStatus === 'running' ? 'play' : 'stop'}"></i>
                ${tradingStatus === 'running' ? '运行中' : '已停止'}
            `;
        }
        
        // 页面加载时初始化
        document.addEventListener('DOMContentLoaded', function() {
            updateStrategiesDisplay();
            updateStatus();
            
            // 定期更新状态
            setInterval(() => {
                fetch('/api/get_status')
                .then(response => response.json())
                .then(data => {
                    selectedSymbols = data.selected_symbols;
                    enabledStrategies = data.enabled_strategies;
                    tradingStatus = data.trading_status;
                    updateStatus();
                    updateStrategiesDisplay();
                });
            }, 10000);
        });
    </script>
</body>
</html>
"""
    
    # 写入HTML模板文件
    with open('templates/spot_control.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("🚀 现货交易控制Web界面已启动")
    print("📄 访问地址: http://127.0.0.1:5001")
    print("📄 主系统地址: http://127.0.0.1:5000")
    
    app.run(debug=True, host='127.0.0.1', port=5001)