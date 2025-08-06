#!/usr/bin/env python3
"""
测试数据库访问修复
"""

import logging
from backend.risk_manager import RiskManager

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_database_access():
    """测试数据库访问"""
    print("🔍 测试数据库访问修复...")
    
    try:
        # 创建风险管理器
        risk_manager = RiskManager()
        print("✅ 风险管理器创建成功")
        
        # 测试策略胜率获取
        win_rate = risk_manager._get_strategy_win_rate('BTCUSDT')
        print(f"📊 BTCUSDT策略胜率: {win_rate:.2%}")
        
        # 测试平均盈利获取
        avg_win = risk_manager._get_average_win('BTCUSDT')
        print(f"💰 BTCUSDT平均盈利: {avg_win:.4f}")
        
        # 测试平均亏损获取
        avg_loss = risk_manager._get_average_loss('BTCUSDT')
        print(f"📉 BTCUSDT平均亏损: {avg_loss:.4f}")
        
        # 测试当前日损失获取
        daily_loss = risk_manager._get_current_daily_loss()
        print(f"📅 当前日损失: {daily_loss:.2%}")
        
        # 测试风险检查
        can_trade, message = risk_manager.check_risk_limits('BTCUSDT', 0.001, 50000)
        print(f"🛡️ 风险检查结果: {can_trade}, 消息: {message}")
        
        print("\n✅ 数据库访问测试完成，所有功能正常！")
        return True
        
    except Exception as e:
        print(f"❌ 数据库访问测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False

if __name__ == '__main__':
    test_database_access()