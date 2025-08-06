#!/usr/bin/env python3
"""
客户端管理器 - 单例模式管理币安客户端
"""

import logging
from typing import Dict, Optional
from backend.binance_client import BinanceClient

class ClientManager:
    """客户端管理器 - 单例模式"""
    
    _instance = None
    _clients: Dict[str, BinanceClient] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClientManager, cls).__new__(cls)
            cls._instance.logger = logging.getLogger(__name__)
        return cls._instance
    
    def get_client(self, trading_mode: str = 'SPOT') -> BinanceClient:
        """
        获取币安客户端实例
        
        Args:
            trading_mode: 'SPOT' 或 'FUTURES'
            
        Returns:
            BinanceClient实例
        """
        trading_mode = trading_mode.upper()
        
        # 如果客户端已存在，直接返回
        if trading_mode in self._clients:
            return self._clients[trading_mode]
        
        # 创建新的客户端实例
        try:
            client = BinanceClient(trading_mode=trading_mode)
            self._clients[trading_mode] = client
            self.logger.info(f"创建新的{trading_mode}客户端实例")
            return client
        except Exception as e:
            self.logger.error(f"创建{trading_mode}客户端失败: {e}")
            raise
    
    def get_spot_client(self) -> BinanceClient:
        """获取现货客户端"""
        return self.get_client('SPOT')
    
    def get_futures_client(self) -> BinanceClient:
        """获取合约客户端"""
        return self.get_client('FUTURES')
    
    def clear_clients(self):
        """清除所有客户端实例"""
        self._clients.clear()
        self.logger.info("已清除所有客户端实例")
    
    def get_client_info(self) -> Dict[str, str]:
        """获取客户端信息"""
        info = {}
        for mode, client in self._clients.items():
            info[mode] = {
                'trading_mode': client.trading_mode,
                'initialized': True
            }
        return info

# 全局客户端管理器实例
client_manager = ClientManager()