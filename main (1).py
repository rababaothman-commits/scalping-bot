"""
Main Application File
ملف تشغيل التطبيق الرئيسي - يجمع بين MT5 و Telegram و Pivot Points Calculator
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# استيراد المودولات المخصصة
from mt5_connector import MT5Connector
from pivot_calculator import PivotCalculator
from telegram_bot import TelegramBotManager

# ===== إعداد نظام السجلات (Logging) =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot_logs.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# تحميل متغيرات البيئة من ملف .env
load_dotenv()


class GoldSilverMonitorBot:
    """فئة رئيسية لإدارة بوت مراقبة الذهب والفضة"""
    
    def __init__(self):
        """تهيئة البوت وجميع المكونات"""
        self.logger = logging.getLogger(__name__)
        
        # ===== استخراج متغيرات البيئة =====
        self.mt5_login = os.getenv("MT5_LOGIN")
        self.mt5_password = os.getenv("MT5_PASSWORD")
        self.mt5_server = os.getenv("MT5_SERVER")
        
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # التحقق من وجود جميع المتغيرات المطلوبة
        self._validate_env_variables()
        
        # تهيئة المكونات
        self.mt5_connector = MT5Connector(
            login=self.mt5_login,
            password=self.mt5_password,
            server=self.mt5_server
        )
        
        self.telegram_manager = TelegramBotManager(
            bot_token=self.telegram_token,
            chat_id=self.telegram_chat_id
        )
        
        self.pivot_calculator = PivotCalculator()
        
        self.logger.info("تم تهيئة البوت بنجاح")
    
    def _validate_env_variables(self) -> None:
        """التحقق من وجود جميع متغيرات البيئة المطلوبة"""
        required_vars = {
            "MT5_LOGIN": self.mt5_login,
            "MT5_PASSWORD": self.mt5_password,
            "MT5_SERVER": self.mt5_server,
            "TELEGRAM_BOT_TOKEN": self.telegram_token,
            "TELEGRAM_CHAT_ID": self.telegram_chat_id
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            error_msg = f"متغيرات البيئة المفقودة: {', '.join(missing_vars)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.info("تم التحقق من جميع متغيرات البيئة بنجاح")
    
    async def startup(self) -> bool:
        """
        بدء تشغيل البوت وإجراء الاختبارات الأولية
        
        Returns:
            bool: True إذا كان الإقلاع ناجحًا
        """
        try:
            self.logger.info("=" * 50)
            self.logger.info("بدء تشغيل بوت مراقبة الذهب والفضة")
            self.logger.info("=" * 50)
            
            # ===== 1. الاتصال بـ MetaTrader 5 =====
            self.logger.info("محاولة الاتصال بـ MetaTrader 5...")
            if not self.mt5_connector.connect():
                self.logger.error("فشل الاتصال بـ MetaTrader 5")
                return False
            
            self.logger.info("✅ تم الاتصال بـ MetaTrader 5 بنجاح")
            
            # ===== 2. إرسال رسالة الترحيب إلى Telegram =====
            self.logger.info("إرسال رسالة الترحيب إلى Telegram...")
            await self.telegram_manager.send_welcome_message()
            self.logger.info("✅ تم إرسال رسالة الترحيب")
            
            # ===== 3. جلب الأسعار الحالية =====
            self.logger.info("جلب الأسعار الحالية للذهب والفضة...")
            current_prices = self.mt5_connector.get_current_prices()
            
            if current_prices:
                self.logger.info("✅ تم جلب الأسعار الحالية:")
                self.logger.info(f"  الذهب: {current_prices['gold']['ask']}")
                self.logger.info(f"  الفضة: {current_prices['silver']['ask']}")
                
                # إرسال تحديث الأسعار إلى Telegram
                await self.telegram_manager.send_prices_update(current_prices)
            else:
                self.logger.warning("فشل جلب الأسعار الحالية")
            
            # ===== 4. جلب بيانات الشمعة السابقة وحساب الارتكاز =====
            self.logger.info("جلب بيانات الشمعة السابقة للذهب...")
            gold_candle = self.mt5_connector.get_last_candle_data("XAUUSD.x")
            
            if gold_candle:
                self.logger.info("✅ تم جلب بيانات شمعة الذهب:")
                self.logger.info(f"  Open: {gold_candle['open']}")
                self.logger.info(f"  High: {gold_candle['high']}")
                self.logger.info(f"  Low: {gold_candle['low']}")
                self.logger.info(f"  Close: {gold_candle['close']}")
                
                # ===== 5. حساب مستويات الارتكاز =====
                self.logger.info("حساب مستويات الارتكاز للذهب...")
                pivot_data = self.pivot_calculator.calculate_pivot_points(gold_candle)
                
                if pivot_data:
                    self.logger.info("✅ تم حساب مستويات الارتكاز:")
                    pivot_points = pivot_data['pivot_points']
                    self.logger.info(f"  R3: {pivot_points['R3']}")
                    self.logger.info(f"  R2: {pivot_points['R2']}")
                    self.logger.info(f"  R1: {pivot_points['R1']}")
                    self.logger.info(f"  Pivot: {pivot_points['Pivot']}")
                    self.logger.info(f"  S1: {pivot_points['S1']}")
                    self.logger.info(f"  S2: {pivot_points['S2']}")
                    self.logger.info(f"  S3: {pivot_points['S3']}")
                    
                    # إرسال تقرير الارتكاز إلى Telegram
                    self.logger.info("إرسال تقرير مستويات الارتكاز إلى Telegram...")
                    await self.telegram_manager.send_pivot_points_report(pivot_data, current_prices)
                    self.logger.info("✅ تم إرسال تقرير الارتكاز")
                else:
                    self.logger.error("فشل حساب مستويات الارتكاز")
            else:
                self.logger.warning("فشل جلب بيانات شمعة الذهب")
            
            # جلب بيانات الفضة أيضًا
            self.logger.info("جلب بيانات الشمعة السابقة للفضة...")
            silver_candle = self.mt5_connector.get_last_candle_data("XAGUSD.x")
            
            if silver_candle:
                self.logger.info("✅ تم جلب بيانات شمعة الفضة")
                self.logger.info(f"  Close: {silver_candle['close']}")
                
                pivot_data_silver = self.pivot_calculator.calculate_pivot_points(silver_candle)
                if pivot_data_silver:
                    self.logger.info("✅ تم حساب مستويات الارتكاز للفضة")
            
            self.logger.info("=" * 50)
            self.logger.info("✅ اكتمل بدء التشغيل بنجاح!")
            self.logger.info("=" * 50)
            
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ أثناء بدء التشغيل: {str(e)}")
            return False
    
    def shutdown(self) -> None:
        """إيقاف البوت وقطع جميع الاتصالات"""
        try:
            self.logger.info("=" * 50)
            self.logger.info("إيقاف البوت...")
            self.logger.info("=" * 50)
            
            self.mt5_connector.disconnect()
            self.logger.info("✅ تم قطع الاتصال بـ MetaTrader 5")
            
        except Exception as e:
            self.logger.error(f"خطأ أثناء الإيقاف: {str(e)}")
    
    async def run(self) -> None:
        """تشغيل البوت الرئيسي"""
        try:
            # بدء التشغيل
            if not await self.startup():
                self.logger.error("فشل بدء التشغيل")
                self.shutdown()
                return
            
            # إبقاء البوت قيد التشغيل
            self.logger.info("البوت في وضع التشغيل... اضغط Ctrl+C للإيقاف")
            
            # بقاء البرنامج مفتوحًا
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("تم استقبال إشارة الإيقاف من المستخدم")
        
        finally:
            self.shutdown()


# ===== نقطة البداية =====
async def main():
    """الدالة الرئيسية"""
    bot = GoldSilverMonitorBot()
    await bot.run()


if __name__ == "__main__":
    # تشغيل البرنامج
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"خطأ في البرنامج الرئيسي: {str(e)}")
        sys.exit(1)
