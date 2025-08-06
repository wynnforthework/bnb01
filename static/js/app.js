// 全局变量
let socket;
let currentSymbol = 'BTCUSDT';

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    loadInitialData();
    bindEvents();
    checkTradingStatus();
});

// 初始化WebSocket连接
function initializeSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('WebSocket连接成功');
    });
    
    socket.on('portfolio_update', function(data) {
        updatePortfolioDisplay(data);
    });
    
    socket.on('trades_update', function(data) {
        updateTradesDisplay(data);
    });
    
    socket.on('disconnect', function() {
        console.log('WebSocket连接断开');
    });
}

// 绑定事件
function bindEvents() {
    // 启动交易按钮
    document.getElementById('start-trading').addEventListener('click', function() {
        startTrading();
    });
    
    // 停止交易按钮
    document.getElementById('stop-trading').addEventListener('click', function() {
        stopTrading();
    });
    
    // 刷新数据按钮
    document.getElementById('refresh-data').addEventListener('click', function() {
        loadInitialData();
    });
    
    // 交易对选择
    document.getElementById('symbol-select').addEventListener('change', function() {
        currentSymbol = this.value;
        loadMarketData(currentSymbol);
    });
    
    // 策略管理面板切换
    document.getElementById('show-strategies').addEventListener('click', function() {
        showStrategyPanel('strategies');
        loadStrategies();
    });
    
    document.getElementById('show-backtest').addEventListener('click', function() {
        showStrategyPanel('backtest');
    });
    
    document.getElementById('show-ml').addEventListener('click', function() {
        showStrategyPanel('ml');
    });
    
    // 技术指标和订单簿按钮
    document.getElementById('show-indicators').addEventListener('click', function() {
        loadTechnicalIndicators(currentSymbol);
    });
    
    document.getElementById('show-orderbook').addEventListener('click', function() {
        loadOrderbook(currentSymbol);
    });
    
    // 数据收集表单
    document.getElementById('data-collection-form').addEventListener('submit', function(e) {
        e.preventDefault();
        collectHistoricalData();
    });
    
    // 回测表单
    document.getElementById('backtest-form').addEventListener('submit', function(e) {
        e.preventDefault();
        runBacktest();
    });
    
    // 策略比较按钮
    document.getElementById('compare-strategies').addEventListener('click', function() {
        compareStrategies();
    });
    
    // 机器学习训练表单
    document.getElementById('ml-train-form').addEventListener('submit', function(e) {
        e.preventDefault();
        trainMLModel();
    });
    
    // 添加策略按钮
    document.getElementById('confirm-add-strategy').addEventListener('click', function() {
        addNewStrategy();
    });
}

// 加载初始数据
function loadInitialData() {
    loadAccountData();
    loadPortfolioData();
    loadTradesData();
    loadMarketData(currentSymbol);
}

// 加载账户数据
async function loadAccountData() {
    try {
        const response = await fetch('/api/account');
        const data = await response.json();
        
        if (data.success) {
            displayAccountBalances(data.balances);
        } else {
            showError('加载账户数据失败: ' + data.message);
        }
    } catch (error) {
        showError('加载账户数据失败: ' + error.message);
    }
}

