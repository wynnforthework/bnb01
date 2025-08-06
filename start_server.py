#!/usr/bin/env python3
"""
启动服务器并测试功能
"""

import logging
from app import app, socketio

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    print("🚀 启动量化交易系统...")
    print("")
    print("📄 页面访问地址:")
    print("  现货交易: http://127.0.0.1:5000/")
    print("  合约交易: http://127.0.0.1:5000/futures")
    print("")
    print("🔧 API端点:")
    print("  现货账户: http://127.0.0.1:5000/api/account")
    print("  现货投资组合: http://127.0.0.1:5000/api/portfolio")
    print("  现货市场数据: http://127.0.0.1:5000/api/market/BTCUSDT")
    print("  合约账户: http://127.0.0.1:5000/api/futures/account")
    print("  合约持仓: http://127.0.0.1:5000/api/futures/positions")
    print("")
    print("⚠️ 按 Ctrl+C 停止服务器")
    print("="*50)
    
    try:
        socketio.run(app, debug=True, host='127.0.0.1', port=5000)
    except KeyboardInterrupt:
        print("\n\n⏹️ 服务器已停止")
    except Exception as e:
        print(f"\n❌ 服务器启动失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")

if __name__ == '__main__':
    main()