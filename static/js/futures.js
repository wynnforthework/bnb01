// 合约交易页面JavaScript
let futuresSocket;
let currentFuturesSymbol = 'BTCUSDT';
let currentLeverage = 10;
let selectedSymbols = ['BTCUSDT', 'ETHUSDT'];
let futuresStrategies = []; // 全局策略数据

// 初始化合约交易页面
document.addEventListener('DOMContentLoaded', function() {
    initializeFuturesSocket();
    loadFuturesInitialData();
    bindFuturesEvents();
    checkFuturesTradingStatus();
});

// 初始化WebSocket连接
function initializeFuturesSocket() {
    futuresSocket = io();
    
    futuresSocket.on('connect', function() {
        console.log('合约交易WebSocket连接成功');
    });
    
    futuresSocket.on('futures_portfolio_update', function(data) {
        updateFuturesPortfolioDisplay(data);
    });
    
    futuresSocket.on('futures_trades_update', function(data) {
        updateFuturesTradesDisplay(data);
    });
    
    futuresSocket.on('disconnect', function() {
        console.log('合约交易WebSocket连接断开');
    });
}

// 绑定合约交易事件
function bindFuturesEvents() {
    // 启动合约交易
    document.getElementById('start-futures-trading').addEventListener('click', function() {
        startFuturesTrading();
    });
    
    // 停止合约交易
    document.getElementById('stop-futures-trading').addEventListener('click', function() {
        stopFuturesTrading();
    });
    
    // 更新配置
    document.getElementById('update-futures-config').addEventListener('click', function() {
        updateFuturesConfig();
    });
    
    // 刷新数据
    document.getElementById('refresh-futures-data').addEventListener('click', function() {
        loadFuturesInitialData();
    });
    
    // 手动下单
    document.getElementById('confirm-futures-order').addEventListener('click', function() {
        submitFuturesOrder();
    });
    
    // 查看持仓
    document.getElementById('refresh-futures-positions').addEventListener('click', function() {
        loadFuturesPositions();
    });
    
    // 杠杆变化
    document.getElementById('futures-leverage').addEventListener('change', function() {
        currentLeverage = parseInt(this.value);
        updateFuturesLeverageStatus();
    });
    
    // 币种选择变化
    document.getElementById('futures-symbols').addEventListener('change', function() {
        updateSelectedSymbols();
    });
    
    // 交易对选择变化
    document.getElementById('futures-symbol-select').addEventListener('change', function() {
        currentFuturesSymbol = this.value;
        loadFuturesMarketData(currentFuturesSymbol);
    });
    
    // 订单类型变化
    document.getElementById('futures-order-type').addEventListener('change', function() {
        toggleFuturesPriceInput(this.value);
    });
    
    // 订单参数变化时更新预览
    document.getElementById('futures-order-quantity').addEventListener('input', updateFuturesOrderPreview);
    document.getElementById('futures-order-price').addEventListener('input', updateFuturesOrderPreview);
    document.getElementById('futures-order-symbol').addEventListener('change', function() {
        updateFuturesMarketInfo(this.value);
    });
    
    // 添加币种
    document.getElementById('add-futures-symbol').addEventListener('click', function() {
        addFuturesSymbol();
    });
    
    // 更新币种选择
    document.getElementById('update-futures-symbols').addEventListener('click', function() {
        updateFuturesSymbols();
    });
}

// 加载合约交易初始数据
function loadFuturesInitialData() {
    loadFuturesAccountData();
    loadFuturesPositions();
    loadFuturesTradesData();
    loadFuturesMarketData(currentFuturesSymbol);
    loadFuturesStrategies();
    loadFuturesSymbols();
}

// 加载合约账户数据
async function loadFuturesAccountData() {
    try {
        const response = await fetch('/api/futures/account');
        const data = await response.json();
        
        if (data.success) {
            displayFuturesAccountInfo(data.data);
        } else {
            showError('加载合约账户数据失败: ' + data.message);
        }
    } catch (error) {
        showError('加载合约账户数据失败: ' + error.message);
    }
}