// 显示账户余额
function displayAccountBalances(balances) {
    const container = document.getElementById('account-balances');
    
    if (balances.length === 0) {
        container.innerHTML = '<p class="text-muted">暂无余额数据</p>';
        return;
    }
    
    // 过滤并排序余额，只显示重要的资产
    const importantAssets = ['USDT', 'BTC', 'ETH', 'BNB', 'ADA'];
    const filteredBalances = balances
        .filter(balance => balance.total > 0.001) // 过滤掉极小余额
        .sort((a, b) => {
            // 重要资产优先显示
            const aIndex = importantAssets.indexOf(a.asset);
            const bIndex = importantAssets.indexOf(b.asset);
            
            if (aIndex !== -1 && bIndex !== -1) {
                return aIndex - bIndex;
            } else if (aIndex !== -1) {
                return -1;
            } else if (bIndex !== -1) {
                return 1;
            } else {
                return b.total - a.total; // 按余额大小排序
            }
        })
        .slice(0, 8); // 最多显示8个资产
    
    let html = '';
    filteredBalances.forEach(balance => {
        const displayAmount = balance.total > 1 ? balance.total.toFixed(4) : balance.total.toFixed(8);
        html += `
            <div class="balance-item">
                <span class="balance-asset">${balance.asset}</span>
                <span class="balance-amount">${displayAmount}</span>
            </div>
        `;
    });
    
    // 如果有更多资产，显示提示
    if (balances.length > filteredBalances.length) {
        html += `
            <div class="balance-item text-muted">
                <small>还有 ${balances.length - filteredBalances.length} 个其他资产...</small>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// 加载投资组合数据
async function loadPortfolioData() {
    try {
        const response = await fetch('/api/portfolio');
        const data = await response.json();
        
        if (data.success) {
            updatePortfolioDisplay(data.data);
        } else {
            showError('加载投资组合失败: ' + data.message);
        }
    } catch (error) {
        showError('加载投资组合失败: ' + error.message);
    }
}

// 更新投资组合显示
function updatePortfolioDisplay(data) {
    // 更新投资组合摘要
    const summaryContainer = document.getElementById('portfolio-summary');
    const totalValue = data.total_value || 0;
    const cashBalance = data.cash_balance || 0;
    const totalAssets = totalValue + cashBalance;
    
    summaryContainer.innerHTML = `
        <div class="row">
            <div class="col-md-4">
                <div class="portfolio-metric">
                    <h6>总资产</h6>
                    <div class="value">$${totalAssets.toFixed(2)}</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="portfolio-metric">
                    <h6>持仓市值</h6>
                    <div class="value">$${totalValue.toFixed(2)}</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="portfolio-metric">
                    <h6>现金余额</h6>
                    <div class="value">$${cashBalance.toFixed(2)}</div>
                </div>
            </div>
        </div>
    `;
    
    // 更新持仓表格
    updatePositionsTable(data.positions || []);
}

// 更新持仓表格
function updatePositionsTable(positions) {
    const tbody = document.querySelector('#positions-table tbody');
    
    if (positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无持仓</td></tr>';
        return;
    }
    
    let html = '';
    positions.forEach(position => {
        const pnlClass = position.unrealized_pnl >= 0 ? 'profit-positive' : 'profit-negative';
        const pnlSign = position.unrealized_pnl >= 0 ? '+' : '';
        
        html += `
            <tr>
                <td>${position.symbol}</td>
                <td>${position.quantity.toFixed(8)}</td>
                <td>$${position.avg_price.toFixed(4)}</td>
                <td>$${position.current_price.toFixed(4)}</td>
                <td>$${position.market_value.toFixed(2)}</td>
                <td class="${pnlClass}">${pnlSign}$${position.unrealized_pnl.toFixed(2)}</td>
                <td class="${pnlClass}">${pnlSign}${position.pnl_percent.toFixed(2)}%</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 加载交易数据
async function loadTradesData() {
    try {
        const response = await fetch('/api/trades');
        const data = await response.json();
        
        if (data.success) {
            updateTradesDisplay(data.trades);
        } else {
            showError('加载交易数据失败: ' + data.message);
        }
    } catch (error) {
        showError('加载交易数据失败: ' + error.message);
    }
}

// 更新交易显示
function updateTradesDisplay(trades) {
    const tbody = document.querySelector('#trades-table tbody');
    
    if (trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无交易记录</td></tr>';
        return;
    }
    
    let html = '';
    trades.forEach(trade => {
        const sideClass = trade.side === 'BUY' ? 'text-success' : 'text-danger';
        const pnlClass = trade.profit_loss >= 0 ? 'profit-positive' : 'profit-negative';
        const pnlSign = trade.profit_loss >= 0 ? '+' : '';
        const timestamp = new Date(trade.timestamp).toLocaleString('zh-CN');
        
        html += `
            <tr>
                <td>${timestamp}</td>
                <td>${trade.symbol}</td>
                <td class="${sideClass}">${trade.side}</td>
                <td>${trade.quantity.toFixed(8)}</td>
                <td>$${trade.price.toFixed(4)}</td>
                <td>${trade.strategy || '-'}</td>
                <td class="${pnlClass}">${pnlSign}$${trade.profit_loss.toFixed(2)}</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 加载市场数据
async function loadMarketData(symbol) {
    try {
        const response = await fetch(`/api/market/${symbol}`);
        const data = await response.json();
        
        if (data.success) {
            displayPriceChart(data.data, symbol);
        } else {
            showError('加载市场数据失败: ' + data.message);
        }
    } catch (error) {
        showError('加载市场数据失败: ' + error.message);
    }
}

// 显示价格图表
function displayPriceChart(data, symbol) {
    const timestamps = data.map(item => new Date(item.timestamp));
    const prices = data.map(item => item.close);
    const volumes = data.map(item => item.volume);
    
    const trace1 = {
        x: timestamps,
        y: prices,
        type: 'scatter',
        mode: 'lines',
        name: '价格',
        line: {
            color: '#007bff',
            width: 2
        }
    };
    
    const trace2 = {
        x: timestamps,
        y: volumes,
        type: 'bar',
        name: '成交量',
        yaxis: 'y2',
        opacity: 0.3,
        marker: {
            color: '#28a745'
        }
    };
    
    const layout = {
        title: `${symbol} 价格走势`,
        xaxis: {
            title: '时间',
            type: 'date'
        },
        yaxis: {
            title: '价格 (USDT)',
            side: 'left'
        },
        yaxis2: {
            title: '成交量',
            side: 'right',
            overlaying: 'y'
        },
        showlegend: true,
        margin: {
            l: 50,
            r: 50,
            t: 50,
            b: 50
        }
    };
    
    Plotly.newPlot('price-chart', [trace1, trace2], layout, {responsive: true});
}

// 启动交易
async function startTrading() {
    try {
        const response = await fetch('/api/trading/start', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            updateTradingStatus(true);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('启动交易失败: ' + error.message);
    }
}

// 停止交易
async function stopTrading() {
    try {
        const response = await fetch('/api/trading/stop', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            updateTradingStatus(false);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('停止交易失败: ' + error.message);
    }
}

// 检查交易状态
async function checkTradingStatus() {
    try {
        const response = await fetch('/api/trading/status');
        const data = await response.json();
        
        if (data.success) {
            updateTradingStatus(data.is_running);
        }
    } catch (error) {
        console.error('检查交易状态失败:', error);
    }
}

// 更新交易状态显示
function updateTradingStatus(isRunning) {
    const statusElement = document.getElementById('trading-status');
    const startButton = document.getElementById('start-trading');
    const stopButton = document.getElementById('stop-trading');
    
    if (isRunning) {
        statusElement.innerHTML = '<i class="fas fa-circle text-success"></i> 运行中';
        statusElement.className = 'nav-link status-running';
        startButton.disabled = true;
        stopButton.disabled = false;
    } else {
        statusElement.innerHTML = '<i class="fas fa-circle text-danger"></i> 未运行';
        statusElement.className = 'nav-link status-stopped';
        startButton.disabled = false;
        stopButton.disabled = true;
    }
}

// 显示成功消息
function showSuccess(message) {
    // 这里可以使用更好的通知组件，比如 toastr
    alert('成功: ' + message);
}

// 显示错误消息
function showError(message) {
    // 这里可以使用更好的通知组件，比如 toastr
    alert('错误: ' + message);
}

// 定期刷新数据
setInterval(() => {
    if (document.visibilityState === 'visible') {
        loadAccountData();
        checkTradingStatus();
    }
}, 30000); // 每30秒刷新一次
// 
新增功能函数

// 策略面板切换
function showStrategyPanel(panelName) {
    // 隐藏所有面板
    document.querySelectorAll('.strategy-panel').forEach(panel => {
        panel.style.display = 'none';
    });
    
    // 显示选中的面板
    document.getElementById(`${panelName}-panel`).style.display = 'block';
    
    // 更新按钮状态
    document.querySelectorAll('.btn-group .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`show-${panelName}`).classList.add('active');
}

// 加载策略列表
async function loadStrategies() {
    try {
        const response = await fetch('/api/strategies/list');
        const data = await response.json();
        
        if (data.success) {
            displayStrategies(data.strategies);
        } else {
            showError('加载策略失败: ' + data.message);
        }
    } catch (error) {
        showError('加载策略失败: ' + error.message);
    }
}

// 显示策略列表
function displayStrategies(strategies) {
    const tbody = document.querySelector('#strategies-table tbody');
    
    if (strategies.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">暂无策略数据</td></tr>';
        return;
    }
    
    let html = '';
    strategies.forEach(strategy => {
        const statusClass = strategy.position !== 0 ? 'text-success' : 'text-muted';
        const statusText = strategy.position !== 0 ? '持仓中' : '空仓';
        
        html += `
            <tr>
                <td>${strategy.name}</td>
                <td>${strategy.symbol}</td>
                <td>${strategy.type}</td>
                <td>${strategy.position.toFixed(6)}</td>
                <td>$${strategy.entry_price.toFixed(4)}</td>
                <td class="${statusClass}">${statusText}</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 加载风险指标
async function loadRiskMetrics() {
    try {
        const response = await fetch('/api/risk/portfolio');
        const data = await response.json();
        
        if (data.success) {
            displayRiskMetrics(data.data);
        }
    } catch (error) {
        console.error('加载风险指标失败:', error);
    }
}

// 显示风险指标
function displayRiskMetrics(risk) {
    const container = document.getElementById('risk-metrics');
    
    container.innerHTML = `
        <div class="row">
            <div class="col-md-3">
                <div class="risk-metric">
                    <h6>投资组合价值</h6>
                    <div class="value">$${risk.portfolio_value.toFixed(2)}</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="risk-metric">
                    <h6>日收益率</h6>
                    <div class="value ${risk.daily_return >= 0 ? 'profit-positive' : 'profit-negative'}">
                        ${(risk.daily_return * 100).toFixed(2)}%
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="risk-metric">
                    <h6>年化波动率</h6>
                    <div class="value">${(risk.volatility * 100).toFixed(2)}%</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="risk-metric">
                    <h6>夏普比率</h6>
                    <div class="value">${risk.sharpe_ratio.toFixed(2)}</div>
                </div>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-md-4">
                <div class="risk-metric">
                    <h6>95% VaR</h6>
                    <div class="value text-danger">$${risk.var_95.toFixed(2)}</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="risk-metric">
                    <h6>最大回撤</h6>
                    <div class="value text-danger">${(risk.max_drawdown * 100).toFixed(2)}%</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="risk-metric">
                    <h6>Beta (vs BTC)</h6>
                    <div class="value">${risk.beta.toFixed(2)}</div>
                </div>
            </div>
        </div>
    `;
}

// 加载系统警告
async function loadSystemAlerts() {
    try {
        const response = await fetch('/api/alerts');
        const data = await response.json();
        
        if (data.success) {
            displaySystemAlerts(data.alerts);
        }
    } catch (error) {
        console.error('加载系统警告失败:', error);
    }
}

// 显示系统警告
function displaySystemAlerts(alerts) {
    const container = document.getElementById('system-alerts');
    
    if (alerts.length === 0) {
        container.innerHTML = '<p class="text-muted">暂无警告</p>';
        return;
    }
    
    let html = '';
    alerts.forEach(alert => {
        const iconClass = alert.level === 'warning' ? 'fa-exclamation-triangle text-warning' : 'fa-info-circle text-info';
        html += `
            <div class="alert alert-${alert.level === 'warning' ? 'warning' : 'info'} alert-sm">
                <i class="fas ${iconClass}"></i>
                ${alert.message}
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// 收集历史数据
async function collectHistoricalData() {
    try {
        const symbol = document.getElementById('collect-symbol').value;
        const days = parseInt(document.getElementById('collect-days').value);
        const interval = document.getElementById('collect-interval').value;
        
        const statusDiv = document.getElementById('collection-status');
        statusDiv.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> 正在收集数据...';
        
        const response = await fetch('/api/data/collect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                days: days,
                interval: interval
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusDiv.innerHTML = `<div class="text-success">✓ ${data.message}</div>`;
            showSuccess(data.message);
        } else {
            statusDiv.innerHTML = `<div class="text-danger">✗ ${data.message}</div>`;
            showError(data.message);
        }
    } catch (error) {
        document.getElementById('collection-status').innerHTML = `<div class="text-danger">✗ 收集失败: ${error.message}</div>`;
        showError('数据收集失败: ' + error.message);
    }
}

// 加载技术指标
async function loadTechnicalIndicators(symbol) {
    try {
        const response = await fetch(`/api/data/indicators/${symbol}`);
        const data = await response.json();
        
        if (data.success) {
            displayTechnicalIndicatorsChart(data.data, symbol);
        } else {
            showError('加载技术指标失败: ' + data.message);
        }
    } catch (error) {
        showError('加载技术指标失败: ' + error.message);
    }
}

// 显示技术指标图表
function displayTechnicalIndicatorsChart(data, symbol) {
    const timestamps = data.map(item => new Date(item.timestamp));
    const closes = data.map(item => item.close);
    const sma20 = data.map(item => item.sma_20);
    const rsi = data.map(item => item.rsi_14);
    
    const trace1 = {
        x: timestamps,
        y: closes,
        type: 'scatter',
        mode: 'lines',
        name: '价格',
        line: { color: '#007bff' }
    };
    
    const trace2 = {
        x: timestamps,
        y: sma20,
        type: 'scatter',
        mode: 'lines',
        name: 'SMA20',
        line: { color: '#28a745' }
    };
    
    const trace3 = {
        x: timestamps,
        y: rsi,
        type: 'scatter',
        mode: 'lines',
        name: 'RSI',
        yaxis: 'y2',
        line: { color: '#ffc107' }
    };
    
    const layout = {
        title: `${symbol} 技术指标`,
        xaxis: { title: '时间' },
        yaxis: { title: '价格', side: 'left' },
        yaxis2: {
            title: 'RSI',
            side: 'right',
            overlaying: 'y',
            range: [0, 100]
        },
        showlegend: true
    };
    
    Plotly.newPlot('price-chart', [trace1, trace2, trace3], layout, {responsive: true});
}

// 加载订单簿
async function loadOrderbook(symbol) {
    try {
        const response = await fetch(`/api/orderbook/${symbol}`);
        const data = await response.json();
        
        if (data.success) {
            displayOrderbook(data.data, symbol);
        } else {
            showError('加载订单簿失败: ' + data.message);
        }
    } catch (error) {
        showError('加载订单簿失败: ' + error.message);
    }
}

// 显示订单簿
function displayOrderbook(orderbook, symbol) {
    const bids = orderbook.bids.slice(0, 10); // 前10档买单
    const asks = orderbook.asks.slice(0, 10); // 前10档卖单
    
    const bidPrices = bids.map(bid => bid[0]);
    const bidVolumes = bids.map(bid => bid[1]);
    const askPrices = asks.map(ask => ask[0]);
    const askVolumes = asks.map(ask => ask[1]);
    
    const trace1 = {
        x: bidVolumes,
        y: bidPrices,
        type: 'bar',
        orientation: 'h',
        name: '买单',
        marker: { color: '#28a745' }
    };
    
    const trace2 = {
        x: askVolumes.map(v => -v), // 负值显示在左侧
        y: askPrices,
        type: 'bar',
        orientation: 'h',
        name: '卖单',
        marker: { color: '#dc3545' }
    };
    
    const layout = {
        title: `${symbol} 订单簿`,
        xaxis: { title: '数量' },
        yaxis: { title: '价格' },
        barmode: 'overlay'
    };
    
    Plotly.newPlot('price-chart', [trace1, trace2], layout, {responsive: true});
}

// 运行回测
async function runBacktest() {
    try {
        const strategy = document.getElementById('backtest-strategy').value;
        const symbol = document.getElementById('backtest-symbol').value;
        const startDate = document.getElementById('backtest-start').value;
        const endDate = document.getElementById('backtest-end').value;
        
        const resultsDiv = document.getElementById('backtest-results');
        resultsDiv.innerHTML = '<div class="spinner-border" role="status"></div> 正在运行回测...';
        
        const response = await fetch('/api/backtest/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                strategy_type: strategy,
                symbol: symbol,
                start_date: startDate,
                end_date: endDate,
                parameters: {}
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayBacktestResults(data.data);
        } else {
            resultsDiv.innerHTML = `<div class="text-danger">回测失败: ${data.message}</div>`;
        }
    } catch (error) {
        document.getElementById('backtest-results').innerHTML = `<div class="text-danger">回测失败: ${error.message}</div>`;
    }
}

// 显示回测结果
function displayBacktestResults(results) {
    const container = document.getElementById('backtest-results');
    
    container.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>收益指标</h6>
                <table class="table table-sm">
                    <tr><td>总收益率</td><td class="${results.total_return >= 0 ? 'profit-positive' : 'profit-negative'}">${(results.total_return * 100).toFixed(2)}%</td></tr>
                    <tr><td>年化收益率</td><td>${(results.annual_return * 100).toFixed(2)}%</td></tr>
                    <tr><td>最大回撤</td><td class="text-danger">${(results.max_drawdown * 100).toFixed(2)}%</td></tr>
                    <tr><td>夏普比率</td><td>${results.sharpe_ratio.toFixed(2)}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>交易统计</h6>
                <table class="table table-sm">
                    <tr><td>总交易次数</td><td>${results.total_trades}</td></tr>
                    <tr><td>胜率</td><td>${(results.win_rate * 100).toFixed(2)}%</td></tr>
                    <tr><td>盈亏比</td><td>${results.profit_factor.toFixed(2)}</td></tr>
                    <tr><td>平均收益</td><td>$${results.avg_trade_return.toFixed(2)}</td></tr>
                </table>
            </div>
        </div>
        <div class="mt-3">
            <canvas id="equity-curve-chart" width="400" height="200"></canvas>
        </div>
    `;
    
    // 绘制权益曲线
    drawEquityCurve(results.equity_curve);
}

// 绘制权益曲线
function drawEquityCurve(equityCurve) {
    const canvas = document.getElementById('equity-curve-chart');
    const ctx = canvas.getContext('2d');
    
    // 简单的权益曲线绘制
    const width = canvas.width;
    const height = canvas.height;
    const padding = 40;
    
    ctx.clearRect(0, 0, width, height);
    
    const minValue = Math.min(...equityCurve);
    const maxValue = Math.max(...equityCurve);
    const valueRange = maxValue - minValue;
    
    ctx.strokeStyle = '#007bff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    equityCurve.forEach((value, index) => {
        const x = padding + (index / (equityCurve.length - 1)) * (width - 2 * padding);
        const y = height - padding - ((value - minValue) / valueRange) * (height - 2 * padding);
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    
    ctx.stroke();
}

// 比较策略
async function compareStrategies() {
    try {
        const symbol = document.getElementById('backtest-symbol').value;
        const startDate = document.getElementById('backtest-start').value;
        const endDate = document.getElementById('backtest-end').value;
        
        const resultsDiv = document.getElementById('backtest-results');
        resultsDiv.innerHTML = '<div class="spinner-border" role="status"></div> 正在比较策略...';
        
        const response = await fetch('/api/backtest/compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayStrategyComparison(data.data);
        } else {
            resultsDiv.innerHTML = `<div class="text-danger">策略比较失败: ${data.message}</div>`;
        }
    } catch (error) {
        document.getElementById('backtest-results').innerHTML = `<div class="text-danger">策略比较失败: ${error.message}</div>`;
    }
}

// 显示策略比较结果
function displayStrategyComparison(comparison) {
    const container = document.getElementById('backtest-results');
    
    let html = '<h6>策略比较结果</h6><div class="table-responsive"><table class="table table-striped"><thead><tr>';
    
    // 表头
    const headers = Object.keys(comparison[0]);
    headers.forEach(header => {
        html += `<th>${header}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    // 数据行
    comparison.forEach(row => {
        html += '<tr>';
        headers.forEach(header => {
            html += `<td>${row[header]}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

// 训练机器学习模型
async function trainMLModel() {
    try {
        const symbol = document.getElementById('ml-symbol').value;
        const modelType = document.getElementById('ml-model-type').value;
        
        const statusDiv = document.getElementById('ml-training-status');
        statusDiv.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> 正在训练模型...';
        
        const response = await fetch('/api/ml/train', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                model_type: modelType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusDiv.innerHTML = `<div class="text-success">✓ ${data.message}</div>`;
            showSuccess(data.message);
        } else {
            statusDiv.innerHTML = `<div class="text-danger">✗ ${data.message}</div>`;
            showError(data.message);
        }
    } catch (error) {
        document.getElementById('ml-training-status').innerHTML = `<div class="text-danger">✗ 训练失败: ${error.message}</div>`;
        showError('模型训练失败: ' + error.message);
    }
}

// 加载系统状态
async function loadSystemStatus() {
    try {
        const response = await fetch('/api/system/status');
        const data = await response.json();
        
        if (data.success) {
            displaySystemStatus(data.status);
        }
    } catch (error) {
        console.error('加载系统状态失败:', error);
    }
}

// 显示系统状态
function displaySystemStatus(status) {
    const container = document.getElementById('system-status');
    
    container.innerHTML = `
        <div class="row">
            <div class="col-6">
                <div class="status-item">
                    <span>交易引擎</span>
                    <span class="${status.trading_engine ? 'text-success' : 'text-danger'}">
                        ${status.trading_engine ? '运行中' : '已停止'}
                    </span>
                </div>
            </div>
            <div class="col-6">
                <div class="status-item">
                    <span>数据收集</span>
                    <span class="${status.data_collection ? 'text-success' : 'text-danger'}">
                        ${status.data_collection ? '运行中' : '已停止'}
                    </span>
                </div>
            </div>
            <div class="col-6">
                <div class="status-item">
                    <span>数据库</span>
                    <span class="${status.database ? 'text-success' : 'text-danger'}">
                        ${status.database ? '正常' : '异常'}
                    </span>
                </div>
            </div>
            <div class="col-6">
                <div class="status-item">
                    <span>策略数量</span>
                    <span class="text-info">${status.strategies_count}</span>
                </div>
            </div>
        </div>
    `;
}

// 扩展初始化数据加载
function loadInitialData() {
    loadAccountData();
    loadPortfolioData();
    loadTradesData();
    loadMarketData(currentSymbol);
    loadRiskMetrics();
    loadSystemAlerts();
    loadSystemStatus();
}

// 扩展定期刷新
setInterval(() => {
    if (document.visibilityState === 'visible') {
        loadAccountData();
        checkTradingStatus();
        loadRiskMetrics();
        loadSystemAlerts();
        loadSystemStatus();
    }
}, 30000); // 每30秒刷新一次// 
添加新策略
async function addNewStrategy() {
    try {
        const symbol = document.getElementById('new-strategy-symbol').value;
        const strategyType = document.getElementById('new-strategy-type').value;
        const positionSize = parseFloat(document.getElementById('new-strategy-position-size').value) / 100;
        const stopLoss = parseFloat(document.getElementById('new-strategy-stop-loss').value) / 100;
        const takeProfit = parseFloat(document.getElementById('new-strategy-take-profit').value) / 100;
        
        if (!symbol || !strategyType) {
            showError('请选择交易对和策略类型');
            return;
        }
        
        const parameters = {
            position_size: positionSize,
            stop_loss: stopLoss,
            take_profit: takeProfit
        };
        
        // 根据策略类型添加特定参数
        if (strategyType === 'MA') {
            parameters.short_window = 10;
            parameters.long_window = 30;
        } else if (strategyType === 'RSI') {
            parameters.rsi_period = 14;
            parameters.oversold = 30;
            parameters.overbought = 70;
        } else if (strategyType === 'ML') {
            parameters.model_type = 'random_forest';
            parameters.min_confidence = 0.55;
            parameters.lookback_period = 20;
        }
        
        const response = await fetch('/api/strategies/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                strategy_type: strategyType,
                parameters: parameters
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('addStrategyModal'));
            modal.hide();
            // 重新加载策略列表
            loadStrategies();
            // 清空表单
            document.getElementById('add-strategy-form').reset();
        } else {
            showError(data.message);
        }
        
    } catch (error) {
        showError('添加策略失败: ' + error.message);
    }
}

// 移除策略
async function removeStrategy(strategyKey) {
    try {
        if (!confirm(`确定要移除策略 ${strategyKey} 吗？`)) {
            return;
        }
        
        const response = await fetch('/api/strategies/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                strategy_key: strategyKey
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            loadStrategies(); // 重新加载策略列表
        } else {
            showError(data.message);
        }
        
    } catch (error) {
        showError('移除策略失败: ' + error.message);
    }
}

// 更新策略列表显示（包含操作按钮）
function displayStrategies(strategies) {
    const tbody = document.querySelector('#strategies-table tbody');
    
    if (strategies.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">暂无策略数据</td></tr>';
        return;
    }
    
    let html = '';
    strategies.forEach(strategy => {
        const statusClass = strategy.position !== 0 ? 'text-success' : 'text-muted';
        const statusText = strategy.position !== 0 ? '持仓中' : '空仓';
        
        html += `
            <tr>
                <td>${strategy.name}</td>
                <td>${strategy.symbol}</td>
                <td>${strategy.type}</td>
                <td>${strategy.position.toFixed(6)}</td>
                <td>$${strategy.entry_price.toFixed(4)}</td>
                <td class="${statusClass}">${statusText}</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="removeStrategy('${strategy.name}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 完善训练机器学习模型函数
async function trainMLModel() {
    try {
        const symbol = document.getElementById('ml-symbol').value;
        const modelType = document.getElementById('ml-model-type').value;
        
        const statusDiv = document.getElementById('ml-training-status');
        statusDiv.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div> 正在训练模型...';
        
        const response = await fetch('/api/ml/train', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                model_type: modelType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusDiv.innerHTML = `<div class="text-success">✓ ${data.message}</div>`;
            showSuccess(data.message);
        } else {
            statusDiv.innerHTML = `<div class="text-danger">✗ ${data.message}</div>`;
            showError(data.message);
        }
    } catch (error) {
        document.getElementById('ml-training-status').innerHTML = `<div class="text-danger">✗ 训练失败: ${error.message}</div>`;
        showError('模型训练失败: ' + error.message);
    }
}

// 加载系统状态
async function loadSystemStatus() {
    try {
        const response = await fetch('/api/system/status');
        const data = await response.json();
        
        if (data.success) {
            displaySystemStatus(data.status);
        }
    } catch (error) {
        console.error('加载系统状态失败:', error);
    }
}

// 显示系统状态
function displaySystemStatus(status) {
    const container = document.getElementById('system-status');
    
    container.innerHTML = `
        <div class="row">
            <div class="col-6">
                <div class="status-item">
                    <span>交易引擎</span>
                    <span class="${status.trading_engine ? 'text-success' : 'text-danger'}">
                        ${status.trading_engine ? '运行中' : '已停止'}
                    </span>
                </div>
            </div>
            <div class="col-6">
                <div class="status-item">
                    <span>数据收集</span>
                    <span class="${status.data_collection ? 'text-success' : 'text-danger'}">
                        ${status.data_collection ? '运行中' : '已停止'}
                    </span>
                </div>
            </div>
            <div class="col-6">
                <div class="status-item">
                    <span>数据库</span>
                    <span class="${status.database ? 'text-success' : 'text-danger'}">
                        ${status.database ? '正常' : '异常'}
                    </span>
                </div>
            </div>
            <div class="col-6">
                <div class="status-item">
                    <span>策略数量</span>
                    <span class="text-info">${status.strategies_count}</span>
                </div>
            </div>
        </div>
    `;
}

// 扩展初始化数据加载
function loadInitialData() {
    loadAccountData();
    loadPortfolioData();
    loadTradesData();
    loadMarketData(currentSymbol);
    loadRiskMetrics();
    loadSystemAlerts();
    loadSystemStatus();
}

// 扩展定期刷新
setInterval(() => {
    if (document.visibilityState === 'visible') {
        loadAccountData();
        checkTradingStatus();
        loadRiskMetrics();
        loadSystemAlerts();
        loadSystemStatus();
    }
}, 30000); // 每30秒刷新一次