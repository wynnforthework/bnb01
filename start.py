#!/usr/bin/env python3
"""
启动量化交易系统
"""

import logging
import sys
import os

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """主函数"""
    try:
        print("🚀 启动量化交易系统...")
        print("📊 系统信息:")
        print(f"  Python版本: {sys.version}")
        print(f"  工作目录: {os.getcwd()}")
        
        # 检查必要的文件
        required_files = [
            'app.py',
            'config/config.py',
            '.env',
            'backend/trading_engine.py',
            'backend/binance_client.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print("❌ 缺少必要文件:")
            for file in missing_files:
                print(f"  - {file}")
            return False
        
        print("✅ 文件检查完成")
        
        # 导入并启动应用
        print("🔧 初始化系统组件...")
        
        try:
            import app
            print("✅ 应用模块加载成功")
        except Exception as e:
            print(f"❌ 应用模块加载失败: {e}")
            return False
        
        print("\n🌐 Web服务器信息:")
        print("  现货交易页面: http://localhost:5000/")
        print("  合约交易页面: http://localhost:5000/futures")
        print("\n💡 使用说明:")
        print("  1. 打开浏览器访问上述地址")
        print("  2. 现货和合约交易页面完全独立")
        print("  3. 可以同时或分别使用两种交易模式")
        print("  4. 按 Ctrl+C 停止服务器")
        
        print("\n🚀 启动Web服务器...")
        
        # 启动Flask应用
        app.socketio.run(app.app, debug=False, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  收到停止信号，正在关闭系统...")
        print("✅ 系统已安全关闭")
        return True
        
    except Exception as e:
        print(f"❌ 系统启动失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)