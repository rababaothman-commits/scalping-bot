import os
import logging
import requests
requests.packages.urllib3.disable_warnings()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import yfinance as yf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name_)

TOKEN = os.environ.get("TOKEN")

PAIRS = {
    "GOLD":      {"symbol": "GC=F",      "name": "XAUUSD 🥇",  "ar": "الذهب"},
    "SILVER":    {"symbol": "SI=F",      "name": "XAGUSD 🥈",  "ar": "الفضة"},
    "NASDAQ":    {"symbol": "NQ=F",      "name": "NASDAQ 📊",  "ar": "ناسداك"},
    "DOW_JONES": {"symbol": "YM=F",      "name": "US30 📈",    "ar": "داو جونز"},
    "EURUSD":    {"symbol": "EURUSD=X",  "name": "EUR/USD 🇪🇺", "ar": "يورو/دولار"},
    "USDJPY":    {"symbol": "USDJPY=X",  "name": "USD/JPY 🇯🇵", "ar": "دولار/ين"},
    "GBPUSD":    {"symbol": "GBPUSD=X",  "name": "GBP/USD 🇬🇧", "ar": "جنيه/دولار"},
    "BITCOIN":   {"symbol": "BTC-USD",   "name": "BITCOIN ₿",  "ar": "بيتكوين"},
    "OIL":       {"symbol": "CL=F",      "name": "USOIL 🛢️",   "ar": "النفط"}
}

SCALP = {
    "GOLD":      {"tp": 0.0015, "sl": 0.0010},
    "SILVER":    {"tp": 0.0020, "sl": 0.0012},
    "NASDAQ":    {"tp": 0.0015, "sl": 0.0010},
    "DOW_JONES": {"tp": 0.0015, "sl": 0.0010},
    "EURUSD":    {"tp": 0.0010, "sl": 0.0007},
    "USDJPY":    {"tp": 0.0010, "sl": 0.0007},
    "GBPUSD":    {"tp": 0.0010, "sl": 0.0007},
    "BITCOIN":   {"tp": 0.0025, "sl": 0.0015},
    "OIL":       {"tp": 0.0020, "sl": 0.0012},
}

