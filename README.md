# 加密货币量化交易系统

基于Binance API的加密货币量化交易系统，包含完整的Web可视化界面。

## 功能特性

### 🎯 核心功能
- 🔄 **自动化交易**: 支持多种交易策略的24/7自动执行
- 📊 **实时数据**: 实时获取Binance市场数据、订单簿和账户信息
- 💹 **策略管理**: 内置MA、RSI、机器学习和深度学习策略
- 🛡️ **风险控制**: 动态止损止盈、VaR风险管理、相关性控制
- 📈 **可视化界面**: 现代化Web界面，实时图表和风险监控
- 🧠 **机器学习**: 随机森林、梯度提升、LSTM深度学习策略
- 📋 **回测分析**: 完整的策略回测和性能分析系统
- 🔍 **数据收集**: 自动收集和存储历史数据及技术指标

### 🚀 交易策略
1. **移动平均线策略 (MA Strategy)**
   - 短期和长期移动平均线交叉信号
   - 金叉买入，死叉卖出
   - 可配置参数：短期窗口、长期窗口、止损止盈

2. **RSI策略 (RSI Strategy)**
   - 基于相对强弱指数的超买超卖信号
   - RSI < 30 买入，RSI > 70 卖出
   - 支持背离检测和多时间框架分析

3. **机器学习策略 (ML Strategy)**
   - 随机森林、梯度提升、逻辑回归模型
   - 自动特征工程和特征选择
   - 模型自动重训练和性能监控
   - 支持多种技术指标和市场特征

4. **LSTM深度学习策略**
   - 基于TensorFlow/Keras的深度学习模型
   - 时间序列预测和序列模式识别
   - 自适应学习和在线更新

### 🛡️ 风险管理系统
- **仓位管理**: Kelly公式最优仓位、波动率调整
- **风险指标**: VaR、最大回撤、夏普比率、Beta系数
- **动态止损**: ATR基础止损、支撑阻力位止损
- **风险限制**: 单资产权重限制、相关性控制、流动性检查
- **实时监控**: 风险警告、系统状态监控

### 📊 数据收集与分析
- **历史数据**: 多时间周期K线数据自动收集
- **实时数据**: WebSocket实时价格和订单簿数据
- **技术指标**: SMA、EMA、RSI、MACD、布林带、ATR等
- **数据存储**: SQLite数据库，支持扩展到PostgreSQL/MyS

## 系统架构

```
crypto-trading-system/
├── backend/              # 后端核心模块
│   ├── binance_client.py # Binance API客户端
│   ├── database.py       # 数据库管理
│   └── trading_engine.py # 交易引擎
├── strategies/           # 交易策略
│   ├── base_strategy.py  # 策略基类
│   ├── ma_strategy.py    # 移动平均线策略
│   └── rsi_strategy.py   # RSI策略
├── config/              # 配置文件
│   └── config.py        # 系统配置
├── templates/           # HTML模板
│   └── index.html       # 主页面
├── static/              # 静态资源
│   ├── css/style.css    # 样式文件
│   └── js/app.js        # 前端JavaScript
└── app.py               # Flask应用主文件
```

## 安装部署

### 1. 环境要求
- Python 3.8+
- Redis (可选，用于缓存)

### 2. 安装依赖

**方法一：自动修复安装**
```bash
python fix_pip_and_install.py
```

**方法二：简化安装（推荐）**
```bash
python install_simple.py
```

**方法三：手动安装**
```bash
# 如果遇到pip问题，先升级pip
python -m pip install --upgrade pip

# 使用国内镜像安装（网络较慢时推荐）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ -r requirements.txt

# 或者逐个安装核心包
pip install python-binance pandas numpy flask flask-cors flask-socketio sqlalchemy python-dotenv psutil
```

### 3. 配置环境变量
复制 `.env.example` 到 `.env` 并填入你的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
# Binance API配置
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
BINANCE_TESTNET=True  # 测试网络，生产环境设为False

