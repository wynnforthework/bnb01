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
    console.log('🔧 开始绑定合约交易事件...');
    
    try {
        // 启动合约交易
        const startButton = document.getElementById('start-futures-trading');
        if (startButton) {
            startButton.addEventListener('click', function() {
                console.log('🚀 启动合约交易按钮被点击');
                startFuturesTrading();
            });
            console.log('✅ 启动合约交易按钮事件绑定成功');
        } else {
            console.error('❌ 未找到启动合约交易按钮');
        }
        
        // 停止合约交易
        const stopButton = document.getElementById('stop-futures-trading');
        if (stopButton) {
            stopButton.addEventListener('click', function() {
                console.log('🛑 停止合约交易按钮被点击');
                stopFuturesTrading();
            });
            console.log('✅ 停止合约交易按钮事件绑定成功');
        } else {
            console.error('❌ 未找到停止合约交易按钮');
        }
        
        // 更新配置
        const updateButton = document.getElementById('update-futures-config');
        if (updateButton) {
            updateButton.addEventListener('click', function() {
                console.log('⚙️ 更新配置按钮被点击');
                updateFuturesConfig();
            });
            console.log('✅ 更新配置按钮事件绑定成功');
        } else {
            console.error('❌ 未找到更新配置按钮');
        }
        
        // 刷新数据
        const refreshButton = document.getElementById('refresh-futures-data');
        if (refreshButton) {
            refreshButton.addEventListener('click', function() {
                console.log('🔄 刷新数据按钮被点击');
                loadFuturesInitialData();
            });
            console.log('✅ 刷新数据按钮事件绑定成功');
        } else {
            console.error('❌ 未找到刷新数据按钮');
        }
        
        // 手动下单
        const manualOrderButton = document.getElementById('manual-futures-order');
        if (manualOrderButton) {
            manualOrderButton.addEventListener('click', function() {
                console.log('📝 手动下单按钮被点击');
                openModal('futuresOrderModal');
            });
            console.log('✅ 手动下单按钮事件绑定成功');
        } else {
            console.error('❌ 未找到手动下单按钮');
        }
        
        // 查看持仓
        const viewPositionsButton = document.getElementById('view-futures-positions');
        if (viewPositionsButton) {
            viewPositionsButton.addEventListener('click', function() {
                console.log('📊 查看持仓按钮被点击');
                openModal('futuresPositionsModal');
            });
            console.log('✅ 查看持仓按钮事件绑定成功');
        } else {
            console.error('❌ 未找到查看持仓按钮');
        }
        
        // 杠杆变化
        const leverageSelect = document.getElementById('futures-leverage');
        if (leverageSelect) {
            leverageSelect.addEventListener('change', function() {
                currentLeverage = parseInt(this.value);
                updateFuturesLeverageStatus();
            });
            console.log('✅ 杠杆选择事件绑定成功');
        } else {
            console.error('❌ 未找到杠杆选择元素');
        }
        
        console.log('✅ 合约交易事件绑定完成');
        
    } catch (error) {
        console.error('❌ 绑定合约交易事件时出错:', error);
    }
}

