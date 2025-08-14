import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from .base_strategy import BaseStrategy

class MLStrategy(BaseStrategy):
    """机器学习策略基类"""
    
    def __init__(self, symbol: str, parameters: Dict[str, Any]):
        super().__init__(symbol, parameters)
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
        
        # ML参数
        self.lookback_period = parameters.get('lookback_period', 30)
        self.prediction_horizon = parameters.get('prediction_horizon', 1)
        self.model_type = parameters.get('model_type', 'random_forest')
        self.retrain_frequency = parameters.get('retrain_frequency', 50)  # 每50个数据点重训练
        self.min_training_samples = parameters.get('min_training_samples', 100)
        
        self.data_count = 0
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """准备特征数据"""
        try:
            df = data.copy()
            
            # 处理可能的嵌套数组数据
            if isinstance(df, pd.DataFrame) and len(df.columns) == 1:
                # 如果数据是单列的嵌套数组，尝试解析
                self.logger.warning("检测到嵌套数组数据，尝试解析...")
                try:
                    # 尝试将第一列解析为JSON或数组
                    first_col = df.iloc[:, 0]
                    if first_col.dtype == 'object':
                        # 尝试解析为数值数组
                        parsed_data = []
                        for item in first_col:
                            if isinstance(item, str):
                                # 移除引号和空格，分割
                                clean_item = item.strip().strip("'[]").split()
                                try:
                                    parsed_data.append([float(x.strip("'")) for x in clean_item])
                                except ValueError:
                                    # 如果解析失败，跳过这一行
                                    continue
                            elif isinstance(item, (list, np.ndarray)):
                                try:
                                    parsed_data.append([float(x) for x in item])
                                except (ValueError, TypeError):
                                    continue
                            else:
                                try:
                                    parsed_data.append([float(item)])
                                except (ValueError, TypeError):
                                    continue
                        
                        # 创建新的DataFrame
                        if parsed_data:
                            df = pd.DataFrame(parsed_data, columns=['open', 'high', 'low', 'close', 'volume'])
                            self.logger.info(f"成功解析嵌套数组数据，形状: {df.shape}")
                except Exception as parse_error:
                    self.logger.error(f"解析嵌套数组失败: {parse_error}")
                    return pd.DataFrame()
            
            # 确保数据类型正确 - 转换字符串为数值
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    # 处理可能的字符串数据
                    if df[col].dtype == 'object':
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    # 确保是float类型
                    df[col] = df[col].astype(float)
            
            # 处理其他可能的数值列 - 只处理存在的列
            other_numeric_columns = ['quote_volume', 'trades_count', 'quote_asset_volume', 
                                   'number_of_trades', 'taker_buy_base_asset_volume', 
                                   'taker_buy_quote_asset_volume', 'ignore']
            for col in other_numeric_columns:
                if col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    df[col] = df[col].astype(float)
            
            # 移除包含NaN的行
            df = df.dropna(subset=numeric_columns)
            
            if df.empty:
                self.logger.warning("数据清理后为空")
                return pd.DataFrame()
            
            # 价格特征
            df['returns'] = df['close'].pct_change()
            # 安全处理log_returns，避免log(0)或log(负数)
            price_ratio = df['close'] / df['close'].shift(1)
            df['log_returns'] = np.log(price_ratio.where(price_ratio > 0, 1))
            df['price_change'] = (df['close'] - df['open']) / df['open'].where(df['open'] != 0, 1)
            df['high_low_ratio'] = (df['high'] - df['low']) / df['close'].where(df['close'] != 0, 1)
            df['volume_change'] = df['volume'].pct_change()
            
            # 移动平均特征
            for window in [5, 10, 20, 50]:
                df[f'sma_{window}'] = df['close'].rolling(window=window).mean()
                # 安全处理除法，避免除零
                df[f'price_to_sma_{window}'] = df['close'] / df[f'sma_{window}'].where(df[f'sma_{window}'] != 0, 1)
                df[f'sma_{window}_slope'] = df[f'sma_{window}'].diff(5)
            
            # 波动率特征
            df['volatility_5'] = df['returns'].rolling(window=5).std()
            df['volatility_20'] = df['returns'].rolling(window=20).std()
            # 安全处理波动率比率
            df['volatility_ratio'] = (df['volatility_5'] / df['volatility_20']).where(df['volatility_20'] != 0, 1)
            
            # RSI特征
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            # 安全处理RSI计算
            rs = (gain / loss).where(loss != 0, 1)
            df['rsi'] = 100 - (100 / (1 + rs))
            df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
            df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
            
            # MACD特征
            ema_12 = df['close'].ewm(span=12).mean()
            ema_26 = df['close'].ewm(span=26).mean()
            df['macd'] = ema_12 - ema_26
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            df['macd_crossover'] = ((df['macd'] > df['macd_signal']) & 
                                   (df['macd'].shift(1) <= df['macd_signal'].shift(1))).astype(int)
            
            # 布林带特征
            bb_middle = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = bb_middle + (bb_std * 2)
            df['bb_lower'] = bb_middle - (bb_std * 2)
            # 安全处理布林带位置计算
            bb_range = df['bb_upper'] - df['bb_lower']
            df['bb_position'] = (df['close'] - df['bb_lower']) / bb_range.where(bb_range != 0, 1)
            df['bb_squeeze'] = bb_range / bb_middle.where(bb_middle != 0, 1)
            
            # 成交量特征
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            # 安全处理成交量比率
            df['volume_ratio'] = df['volume'] / df['volume_sma'].where(df['volume_sma'] != 0, 1)
            df['price_volume'] = df['close'] * df['volume']
            df['volume_price_trend'] = df['price_volume'].rolling(window=5).mean()
            
            # 时间特征
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
            
            # 滞后特征
            for lag in [1, 2, 3, 5]:
                df[f'returns_lag_{lag}'] = df['returns'].shift(lag)
                df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
                df[f'rsi_lag_{lag}'] = df['rsi'].shift(lag)
            
            # 技术形态特征
            df['higher_high'] = ((df['high'] > df['high'].shift(1)) & 
                               (df['high'].shift(1) > df['high'].shift(2))).astype(int)
            df['lower_low'] = ((df['low'] < df['low'].shift(1)) & 
                             (df['low'].shift(1) < df['low'].shift(2))).astype(int)
            
            # 趋势特征
            df['trend_5'] = np.where(df['close'] > df['close'].shift(5), 1, 
                                   np.where(df['close'] < df['close'].shift(5), -1, 0))
            df['trend_20'] = np.where(df['close'] > df['close'].shift(20), 1, 
                                    np.where(df['close'] < df['close'].shift(20), -1, 0))
            
            # 清理无穷大和NaN值
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.fillna(0)
            
            return df
            
        except Exception as e:
            self.logger.error(f"准备特征失败: {e}")
            return data
    
    def create_labels(self, data: pd.DataFrame, relaxed: bool = False) -> pd.Series:
        """创建标签（预测目标）"""
        try:
            # 计算未来收益率
            future_returns = data['close'].shift(-self.prediction_horizon) / data['close'] - 1
            
            # 创建分类标签
            # 1: 上涨超过阈值, 0: 横盘, -1: 下跌超过阈值
            if relaxed:
                # 使用更宽松的阈值以增加交易信号
                up_threshold = self.parameters.get('up_threshold', 0.01) * 0.3  # 0.3%
                down_threshold = self.parameters.get('down_threshold', -0.01) * 0.3  # -0.3%
            else:
                up_threshold = self.parameters.get('up_threshold', 0.01)  # 1%
                down_threshold = self.parameters.get('down_threshold', -0.01)  # -1%
            
            labels = np.where(future_returns > up_threshold, 1,
                            np.where(future_returns < down_threshold, -1, 0))
            
            # 检查标签分布
            label_counts = pd.Series(labels).value_counts()
            self.logger.info(f"标签分布: {label_counts.to_dict()}")
            
            # 如果分布过于不均衡，进一步调整阈值
            if len(label_counts) >= 2:
                min_count = min(label_counts)
                total_count = len(labels)
                min_ratio = min_count / total_count
                
                if min_ratio < 0.1:  # 如果某个类别占比少于10%
                    self.logger.warning(f"标签分布不均衡，最小类别占比: {min_ratio:.2%}")
                    # 使用更宽松的阈值
                    up_threshold = up_threshold * 0.5
                    down_threshold = down_threshold * 0.5
                    
                    labels = np.where(future_returns > up_threshold, 1,
                                    np.where(future_returns < down_threshold, -1, 0))
                    
                    # 再次检查分布
                    new_label_counts = pd.Series(labels).value_counts()
                    self.logger.info(f"调整后标签分布: {new_label_counts.to_dict()}")
            
            return pd.Series(labels, index=data.index)
            
        except Exception as e:
            self.logger.error(f"创建标签失败: {e}")
            return pd.Series()
    
    def train_model(self, data: pd.DataFrame) -> bool:
        """训练模型"""
        try:
            if len(data) < self.min_training_samples:
                self.logger.warning(f"训练数据不足: {len(data)} < {self.min_training_samples}")
                return False
            
            # 数据验证和清理
            cleaned_data = self._validate_and_clean_data(data)
            if cleaned_data.empty:
                self.logger.warning("数据验证后为空")
                return False
            
            # 准备特征
            self.logger.info(f"开始准备特征，清理后数据形状: {cleaned_data.shape}")
            
            feature_data = self.prepare_features(cleaned_data)
            if feature_data.empty:
                self.logger.warning("特征准备后数据为空")
                return False
            
            # self.logger.info(f"特征数据形状: {feature_data.shape}")
            # self.logger.info(f"特征数据类型: {feature_data.dtypes}")
                
            labels = self.create_labels(feature_data)
            
            # 选择特征列
            self.feature_columns = [col for col in feature_data.columns 
                                  if col not in ['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            
            # 确保特征列存在且有效
            available_features = [col for col in self.feature_columns if col in feature_data.columns]
            if not available_features:
                self.logger.error("没有可用的特征列")
                return False
            
            self.logger.info(f"可用特征列: {available_features}")
            
            # 更新特征列列表为实际可用的特征
            self.feature_columns = available_features
            
            # 准备训练数据
            X = feature_data[available_features].fillna(0)
            y = labels
            
            # 移除无效数据
            valid_idx = ~(np.isnan(y) | np.isinf(y))
            X = X[valid_idx]
            y = y[valid_idx]
            
            if len(X) < self.min_training_samples:
                self.logger.warning("有效训练数据不足")
                return False
            
            # 清理特征数据中的无穷大和异常值
            X_cleaned = X.copy()
            
            # 替换无穷大值
            X_cleaned = X_cleaned.replace([np.inf, -np.inf], np.nan)
            
            # 使用中位数填充NaN值
            X_cleaned = X_cleaned.fillna(X_cleaned.median())
            
            # 处理异常值 - 使用IQR方法
            for col in X_cleaned.columns:
                Q1 = X_cleaned[col].quantile(0.25)
                Q3 = X_cleaned[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # 将异常值替换为边界值
                X_cleaned[col] = X_cleaned[col].clip(lower_bound, upper_bound)
            
            # 检查标签分布，确保有足够的多样性
            label_counts = pd.Series(y).value_counts()
            self.logger.info(f"标签分布: {label_counts.to_dict()}")
            
            # 如果某个类别样本太少，调整阈值
            if len(label_counts) < 2 or min(label_counts) < 5:
                self.logger.warning("标签分布不均衡，调整阈值")
                # 重新创建更宽松的标签
                labels = self.create_labels(feature_data, relaxed=True)
                y = labels[valid_idx]
                label_counts = pd.Series(y).value_counts()
                self.logger.info(f"调整后标签分布: {label_counts.to_dict()}")
                
                # 如果仍然不均衡，使用更激进的方法
                if len(label_counts) < 2 or min(label_counts) < 3:
                    self.logger.warning("使用更激进的阈值调整")
                    # 使用非常宽松的阈值
                    future_returns = feature_data['close'].shift(-self.prediction_horizon) / feature_data['close'] - 1
                    up_threshold = 0.001  # 0.1%
                    down_threshold = -0.001  # -0.1%
                    
                    labels = np.where(future_returns > up_threshold, 1,
                                    np.where(future_returns < down_threshold, -1, 0))
                    y = pd.Series(labels, index=feature_data.index)[valid_idx]
                    label_counts = pd.Series(y).value_counts()
                    self.logger.info(f"激进调整后标签分布: {label_counts.to_dict()}")
            
            # 数据标准化
            X_scaled = self.scaler.fit_transform(X_cleaned)
            
            # 分割训练测试集
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.2, random_state=42, stratify=y
                )
            except ValueError:
                # 如果分层失败，不使用分层
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.2, random_state=42
                )
            
            # 创建模型
            if self.model_type == 'random_forest':
                self.model = RandomForestClassifier(
                    n_estimators=50,  # 减少树的数量以提高速度
                    max_depth=8,      # 减少深度避免过拟合
                    min_samples_split=10,
                    min_samples_leaf=5,
                    random_state=42,
                    class_weight='balanced'  # 处理类别不平衡
                )
            elif self.model_type == 'gradient_boosting':
                self.model = GradientBoostingClassifier(
                    n_estimators=50,
                    learning_rate=0.1,
                    max_depth=4,
                    random_state=42
                )
            elif self.model_type == 'logistic_regression':
                self.model = LogisticRegression(
                    random_state=42,
                    max_iter=1000,
                    class_weight='balanced'
                )
            else:
                self.logger.error(f"不支持的模型类型: {self.model_type}")
                return False
            
            # 训练模型
            self.model.fit(X_train, y_train)
            
            # 评估模型
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            # 交叉验证
            try:
                cv_scores = cross_val_score(self.model, X_scaled, y, cv=3)  # 减少CV折数
                cv_mean = cv_scores.mean()
                cv_std = cv_scores.std()
            except:
                cv_mean = test_score
                cv_std = 0
            
            self.logger.info(f"模型训练完成:")
            self.logger.info(f"  训练集准确率: {train_score:.3f}")
            self.logger.info(f"  测试集准确率: {test_score:.3f}")
            self.logger.info(f"  交叉验证平均准确率: {cv_mean:.3f} (+/- {cv_std * 2:.3f})")
            
            # 特征重要性
            if hasattr(self.model, 'feature_importances_'):
                feature_importance = pd.DataFrame({
                    'feature': self.feature_columns,
                    'importance': self.model.feature_importances_
                }).sort_values('importance', ascending=False)
                
                self.logger.info("前5个重要特征:")
                for _, row in feature_importance.head(5).iterrows():
                    self.logger.info(f"  {row['feature']}: {row['importance']:.3f}")
            
            self.is_trained = True
            return True
            
        except Exception as e:
            self.logger.error(f"模型训练失败: {e}")
            import traceback
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            return False
    
    def predict(self, data: pd.DataFrame) -> Tuple[int, float]:
        """预测信号"""
        try:
            if not self.is_trained or self.model is None:
                return 0, 0.0
            
            # 数据验证
            cleaned_data = self._validate_and_clean_data(data)
            if cleaned_data.empty:
                return 0, 0.0
            
            # 准备特征
            feature_data = self.prepare_features(cleaned_data)
            
            # 获取最新数据 - 使用训练时的特征列
            if not self.feature_columns:
                self.logger.error("特征列未定义")
                return 0, 0.0
            
            # 检查所有训练时的特征列是否都存在
            missing_features = [col for col in self.feature_columns if col not in feature_data.columns]
            if missing_features:
                self.logger.error(f"缺少特征列: {missing_features}")
                return 0, 0.0
            
            latest_features = feature_data[self.feature_columns].iloc[-1:].fillna(0)
            
            # 清理最新数据中的无穷大值
            latest_features = latest_features.replace([np.inf, -np.inf], np.nan)
            latest_features = latest_features.fillna(latest_features.median())
            
            # 标准化
            latest_scaled = self.scaler.transform(latest_features)
            
            # 确保特征数量匹配
            if latest_scaled.shape[1] != len(self.feature_columns):
                self.logger.error(f"特征数量不匹配: {latest_scaled.shape[1]} vs {len(self.feature_columns)}")
                return 0, 0.0
            
            # 预测
            prediction = self.model.predict(latest_scaled)[0]
            
            # 获取预测概率
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(latest_scaled)[0]
                confidence = max(probabilities)
            else:
                confidence = 0.5
            
            return int(prediction), float(confidence)
            
        except Exception as e:
            self.logger.error(f"预测失败: {e}")
            return 0, 0.0
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        """生成交易信号"""
        try:
            self.data_count += 1
            
            # 数据验证
            cleaned_data = self._validate_and_clean_data(data)
            if cleaned_data.empty:
                self.logger.warning("数据验证失败，使用备选信号")
                return self._generate_fallback_signal(data)
            
            # 检查数据是否足够
            if len(cleaned_data) < self.min_training_samples:
                return 'HOLD'
            
            # 首次训练或需要重新训练
            if not self.is_trained:
                self.logger.info("首次训练模型...")
                success = self.train_model(cleaned_data)
                if not success:
                    self.logger.warning("模型训练失败，使用简化信号")
                    return self._generate_fallback_signal(cleaned_data)
            elif self.data_count % self.retrain_frequency == 0:
                self.logger.info("重新训练模型...")
                success = self.train_model(cleaned_data)
                if not success:
                    self.logger.warning("重新训练失败，继续使用现有模型")
            
            # 如果模型仍未训练，使用备选信号
            if not self.is_trained:
                return self._generate_fallback_signal(cleaned_data)
            
            # 预测
            prediction, confidence = self.predict(data)
            
            # 降低信心阈值以增加交易频率
            min_confidence = self.parameters.get('min_confidence', 0.5)  # 进一步降低到0.5
            
            self.logger.debug(f"ML预测: {prediction}, 信心度: {confidence:.3f}, 阈值: {min_confidence}")
            
            if confidence < min_confidence:
                # 如果信心度不够，有一定概率使用备选信号
                if np.random.random() < 0.3:  # 30%概率使用备选信号
                    return self._generate_fallback_signal(data)
                return 'HOLD'
            
            # 转换预测结果为交易信号
            if prediction == 1:
                return 'BUY'
            elif prediction == -1:
                return 'SELL'
            else:
                return 'HOLD'
                
        except Exception as e:
            self.logger.error(f"生成信号失败: {e}")
            return self._generate_fallback_signal(data)
    
    def _generate_fallback_signal(self, data: pd.DataFrame) -> str:
        """生成备选信号（基于简单技术分析）"""
        try:
            if len(data) < 20:
                return 'HOLD'
            
            # 使用简单的移动平均交叉策略
            short_ma = data['close'].rolling(window=5).mean()
            long_ma = data['close'].rolling(window=20).mean()
            
            current_short = short_ma.iloc[-1]
            current_long = long_ma.iloc[-1]
            prev_short = short_ma.iloc[-2]
            prev_long = long_ma.iloc[-2]
            
            # 金叉买入
            if prev_short <= prev_long and current_short > current_long:
                return 'BUY'
            # 死叉卖出
            elif prev_short >= prev_long and current_short < current_long:
                return 'SELL'
            
            return 'HOLD'
            
        except Exception as e:
            self.logger.error(f"生成备选信号失败: {e}")
            return 'HOLD'
    
    def calculate_position_size(self, current_price: float, balance: float) -> float:
        """计算仓位大小"""
        try:
            # 基础仓位大小
            base_position_size = balance * self.parameters.get('position_size', 0.1)
            
            # 如果有预测信心度，根据信心度调整仓位
            if hasattr(self, 'last_confidence'):
                confidence_multiplier = min(2.0, self.last_confidence * 2)
                base_position_size *= confidence_multiplier
            
            return base_position_size / current_price
            
        except Exception as e:
            self.logger.error(f"计算仓位大小失败: {e}")
            return 0.0
    
    def save_model(self, filepath: str):
        """保存模型"""
        try:
            if self.model is not None:
                model_data = {
                    'model': self.model,
                    'scaler': self.scaler,
                    'feature_columns': self.feature_columns,
                    'parameters': self.parameters,
                    'is_trained': self.is_trained
                }
                joblib.dump(model_data, filepath)
                self.logger.info(f"模型已保存到: {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存模型失败: {e}")
    
    def load_model(self, filepath: str):
        """加载模型"""
        try:
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.is_trained = model_data['is_trained']
            
            self.logger.info(f"模型已从 {filepath} 加载")
            
        except Exception as e:
            self.logger.error(f"加载模型失败: {e}")

    def _validate_and_clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """验证和清理数据"""
        try:
            if data is None or data.empty:
                self.logger.warning("输入数据为空或None")
                return pd.DataFrame()
            
            # 检查数据类型
            # self.logger.info(f"原始数据形状: {data.shape}")
            # self.logger.info(f"原始数据类型: {data.dtypes}")
            # self.logger.info(f"原始数据列: {list(data.columns)}")
            
            # 处理可能的字符串数据
            df = data.copy()
            
            # 检查是否是嵌套数组格式
            if len(df.columns) == 1 and df.iloc[:, 0].dtype == 'object':
                self.logger.warning("检测到可能的嵌套数组格式")
                try:
                    # 尝试解析嵌套数组
                    first_col = df.iloc[:, 0]
                    parsed_data = []
                    
                    for item in first_col:
                        if isinstance(item, str):
                            # 处理字符串格式的数组
                            try:
                                # 移除所有引号和方括号
                                clean_item = item.replace("'", "").replace("[", "").replace("]", "")
                                # 分割并转换为数值
                                parts = clean_item.split()
                                row_data = [float(x) for x in parts]
                                if len(row_data) >= 5:  # 确保有足够的数据
                                    parsed_data.append(row_data[:5])  # 只取前5个值
                            except (ValueError, IndexError):
                                continue
                        elif isinstance(item, (list, np.ndarray)):
                            # 处理列表或数组格式
                            try:
                                row_data = [float(x) for x in item]
                                if len(row_data) >= 5:
                                    parsed_data.append(row_data[:5])
                            except (ValueError, TypeError):
                                continue
                        else:
                            continue
                    
                    if parsed_data:
                        df = pd.DataFrame(parsed_data, columns=['open', 'high', 'low', 'close', 'volume'])
                        self.logger.info(f"成功解析嵌套数组，新数据形状: {df.shape}")
                    else:
                        self.logger.error("无法解析嵌套数组数据")
                        return pd.DataFrame()
                        
                except Exception as e:
                    self.logger.error(f"解析嵌套数组失败: {e}")
                    return pd.DataFrame()
            
            # 确保必要的列存在 - 只检查核心列
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.warning(f"缺少必要的列: {missing_columns}")
                # 尝试从现有列中映射
                column_mapping = {
                    'open_price': 'open',
                    'high_price': 'high', 
                    'low_price': 'low',
                    'close_price': 'close',
                    'quote_volume': 'volume'
                }
                
                for old_col, new_col in column_mapping.items():
                    if old_col in df.columns and new_col not in df.columns:
                        df[new_col] = df[old_col]
                        self.logger.info(f"映射列 {old_col} -> {new_col}")
                
                # 再次检查必要列
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    self.logger.error(f"仍然缺少必要的列: {missing_columns}")
                    return pd.DataFrame()
            
            # 转换数据类型
            for col in required_columns:
                if col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    df[col] = df[col].astype(float)
            
            # 处理其他可能的数值列 - 只处理存在的列
            other_numeric_columns = ['quote_volume', 'trades_count', 'quote_asset_volume', 
                                   'number_of_trades', 'taker_buy_base_asset_volume', 
                                   'taker_buy_quote_asset_volume', 'ignore']
            for col in other_numeric_columns:
                if col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    df[col] = df[col].astype(float)
            
            # 移除包含NaN的行
            df = df.dropna(subset=required_columns)
            
            if df.empty:
                self.logger.warning("数据清理后为空")
                return pd.DataFrame()
            
            # 检查数据范围
            for col in required_columns:
                if df[col].min() < 0:
                    self.logger.warning(f"{col}列包含负值，这可能不是价格数据")
                if df[col].max() > 1e10:
                    self.logger.warning(f"{col}列包含极大值，可能数据有误")
            
            self.logger.info(f"数据验证完成，最终形状: {df.shape}")
            return df
            
        except Exception as e:
            self.logger.error(f"数据验证失败: {e}")
            return pd.DataFrame()

class LSTMStrategy(BaseStrategy):
    """LSTM深度学习策略"""
    
    def __init__(self, symbol: str, parameters: Dict[str, Any]):
        super().__init__(symbol, parameters)
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
        
        # LSTM参数
        self.sequence_length = parameters.get('sequence_length', 60)
        self.prediction_horizon = parameters.get('prediction_horizon', 1)
        self.epochs = parameters.get('epochs', 50)
        self.batch_size = parameters.get('batch_size', 32)
        
    def prepare_sequences(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """准备LSTM序列数据"""
        try:
            # 准备特征
            features = ['close', 'volume', 'high', 'low']
            feature_data = data[features].values
            
            # 标准化
            scaled_data = self.scaler.fit_transform(feature_data)
            
            # 创建序列
            X, y = [], []
            for i in range(self.sequence_length, len(scaled_data) - self.prediction_horizon):
                X.append(scaled_data[i-self.sequence_length:i])
                
                # 预测未来价格变化方向
                future_price = data['close'].iloc[i + self.prediction_horizon]
                current_price = data['close'].iloc[i]
                price_change = (future_price - current_price) / current_price
                
                # 分类标签
                if price_change > 0.01:
                    y.append(1)  # 上涨
                elif price_change < -0.01:
                    y.append(-1)  # 下跌
                else:
                    y.append(0)  # 横盘
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            self.logger.error(f"准备序列数据失败: {e}")
            return np.array([]), np.array([])
    
    def train_model(self, data: pd.DataFrame) -> bool:
        """训练LSTM模型"""
        try:
            # 检查是否安装了tensorflow
            try:
                import tensorflow as tf
                from tensorflow.keras.models import Sequential
                from tensorflow.keras.layers import LSTM, Dense, Dropout
                from tensorflow.keras.optimizers import Adam
            except ImportError:
                self.logger.warning("TensorFlow未安装，跳过LSTM训练")
                return False
            
            if len(data) < self.sequence_length + 100:
                self.logger.warning("LSTM训练数据不足")
                return False
            
            # 准备数据
            X, y = self.prepare_sequences(data)
            
            if len(X) == 0:
                return False
            
            # 转换为分类问题
            from tensorflow.keras.utils import to_categorical
            y_categorical = to_categorical(y + 1, num_classes=3)  # -1,0,1 -> 0,1,2
            
            # 分割数据
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y_categorical[:split_idx], y_categorical[split_idx:]
            
            # 构建模型
            self.model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(self.sequence_length, X.shape[2])),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(3, activation='softmax')
            ])
            
            self.model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            # 训练模型
            history = self.model.fit(
                X_train, y_train,
                batch_size=self.batch_size,
                epochs=self.epochs,
                validation_data=(X_test, y_test),
                verbose=0
            )
            
            # 评估模型
            train_loss, train_acc = self.model.evaluate(X_train, y_train, verbose=0)
            test_loss, test_acc = self.model.evaluate(X_test, y_test, verbose=0)
            
            self.logger.info(f"LSTM模型训练完成:")
            self.logger.info(f"  训练集准确率: {train_acc:.3f}")
            self.logger.info(f"  测试集准确率: {test_acc:.3f}")
            
            self.is_trained = True
            return True
            
        except Exception as e:
            self.logger.error(f"LSTM模型训练失败: {e}")
            return False
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        """生成交易信号"""
        try:
            if not self.is_trained or self.model is None:
                # 尝试训练模型
                if not self.train_model(data):
                    return 'HOLD'
            
            if len(data) < self.sequence_length:
                return 'HOLD'
            
            # 准备最新序列
            features = ['close', 'volume', 'high', 'low']
            latest_data = data[features].tail(self.sequence_length).values
            latest_scaled = self.scaler.transform(latest_data)
            
            # 预测
            X_pred = latest_scaled.reshape(1, self.sequence_length, len(features))
            prediction = self.model.predict(X_pred, verbose=0)[0]
            
            # 获取预测类别
            predicted_class = np.argmax(prediction) - 1  # 0,1,2 -> -1,0,1
            confidence = max(prediction)
            
            # 设置信心阈值
            min_confidence = self.parameters.get('min_confidence', 0.6)
            
            if confidence < min_confidence:
                return 'HOLD'
            
            if predicted_class == 1:
                return 'BUY'
            elif predicted_class == -1:
                return 'SELL'
            else:
                return 'HOLD'
                
        except Exception as e:
            self.logger.error(f"LSTM信号生成失败: {e}")
            return 'HOLD'
    
    def calculate_position_size(self, current_price: float, balance: float) -> float:
        """计算仓位大小"""
        base_position_size = balance * self.parameters.get('position_size', 0.1)
        return base_position_size / current_price