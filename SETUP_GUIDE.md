# دليل الإعداد التفصيلي 📋

هذا الملف يشرح بالتفصيل كيفية الحصول على كل بيانة مطلوبة لتشغيل البوت.

---

## 1️⃣ الحصول على بيانات MetaTrader 5 💼

### متى تحتاج إلى بيانات MT5؟
عندما تريد تشغيل البوت على منصة Railway، تحتاج إلى:
- **MT5_LOGIN**: رقم حسابك
- **MT5_PASSWORD**: كلمة المرور الخاصة بحسابك
- **MT5_SERVER**: اسم خادم الوسيط

### خطوات الحصول على البيانات:

#### الخطوة 1: تثبيت MetaTrader 5
1. انتقل إلى [موقع MetaTrader 5 الرسمي](https://www.metatrader5.com)
2. اختر "تنزيل" واختر نظام التشغيل الخاص بك
3. ثبت البرنامج

#### الخطوة 2: فتح حساب Demo أو Real
1. افتح MetaTrader 5
2. اختر من القائمة: **File > Open an Account**
3. اختر الوسيط الذي تريد (مثل: Pepperstone, ICMarkets, وغيرها)
4. اختر نوع الحساب:
   - **Demo Account**: لا تحتاج أموال حقيقية (للاختبار)
   - **Real Account**: تحتاج أموال حقيقية (للتداول الفعلي)

#### الخطوة 3: الحصول على بيانات الدخول
1. بعد فتح الحساب، ستظهر نافذة بـ:
   - رقم الحساب (Login)
   - كلمة المرور (Password)
   - اسم السيرفر (Server)
2. **احفظ هذه البيانات بأمان**

#### الخطوة 4: التحقق من البيانات
في MT5، انظر في الزاوية العلوية اليسرى:
```
الحساب: 123456789 (هذا هو MT5_LOGIN)
السيرفر: ICMarkets-Demo (هذا هو MT5_SERVER)
```

#### الخطوة 5: التأكد من توفر رموز XAUUSD و XAGUSD
1. في MT5، انقر بزر الماوس الأيمن على **Market Watch**
2. اختر **Show All Symbols** أو **Symbols**
3. ابحث عن:
   - **XAUUSD** (الذهب)
   - **XAGUSD** (الفضة)
4. تأكد من أنهما موجودان (يجب أن يكونا أزرقين أو بارزين)

---

## 2️⃣ الحصول على بيانات Telegram Bot 📱

### متى تحتاج إلى بيانات Telegram؟
عندما تريد أن يرسل البوت الرسائل إليك، تحتاج إلى:
- **TELEGRAM_BOT_TOKEN**: توكن البوت الفريد
- **TELEGRAM_CHAT_ID**: معرف محادثتك مع البوت

### خطوات الحصول على البيانات:

#### الخطوة 1: إنشاء البوت
1. افتح Telegram (تطبيق أو ويب)
2. ابحث عن **@BotFather** (هذا هو البوت الرسمي لإدارة البوتات)
3. انقر على **Start** أو اكتب `/start`
4. اكتب `/newbot`
5. سيطلب منك:
   - **اسم البوت** (مثل: Gold Silver Bot)
   - **اسم المستخدم للبوت** (يجب أن ينتهي بـ "bot"، مثل: gold_silver_bot)

#### الخطوة 2: الحصول على Bot Token
بعد إنشاء البوت، سيرسل لك BotFather رسالة تحتوي على:
```
Done! Congratulations on your new bot. 
You will find it at t.me/gold_silver_bot. 
You can now add a description, about section and profile picture for your bot, see /help for a list of commands.

Use this token to access the HTTP API:
123456789:ABCdefGHIjklmNOpqrsTUVwxyzABCdefGHI

Keep your token secure and store it safely, it can be used by anyone to control your bot.
```

> **⚠️ احفظ هذا التوكن في مكان آمن! لا تشاركه مع أحد!**

البوت توكن = `123456789:ABCdefGHIjklmNOpqrsTUVwxyzABCdefGHI`

#### الخطوة 3: الحصول على Chat ID
الآن تحتاج إلى معرف محادثتك (Chat ID):

**الطريقة الأولى (سهلة):**
1. ابحث عن البوت **@userinfobot**
2. انقر على **Start**
3. سيخبرك برقم معرف محادثتك (Chat ID)
4. سينسخ الرقم مباشرة

**الطريقة الثانية (يدوية):**
1. ابحث عن البوت **@JsonDumpBot**
2. انقر على **Start**
3. سيظهر لك JSON يحتوي على `"id"` (هذا هو Chat ID)

**الطريقة الثالثة (عبر BotFather):**
1. في @BotFather، اكتب `/mybots`
2. اختر البوت الذي أنشأته
3. انقر على **Edit Bot** ثم **Edit Commands**
4. أضف أي أمر مثل:
   - `/start` - يبدأ البوت
   - `/help` - يعرض المساعدة

5. أرسل رسالة إلى البوت الخاص بك (أي رسالة)
6. افتح هذا الرابط في المتصفح:
```
https://api.telegram.org/bot[YOUR_BOT_TOKEN]/getUpdates
```
استبدل `[YOUR_BOT_TOKEN]` بتوكنك الفعلي

7. ستظهر استجابة JSON. ابحث عن:
```json
"message": {
  "chat": {
    "id": 123456789,
    ...
  }
}
```

Chat ID = `123456789`

---

## 3️⃣ ملخص البيانات المطلوبة 📝

اجمع كل البيانات التالية:

| الاسم | القيمة | مثال | الملاحظات |
|------|-------|------|----------|
| **MT5_LOGIN** | رقم حسابك في MT5 | `123456789` | من خصائص الحساب في MT5 |
| **MT5_PASSWORD** | كلمة مرور MT5 | `MyPassword123!` | لا تنسَ كلمة المرور! |
| **MT5_SERVER** | اسم سيرفر الوسيط | `ICMarkets-Demo` | موجود في زاوية MT5 |
| **TELEGRAM_BOT_TOKEN** | توكن البوت | `123456789:ABC...` | من @BotFather |
| **TELEGRAM_CHAT_ID** | رقم معرف محادثتك | `987654321` | من @userinfobot أو @JsonDumpBot |

---

## 4️⃣ إضافة البيانات إلى الملف `.env` 🔒

### على جهازك المحلي:

1. افتح المجلد الذي يحتوي على الملفات
2. أنشئ ملف بنفس اسم `.env.example` لكن اسمه `.env` (بدون `.example`)
3. انسخ محتوى `.env.example`:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
MT5_LOGIN=your_mt5_login_here
MT5_PASSWORD=your_mt5_password_here
MT5_SERVER=your_mt5_server_here
LOG_LEVEL=INFO
CHECK_INTERVAL=3600
```

4. استبدل `your_...` بالقيم الفعلية:
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmNOpqrsTUVwxyzABCdefGHI
TELEGRAM_CHAT_ID=987654321
MT5_LOGIN=123456789
MT5_PASSWORD=MyPassword123!
MT5_SERVER=ICMarkets-Demo
LOG_LEVEL=INFO
CHECK_INTERVAL=3600
```

5. **احفظ الملف**

### على منصة Railway:

1. في لوحة تحكم Railway، اذهب إلى مشروعك
2. انقر على **Variables**
3. أضف كل متغير:
   - انقر **+ Add Variable**
   - ادخل الاسم والقيمة
4. **احفظ التغييرات**

---

## 5️⃣ اختبار البيانات ✅

بعد إدخال البيانات، يمكنك اختبارها:

### محليًا:
```bash
python main.py
```

إذا رأيت رسائل خضراء بدون أخطاء، فالبيانات صحيحة! ✅

### على Railway:
انقر على **Deploy** وشاهد السجلات. يجب أن ترى:
```
✅ تم الاتصال بـ MetaTrader 5 بنجاح
✅ تم إرسال رسالة الترحيب
✅ تم جلب الأسعار الحالية
```

---

## 6️⃣ أسئلة شائعة ❓

### س: ماذا لو نسيت كلمة المرور؟
**الجواب:** يمكنك إعادة تعيين كلمة المرور من خلال موقع وسيطك.

### س: هل يمكن استخدام حساب Real بدلاً من Demo؟
**الجواب:** نعم، لكن تأكد من أنك تريد ذلك! استخدم Demo للاختبار أولاً.

### س: ماذا لو فشل الاتصال بـ MT5 على Railway؟
**الجواب:** Railway قد لا يتمكن من الاتصال بـ MT5 مباشرة (قد يكون حظرًا من المنصة). في هذه الحالة، يمكنك:
- استخدام API وسيط آخر
- استخدام سيرفر VPS خاص يدعم MT5

### س: هل البيانات آمنة على Railway؟
**الجواب:** نعم، Railway تشفر المتغيرات. لكن **لا تشارك توكن البوت مع أحد!**

---

## 7️⃣ نصائح الأمان 🔐

✅ **افعل:**
- احفظ البيانات في مكان آمن
- استخدم حساب Demo للاختبار أولاً
- غيّر كلمة مرورك بانتظام

❌ **لا تفعل:**
- لا تشارك `.env` ملفك مع أحد
- لا تضع البيانات في التعليقات على GitHub
- لا تشارك توكن البوت

---

**إذا اتبعت هذه الخطوات بعناية، سيعمل البوت بنجاح! 🎉**