def get_scalp_data(pair):
    try:
        symbol = PAIRS[pair]["symbol"]
        logger.info(f"Fetching {symbol}")

        tk  = yf.Ticker(symbol)
        h5  = tk.history(period="1d", interval="5m")
        h15 = tk.history(period="5d", interval="15m")

        if h5.empty or len(h5) < 20:
            logger.warning(f"5m data empty for {symbol}")
            return None
        if h15.empty or len(h15) < 20:
            logger.warning(f"15m data empty for {symbol}")
            return None

        price = round(float(h5['Close'].iloc[-1]), 5)

        # ── 5M indicators ──────────────────────────────────────────
        delta5 = h5['Close'].diff()
        gain5  = delta5.where(delta5 > 0, 0).rolling(14).mean().iloc[-1]
        loss5  = -delta5.where(delta5 < 0, 0).rolling(14).mean().iloc[-1]
        rsi5   = round(100 - (100 / (1 + gain5 / loss5)), 1) if loss5 and loss5 != 0 else 100.0

        ema9_5  = float(h5['Close'].ewm(span=9,  adjust=False).mean().iloc[-1])
        ema21_5 = float(h5['Close'].ewm(span=21, adjust=False).mean().iloc[-1])

        low14_5  = float(h5['Low'].rolling(14).min().iloc[-1])
        high14_5 = float(h5['High'].rolling(14).max().iloc[-1])
        stoch5   = round(100 * (price - low14_5) / (high14_5 - low14_5), 1) if (high14_5 - low14_5) != 0 else 50.0

        ema12_5  = h5['Close'].ewm(span=12, adjust=False).mean()
        ema26_5  = h5['Close'].ewm(span=26, adjust=False).mean()
        macd5    = float((ema12_5 - ema26_5).iloc[-1])
        signal5  = float((ema12_5 - ema26_5).ewm(span=9, adjust=False).mean().iloc[-1])
        macd_cross5 = "🟢 صاعد" if macd5 > signal5 else "🔴 هابط"

        # ── 15M indicators ─────────────────────────────────────────
        delta15 = h15['Close'].diff()
        gain15  = delta15.where(delta15 > 0, 0).rolling(14).mean().iloc[-1]
        loss15  = -delta15.where(delta15 < 0, 0).rolling(14).mean().iloc[-1]
        rsi15   = round(100 - (100 / (1 + gain15 / loss15)), 1) if loss15 and loss15 != 0 else 100.0

        ema9_15  = float(h15['Close'].ewm(span=9,  adjust=False).mean().iloc[-1])
        ema21_15 = float(h15['Close'].ewm(span=21, adjust=False).mean().iloc[-1])

        low14_15  = float(h15['Low'].rolling(14).min().iloc[-1])
        high14_15 = float(h15['High'].rolling(14).max().iloc[-1])
        stoch15   = round(100 * (price - low14_15) / (high14_15 - low14_15), 1) if (high14_15 - low14_15) != 0 else 50.0

        # ── Support / Resistance ───────────────────────────────────
        recent = h15.tail(20)
        res = round(float(recent['High'].max()), 5)
        sup = round(float(recent['Low'].min()), 5)
        mid = round((res + sup) / 2, 5)

        # ── Signal logic ───────────────────────────────────────────
        tp_pct = SCALP[pair]["tp"]
        sl_pct = SCALP[pair]["sl"]

        buy_score  = sum([rsi5 < 35, rsi15 < 40, stoch5 < 25, price > ema9_15, macd5 > signal5])
        sell_score = sum([rsi5 > 65, rsi15 > 60, stoch5 > 75, price < ema9_15, macd5 < signal5])

        if buy_score >= 3:
            sig      = "🟢 شراء سكالبينج"
            entry    = price
            tp       = round(price * (1 + tp_pct), 5)
            sl       = round(price * (1 - sl_pct), 5)
            strength = "⭐" * buy_score
        elif sell_score >= 3:
            sig      = "🔴 بيع سكالبينج"
            entry    = price
            tp       = round(price * (1 - tp_pct), 5)
            sl       = round(price * (1 + sl_pct), 5)
            strength = "⭐" * sell_score
        else:
            sig      = "⏸️ انتظار إشارة"
            entry    = None
            tp       = None
            sl       = None
            strength = ""

        trend5  = "🔼 صاعد" if ema9_5  > ema21_5  else "🔽 هابط"
        trend15 = "🔼 صاعد" if ema9_15 > ema21_15 else "🔽 هابط"

        return {
            "price": price,
            "rsi5": rsi5,     "rsi15": rsi15,
            "stoch5": stoch5, "stoch15": stoch15,
            "macd_cross5": macd_cross5,
            "trend5": trend5, "trend15": trend15,
            "res": res, "sup": sup, "mid": mid,
            "sig": sig, "entry": entry, "tp": tp, "sl": sl,
            "strength": strength
        }

    except Exception as e:
        logger.error(f"Error fetching {pair}: {e}")
        return None


