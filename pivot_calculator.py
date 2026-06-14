"""
Pivot Points Calculator Module
يحسب مستويات الارتكاز اليومية بناءً على بيانات الشمعة السابقة
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PivotCalculator:
    """فئة لحساب مستويات الارتكاز"""
    
    @staticmethod
    def calculate_pivot_points(candle_data: Dict) -> Optional[Dict]:
        """
        حساب مستويات الارتكاز (Pivot Points) باستخدام الطريقة الكلاسيكية
        
        الصيغة:
        - Pivot = (High + Low + Close) / 3
        - R1 = (2 * Pivot) - Low
        - R2 = Pivot + (High - Low)
        - S1 = (2 * Pivot) - High
        - S2 = Pivot - (High - Low)
        
        Args:
            candle_data: dict يحتوي على High, Low, Close من الشمعة السابقة
        
        Returns:
            dict يحتوي على مستويات الارتكاز المحسوبة
        """
        try:
            # استخراج البيانات المطلوبة
            high = float(candle_data.get("high", 0))
            low = float(candle_data.get("low", 0))
            close = float(candle_data.get("close", 0))
            symbol = candle_data.get("symbol", "Unknown")
            
            if high == 0 or low == 0 or close == 0:
                logger.error("بيانات الشمعة غير كاملة")
                return None
            
            # حساب الارتكاز الرئيسي
            pivot = (high + low + close) / 3
            
            # حساب مستويات المقاومة
            r1 = (2 * pivot) - low
            r2 = pivot + (high - low)
            r3 = high + 2 * (pivot - low)  # مستوى مقاومة إضافي
            
            # حساب مستويات الدعم
            s1 = (2 * pivot) - high
            s2 = pivot - (high - low)
            s3 = low - 2 * (high - pivot)  # مستوى دعم إضافي
            
            pivot_data = {
                "symbol": symbol,
                "timestamp": candle_data.get("time"),
                "previous_candle": {
                    "high": high,
                    "low": low,
                    "close": close
                },
                "pivot_points": {
                    "S3": round(s3, 2),
                    "S2": round(s2, 2),
                    "S1": round(s1, 2),
                    "Pivot": round(pivot, 2),
                    "R1": round(r1, 2),
                    "R2": round(r2, 2),
                    "R3": round(r3, 2)
                }
            }
            
            logger.info(f"تم حساب مستويات الارتكاز للـ {symbol}")
            logger.debug(f"Pivot Points: {pivot_data['pivot_points']}")
            
            return pivot_data
            
        except Exception as e:
            logger.error(f"خطأ في حساب مستويات الارتكاز: {str(e)}")
            return None
    
    @staticmethod
    def calculate_camarilla_levels(candle_data: Dict) -> Optional[Dict]:
        """
        حساب مستويات Camarilla (بديل للـ Pivot Points)
        
        الصيغة:
        - H4 = Close + 1.5 * (High - Low)
        - H3 = Close + 1.25 * (High - Low)
        - H2 = Close + (High - Low)
        - H1 = Close + 0.5 * (High - Low)
        - L1 = Close - 0.5 * (High - Low)
        - L2 = Close - (High - Low)
        - L3 = Close - 1.25 * (High - Low)
        - L4 = Close - 1.5 * (High - Low)
        
        Args:
            candle_data: dict يحتوي على High, Low, Close
        
        Returns:
            dict يحتوي على مستويات Camarilla
        """
        try:
            high = float(candle_data.get("high", 0))
            low = float(candle_data.get("low", 0))
            close = float(candle_data.get("close", 0))
            symbol = candle_data.get("symbol", "Unknown")
            
            hl_range = high - low
            
            h4 = close + 1.5 * hl_range
            h3 = close + 1.25 * hl_range
            h2 = close + hl_range
            h1 = close + 0.5 * hl_range
            
            l1 = close - 0.5 * hl_range
            l2 = close - hl_range
            l3 = close - 1.25 * hl_range
            l4 = close - 1.5 * hl_range
            
            camarilla_data = {
                "symbol": symbol,
                "timestamp": candle_data.get("time"),
                "camarilla_levels": {
                    "H4": round(h4, 2),
                    "H3": round(h3, 2),
                    "H2": round(h2, 2),
                    "H1": round(h1, 2),
                    "L1": round(l1, 2),
                    "L2": round(l2, 2),
                    "L3": round(l3, 2),
                    "L4": round(l4, 2)
                }
            }
            
            logger.info(f"تم حساب مستويات Camarilla للـ {symbol}")
            return camarilla_data
            
        except Exception as e:
            logger.error(f"خطأ في حساب مستويات Camarilla: {str(e)}")
            return None