// 加载合约交易初始数据
function loadFuturesInitialData() {
    console.log('🔄 开始加载合约交易初始数据...');
    
    try {
        loadFuturesAccountData();
        loadFuturesPositions();
        loadFuturesTradesData();
        loadSpotConfigForFutures(); // 加载现货配置用于合约交易
        
        console.log('✅ 合约交易初始数据加载完成');
    } catch (error) {
        console.error('❌ 加载合约交易初始数据失败:', error);
    }
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
        // 获取现货配置
        const configResponse = await fetch('/api/futures/spot-config');
        const configData = await configResponse.json();
        
        if (!configData.success) {
            showError('获取现货配置失败: ' + configData.message);
            return;
        }
        
        if (configData.total_strategies === 0) {
            showError('请先在现货交易中启用至少一个策略');
            return;
        }
        
        const response = await fetch('/api/futures/trading/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                leverage: currentLeverage,
                symbols: selectedSymbols,
                enabled_strategies: configData.enabled_strategies
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(`合约交易已启动，使用现货策略: ${configData.enabled_strategies.join(', ')}`);
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

// 加载现货配置用于合约交易
async function loadSpotConfigForFutures() {
    try {
        console.log('开始加载现货配置用于合约交易...');
        
        // 使用新的API端点获取现货配置
        const response = await fetch('/api/futures/spot-config');
        const data = await response.json();
        
        if (data.success) {
            // 更新全局变量
            selectedSymbols = data.symbols;
            
            console.log('现货配置加载成功:', {
                symbols: data.symbols,
                enabledStrategies: data.enabled_strategies,
                totalSymbols: data.total_symbols,
                totalStrategies: data.total_strategies
            });
            
            // 更新合约交易控制面板显示
            updateFuturesControlPanel(data.symbols, data.enabled_strategies);
            
        } else {
            console.error('加载现货配置失败:', data.message);
        }
    } catch (error) {
        console.error('加载现货配置异常:', error);
    }
}

// 更新合约交易控制面板显示
function updateFuturesControlPanel(symbols, enabledStrategies) {
    console.log('🔄 更新合约交易控制面板显示...');
    console.log('币种列表:', symbols);
    console.log('启用策略:', enabledStrategies);
    
    // 更新币种显示
    const enabledSymbolsDisplay = document.getElementById('futures-enabled-symbols-display');
    if (enabledSymbolsDisplay) {
        console.log('✅ 找到币种显示容器');
        enabledSymbolsDisplay.innerHTML = '';
        
        if (symbols && symbols.length > 0) {
            // 显示前5个币种，其余的用数字表示
            const displaySymbols = symbols.slice(0, 5);
            const remainingCount = symbols.length - 5;
            
            displaySymbols.forEach(symbol => {
                const tag = document.createElement('span');
                tag.className = 'tag is-info';
                tag.textContent = symbol.replace('USDT', '/USDT');
                enabledSymbolsDisplay.appendChild(tag);
                console.log('添加币种标签:', symbol);
            });
            
            if (remainingCount > 0) {
                const moreTag = document.createElement('span');
                moreTag.className = 'tag is-light';
                moreTag.textContent = `+${remainingCount}`;
                enabledSymbolsDisplay.appendChild(moreTag);
                console.log('添加更多币种标签:', `+${remainingCount}`);
            }
        } else {
            // 如果没有币种，显示提示
            const noSymbolsTag = document.createElement('span');
            noSymbolsTag.className = 'tag is-warning';
            noSymbolsTag.textContent = '未选择币种';
            enabledSymbolsDisplay.appendChild(noSymbolsTag);
            console.log('显示未选择币种提示');
        }
    } else {
        console.error('❌ 未找到币种显示容器: futures-enabled-symbols-display');
    }
    
    // 更新币种状态显示
    const symbolsStatus = document.getElementById('futures-symbols-status');
    if (symbolsStatus) {
        if (symbols && symbols.length > 0) {
            const displayText = symbols.length > 3 ? 
                `${symbols.slice(0, 3).map(s => s.replace('USDT', '')).join(', ')}...` :
                symbols.map(s => s.replace('USDT', '')).join(', ');
            symbolsStatus.textContent = displayText;
            console.log('更新币种状态显示:', displayText);
        } else {
            symbolsStatus.textContent = '未选择币种';
            console.log('更新币种状态显示: 未选择币种');
        }
    } else {
        console.error('❌ 未找到币种状态显示元素: futures-symbols-status');
    }
    
    // 更新策略状态显示（如果有的话）
    const modeStatus = document.getElementById('futures-mode-status');
    if (modeStatus && enabledStrategies && enabledStrategies.length > 0) {
        const strategyText = enabledStrategies.join(', ');
        modeStatus.textContent = `合约模式 (${strategyText})`;
        console.log('更新策略状态显示:', `合约模式 (${strategyText})`);
    } else if (modeStatus) {
        modeStatus.textContent = '合约模式';
        console.log('更新策略状态显示: 合约模式');
    } else {
        console.error('❌ 未找到模式状态显示元素: futures-mode-status');
    }
    
    console.log('✅ 合约交易控制面板显示更新完成');
}

// ==================== 合约策略管理功能 ====================