def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 مسح الكل", callback_data="ALL")],
        [InlineKeyboardButton("🥇 GOLD",      callback_data="GOLD"),
         InlineKeyboardButton("🥈 SILVER",    callback_data="SILVER")],
        [InlineKeyboardButton("📊 NASDAQ",    callback_data="NASDAQ"),
         InlineKeyboardButton("📈 US30",      callback_data="DOW_JONES")],
        [InlineKeyboardButton("🇪🇺 EUR/USD",  callback_data="EURUSD"),
         InlineKeyboardButton("🇯🇵 USD/JPY",  callback_data="USDJPY")],
        [InlineKeyboardButton("🇬🇧 GBP/USD",  callback_data="GBPUSD"),
         InlineKeyboardButton("₿ BITCOIN",    callback_data="BITCOIN")],
        [InlineKeyboardButton("🛢️ OIL",       callback_data="OIL")]
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="back")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ بوت سكالبينج الاحترافي\n"
        "━━━━━━━━━━━━━━━━\n"
        "📊 تحليل على فريم 5M و 15M فقط\n"
        "🎯 إشارات دخول وخروج سريعة\n"
        "━━━━━━━━━━━━━━━━\n"
        "اختر الزوج 👇",
        reply_markup=main_keyboard()
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "back":
        await q.edit_message_text(
            "⚡ بوت سكالبينج الاحترافي\n"
            "━━━━━━━━━━━━━━━━\n"
            "📊 تحليل على فريم 5M و 15M فقط\n"
            "🎯 إشارات دخول وخروج سريعة\n"
            "━━━━━━━━━━━━━━━━\n"
            "اختر الزوج 👇",
            reply_markup=main_keyboard()
        )
        return

    if q.data == "ALL":
        await q.edit_message_text("⏳ جاري مسح الأسواق...", reply_markup=None)
        msg = "⚡ مسح سكالبينج - جميع الأزواج\n━━━━━━━━━━━━━━━━━━━━\n"
        for key in PAIRS:
            d = get_scalp_data(key)
            if d:
                icon = "🟢" if "شراء" in d['sig'] else ("🔴" if "بيع" in d['sig'] else "⏸️")
                msg += f"{icon} {PAIRS[key]['name']}: {d['price']}  |  {d['sig']}\n"
            else:
                msg += f"❌ {PAIRS[key]['name']}: خطأ\n"
        await q.edit_message_text(msg, reply_markup=back_keyboard())
        return

    await q.edit_message_text("⏳ جاري التحليل...", reply_markup=None)
    d = get_scalp_data(q.data)
    if not d:
        await q.edit_message_text(
            "❌ خطأ في جلب البيانات\n"
            "السوق مغلق أو البيانات غير متاحة الآن\n"
            "حاول مرة أخرى بعد قليل",
            reply_markup=back_keyboard()
        )
        return

    name = PAIRS[q.data]['name']
    msg = (
        f"{'━'*22}\n⚡ {name}  —  سكالبينج\n{'━'*22}\n\n"
        f"💰 السعر الحالي : {d['price']}\n\n"
        f"📊 فريم 5 دقائق:\n"
        f"  RSI    : {d['rsi5']}\n"
        f"  Stoch  : {d['stoch5']}\n"
        f"  MACD   : {d['macd_cross5']}\n"
        f"  الاتجاه: {d['trend5']}\n\n"
        f"📊 فريم 15 دقيقة:\n"
        f"  RSI    : {d['rsi15']}\n"
        f"  Stoch  : {d['stoch15']}\n"
        f"  الاتجاه: {d['trend15']}\n\n"
        f"{'━'*22}\n"
        f"📌 المستويات:\n"
        f"  🔴 مقاومة : {d['res']}\n"
        f"  ⚪ وسط    : {d['mid']}\n"
        f"  🟢 دعم    : {d['sup']}\n\n"
        f"{'━'*22}\n"
        f"🎯 الإشارة: {d['sig']}  {d['strength']}\n"
    )
    if d['entry']:
        rr = round(abs(d['tp'] - d['entry']) / abs(d['sl'] - d['entry']), 2) if d['sl'] != d['entry'] else 0
        msg += (
            f"\n💵 الدخول       : {d['entry']}"
            f"\n🎯 الهدف        : {d['tp']}"
            f"\n🛑 وقف الخسارة : {d['sl']}"
            f"\n⚖️ RR           : 1:{rr}"
        )
    else:
        msg += "\n⚠️ انتظر تأكيداً أقوى للدخول"
    msg += f"\n{'━'*22}"

    await q.edit_message_text(msg, reply_markup=back_keyboard())


app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
print("⚡ Scalping Bot is running!")
app.run_polling(drop_pending_updates=True)