// 显示合约账户信息
function displayFuturesAccountInfo(account) {
    const container = document.getElementById('futures-account-info');
    
    const html = `
        <div class="row">
            <div class="col-6">
                <div class="text-center">
                    <h6 class="text-muted mb-1">总钱包余额</h6>
                    <h4 class="text-primary">$${account.totalWalletBalance.toFixed(2)}</h4>
                </div>
            </div>
            <div class="col-6">
                <div class="text-center">
                    <h6 class="text-muted mb-1">可用余额</h6>
                    <h4 class="text-success">$${account.availableBalance.toFixed(2)}</h4>
                </div>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-6">
                <div class="text-center">
                    <h6 class="text-muted mb-1">未实现盈亏</h6>
                    <h5 class="${account.totalUnrealizedProfit >= 0 ? 'text-success' : 'text-danger'}">
                        ${account.totalUnrealizedProfit >= 0 ? '+' : ''}$${account.totalUnrealizedProfit.toFixed(2)}
                    </h5>
                </div>
            </div>
            <div class="col-6">
                <div class="text-center">
                    <h6 class="text-muted mb-1">保证金余额</h6>
                    <h5 class="text-info">$${account.totalMarginBalance.toFixed(2)}</h5>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// 加载合约持仓
async function loadFuturesPositions() {
    try {
        const response = await fetch('/api/futures/positions');
        const data = await response.json();
        
        if (data.success) {
            displayFuturesPositions(data.positions);
            updateFuturesPortfolioSummary(data.positions);
        } else {
            showError('加载合约持仓失败: ' + data.message);
        }
    } catch (error) {
        showError('加载合约持仓失败: ' + error.message);
    }
}

// 显示合约持仓
function displayFuturesPositions(positions) {
    const tbody = document.querySelector('#futures-positions-table tbody');
    const detailTbody = document.querySelector('#futures-positions-detail-table tbody');
    
    if (positions.length === 0) {
        const emptyRow = '<tr><td colspan="10" class="text-center">暂无合约持仓</td></tr>';
        tbody.innerHTML = emptyRow;
        detailTbody.innerHTML = emptyRow;
        return;
    }
    
    let html = '';
    positions.forEach(position => {
        const pnlClass = position.unRealizedProfit >= 0 ? 'text-success' : 'text-danger';
        const pnlSign = position.unRealizedProfit >= 0 ? '+' : '';
        const sideClass = position.positionAmt > 0 ? 'text-success' : 'text-danger';
        const sideText = position.positionAmt > 0 ? '做多' : '做空';
        
        html += `
            <tr>
                <td>${position.symbol}</td>
                <td class="${sideClass}">${sideText}</td>
                <td>${Math.abs(position.positionAmt).toFixed(6)}</td>
                <td>$${position.entryPrice.toFixed(2)}</td>
                <td>$${position.markPrice.toFixed(2)}</td>
                <td class="${pnlClass}">${pnlSign}$${position.unRealizedProfit.toFixed(2)}</td>
                <td class="${pnlClass}">${pnlSign}${(position.percentage || 0).toFixed(2)}%</td>
                <td>$${position.isolatedMargin.toFixed(2)}</td>
                <td>${position.leverage}x</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-info btn-sm" onclick="showPositionDetails('${position.symbol}', '${position.positionSide}')" title="查看详情">
                            <i class="fas fa-info-circle"></i>
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="closeFuturesPosition('${position.symbol}', '${position.positionSide}')" title="平仓">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    detailTbody.innerHTML = html;
}