# 数据库配置
DATABASE_URL=sqlite:///trading.db

# Flask配置
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 4. 获取Binance API密钥
1. 登录 [Binance](https://www.binance.com)
2. 进入账户设置 -> API管理
3. 创建新的API密钥
4. 启用现货交易权限
5. 将API Key和Secret填入 `.env` 文件

**注意**: 建议先在测试网络测试，测试网络地址：https://testnet.binance.vision/

### 5. 启动应用
```bash
python app.py
```

访问 http://localhost:5000 查看Web界面

## 使用说明

### Web界面功能

1. **控制面板**
   - 启动/停止交易
   - 刷新数据
   - 查看交易状态

2. **账户信息**
   - 显示各币种余额
   - 实时更新账户状态

3. **投资组合**
   - 总资产概览
   - 持仓详情
   - 未实现盈亏

4. **交易历史**
   - 历史交易记录
   - 盈亏统计
   - 策略表现

5. **市场数据**
   - 实时价格图表
   - 成交量显示
   - 多币种切换

### 策略配置

在 `backend/trading_engine.py` 中可以调整策略参数：

```python
# MA策略参数
ma_strategy = MovingAverageStrategy(
    symbol=symbol,
    parameters={
        'short_window': 10,    # 短期均线周期
        'long_window': 30,     # 长期均线周期
        'stop_loss': 0.02,     # 止损比例 2%
        'take_profit': 0.05,   # 止盈比例 5%
        'position_size': 0.05  # 仓位大小 5%
    }
)

# RSI策略参数
rsi_strategy = RSIStrategy(
    symbol=symbol,
    parameters={
        'rsi_period': 14,      # RSI计算周期
        'oversold': 30,        # 超卖阈值
        'overbought': 70,      # 超买阈值
        'stop_loss': 0.02,     # 止损比例
        'take_profit': 0.05,   # 止盈比例
        'position_size': 0.05  # 仓位大小
    }
)
```

## 安全注意事项

1. **API权限**: 只授予必要的交易权限，不要开启提现权限
2. **IP白名单**: 在Binance设置API的IP白名单
3. **测试环境**: 先在测试网络充分测试
4. **资金管理**: 不要投入超过承受能力的资金
5. **监控**: 定期检查交易状态和账户安全

## 开发扩展

### 添加新策略
1. 继承 `BaseStrategy` 类
2. 实现 `generate_signal()` 方法
3. 实现 `calculate_position_size()` 方法
4. 在交易引擎中注册新策略

### 数据库扩展
系统使用SQLAlchemy ORM，支持多种数据库：
- SQLite (默认)
- PostgreSQL
- MySQL

### API扩展
可以轻松添加新的API端点来扩展功能。

## 常见问题

### Q: 安装依赖时出现错误怎么办？
A: 
1. 先运行 `python install_simple.py` 使用简化安装
2. 如果仍有问题，尝试升级pip: `python -m pip install --upgrade pip`
3. 使用国内镜像: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple/ 包名`
4. 检查Python版本是否为3.8+

### Q: 如何切换到实盘交易？
A: 将 `.env` 文件中的 `BINANCE_TESTNET=False`，并使用实盘API密钥。

### Q: 策略不执行交易怎么办？
A: 检查API权限、余额是否充足、策略参数是否合理。

### Q: 如何备份交易数据？
A: 定期备份 `trading.db` 数据库文件。

### Q: 系统支持哪些交易对？
A: 默认支持 BTC/USDT、ETH/USDT、BNB/USDT、ADA/USDT，可在配置中修改。

### Q: 出现"can't open file"错误？
A: 这通常是pip损坏导致的，运行 `python fix_pip_and_install.py` 修复。

## 免责声明

本系统仅供学习和研究使用。加密货币交易存在高风险，可能导致资金损失。使用本系统进行实盘交易的所有风险由用户自行承担。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 联系方式

如有问题或建议，请通过GitHub Issues联系。