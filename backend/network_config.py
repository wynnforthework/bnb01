#!/usr/bin/env python3
"""
网络配置模块
处理SSL错误、代理问题和网络超时，提供健壮的重试机制
"""

import requests
import time
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import SSLError, ProxyError, ReadTimeoutError
import ssl
import socket
import random
import urllib3

class NetworkConfig:
    """网络配置类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 重试配置 - 更激进的设置
        self.max_retries = 8  # 增加重试次数
        self.backoff_factor = 0.3  # 减少退避因子，更快重试
        self.status_forcelist = [500, 502, 503, 504, 429, 408]
        
        # 超时配置 - 更宽松的设置
        self.connect_timeout = 15
        self.read_timeout = 60
        
        # 禁用代理设置
        self.proxy_settings = {
            'http': None,
            'https': None
        }
        
        # SSL配置 - 改进的SSL处理
        self.ssl_verify = True  # 启用SSL验证但使用自定义上下文
        self.ssl_context = self._create_ssl_context()
        
        # 禁用SSL警告
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    def _create_ssl_context(self):
        """创建改进的SSL上下文"""
        try:
            # 创建更兼容的SSL上下文
            ssl_context = ssl.create_default_context()
            
            # 设置更宽松的SSL选项
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 添加更多SSL选项以提高兼容性
            ssl_context.options |= ssl.OP_NO_SSLv2
            ssl_context.options |= ssl.OP_NO_SSLv3
            ssl_context.options |= ssl.OP_NO_TLSv1
            ssl_context.options |= ssl.OP_NO_TLSv1_1
            
            # 设置密码套件
            ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')
            
            # 设置最小和最大TLS版本
            ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
            
            return ssl_context
        except Exception as e:
            self.logger.warning(f"创建SSL上下文失败: {e}")
            return None
    
    def create_session(self):
        """创建配置好的requests会话"""
        session = requests.Session()
        
        # 配置重试策略 - 更激进的设置
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=self.status_forcelist,
            backoff_factor=self.backoff_factor,
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
            respect_retry_after_header=True,
            raise_on_status=False
        )
        
        # 配置适配器
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 设置超时
        session.timeout = (self.connect_timeout, self.read_timeout)
        
        # 设置SSL配置
        session.verify = self.ssl_verify
        
        # 禁用代理
        session.proxies = self.proxy_settings
        
        # 设置用户代理
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return session
    
    def create_binance_session(self):
        """创建专门用于币安API的会话"""
        session = self.create_session()
        
        # 币安特定的配置
        session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        return session
    
    def handle_network_error(self, error, operation="API请求"):
        """处理网络错误"""
        error_msg = str(error)
        
        if "SSL" in error_msg or "SSLError" in error_msg:
            self.logger.warning(f"{operation} SSL错误: {error_msg}")
            return "SSL_ERROR"
        elif "ProxyError" in error_msg or "proxy" in error_msg.lower():
            self.logger.warning(f"{operation} 代理错误: {error_msg}")
            return "PROXY_ERROR"
        elif "Read timed out" in error_msg or "timeout" in error_msg.lower():
            self.logger.warning(f"{operation} 超时错误: {error_msg}")
            return "TIMEOUT_ERROR"
        elif "Connection" in error_msg:
            self.logger.warning(f"{operation} 连接错误: {error_msg}")
            return "CONNECTION_ERROR"
        else:
            self.logger.error(f"{operation} 未知网络错误: {error_msg}")
            return "UNKNOWN_ERROR"
    
    def retry_with_backoff(self, func, *args, **kwargs):
        """带退避的重试机制 - 改进版本"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # 添加随机延迟以避免同时请求
                if attempt > 0:
                    jitter = random.uniform(0.1, 0.5)
                    time.sleep(jitter)
                
                return func(*args, **kwargs)
            except (requests.exceptions.RequestException, 
                   SSLError, ProxyError, ReadTimeoutError,
                   socket.error, ssl.SSLError) as e:
                last_error = e
                error_type = self.handle_network_error(e)
                
                if attempt < self.max_retries - 1:
                    # 指数退避 + 随机抖动
                    wait_time = self.backoff_factor * (2 ** attempt) + random.uniform(0, 1)
                    self.logger.info(f"第{attempt + 1}次重试失败，等待{wait_time:.1f}秒后重试...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"重试{self.max_retries}次后仍然失败")
        
        raise last_error

class BinanceNetworkConfig(NetworkConfig):
    """币安网络配置类"""
    
    def __init__(self):
        super().__init__()
        
        # 币安特定的配置 - 更宽松的设置
        self.max_retries = 5  # 币安API重试次数
        self.connect_timeout = 20
        self.read_timeout = 90
        
    def create_session(self):
        """创建币安专用的会话"""
        session = super().create_session()
        
        # 币安特定的头部
        session.headers.update({
            'X-MBX-APIKEY': '',  # 将在使用时设置
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        
        return session
    
    def test_connection(self, testnet=True):
        """测试币安连接"""
        try:
            if testnet:
                url = "https://testnet.binance.vision/api/v3/ping"
            else:
                url = "https://api.binance.com/api/v3/ping"
            
            session = self.create_session()
            response = session.get(url, timeout=(10, 30))
            
            if response.status_code == 200:
                self.logger.info("币安连接测试成功")
                return True
            else:
                self.logger.warning(f"币安连接测试失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"币安连接测试异常: {e}")
            return False

# 全局网络配置实例
network_config = NetworkConfig()
binance_network_config = BinanceNetworkConfig()
