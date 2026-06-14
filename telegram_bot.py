"""
Telegram Bot Module
يتعامل مع إرسال الرسائل والبيانات عبر Telegram
"""

import logging
from telegram import Bot
from telegram.error import TelegramError
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TelegramBotManager:
    """فئة إدارة بوت Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        تهيئة بوت Telegram
        
        Args:
            bot_token: توكن البوت من BotFather
            chat_id: معرف المحادثة (Chat ID)
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token)
    
    async def send_welcome_message(self) -> bool:
        """
        إرسال رسالة ترحيب اختبارية
        
        Returns:
            bool: True إذا نجحت الرسالة
        """
        try:
            message = """
🤖 *بوت مراقبة الذهب والفضة*

تم بدء البوت بنجاح! ✅

سيقوم هذا البوت بـ:
• مراقبة أسعار الذهب (XAUUSD)
• مراقبة أسعار الفضة (XAGUSD)
• حساب مستويات الارتكاز اليومية
• إرسال التنبيهات والتحديثات

📊 جاري جمع البيانات...
            """
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )
            
            logger.info("تم إرسال رسالة الترحيب بنجاح")
            return True
            
        except TelegramError as e:
            logger.error(f"خطأ في إرسال رسالة الترحيب: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"خطأ غير متوقع: {str(e)}")
            return False
    
    async def send_pivot_points_report(self, pivot_data: Dict, prices: Dict) -> bool:
        """
        إرسال تقرير مستويات الارتكاز
        
        Args:
            pivot_data: بيانات مستويات الارتكاز
            prices: الأسعار الحالية
        
        Returns:
            bool: True إذا نجحت الرسالة
        """
        try:
            symbol = pivot_data.get("symbol", "Unknown")
            pivot_points = pivot_data.get("pivot_points", {})
            
            # اختيار اسم المعدن
            if "GOLD" in symbol or "XAUUSD" in symbol:
                metal_name = "🥇 الذهب (XAUUSD)"
            elif "SILVER" in symbol or "XAGUSD" in symbol:
                metal_name = "🥈 الفضة (XAGUSD)"
            else:
                metal_name = f"معدن: {symbol}"
            
            # الحصول على السعر الحالي
            current_price = "N/A"
            if prices and symbol in str(prices):
                current_price = prices.get(symbol.lower().replace("usd", ""), {}).get("ask", "N/A")
            
            # بناء الرسالة
            message = f"""
{metal_name}

💰 *السعر الحالي:* {current_price}

📍 *مستويات الارتكاز اليومية:*

🔴 *مستويات المقاومة:*
R3: {pivot_points.get('R3', 'N/A')}
R2: {pivot_points.get('R2', 'N/A')}
R1: {pivot_points.get('R1', 'N/A')}

🎯 *الارتكاز الرئيسي:*
Pivot: {pivot_points.get('Pivot', 'N/A')}

🟢 *مستويات الدعم:*
S1: {pivot_points.get('S1', 'N/A')}
S2: {pivot_points.get('S2', 'N/A')}
S3: {pivot_points.get('S3', 'N/A')}

⏰ محدث الآن
            """
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )
            
            logger.info(f"تم إرسال تقرير مستويات الارتكاز للـ {symbol} بنجاح")
            return True
            
        except TelegramError as e:
            logger.error(f"خطأ في إرسال تقرير الارتكاز: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"خطأ غير متوقع: {str(e)}")
            return False
    
    async def send_prices_update(self, prices: Dict) -> bool:
        """
        إرسال تحديث الأسعار الحالية
        
        Args:
            prices: قاموس يحتوي على أسعار الذهب والفضة
        
        Returns:
            bool: True إذا نجحت الرسالة
        """
        try:
            gold = prices.get("gold", {})
            silver = prices.get("silver", {})
            
            message = f"""
📊 *تحديث الأسعار الحالية*

🥇 *الذهب (XAUUSD)*
Bid: {gold.get('bid', 'N/A')}
Ask: {gold.get('ask', 'N/A')}
Last: {gold.get('last', 'N/A')}

🥈 *الفضة (XAGUSD)*
Bid: {silver.get('bid', 'N/A')}
Ask: {silver.get('ask', 'N/A')}
Last: {silver.get('last', 'N/A')}

⏰ محدث الآن
            """
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )
            
            logger.info("تم إرسال تحديث الأسعار بنجاح")
            return True
            
        except TelegramError as e:
            logger.error(f"خطأ في إرسال تحديث الأسعار: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"خطأ غير متوقع: {str(e)}")
            return False
    
    async def send_error_message(self, error_text: str) -> bool:
        """
        إرسال رسالة خطأ
        
        Args:
            error_text: نص الخطأ
        
        Returns:
            bool: True إذا نجحت الرسالة
        """
        try:
            message = f"""
❌ *حدث خطأ*

{error_text}

⏰ {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )
            
            logger.error(f"تم إرسال رسالة خطأ: {error_text}")
            return True
            
        except TelegramError as e:
            logger.error(f"خطأ في إرسال رسالة الخطأ: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"خطأ غير متوقع: {str(e)}")
            return False
