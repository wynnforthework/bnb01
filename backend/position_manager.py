#!/usr/bin/env python3
"""
持仓管理器 - 自动减仓和再平衡功能
"""

import logging
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from backend.binance_client import BinanceClient
from backend.risk_manager import RiskManager
from backend.database import DatabaseManager

class PositionManager:
    """持仓管理器 - 负责自动减仓和投资组合再平衡"""
    
    def __init__(self, trading_mode='SPOT'):
        self.trading_mode = trading_mode.upper()
        self.binance_client = BinanceClient(trading_mode=trading_mode)
        self.risk_manager = RiskManager()
        self.db_manager = DatabaseManager()
        self.logger = logging.getLogger(__name__)
        
        # 减仓配置
        self.auto_reduce_enabled = True
        self.max_position_weight = 0.25  # 最大持仓权重25%
        self.reduction_threshold = 0.30  # 超过30%开始减仓
        self.reduction_step = 0.05  # 每次减仓5%
        
        # 再平衡配置
        self.rebalance_enabled = True
        self.rebalance_threshold = 0.10  # 偏离目标权重10%时再平衡
        self.min_rebalance_amount = 10.0  # 最小再平衡金额$10
        
        self.logger.info(f"持仓管理器初始化完成，模式: {self.trading_mode}")
    
    def check_and_reduce_positions(self) -> Dict[str, Dict]:
        """检查并执行自动减仓"""
        results = {}
        
        try:
            # 获取所有持仓
            positions = self._get_all_positions()
            portfolio_value = self.risk_manager._get_portfolio_value()
            
            self.logger.info(f"检查持仓减仓，投资组合总值: ${portfolio_value:.2f}")
            
            for symbol, position in positions.items():
                if position['quantity'] <= 0:
                    continue
                
                # 计算持仓权重
                position_value = position['quantity'] * position['current_price']
                position_weight = position_value / portfolio_value if portfolio_value > 0 else 0
                
                self.logger.info(f"{symbol} 持仓权重: {position_weight:.1%}")
                
                # 检查是否需要减仓
                if position_weight > self.reduction_threshold:
                    reduction_result = self._reduce_position(
                        symbol, position, position_weight, portfolio_value
                    )
                    results[symbol] = reduction_result
                    
                    if reduction_result['success']:
                        self.logger.info(f"✅ {symbol} 自动减仓成功: {reduction_result['reduced_quantity']:.6f}")
                    else:
                        self.logger.warning(f"❌ {symbol} 自动减仓失败: {reduction_result['error']}")
                else:
                    self.logger.info(f"✅ {symbol} 持仓权重合理: {position_weight:.1%}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"检查持仓减仓失败: {e}")
            return {}
    
    def _reduce_position(self, symbol: str, position: Dict, current_weight: float, 
                        portfolio_value: float) -> Dict:
        """执行减仓操作"""
        try:
            current_price = position['current_price']
            current_quantity = position['quantity']
            
            # 计算目标权重和需要减仓的数量
            target_weight = self.max_position_weight
            target_value = portfolio_value * target_weight
            target_quantity = target_value / current_price
            
            # 计算需要减仓的数量
            reduce_quantity = current_quantity - target_quantity
            
            # 确保减仓数量合理
            if reduce_quantity <= 0:
                return {
                    'success': False,
                    'error': '减仓数量计算错误',
                    'reduced_quantity': 0
                }
            
            # 限制单次减仓数量，避免大幅波动
            max_reduction = current_quantity * self.reduction_step
            actual_reduction = min(reduce_quantity, max_reduction)
            
            self.logger.info(f"减仓计算 - {symbol}:")
            self.logger.info(f"  当前权重: {current_weight:.1%}")
            self.logger.info(f"  目标权重: {target_weight:.1%}")
            self.logger.info(f"  当前数量: {current_quantity:.6f}")
            self.logger.info(f"  目标数量: {target_quantity:.6f}")
            self.logger.info(f"  建议减仓: {reduce_quantity:.6f}")
            self.logger.info(f"  实际减仓: {actual_reduction:.6f}")
            
            # 执行减仓交易
            if self.trading_mode == 'FUTURES':
                order = self.binance_client.place_order(
                    symbol=symbol,
                    side='SELL',
                    quantity=actual_reduction,
                    position_side='LONG',
                    reduce_only=True
                )
            else:
                order = self.binance_client.place_order(
                    symbol=symbol,
                    side='SELL',
                    quantity=actual_reduction
                )
            
            if order:
                # 计算减仓收益
                reduction_value = actual_reduction * current_price
                profit_loss = (current_price - position.get('avg_price', current_price)) * actual_reduction
                
                # 更新数据库
                self.db_manager.add_trade(
                    symbol=symbol,
                    side='SELL',
                    quantity=actual_reduction,
                    price=current_price,
                    strategy='PositionManager_AutoReduce',
                    profit_loss=profit_loss
                )
                
                # 更新持仓记录
                remaining_quantity = current_quantity - actual_reduction
                if remaining_quantity > 0:
                    self.db_manager.update_position(
                        symbol=symbol,
                        quantity=remaining_quantity,
                        avg_price=position.get('avg_price', current_price),
                        current_price=current_price
                    )
                else:
                    # 如果全部卖出，删除持仓记录
                    from backend.database import Position
                    position_record = self.db_manager.session.query(Position).filter_by(symbol=symbol).first()
                    if position_record:
                        self.db_manager.session.delete(position_record)
                        self.db_manager.session.commit()
                
                return {
                    'success': True,
                    'reduced_quantity': actual_reduction,
                    'reduction_value': reduction_value,
                    'profit_loss': profit_loss,
                    'remaining_quantity': remaining_quantity,
                    'new_weight': (remaining_quantity * current_price) / portfolio_value if portfolio_value > 0 else 0
                }
            else:
                return {
                    'success': False,
                    'error': '下单失败',
                    'reduced_quantity': 0
                }
                
        except Exception as e:
            self.logger.error(f"减仓操作失败 {symbol}: {e}")
            return {
                'success': False,
                'error': str(e),
                'reduced_quantity': 0
            }
    
    def rebalance_portfolio(self, target_weights: Dict[str, float]) -> Dict[str, Dict]:
        """投资组合再平衡"""
        results = {}
        
        try:
            positions = self._get_all_positions()
            portfolio_value = self.risk_manager._get_portfolio_value()
            
            self.logger.info(f"开始投资组合再平衡，总值: ${portfolio_value:.2f}")
            
            for symbol, target_weight in target_weights.items():
                current_position = positions.get(symbol, {'quantity': 0, 'current_price': 0})
                current_quantity = current_position['quantity']
                current_price = current_position['current_price']
                
                # 计算当前权重
                current_value = current_quantity * current_price
                current_weight = current_value / portfolio_value if portfolio_value > 0 else 0
                
                # 计算目标数量
                target_value = portfolio_value * target_weight
                target_quantity = target_value / current_price
                
                # 计算调整数量
                adjustment_quantity = target_quantity - current_quantity
                adjustment_value = abs(adjustment_quantity * current_price)
                
                # 检查是否需要调整
                if abs(current_weight - target_weight) > self.rebalance_threshold and adjustment_value > self.min_rebalance_amount:
                    if adjustment_quantity > 0:
                        # 需要买入
                        result = self._buy_position(symbol, adjustment_quantity, current_price, 'Rebalance')
                    else:
                        # 需要卖出
                        result = self._sell_position(symbol, abs(adjustment_quantity), current_price, 'Rebalance')
                    
                    results[symbol] = result
                    
                    if result['success']:
                        self.logger.info(f"✅ {symbol} 再平衡成功: {adjustment_quantity:+.6f}")
                    else:
                        self.logger.warning(f"❌ {symbol} 再平衡失败: {result['error']}")
                else:
                    self.logger.info(f"✅ {symbol} 权重合理，无需调整")
            
            return results
            
        except Exception as e:
            self.logger.error(f"投资组合再平衡失败: {e}")
            return {}
    
    def _buy_position(self, symbol: str, quantity: float, price: float, reason: str) -> Dict:
        """买入持仓"""
        try:
            if self.trading_mode == 'FUTURES':
                order = self.binance_client.place_order(
                    symbol=symbol,
                    side='BUY',
                    quantity=quantity,
                    position_side='LONG'
                )
            else:
                order = self.binance_client.place_order(
                    symbol=symbol,
                    side='BUY',
                    quantity=quantity
                )
            
            if order:
                # 更新数据库
                self.db_manager.add_trade(
                    symbol=symbol,
                    side='BUY',
                    quantity=quantity,
                    price=price,
                    strategy=f'PositionManager_{reason}'
                )
                
                return {
                    'success': True,
                    'quantity': quantity,
                    'value': quantity * price
                }
            else:
                return {
                    'success': False,
                    'error': '买入订单失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _sell_position(self, symbol: str, quantity: float, price: float, reason: str) -> Dict:
        """卖出持仓"""
        try:
            if self.trading_mode == 'FUTURES':
                order = self.binance_client.place_order(
                    symbol=symbol,
                    side='SELL',
                    quantity=quantity,
                    position_side='LONG',
                    reduce_only=True
                )
            else:
                order = self.binance_client.place_order(
                    symbol=symbol,
                    side='SELL',
                    quantity=quantity
                )
            
            if order:
                # 更新数据库
                self.db_manager.add_trade(
                    symbol=symbol,
                    side='SELL',
                    quantity=quantity,
                    price=price,
                    strategy=f'PositionManager_{reason}'
                )
                
                return {
                    'success': True,
                    'quantity': quantity,
                    'value': quantity * price
                }
            else:
                return {
                    'success': False,
                    'error': '卖出订单失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_all_positions(self) -> Dict[str, Dict]:
        """获取所有持仓信息"""
        positions = {}
        
        try:
            # 从数据库获取持仓
            db_positions = self.db_manager.get_positions()
            
            for position in db_positions:
                current_price = self.binance_client.get_ticker_price(position.symbol)
                if current_price:
                    positions[position.symbol] = {
                        'quantity': position.quantity,
                        'avg_price': position.avg_price,
                        'current_price': current_price,
                        'market_value': position.quantity * current_price,
                        'unrealized_pnl': (current_price - position.avg_price) * position.quantity
                    }
            
            return positions
            
        except Exception as e:
            self.logger.error(f"获取持仓信息失败: {e}")
            return {}
    
    def get_position_analysis(self) -> Dict:
        """获取持仓分析报告"""
        try:
            positions = self._get_all_positions()
            portfolio_value = self.risk_manager._get_portfolio_value()
            
            analysis = {
                'portfolio_value': portfolio_value,
                'positions': {},
                'risk_metrics': {},
                'recommendations': []
            }
            
            total_position_value = 0
            high_risk_positions = []
            
            for symbol, position in positions.items():
                position_value = position['market_value']
                position_weight = position_value / portfolio_value if portfolio_value > 0 else 0
                total_position_value += position_value
                
                position_analysis = {
                    'quantity': position['quantity'],
                    'avg_price': position['avg_price'],
                    'current_price': position['current_price'],
                    'market_value': position_value,
                    'weight': position_weight,
                    'unrealized_pnl': position['unrealized_pnl'],
                    'pnl_percent': (position['unrealized_pnl'] / (position['avg_price'] * position['quantity'])) * 100 if position['avg_price'] > 0 else 0
                }
                
                analysis['positions'][symbol] = position_analysis
                
                # 检查高风险持仓
                if position_weight > self.reduction_threshold:
                    high_risk_positions.append({
                        'symbol': symbol,
                        'weight': position_weight,
                        'recommended_reduction': position['quantity'] * (position_weight - self.max_position_weight) / position_weight
                    })
            
            # 计算风险指标
            analysis['risk_metrics'] = {
                'total_position_value': total_position_value,
                'cash_ratio': (portfolio_value - total_position_value) / portfolio_value if portfolio_value > 0 else 0,
                'concentration_risk': len([p for p in analysis['positions'].values() if p['weight'] > 0.2]),
                'high_risk_positions': len(high_risk_positions)
            }
            
            # 生成建议
            if high_risk_positions:
                for pos in high_risk_positions:
                    analysis['recommendations'].append({
                        'type': 'reduce_position',
                        'symbol': pos['symbol'],
                        'current_weight': f"{pos['weight']:.1%}",
                        'recommended_reduction': f"{pos['recommended_reduction']:.6f}",
                        'priority': 'high' if pos['weight'] > 0.4 else 'medium'
                    })
            
            if analysis['risk_metrics']['cash_ratio'] < 0.1:
                analysis['recommendations'].append({
                    'type': 'increase_cash',
                    'message': '现金比例过低，建议增加现金储备',
                    'priority': 'medium'
                })
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"获取持仓分析失败: {e}")
            return {}
    
    def set_config(self, **kwargs):
        """设置配置参数"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                self.logger.info(f"设置配置 {key}: {value}")
    
    def get_config(self) -> Dict:
        """获取当前配置"""
        return {
            'auto_reduce_enabled': self.auto_reduce_enabled,
            'max_position_weight': self.max_position_weight,
            'reduction_threshold': self.reduction_threshold,
            'reduction_step': self.reduction_step,
            'rebalance_enabled': self.rebalance_enabled,
            'rebalance_threshold': self.rebalance_threshold,
            'min_rebalance_amount': self.min_rebalance_amount
        }