// 更新合约投资组合概览
function updateFuturesPortfolioSummary(positions) {
    const container = document.getElementById('futures-portfolio-summary');
    
    let totalValue = 0;
    let totalPnl = 0;
    let positionCount = positions.length;
    
    positions.forEach(pos => {
        totalValue += Math.abs(pos.positionAmt) * pos.markPrice;
        totalPnl += pos.unRealizedProfit;
    });
    
    const html = `
        <div class="row">
            <div class="col-4">
                <div class="text-center">
                    <h6 class="text-muted mb-1">持仓数量</h6>
                    <h4 class="text-primary">${positionCount}</h4>
                </div>
            </div>
            <div class="col-4">
                <div class="text-center">
                    <h6 class="text-muted mb-1">持仓价值</h6>
                    <h4 class="text-info">$${totalValue.toFixed(2)}</h4>
                </div>
            </div>
            <div class="col-4">
                <div class="text-center">
                    <h6 class="text-muted mb-1">总盈亏</h6>
                    <h4 class="${totalPnl >= 0 ? 'text-success' : 'text-danger'}">
                        ${totalPnl >= 0 ? '+' : ''}$${totalPnl.toFixed(2)}
                    </h4>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// 加载合约交易历史
async function loadFuturesTradesData() {
    try {
        const response = await fetch('/api/futures/trades');
        const data = await response.json();
        
        if (data.success) {
            displayFuturesTradesData(data.trades);
        } else {
            showError('加载合约交易历史失败: ' + data.message);
        }
    } catch (error) {
        showError('加载合约交易历史失败: ' + error.message);
    }
}

// 显示合约交易历史
function displayFuturesTradesData(trades) {
    const tbody = document.querySelector('#futures-trades-table tbody');
    
    if (trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">暂无合约交易记录</td></tr>';
        return;
    }
    
    let html = '';
    trades.forEach(trade => {
        const sideClass = trade.side === 'BUY' ? 'text-success' : 'text-danger';
        const pnlClass = trade.profit_loss >= 0 ? 'text-success' : 'text-danger';
        const pnlSign = trade.profit_loss >= 0 ? '+' : '';
        
        html += `
            <tr>
                <td>${new Date(trade.timestamp).toLocaleString()}</td>
                <td>${trade.symbol}</td>
                <td class="${sideClass}">${trade.side}</td>
                <td>${trade.quantity.toFixed(6)}</td>
                <td>$${trade.price.toFixed(2)}</td>
                <td>${trade.strategy || 'N/A'}</td>
                <td class="${pnlClass}">${pnlSign}$${trade.profit_loss.toFixed(2)}</td>
                <td><span class="badge bg-warning">合约</span></td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 启动合约交易
async function startFuturesTrading() {
    try {
        const response = await fetch('/api/futures/trading/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                leverage: currentLeverage,
                symbols: selectedSymbols
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            updateFuturesTradingStatus(true);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('启动合约交易失败: ' + error.message);
    }
}

// 停止合约交易
async function stopFuturesTrading() {
    try {
        const response = await fetch('/api/futures/trading/stop', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            updateFuturesTradingStatus(false);
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('停止合约交易失败: ' + error.message);
    }
}

// 更新合约配置
async function updateFuturesConfig() {
    try {
        const leverage = parseInt(document.getElementById('futures-leverage').value);
        const symbols = Array.from(document.getElementById('futures-symbols').selectedOptions)
                           .map(option => option.value);
        
        if (symbols.length === 0) {
            showError('请至少选择一个交易币种');
            return;
        }
        
        // 保存配置到服务器
        const response = await fetch('/api/futures/config/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                leverage: leverage,
                symbols: symbols
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 更新本地变量
            currentLeverage = leverage;
            selectedSymbols = symbols;
            
            // 更新显示
            updateFuturesLeverageStatus();
            updateSelectedSymbolsStatus();
            
            showSuccess(result.message);
        } else {
            showError('保存配置失败: ' + result.message);
        }
        
    } catch (error) {
        showError('更新合约配置失败: ' + error.message);
    }
}

// 更新杠杆状态显示
function updateFuturesLeverageStatus() {
    document.getElementById('futures-leverage-status').textContent = currentLeverage + 'x';
}

// 更新选中币种状态
function updateSelectedSymbols() {
    selectedSymbols = Array.from(document.getElementById('futures-symbols').selectedOptions)
                          .map(option => option.value);
    updateSelectedSymbolsStatus();
}

// 更新选中币种状态显示
function updateSelectedSymbolsStatus() {
    const symbolsText = selectedSymbols.map(s => s.replace('USDT', '')).join(', ');
    document.getElementById('futures-symbols-status').textContent = symbolsText;
}

// 检查合约交易状态
async function checkFuturesTradingStatus() {
    try {
        const response = await fetch('/api/futures/trading/status');
        const data = await response.json();
        
        if (data.success) {
            updateFuturesTradingStatus(data.is_running);
            if (data.leverage) {
                currentLeverage = data.leverage;
                updateFuturesLeverageStatus();
            }
        }
    } catch (error) {
        console.error('检查合约交易状态失败:', error);
    }
}

// 更新合约交易状态显示
function updateFuturesTradingStatus(isRunning) {
    const statusElement = document.getElementById('futures-trading-status');
    const badgeElement = document.getElementById('futures-mode-status');
    
    if (isRunning) {
        statusElement.innerHTML = '<i class="fas fa-circle text-success"></i> 运行中';
        if (badgeElement) {
            badgeElement.className = 'badge bg-success text-white';
            badgeElement.textContent = '运行中';
        }
    } else {
        statusElement.innerHTML = '<i class="fas fa-circle text-danger"></i> 未运行';
        if (badgeElement) {
            badgeElement.className = 'badge bg-warning text-dark';
            badgeElement.textContent = '合约模式';
        }
    }
}

// 加载合约市场数据
async function loadFuturesMarketData(symbol) {
    try {
        const response = await fetch(`/api/futures/market/${symbol}`);
        const data = await response.json();
        
        if (data.success) {
            displayFuturesMarketData(data.data);
        } else {
            showError('加载合约市场数据失败: ' + data.message);
        }
    } catch (error) {
        showError('加载合约市场数据失败: ' + error.message);
    }
}

// 显示合约市场数据
function displayFuturesMarketData(marketData) {
    // 更新图表数据
    if (marketData.klines && marketData.klines.length > 0) {
        const traces = [{
            x: marketData.klines.map(k => new Date(k.timestamp)),
            close: marketData.klines.map(k => k.close),
            high: marketData.klines.map(k => k.high),
            low: marketData.klines.map(k => k.low),
            open: marketData.klines.map(k => k.open),
            type: 'candlestick',
            name: currentFuturesSymbol
        }];
        
        const layout = {
            title: `${currentFuturesSymbol} 合约价格`,
            xaxis: { title: '时间' },
            yaxis: { title: '价格 (USDT)' },
            height: 400
        };
        
        Plotly.newPlot('futures-price-chart', traces, layout);
    }
}

// 切换合约价格输入显示
function toggleFuturesPriceInput(orderType) {
    const priceInput = document.getElementById('futures-price-input');
    if (orderType === 'LIMIT') {
        priceInput.style.display = 'block';
        document.getElementById('futures-order-price').required = true;
    } else {
        priceInput.style.display = 'none';
        document.getElementById('futures-order-price').required = false;
    }
    updateFuturesOrderPreview();
}

// 更新合约市场信息
async function updateFuturesMarketInfo(symbol) {
    try {
        const response = await fetch(`/api/futures/market/${symbol}`);
        const data = await response.json();
        
        if (data.success) {
            const marketData = data.data;
            
            document.getElementById('futures-current-price').textContent = '$' + marketData.currentPrice.toFixed(2);
            document.getElementById('futures-mark-price').textContent = '$' + marketData.markPrice.toFixed(2);
            document.getElementById('futures-funding-rate').textContent = (marketData.fundingRate * 100).toFixed(4) + '%';
            
            if (marketData.nextFundingTime) {
                const nextFunding = new Date(marketData.nextFundingTime);
                document.getElementById('futures-next-funding').textContent = nextFunding.toLocaleTimeString();
            }
            
            updateFuturesOrderPreview();
        }
    } catch (error) {
        console.error('更新合约市场信息失败:', error);
    }
}

// 更新合约订单预览
function updateFuturesOrderPreview() {
    const quantity = parseFloat(document.getElementById('futures-order-quantity').value) || 0;
    const orderType = document.getElementById('futures-order-type').value;
    const price = orderType === 'LIMIT' ? 
        (parseFloat(document.getElementById('futures-order-price').value) || 0) :
        (parseFloat(document.getElementById('futures-current-price').textContent.replace('$', '')) || 0);
    
    const estimatedCost = quantity * price;
    document.getElementById('futures-estimated-cost').textContent = '$' + estimatedCost.toFixed(2);
    
    const leverage = parseInt(document.getElementById('futures-order-leverage').value) || 10;
    const requiredMargin = estimatedCost / leverage;
    document.getElementById('futures-required-margin').textContent = '$' + requiredMargin.toFixed(2);
}

// 提交合约订单
async function submitFuturesOrder() {
    try {
        const symbol = document.getElementById('futures-order-symbol').value;
        const side = document.querySelector('input[name="futures-order-side"]:checked').value;
        const quantity = parseFloat(document.getElementById('futures-order-quantity').value);
        const orderType = document.getElementById('futures-order-type').value;
        const price = orderType === 'LIMIT' ? parseFloat(document.getElementById('futures-order-price').value) : null;
        const leverage = parseInt(document.getElementById('futures-order-leverage').value);
        const positionSide = document.getElementById('futures-position-side').value;
        
        const orderData = {
            symbol: symbol,
            side: side,
            quantity: quantity,
            order_type: orderType,
            leverage: leverage,
            position_side: positionSide
        };
        
        if (price) {
            orderData.price = price;
        }
        
        const response = await fetch('/api/futures/order/place', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('合约订单提交成功: ' + data.order_id);
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('futuresOrderModal'));
            modal.hide();
            
            // 刷新数据
            loadFuturesInitialData();
        } else {
            showError('合约订单提交失败: ' + data.message);
        }
    } catch (error) {
        showError('合约订单提交失败: ' + error.message);
    }
}

// 平仓
async function closeFuturesPosition(symbol, positionSide) {
    if (!confirm(`确认平仓 ${symbol} ${positionSide} 持仓？`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/futures/position/close', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                position_side: positionSide
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            loadFuturesPositions();
        } else {
            showError(data.message);
        }
    } catch (error) {
        showError('平仓失败: ' + error.message);
    }
}

// 加载合约策略
async function loadFuturesStrategies() {
    try {
        const response = await fetch('/api/futures/strategies/list');
        const data = await response.json();
        
        if (data.success) {
            // 更新全局策略数据
            futuresStrategies = data.strategies;
            
            // 显示策略表格
            displayFuturesStrategies(data.strategies);
            
            // 显示策略管理面板
            displayFuturesStrategiesManagement(data.strategies);
            
            // 显示策略管理部分
            const strategiesSection = document.getElementById('futures-strategies-section');
            if (strategiesSection) {
                strategiesSection.style.display = 'block';
            }
        }
    } catch (error) {
        console.error('加载合约策略失败:', error);
    }
}

// 显示合约策略
function displayFuturesStrategies(strategies) {
    const tbody = document.querySelector('#futures-strategies-table tbody');
    
    if (strategies.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">暂无合约策略数据</td></tr>';
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
                <td>$${strategy.entry_price.toFixed(2)}</td>
                <td>${currentLeverage}x</td>
                <td class="${statusClass}">${statusText}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewStrategyDetails('${strategy.name}')">
                        详情
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 显示合约策略管理面板
function displayFuturesStrategiesManagement(strategies) {
    const container = document.getElementById('futures-strategies-container');
    if (!container) return;

    container.innerHTML = '';

    if (!strategies || strategies.length === 0) {
        container.innerHTML = '<div class="notification is-warning is-light">暂无策略数据</div>';
        return;
    }

    strategies.forEach(strategy => {
        const strategyDiv = document.createElement('div');
        strategyDiv.className = 'field';
        strategyDiv.innerHTML = `
            <div class="control">
                <label class="checkbox">
                    <input type="checkbox" 
                           ${strategy.enabled ? 'checked' : ''} 
                           onchange="toggleFuturesStrategy('${strategy.name}', this.checked)">
                    <span class="ml-2">${strategy.name}</span>
                    <span class="tag is-small ml-2 ${strategy.enabled ? 'is-success' : 'is-light'}">
                        ${strategy.enabled ? '已启用' : '已禁用'}
                    </span>
                </label>
            </div>
        `;
        container.appendChild(strategyDiv);
    });

    // 更新统计信息
    updateFuturesStrategyStatistics(strategies);
}

// 工具函数
function showSuccess(message) {
    // 显示成功消息的实现
    console.log('Success:', message);
    // 这里可以添加toast或alert的实现
}

function showError(message) {
    // 显示错误消息的实现
    console.error('Error:', message);
    // 这里可以添加toast或alert的实现
}

// 定期刷新合约数据
setInterval(() => {
    if (document.visibilityState === 'visible') {
        loadFuturesAccountData();
        loadFuturesPositions();
    }
}, 30000); // 每30秒刷新一次

// 显示持仓详情
async function showPositionDetails(symbol, positionSide) {
    try {
        const response = await fetch(`/api/futures/position/details?symbol=${symbol}&position_side=${positionSide}`);
        const data = await response.json();
        
        if (data.success) {
            const position = data.position;
            
            // 创建详情模态框内容
            const modalContent = `
                <div class="modal fade" id="positionDetailsModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    <i class="fas fa-info-circle"></i> 持仓详情 - ${symbol}
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <h6>基本信息</h6>
                                        <table class="table table-sm">
                                            <tr><td>交易对</td><td><strong>${position.symbol}</strong></td></tr>
                                            <tr><td>持仓方向</td><td><span class="badge ${position.positionAmt > 0 ? 'bg-success' : 'bg-danger'}">${position.positionAmt > 0 ? '做多' : '做空'}</span></td></tr>
                                            <tr><td>持仓数量</td><td>${Math.abs(position.positionAmt).toFixed(6)}</td></tr>
                                            <tr><td>杠杆倍数</td><td>${position.leverage}x</td></tr>
                                            <tr><td>保证金模式</td><td>${position.marginType === 'isolated' ? '逐仓' : '全仓'}</td></tr>
                                        </table>
                                    </div>
                                    <div class="col-md-6">
                                        <h6>价格信息</h6>
                                        <table class="table table-sm">
                                            <tr><td>开仓价格</td><td>${position.entryPrice.toFixed(2)} USDT</td></tr>
                                            <tr><td>标记价格</td><td>${position.markPrice.toFixed(2)} USDT</td></tr>
                                            <tr><td>强平价格</td><td>${position.liquidationPrice ? position.liquidationPrice.toFixed(2) : 'N/A'} USDT</td></tr>
                                            <tr><td>价格变化</td><td class="${(position.markPrice - position.entryPrice) >= 0 ? 'text-success' : 'text-danger'}">${((position.markPrice - position.entryPrice) / position.entryPrice * 100).toFixed(2)}%</td></tr>
                                        </table>
                                    </div>
                                </div>
                                <div class="row mt-3">
                                    <div class="col-md-6">
                                        <h6>盈亏信息</h6>
                                        <table class="table table-sm">
                                            <tr><td>未实现盈亏</td><td class="${position.unRealizedProfit >= 0 ? 'text-success' : 'text-danger'}">${position.unRealizedProfit >= 0 ? '+' : ''}${position.unRealizedProfit.toFixed(2)} USDT</td></tr>
                                            <tr><td>盈亏比例</td><td class="${(position.percentage || 0) >= 0 ? 'text-success' : 'text-danger'}">${(position.percentage || 0) >= 0 ? '+' : ''}${(position.percentage || 0).toFixed(2)}%</td></tr>
                                            <tr><td>持仓价值</td><td>${(Math.abs(position.positionAmt) * position.markPrice).toFixed(2)} USDT</td></tr>
                                        </table>
                                    </div>
                                    <div class="col-md-6">
                                        <h6>保证金信息</h6>
                                        <table class="table table-sm">
                                            <tr><td>初始保证金</td><td>${position.initialMargin ? position.initialMargin.toFixed(2) : 'N/A'} USDT</td></tr>
                                            <tr><td>维持保证金</td><td>${position.maintMargin ? position.maintMargin.toFixed(2) : 'N/A'} USDT</td></tr>
                                            <tr><td>逐仓保证金</td><td>${position.isolatedMargin.toFixed(2)} USDT</td></tr>
                                        </table>
                                    </div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                                <button type="button" class="btn btn-danger" onclick="closeFuturesPosition('${symbol}', '${positionSide}')">
                                    <i class="fas fa-times"></i> 平仓
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // 移除已存在的模态框
            const existingModal = document.getElementById('positionDetailsModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // 添加新的模态框到页面
            document.body.insertAdjacentHTML('beforeend', modalContent);
            
            // 显示模态框
            const modal = new bootstrap.Modal(document.getElementById('positionDetailsModal'));
            modal.show();
            
        } else {
            showError('获取持仓详情失败: ' + data.message);
        }
    } catch (error) {
        showError('获取持仓详情失败: ' + error.message);
    }
}

// 加载保存的配置
async function loadSavedConfig() {
    console.log('开始加载保存的配置...');
    
    try {
        const response = await fetch('/api/futures/config/get');
        const data = await response.json();
        
        console.log('配置API响应:', data);
        
        if (data.success && data.config) {
            const config = data.config;
            console.log('准备应用配置:', config);
            
            // 检查DOM元素是否存在
            const leverageSelect = document.getElementById('futures-leverage');
            const symbolsSelect = document.getElementById('futures-symbols');
            
            if (!leverageSelect) {
                console.error('未找到杠杆选择元素 #futures-leverage');
                return;
            }
            
            if (!symbolsSelect) {
                console.error('未找到币种选择元素 #futures-symbols');
                return;
            }
            
            // 更新杠杆选择
            leverageSelect.value = config.leverage;
            currentLeverage = config.leverage;
            console.log('杠杆设置为:', config.leverage);
            
            // 更新币种选择
            let selectedCount = 0;
            Array.from(symbolsSelect.options).forEach(option => {
                const shouldSelect = config.symbols.includes(option.value);
                option.selected = shouldSelect;
                if (shouldSelect) selectedCount++;
            });
            selectedSymbols = config.symbols;
            console.log('币种选择完成，选中数量:', selectedCount);
            
            // 更新显示
            if (typeof updateFuturesLeverageStatus === 'function') {
                updateFuturesLeverageStatus();
                console.log('杠杆状态显示已更新');
            } else {
                console.warn('updateFuturesLeverageStatus 函数不存在');
            }
            
            if (typeof updateSelectedSymbolsStatus === 'function') {
                updateSelectedSymbolsStatus();
                console.log('币种状态显示已更新');
            } else {
                console.warn('updateSelectedSymbolsStatus 函数不存在');
            }
            
            console.log('✅ 配置加载成功:', config);
        } else {
            console.error('配置加载失败:', data.message || '未知错误');
        }
    } catch (error) {
        console.error('❌ 加载配置异常:', error);
    }
}

// 在页面加载时调用配置加载
document.addEventListener('DOMContentLoaded', function() {
    // 延迟加载配置，确保DOM元素已经准备好
    setTimeout(loadSavedConfig, 1000); // 增加延迟到1秒
    
    // 如果第一次加载失败，再尝试一次
    setTimeout(function() {
        console.log('执行第二次配置加载尝试...');
        loadSavedConfig();
    }, 2000);
});

// ==================== 合约策略管理功能 ====================

// 初始化合约策略管理
function initializeFuturesStrategyManagement() {
    // 绑定策略管理相关事件
    bindFuturesStrategyEvents();
    
    // 加载初始数据
    loadFuturesStrategiesStatus();
    loadFuturesSymbols();
}

// 绑定合约策略管理事件
function bindFuturesStrategyEvents() {
    // 显示/隐藏不同部分
    document.getElementById('show-futures-symbols').addEventListener('click', function() {
        showFuturesSection('futures-symbols-section');
    });
    
    document.getElementById('show-futures-strategies').addEventListener('click', function() {
        showFuturesSection('futures-strategies-section');
    });
    
    document.getElementById('show-futures-backtest').addEventListener('click', function() {
        showFuturesSection('futures-backtest-section');
    });
    
    // 保存币种选择
    document.getElementById('update-futures-symbols').addEventListener('click', function() {
        updateFuturesSymbols();
    });
    
    // 更新策略
    document.getElementById('update-futures-strategies').addEventListener('click', function() {
        updateFuturesStrategies();
    });
    
    // 策略对比
    document.getElementById('compare-futures-strategies').addEventListener('click', function() {
        compareFuturesStrategies();
    });
    
    // 运行回测
    document.getElementById('run-futures-backtest').addEventListener('click', function() {
        runFuturesBacktest();
    });
}

// 显示指定的合约策略管理部分
function showFuturesSection(sectionId) {
    // 隐藏所有部分
    const sections = ['futures-symbols-section', 'futures-strategies-section', 'futures-backtest-section'];
    sections.forEach(id => {
        document.getElementById(id).style.display = 'none';
    });
    
    // 显示指定部分
    document.getElementById(sectionId).style.display = 'block';
    
    // 更新按钮状态
    updateFuturesSectionButtons(sectionId);
}

// 更新合约策略管理按钮状态
function updateFuturesSectionButtons(activeSection) {
    const buttons = {
        'futures-symbols-section': 'show-futures-symbols',
        'futures-strategies-section': 'show-futures-strategies',
        'futures-backtest-section': 'show-futures-backtest'
    };
    
    Object.entries(buttons).forEach(([section, buttonId]) => {
        const button = document.getElementById(buttonId);
        if (section === activeSection) {
            button.classList.remove('is-outlined');
            button.classList.add('is-primary');
        } else {
            button.classList.remove('is-primary');
            button.classList.add('is-outlined');
        }
    });
}

// 加载合约币种列表
async function loadFuturesSymbols() {
    try {
        const response = await fetch('/api/futures/symbols');
        if (response.ok) {
            const data = await response.json();
            displayFuturesSymbols(data.symbols || []);
        } else {
            console.error('加载合约币种失败:', response.statusText);
        }
    } catch (error) {
        console.error('加载合约币种出错:', error);
    }
}

// 显示合约币种选择框
function displayFuturesSymbols(symbols) {
    const container = document.getElementById('futures-symbols-container');
    container.innerHTML = '';
    
    const defaultSymbols = ['BTCUSDT', 'ETHUSDT', 'MATICUSDT', 'BNBUSDT', 'ADAUSDT'];
    
    defaultSymbols.forEach(symbol => {
        const isSelected = symbols.includes(symbol);
        const symbolDiv = document.createElement('div');
        symbolDiv.className = 'control';
        symbolDiv.innerHTML = `
            <label class="checkbox">
                <input type="checkbox" value="${symbol}" ${isSelected ? 'checked' : ''}>
                <span class="ml-2">${symbol}</span>
            </label>
            <button class="button is-small is-danger is-outlined ml-2" onclick="deleteFuturesSymbol('${symbol}')">
                <span class="icon is-small">
                    <i class="fas fa-trash"></i>
                </span>
            </button>
        `;
        container.appendChild(symbolDiv);
        
        // 为复选框添加change事件监听器
        const checkbox = symbolDiv.querySelector('input[type="checkbox"]');
        checkbox.addEventListener('change', function() {
            updateFuturesEnabledSymbolsDisplay();
        });
    });
    
    // 更新合约交易控制面板中的启用币种显示
    updateFuturesEnabledSymbolsDisplay();
}

// 更新合约币种选择
async function updateFuturesSymbols() {
    const selectedSymbols = Array.from(
        document.querySelectorAll('#futures-symbols-container input[type="checkbox"]:checked')
    ).map(cb => cb.value);
    
    try {
        const response = await fetch('/api/futures/symbols/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ symbols: selectedSymbols })
        });
        
        if (response.ok) {
            showSuccess('币种选择已更新');
            loadFuturesStrategiesStatus();
            // 更新合约交易控制面板中的启用币种显示
            updateFuturesEnabledSymbolsDisplay();
        } else {
            const error = await response.json();
            showError(`更新币种选择失败: ${error.message}`);
        }
    } catch (error) {
        console.error('更新币种选择出错:', error);
        showError('更新币种选择时发生错误');
    }
}

// 添加合约币种
async function addFuturesSymbol() {
    const newSymbolInput = document.getElementById('futures-new-symbol');
    const newSymbol = newSymbolInput.value.trim().toUpperCase();
    
    if (!newSymbol) {
        showError('请输入币种代码');
        return;
    }
    
    // 验证币种格式
    if (!newSymbol.endsWith('USDT')) {
        showError('币种代码必须以USDT结尾');
        return;
    }
    
    try {
        const response = await fetch('/api/futures/symbols/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ symbol: newSymbol })
        });
        
        if (response.ok) {
            showSuccess(`币种 ${newSymbol} 添加成功`);
            newSymbolInput.value = '';
            // 重新加载币种列表
            loadFuturesSymbols();
        } else {
            const error = await response.json();
            showError(`添加币种失败: ${error.message}`);
        }
    } catch (error) {
        console.error('添加币种出错:', error);
        showError('添加币种时发生错误');
    }
}

// 删除合约币种
async function deleteFuturesSymbol(symbol) {
    if (!confirm(`确定要删除币种 ${symbol} 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/futures/symbols/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ symbol: symbol })
        });
        
        if (response.ok) {
            showSuccess(`币种 ${symbol} 删除成功`);
            // 重新加载币种列表
            loadFuturesSymbols();
        } else {
            const error = await response.json();
            showError(`删除币种失败: ${error.message}`);
        }
    } catch (error) {
        console.error('删除币种出错:', error);
        showError('删除币种时发生错误');
    }
}

// 加载合约策略状态
async function loadFuturesStrategiesStatus() {
    try {
        const response = await fetch('/api/futures/strategies/status');
        if (response.ok) {
            const data = await response.json();
            displayFuturesStrategiesStatus(data);
        } else {
            console.error('加载合约策略状态失败:', response.statusText);
        }
    } catch (error) {
        console.error('加载合约策略状态出错:', error);
    }
}

// 显示合约策略状态
function displayFuturesStrategiesStatus(data) {
    const container = document.getElementById('futures-strategies-status');
    const { enabledStrategies = [], selectedSymbols = [] } = data;
    
    let html = '<div class="columns is-multiline">';
    
    // 显示启用的策略
    html += '<div class="column is-6">';
    html += '<h6 class="title is-6">启用的策略</h6>';
    if (enabledStrategies.length > 0) {
        enabledStrategies.forEach(strategy => {
            html += `<span class="tag is-info mr-2 mb-2">${strategy}</span>`;
        });
    } else {
        html += '<p class="has-text-grey">暂无启用的策略</p>';
    }
    html += '</div>';
    
    // 显示选中的币种
    html += '<div class="column is-6">';
    html += '<h6 class="title is-6">选中的币种</h6>';
    if (selectedSymbols.length > 0) {
        selectedSymbols.forEach(symbol => {
            html += `<span class="tag is-success mr-2 mb-2">${symbol}</span>`;
        });
    } else {
        html += '<p class="has-text-grey">暂无选中的币种</p>';
    }
    html += '</div>';
    
    html += '</div>';
    container.innerHTML = html;
}

// 更新合约策略
async function updateFuturesStrategies() {
    const strategyType = document.getElementById('futures-strategy-type').value;
    
    try {
        const response = await fetch('/api/futures/strategies/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ strategy_type: strategyType })
        });
        
        if (response.ok) {
            const data = await response.json();
            showSuccess(`策略更新成功，共处理 ${data.total_symbols} 个币种`);
            loadFuturesStrategiesStatus();
        } else {
            const error = await response.json();
            showError(`策略更新失败: ${error.message}`);
        }
    } catch (error) {
        console.error('更新合约策略出错:', error);
        showError('更新策略时发生错误');
    }
}

