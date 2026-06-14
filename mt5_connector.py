"""
MT5 Connector Module
يتعامل مع الاتصال بـ MetaTrader 5 وجلب أسعار الذهب والفضة
"""

import MetaTrader5 as mt5
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MT5Connector:
    """فئة للاتصال بـ MetaTrader 5"""
    
    def __init__(self, login: str, password: str, server: str):
        """
        تهيئة الاتصال بـ MetaTrader 5
        
        Args:
            login: رقم حساب MetaTrader 5
            password: كلمة المرور
            server: اسم السيرفر (مثل: ICMarkets-Demo)
        """
        self.login = login
        self.password = password
        self.server = server
        self.is_connected = False
    
    def connect(self) -> bool:
        """
        محاولة الاتصال بـ MetaTrader 5
        
        Returns:
            bool: True إذا كان الاتصال ناجحًا
        """
        try:
            # البدء في عملية الاتصال
            if not mt5.initialize():
                logger.error(f"فشل تهيئة MT5: {mt5.last_error()}")
                return False
            
            # محاولة تسجيل الدخول
            authorized = mt5.login(
                login=int(self.login),
                password=self.password,
                server=self.server
            )
            
            if not authorized:
                logger.error(f"فشل تسجيل الدخول لـ MT5: {mt5.last_error()}")
                mt5.shutdown()
                return False
            
            self.is_connected = True
            logger.info(f"تم الاتصال بـ MT5 بنجاح - الحساب: {self.login}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في الاتصال بـ MT5: {str(e)}")
            return False
    
    def disconnect(self) -> None:
        """قطع الاتصال بـ MetaTrader 5"""
        try:
            if self.is_connected:
                mt5.shutdown()
                self.is_connected = False
                logger.info("تم قطع الاتصال بـ MT5")
        except Exception as e:
            logger.error(f"خطأ في قطع الاتصال: {str(e)}")
    
    def get_current_prices(self) -> Optional[Dict]:
        """
        جلب الأسعار الحالية للذهب والفضة
        
        Returns:
            Dict يحتوي على أسعار الذهب والفضة، أو None في حالة الفشل
        """
        if not self.is_connected:
            logger.error("لا يوجد اتصال نشط مع MT5")
            return None
        
        try:
            # جلب سعر الذهب (XAUUSD)
            gold_tick = mt5.symbol_info_tick("XAUUSD")
            
            # جلب سعر الفضة (XAGUSD)
            silver_tick = mt5.symbol_info_tick("XAGUSD")
            
            if gold_tick is None or silver_tick is None:
                logger.error("فشل جلب أسعار المعادن")
                return None
            
            prices = {
                "gold": {
                    "symbol": "XAUUSD",
                    "bid": gold_tick.bid,      # سعر الشراء
                    "ask": gold_tick.ask,      # سعر البيع
                    "last": gold_tick.last,    # آخر سعر
                    "time": gold_tick.time
                },
                "silver": {
                    "symbol": "XAGUSD",
                    "bid": silver_tick.bid,
                    "ask": silver_tick.ask,
                    "last": silver_tick.last,
                    "time": silver_tick.time
                }
            }
            
            logger.info(f"تم جلب الأسعار بنجاح - الذهب: {gold_tick.ask}, الفضة: {silver_tick.ask}")
            return prices
            
        except Exception as e:
            logger.error(f"خطأ في جلب الأسعار: {str(e)}")
            return None
    
    def get_last_candle_data(self, symbol: str, timeframe: str = "D1") -> Optional[Dict]:
        """
        جلب بيانات الشمعة السابقة (اليوم السابق)
        
        Args:
            symbol: رمز المعدن (XAUUSD أو XAGUSD)
            timeframe: الإطار الزمني (D1 لليومي)
        
        Returns:
            Dict يحتوي على بيانات الشمعة السابقة
        """
        if not self.is_connected:
            logger.error("لا يوجد اتصال نشط مع MT5")
            return None
        
        try:
            # تحويل الإطار الزمني إلى رقم MT5
            if timeframe == "D1":
                tf = mt5.TIMEFRAME_D1
            else:
                tf = mt5.TIMEFRAME_D1
            
            # جلب آخر شمعة (اليوم السابق)
            candles = mt5.copy_rates_from_pos(symbol, tf, 1, 1)
            
            if candles is None or len(candles) == 0:
                logger.error(f"فشل جلب بيانات الشمعة للـ {symbol}")
                return None
            
            candle = candles[0]
            
            candle_data = {
                "symbol": symbol,
                "time": candle["time"],
                "open": candle["open"],
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
                "volume": candle["tick_volume"]
            }
            
            logger.info(f"تم جلب بيانات الشمعة للـ {symbol}: O={candle['open']}, H={candle['high']}, L={candle['low']}, C={candle['close']}")
            return candle_data
            
        except Exception as e:
            logger.error(f"خطأ في جلب بيانات الشمعة: {str(e)}")
            return None
