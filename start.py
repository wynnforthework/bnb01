#!/usr/bin/env python3
"""
加密货币量化交易系统启动脚本
"""

import os
import sys
import logging
from datetime import datetime

def setup_logging():
    """设置日志"""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f'trading_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_environment():
    """检查环境配置"""
    # 确保加载.env文件
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'BINANCE_API_KEY',
        'BINANCE_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.strip() == '' or 'your_' in value.lower():
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ 缺少必要的环境变量:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n请检查 .env 文件配置")
        return False
    
    print("✅ 环境变量检查通过")
    return True

def check_dependencies():
    """检查依赖包"""
    try:
        import flask
        import binance
        import pandas
        import numpy
        import sqlalchemy
        print("✅ 依赖包检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def main():
    """主函数"""
    print("🚀 启动加密货币量化交易系统...")
    print("=" * 50)
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 检查环境
    if not check_dependencies():
        sys.exit(1)
    
    if not check_environment():
        sys.exit(1)
    
    # 启动应用
    try:
        from app import app, socketio
        logger.info("系统启动成功")
        print("\n🎉 系统启动成功!")
        print("📊 Web界面: http://localhost:5000")
        print("📝 日志文件: logs/")
        print("\n按 Ctrl+C 停止系统")
        print("=" * 50)
        
        socketio.run(
            app, 
            debug=False, 
            host='0.0.0.0', 
            port=5000,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        logger.info("用户停止系统")
        print("\n👋 系统已停止")
    except Exception as e:
        logger.error(f"系统启动失败: {e}")
        print(f"❌ 系统启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()