// 对比合约策略
async function compareFuturesStrategies() {
    try {
        showSuccess('开始策略对比分析...');
        
        const response = await fetch('/api/futures/strategies/compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            displayFuturesStrategyComparison(data);
        } else {
            const error = await response.json();
            showError(`策略对比失败: ${error.message}`);
        }
    } catch (error) {
        console.error('合约策略对比出错:', error);
        showError('策略对比时发生错误');
    }
}

// 显示合约策略对比结果
function displayFuturesStrategyComparison(data) {
    const container = document.getElementById('futures-backtest-table');
    
    if (!data || !data.results || data.results.length === 0) {
        container.innerHTML = '<p class="has-text-grey">暂无策略对比数据</p>';
        return;
    }
    
    let html = '<div class="table-container">';
    html += '<table class="table is-fullwidth is-striped">';
    html += '<thead><tr>';
    html += '<th>策略类型</th>';
    html += '<th>币种</th>';
    html += '<th>总收益率</th>';
    html += '<th>胜率</th>';
    html += '<th>交易次数</th>';
    html += '<th>夏普比率</th>';
    html += '</tr></thead><tbody>';
    
    data.results.forEach(result => {
        const returnPercent = (result.total_return * 100).toFixed(2);
        const winRate = (result.win_rate * 100).toFixed(1);
        const sharpeRatio = result.sharpe_ratio ? result.sharpe_ratio.toFixed(2) : 'N/A';
        
        html += `<tr>`;
        html += `<td><span class="tag is-info">${result.strategy_type}</span></td>`;
        html += `<td>${result.symbol}</td>`;
        html += `<td class="${returnPercent >= 0 ? 'has-text-success' : 'has-text-danger'}">${returnPercent}%</td>`;
        html += `<td>${winRate}%</td>`;
        html += `<td>${result.trade_count}</td>`;
        html += `<td>${sharpeRatio}</td>`;
        html += `</tr>`;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
    
    // 显示回测结果
    document.getElementById('futures-backtest-results').style.display = 'block';
}

// 运行合约回测
async function runFuturesBacktest() {
    try {
        showSuccess('开始运行回测...');
        
        const response = await fetch('/api/futures/backtest/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            displayFuturesBacktestResults(data);
        } else {
            const error = await response.json();
            showError(`回测运行失败: ${error.message}`);
        }
    } catch (error) {
        console.error('运行合约回测出错:', error);
        showError('运行回测时发生错误');
    }
}

// 显示合约回测结果
function displayFuturesBacktestResults(data) {
    const container = document.getElementById('futures-backtest-table');
    
    if (!data || !data.results || data.results.length === 0) {
        container.innerHTML = '<p class="has-text-grey">暂无回测数据</p>';
        return;
    }
    
    let html = '<div class="table-container">';
    html += '<table class="table is-fullwidth is-striped">';
    html += '<thead><tr>';
    html += '<th>币种</th>';
    html += '<th>策略类型</th>';
    html += '<th>总收益率</th>';
    html += '<th>胜率</th>';
    html += '<th>交易次数</th>';
    html += '<th>最大回撤</th>';
    html += '<th>夏普比率</th>';
    html += '</tr></thead><tbody>';
    
    data.results.forEach(result => {
        const returnPercent = (result.total_return * 100).toFixed(2);
        const winRate = (result.win_rate * 100).toFixed(1);
        const maxDrawdown = result.max_drawdown ? (result.max_drawdown * 100).toFixed(2) : 'N/A';
        const sharpeRatio = result.sharpe_ratio ? result.sharpe_ratio.toFixed(2) : 'N/A';
        
        html += `<tr>`;
        html += `<td><strong>${result.symbol}</strong></td>`;
        html += `<td><span class="tag is-info">${result.strategy_type}</span></td>`;
        html += `<td class="${returnPercent >= 0 ? 'has-text-success' : 'has-text-danger'}">${returnPercent}%</td>`;
        html += `<td>${winRate}%</td>`;
        html += `<td>${result.trade_count}</td>`;
        html += `<td class="has-text-warning">${maxDrawdown}%</td>`;
        html += `<td>${sharpeRatio}</td>`;
        html += `</tr>`;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
    
    // 显示回测结果
    document.getElementById('futures-backtest-results').style.display = 'block';
}

// 启用全部合约策略
async function enableAllFuturesStrategies() {
    try {
        const response = await fetch('/api/futures/strategies/enable-all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            showSuccess('已启用全部策略');
            loadFuturesStrategies();
        } else {
            const error = await response.json();
            showError(`启用全部策略失败: ${error.message}`);
        }
    } catch (error) {
        console.error('启用全部策略出错:', error);
        showError('启用全部策略时发生错误');
    }
}

// 禁用全部合约策略
async function disableAllFuturesStrategies() {
    try {
        const response = await fetch('/api/futures/strategies/disable-all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            showSuccess('已禁用全部策略');
            loadFuturesStrategies();
        } else {
            const error = await response.json();
            showError(`禁用全部策略失败: ${error.message}`);
        }
    } catch (error) {
        console.error('禁用全部策略出错:', error);
        showError('禁用全部策略时发生错误');
    }
}

// 更新合约策略统计信息
function updateFuturesStrategyStatistics(strategies) {
    const totalCountElement = document.getElementById('futures-total-strategies-count');
    const enabledCountElement = document.getElementById('futures-enabled-strategies-count');
    const avgReturnElement = document.getElementById('futures-avg-return');
    const avgWinRateElement = document.getElementById('futures-avg-win-rate');

    if (totalCountElement) {
        totalCountElement.textContent = strategies ? strategies.length : 0;
    }

    if (enabledCountElement) {
        const enabledCount = strategies ? strategies.filter(s => s.enabled).length : 0;
        enabledCountElement.textContent = enabledCount;
    }

    if (avgReturnElement) {
        avgReturnElement.textContent = '0%';
    }

    if (avgWinRateElement) {
        avgWinRateElement.textContent = '0%';
    }
}

// 更新合约交易控制面板中的启用币种显示
function updateFuturesEnabledSymbolsDisplay() {
    const enabledSymbolsDisplay = document.getElementById('futures-enabled-symbols-display');
    if (!enabledSymbolsDisplay) return;
    
    // 获取当前启用的币种
    const enabledSymbols = Array.from(
        document.querySelectorAll('#futures-symbols-container input[type="checkbox"]:checked')
    ).map(cb => cb.value);
    
    // 清空现有显示
    enabledSymbolsDisplay.innerHTML = '';
    
    // 添加启用的币种作为标签
    enabledSymbols.forEach(symbol => {
        const tag = document.createElement('span');
        tag.className = 'tag is-info';
        tag.textContent = symbol.replace('USDT', '/USDT');
        enabledSymbolsDisplay.appendChild(tag);
    });
    
    // 如果没有启用的币种，显示提示信息
    if (enabledSymbols.length === 0) {
        const noSymbolsMsg = document.createElement('span');
        noSymbolsMsg.className = 'has-text-grey-light';
        noSymbolsMsg.textContent = '暂无启用的币种';
        enabledSymbolsDisplay.appendChild(noSymbolsMsg);
    }
}


// 切换合约策略状态
async function toggleFuturesStrategy(strategyName, enabled) {
    try {
        const response = await fetch('/api/futures/strategies/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                strategy_name: strategyName,
                enabled: enabled
            })
        });

        if (response.ok) {
            showSuccess(`策略 ${strategyName} ${enabled ? '已启用' : '已禁用'}`);
            // 更新本地数据
            const strategy = futuresStrategies.find(s => s.name === strategyName);
            if (strategy) {
                strategy.enabled = enabled;
            }
            updateFuturesStrategyStatistics(futuresStrategies);
        } else {
            const error = await response.json();
            showError(`更新策略失败: ${error.message}`);
            // 恢复复选框状态
            const checkbox = document.querySelector(`input[onchange*="${strategyName}"]`);
            if (checkbox) {
                checkbox.checked = !enabled;
            }
        }
    } catch (error) {
        console.error('切换策略状态出错:', error);
        showError('切换策略状态时发生错误');
        // 恢复复选框状态
        const checkbox = document.querySelector(`input[onchange*="${strategyName}"]`);
        if (checkbox) {
            checkbox.checked = !enabled;
        }
    }
}

// 在页面加载完成后初始化合约策略管理
document.addEventListener('DOMContentLoaded', function() {
    // 延迟初始化，确保DOM完全加载
    setTimeout(() => {
        if (document.getElementById('show-futures-symbols')) {
            initializeFuturesStrategyManagement();
        }
    }, 100);
});