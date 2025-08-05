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
    
    let html = '';
    balances.forEach(balance => {
        if (balance.total > 0) {
            html += `
                <div class="balance-item">
                    <span class="balance-asset">${balance.asset}</span>
                    <span class="balance-amount">${balance.total.toFixed(8)}</span>
                </div>
            `;
        }
    });
    
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