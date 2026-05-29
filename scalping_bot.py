import os
import requests

TOKEN = os.environ.get("TOKEN")
TWELVE_KEY = os.environ.get("TWELVE_KEY")

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Twelve Data symbols
PAIRS = {
    "GOLD":      {"symbol": "XAU/USD",  "name": "XAUUSD 🥇",  "ar": "الذهب"},
    "SILVER":    {"symbol": "XAG/USD",  "name": "XAGUSD 🥈",  "ar": "الفضة"},
    "NASDAQ":    {"symbol": "IXIC",     "name": "NASDAQ 📊",  "ar": "ناسداك"},
    "DOW_JONES": {"symbol": "DJI",      "name": "US30 📈",    "ar": "داو جونز"},
    "EURUSD":    {"symbol": "EUR/USD",  "name": "EUR/USD 🇪🇺", "ar": "يورو/دولار"},
    "USDJPY":    {"symbol": "USD/JPY",  "name": "USD/JPY 🇯🇵", "ar": "دولار/ين"},
    "GBPUSD":    {"symbol": "GBP/USD",  "name": "GBP/USD 🇬🇧", "ar": "جنيه/دولار"},
    "BITCOIN":   {"symbol": "BTC/USD",  "name": "BITCOIN ₿",  "ar": "بيتكوين"},
    "OIL":       {"symbol": "WTI/USD",  "name": "USOIL 🛢️",   "ar": "النفط"}
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


def ema(values, span):
    k = 2 / (span + 1)
    e = values[0]
    for v in values[1:]:
        e = v * k + e * (1 - k)
    return e


def rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


def fetch_series(symbol, interval):
    """Fetch candles from Twelve Data. Returns lists of close/high/low, newest last."""
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": 50,
        "apikey": TWELVE_KEY,
    }
    r = requests.get(url, params=params, timeout=30)
    data = r.json()
    if data.get("status") == "error" or "values" not in data:
        print(f"TwelveData error for {symbol} {interval}: {data}")
        return None
    vals = list(reversed(data["values"]))  # API returns newest first
    closes = [float(v["close"]) for v in vals]
    highs  = [float(v["high"])  for v in vals]
    lows   = [float(v["low"])   for v in vals]
    return {"close": closes, "high": highs, "low": lows}


def get_scalp_data(pair):
    try:
        symbol = PAIRS[pair]["symbol"]
        print(f"Fetching {symbol}")

        s5  = fetch_series(symbol, "5min")
        s15 = fetch_series(symbol, "15min")

        if not s5 or len(s5["close"]) < 20:
            print(f"5m data empty for {symbol}")
            return None
        if not s15 or len(s15["close"]) < 20:
            print(f"15m data empty for {symbol}")
            return None

        price = round(s5["close"][-1], 5)

        # 5M indicators
        rsi5 = rsi(s5["close"])
        ema9_5  = ema(s5["close"][-30:], 9)
        ema21_5 = ema(s5["close"][-30:], 21)
        low14_5  = min(s5["low"][-14:])
        high14_5 = max(s5["high"][-14:])
        stoch5 = round(100 * (price - low14_5) / (high14_5 - low14_5), 1) if (high14_5 - low14_5) != 0 else 50.0
        ema12_5 = ema(s5["close"], 12)
        ema26_5 = ema(s5["close"], 26)
        macd5 = ema12_5 - ema26_5
        macd_cross5 = "🟢 صاعد" if macd5 > 0 else "🔴 هابط"

        # 15M indicators
        rsi15 = rsi(s15["close"])
        ema9_15  = ema(s15["close"][-30:], 9)
        ema21_15 = ema(s15["close"][-30:], 21)
        low14_15  = min(s15["low"][-14:])
        high14_15 = max(s15["high"][-14:])
        stoch15 = round(100 * (price - low14_15) / (high14_15 - low14_15), 1) if (high14_15 - low14_15) != 0 else 50.0

        # S/R from last 20 of 15M
        res = round(max(s15["high"][-20:]), 5)
        sup = round(min(s15["low"][-20:]), 5)
        mid = round((res + sup) / 2, 5)

        tp_pct = SCALP[pair]["tp"]
        sl_pct = SCALP[pair]["sl"]

        buy_score  = sum([rsi5 < 35, rsi15 < 40, stoch5 < 25, price > ema9_15, macd5 > 0])
        sell_score = sum([rsi5 > 65, rsi15 > 60, stoch5 > 75, price < ema9_15, macd5 < 0])

        if buy_score >= 3:
            sig = "🟢 شراء سكالبينج"; entry = price
            tp = round(price * (1 + tp_pct), 5); sl = round(price * (1 - sl_pct), 5)
            strength = "⭐" * buy_score
        elif sell_score >= 3:
            sig = "🔴 بيع سكالبينج"; entry = price
            tp = round(price * (1 - tp_pct), 5); sl = round(price * (1 + sl_pct), 5)
            strength = "⭐" * sell_score
        else:
            sig = "⏸️ انتظار إشارة"; entry = None; tp = None; sl = None; strength = ""

        trend5  = "🔼 صاعد" if ema9_5  > ema21_5  else "🔽 هابط"
        trend15 = "🔼 صاعد" if ema9_15 > ema21_15 else "🔽 هابط"

        return {
            "price": price, "rsi5": rsi5, "rsi15": rsi15,
            "stoch5": stoch5, "stoch15": stoch15, "macd_cross5": macd_cross5,
            "trend5": trend5, "trend15": trend15,
            "res": res, "sup": sup, "mid": mid,
            "sig": sig, "entry": entry, "tp": tp, "sl": sl, "strength": strength
        }

    except Exception as e:
        print(f"Error fetching {pair}: {e}")
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
            "السوق مغلق أو البيانات غير متاحة\n"
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
