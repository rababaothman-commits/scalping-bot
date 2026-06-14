# بوت مراقبة الذهب والفضة 🥇🥈

برنامج Python بسيط وفعّال لمراقبة أسعار الذهب (XAUUSD) والفضة (XAGUSD)، مع حساب مستويات الارتكاز اليومية وإرسال التنبيهات عبر Telegram.

---

## المميزات ✨

- ✅ الاتصال بـ MetaTrader 5 وجلب الأسعار الحالية
- ✅ حساب مستويات الارتكاز (Pivot Points) بناءً على بيانات الشمعة السابقة
- ✅ إرسال التقارير والتنبيهات عبر Telegram
- ✅ تصميم معياري قابل للتوسع
- ✅ دعم متغيرات البيئة (Environment Variables)
- ✅ جاهز للنشر على منصات السحابة مثل Railway

---

## البنية الأساسية للمشروع 📁

```
.
├── main.py                 # الملف الرئيسي - بدء التطبيق
├── mt5_connector.py        # الاتصال بـ MetaTrader 5
├── pivot_calculator.py     # حساب مستويات الارتكاز
├── telegram_bot.py         # إدارة بوت Telegram
├── requirements.txt        # المكتبات المطلوبة
├── Procfile               # تعريف عملية التشغيل على Railway
├── .env.example           # مثال على متغيرات البيئة
├── bot_logs.log           # ملف السجلات (يتم إنشاؤه تلقائيًا)
└── README.md              # هذا الملف
```

---

## المتطلبات 🔧

### على جهاز التطوير المحلي:
- **Python 3.8+**
- **حساب MetaTrader 5** (Demo أو Real)
- **بوت Telegram** (يتم إنشاؤه عبر BotFather)
- **git** (اختياري، للتحكم بالإصدارات)

### على Railway:
- لا تحتاج إلى تثبيت أي شيء! Railway يتولى كل شيء تلقائيًا

---

## طريقة الإعداد والتشغيل 🚀

### الخطوة 1: تجهيز حساب MetaTrader 5

1. **تحميل MetaTrader 5** من [هنا](https://www.metatrader5.com/en/download)
2. **فتح حساب Demo/Real**
3. **الحصول على بيانات الدخول:**
   - رقم الحساب (Login)
   - كلمة المرور (Password)
   - اسم السيرفر (Server Name)
   
   > يمكنك العثور على هذه البيانات في نافذة "خصائص الحساب" في MT5

### الخطوة 2: إنشاء بوت Telegram

1. **افتح Telegram وابحث عن** `@BotFather`
2. **اكتب** `/newbot` واتبع التعليمات
3. **احصل على:**
   - **Bot Token**: مثل `123456789:ABCdefGHIjklmNOpqrsTUVwxyz`
   - **Chat ID**: اكتب `/start` مع البوت الجديد ثم اكتب `/my_id` في `@userinfobot` للحصول عليه

### الخطوة 3: الإعداد المحلي (اختياري للاختبار)

```bash
# 1. استنساخ المشروع أو نسخ الملفات
git clone <repo-url>
cd gold-silver-monitor

# 2. إنشاء ملف .env
cp .env.example .env

# 3. تحرير ملف .env وإدخال البيانات الخاصة بك
# اضغط على الملف وأدخل:
# MT5_LOGIN=your_login_here
# MT5_PASSWORD=your_password_here
# MT5_SERVER=your_server_here
# TELEGRAM_BOT_TOKEN=your_bot_token_here
# TELEGRAM_CHAT_ID=your_chat_id_here

# 4. تثبيت المكتبات
pip install -r requirements.txt

# 5. تشغيل البوت
python main.py
```

---

## طريقة النشر على Railway 🚂

### الطريقة الأولى: عبر واجهة Railway الويب

1. **قم بـ Push الملفات إلى GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/your-repo.git
   git push -u origin main
   ```

2. **انتقل إلى [Railway.app](https://railway.app)**

3. **انقر على "New Project" ثم اختر "Deploy from GitHub"**

4. **اختر المستودع الخاص بك**

5. **أضف متغيرات البيئة:**
   - اذهب إلى "Variables" في لوحة التحكم
   - أضف المتغيرات التالية:
     ```
     MT5_LOGIN=your_login
     MT5_PASSWORD=your_password
     MT5_SERVER=your_server
     TELEGRAM_BOT_TOKEN=your_bot_token
     TELEGRAM_CHAT_ID=your_chat_id
     LOG_LEVEL=INFO
     CHECK_INTERVAL=3600
     ```

6. **انقر على "Deploy"** وانتظر اكتمال النشر

### الطريقة الثانية: عبر Railway CLI

```bash
# 1. تثبيت Railway CLI
npm install -g @railway/cli

# 2. تسجيل الدخول
railway login

# 3. إنشاء مشروع جديد
railway init

# 4. إضافة متغيرات البيئة
railway variables set MT5_LOGIN=your_login
railway variables set MT5_PASSWORD=your_password
railway variables set MT5_SERVER=your_server
railway variables set TELEGRAM_BOT_TOKEN=your_bot_token
railway variables set TELEGRAM_CHAT_ID=your_chat_id

# 5. نشر المشروع
railway up
```

---

## شرح الملفات الرئيسية 📄

### `main.py`
الملف الرئيسي الذي يجمع كل المكونات معًا:
- تهيئة المكونات
- الاتصال بـ MT5
- إرسال رسالة الترحيب إلى Telegram
- جلب البيانات وحساب مستويات الارتكاز

### `mt5_connector.py`
مسؤول عن الاتصال بـ MetaTrader 5:
- `connect()`: الاتصال بـ MT5
- `get_current_prices()`: جلب الأسعار الحالية
- `get_last_candle_data()`: جلب بيانات الشمعة السابقة

### `pivot_calculator.py`
حساب مستويات الارتكاز:
- `calculate_pivot_points()`: الطريقة الكلاسيكية
- `calculate_camarilla_levels()`: طريقة Camarilla (بديلة)

### `telegram_bot.py`
إدارة بوت Telegram:
- `send_welcome_message()`: رسالة الترحيب
- `send_prices_update()`: تحديث الأسعار
- `send_pivot_points_report()`: تقرير مستويات الارتكاز
- `send_error_message()`: رسائل الخطأ

---

## متغيرات البيئة 🔐

| المتغير | الوصف | مثال |
|--------|-------|------|
| `MT5_LOGIN` | رقم حساب MetaTrader 5 | `123456789` |
| `MT5_PASSWORD` | كلمة مرور MT5 | `password123` |
| `MT5_SERVER` | اسم السيرفر | `ICMarkets-Demo` |
| `TELEGRAM_BOT_TOKEN` | توكن البوت | `123456:ABC...` |
| `TELEGRAM_CHAT_ID` | معرف المحادثة | `123456789` |
| `LOG_LEVEL` | مستوى السجلات | `INFO` |
| `CHECK_INTERVAL` | فترة الفحص (بالثواني) | `3600` |

---

## معادلات مستويات الارتكاز 📊

### الطريقة الكلاسيكية (Classic Pivot Points):
```
Pivot = (High + Low + Close) / 3

المقاومة:
R1 = (2 × Pivot) - Low
R2 = Pivot + (High - Low)
R3 = High + 2 × (Pivot - Low)

الدعم:
S1 = (2 × Pivot) - High
S2 = Pivot - (High - Low)
S3 = Low - 2 × (High - Pivot)
```

### طريقة Camarilla (اختيارية):
```
Range = High - Low

H4 = Close + 1.5 × Range
H3 = Close + 1.25 × Range
H2 = Close + Range
H1 = Close + 0.5 × Range

L1 = Close - 0.5 × Range
L2 = Close - Range
L3 = Close - 1.25 × Range
L4 = Close - 1.5 × Range
```

---

## استكشاف الأخطاء 🐛

### المشكلة: "فشل الاتصال بـ MetaTrader 5"
**الحل:**
- تأكد من أن MT5 قيد التشغيل
- تحقق من صحة بيانات الدخول
- تأكد من أن اسم السيرفر صحيح

### المشكلة: "خطأ في إرسال رسالة Telegram"
**الحل:**
- تحقق من صحة Bot Token
- تحقق من صحة Chat ID
- تأكد من أن الإنترنت متصل

### المشكلة: "فشل جلب الأسعار"
**الحل:**
- تأكد من أن الرموز (XAUUSD, XAGUSD) متاحة في حسابك
- تحقق من أن السوق مفتوح
- تأكد من أن الاتصال بـ MT5 نشط

---

## الخطوات التالية 📈

في المراحل المستقبلية، يمكن إضافة:

1. **مراقبة مستمرة:** تحديث الأسعار كل دقيقة/ساعة
2. **تنبيهات مخصصة:** إرسال تنبيهات عند وصول السعر لمستويات معينة
3. **استراتيجيات تداول:** إضافة منطق لفتح وإغلاق الصفقات
4. **قاعدة بيانات:** حفظ البيانات التاريخية
5. **لوحة تحكم ويب:** واجهة مستخدم لمراقبة الأداء

---

## الترخيص 📜

هذا المشروع مفتوح المصدر. يمكنك استخدامه وتعديله بحرية.

---

## التواصل والدعم 💬

إذا واجهت أي مشاكل:
1. تحقق من السجلات في ملف `bot_logs.log`
2. اقرأ رسائل الخطأ بعناية
3. تأكد من أن جميع متغيرات البيئة محددة بشكل صحيح

---

**نتمنى لك استخدامًا سعيدًا! 🚀**
