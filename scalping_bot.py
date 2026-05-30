"""
Smart Market Explorer Bot - مستكشف الأسواق الذكي
===================================================
الأصول: XAUUSD, BTCUSD, NAS100, EURUSD, GBPJPY
المنهجية: SMC (Smart Money Concepts)
مزود البيانات: Twelve Data (twelvedata.com)
"""

import os
import logging
import asyncio
import requests
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ─────────────────────────────────────────────
# الإعدادات العامة
# ─────────────────────────────────────────────
TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN", "YOUR_TOKEN_HERE")
CHAT_ID         = os.getenv("CHAT_ID", "YOUR_CHAT_ID_HERE")
TWELVE_KEY      = os.getenv("TWELVE_KEY", "YOUR_TWELVEDATA_KEY_HERE")
ACCOUNT_BALANCE = float(os.getenv("ACCOUNT_BALANCE", "10000"))
RISK_PERCENT    = 0.01          # ريسك 1% لكل صفقة
SCAN_INTERVAL   = int(os.getenv("SCAN_INTERVAL", "300"))   # فحص كل 5 دقائق

TWELVE_BASE = "https://api.twelvedata.com"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# رموز الأصول ومعاملاتها
# رمز Twelve Data مختلف قليلاً لبعض الأصول
# ─────────────────────────────────────────────
ASSETS = {
    "XAU/USD": {
        "display": "XAUUSD",
        "name": "الذهب / دولار",
        "pip_value": 1.0,        # $1 لكل نقطة لكل لوت قياسي (100oz)
        "min_lot": 0.01,
        "lot_digits": 2,
    },
    "BTC/USD": {
        "display": "BTCUSD",
        "name": "بيتكوين / دولار",
        "pip_value": 1.0,
        "min_lot": 0.001,
        "lot_digits": 3,
    },
    "NDX": {
        "display": "NAS100",
        "name": "ناسداك 100",
        "pip_value": 1.0,
        "min_lot": 0.01,
        "lot_digits": 2,
    },
    "EUR/USD": {
        "display": "EURUSD",
        "name": "يورو / دولار",
        "pip_value": 10.0,       # $10 لكل نقطة (pip) لكل لوت قياسي
        "min_lot": 0.01,
        "lot_digits": 2,
    },
    "GBP/JPY": {
        "display": "GBPJPY",
        "name": "جنيه / ين",
        "pip_value": 0.07,       # تقريبي ويتغير مع USDJPY
        "min_lot": 0.01,
        "lot_digits": 2,
    },
}

# ─────────────────────────────────────────────
# جلب البيانات من Twelve Data
# ─────────────────────────────────────────────

def fetch_candles(symbol: str, interval: str, limit: int = 300) -> list[dict]:
    """
    جلب الشمعات من Twelve Data.
    interval: '1min' | '5min' | '15min' | '1h' | '4h'
    يُعيد: [{time, open, high, low, close, volume}] من الأقدم للأحدث
    """
    url = f"{TWELVE_BASE}/time_series"
    params = {
        "symbol":     symbol,
        "interval":   interval,
        "outputsize": limit,
        "apikey":     TWELVE_KEY,
        "format":     "JSON",
        "order":      "ASC",   # من الأقدم للأحدث مباشرةً
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.error(f"[API] خطأ في جلب {symbol} ({interval}): {e}")
        return []

    if data.get("status") == "error":
        log.warning(f"[API] {symbol} ({interval}): {data.get('message', 'unknown error')}")
        return []

    values = data.get("values", [])
    candles = []
    for v in values:
        try:
            candles.append({
                "time":   v["datetime"],
                "open":   float(v["open"]),
                "high":   float(v["high"]),
                "low":    float(v["low"]),
                "close":  float(v["close"]),
                "volume": float(v.get("volume", 0)),
            })
        except Exception:
            continue
    return candles


def fetch_price(symbol: str) -> float | None:
    """جلب السعر الحالي من Twelve Data"""
    url = f"{TWELVE_BASE}/price"
    params = {"symbol": symbol, "apikey": TWELVE_KEY}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        return float(data["price"])
    except Exception as e:
        log.error(f"[API] خطأ في جلب سعر {symbol}: {e}")
        return None


# ─────────────────────────────────────────────
# حسابات المؤشرات الفنية
# ─────────────────────────────────────────────

def calc_ema(closes: list[float], period: int) -> list[float | None]:
    """حساب EMA — يُعيد قائمة بنفس طول المدخلات (None للعناصر قبل period)"""
    if len(closes) < period:
        return [None] * len(closes)
    k       = 2 / (period + 1)
    ema     = [None] * (period - 1)
    ema_val = sum(closes[:period]) / period
    ema.append(ema_val)
    for price in closes[period:]:
        ema_val = price * k + ema_val * (1 - k)
        ema.append(ema_val)
    return ema


def calc_atr(candles: list[dict], period: int = 14) -> float:
    """حساب ATR (متوسط المدى الحقيقي)"""
    if len(candles) < period + 1:
        return 0.0
    true_ranges = []
    for i in range(1, len(candles)):
        h  = candles[i]["high"]
        l  = candles[i]["low"]
        pc = candles[i - 1]["close"]
        true_ranges.append(max(h - l, abs(h - pc), abs(l - pc)))
    if not true_ranges:
        return 0.0
    atr = sum(true_ranges[:period]) / period
    for tr in true_ranges[period:]:
        atr = (atr * (period - 1) + tr) / period
    return atr


# ─────────────────────────────────────────────
# منطق SMC: Order Blocks & FVG
# ─────────────────────────────────────────────

def detect_order_blocks(candles: list[dict], lookback: int = 30) -> dict:
    """
    كشف Order Blocks على فريم 15 دقيقة.
    OB صاعد : آخر شمعة هابطة قبل حركة صعودية قوية (شمعتان خضراوتان بعدها).
    OB هابط : آخر شمعة صاعدة قبل حركة هبوطية قوية (شمعتان حمراوتان بعدها).
    """
    bullish_obs, bearish_obs = [], []
    recent = candles[-lookback:] if len(candles) >= lookback else candles

    for i in range(1, len(recent) - 2):
        c0 = recent[i]
        c1 = recent[i + 1]
        c2 = recent[i + 2]
        body0 = abs(c0["close"] - c0["open"])
        move1 = abs(c1["close"] - c1["open"])

        # OB صاعد
        if (c0["close"] < c0["open"] and
                c1["close"] > c1["open"] and
                c2["close"] > c2["open"] and
                move1 > body0 * 0.5):
            bullish_obs.append((c0["high"], c0["low"]))

        # OB هابط
        if (c0["close"] > c0["open"] and
                c1["close"] < c1["open"] and
                c2["close"] < c2["open"] and
                move1 > body0 * 0.5):
            bearish_obs.append((c0["high"], c0["low"]))

    return {"bullish": bullish_obs[-3:], "bearish": bearish_obs[-3:]}


def detect_fvg(candles: list[dict], lookback: int = 40) -> dict:
    """
    كشف Fair Value Gaps (FVG).
    FVG صاعد : low[i+2] > high[i]  → فجوة فوق
    FVG هابط : high[i+2] < low[i]  → فجوة تحت
    """
    bullish_fvg, bearish_fvg = [], []
    recent = candles[-lookback:] if len(candles) >= lookback else candles

    for i in range(len(recent) - 2):
        c0 = recent[i]
        c2 = recent[i + 2]
        if c2["low"] > c0["high"]:
            bullish_fvg.append((c2["low"], c0["high"]))   # (top, bottom)
        if c2["high"] < c0["low"]:
            bearish_fvg.append((c0["low"], c2["high"]))

    return {"bullish": bullish_fvg[-3:], "bearish": bearish_fvg[-3:]}


def price_in_zone(price: float, zones: list[tuple]) -> bool:
    """هل السعر داخل إحدى المناطق؟"""
    return any(bottom <= price <= top for top, bottom in zones)


# ─────────────────────────────────────────────
# منطق SMC: Liquidity Sweep & CHoCH
# ─────────────────────────────────────────────

def detect_liquidity_sweep(candles_5m: list[dict], lookback: int = 20) -> dict:
    """
    صيد السيولة على فريم 5 دقائق.
    صيد هابط (→ BUY): السعر يخترق أدنى نقطة سابقة ثم يُغلق فوقها.
    صيد صاعد (→ SELL): السعر يخترق أعلى نقطة سابقة ثم يُغلق دونها.
    """
    if len(candles_5m) < lookback + 3:
        return {"bullish_sweep": False, "bearish_sweep": False}

    window = candles_5m[-(lookback + 3):-3]
    last3  = candles_5m[-3:]

    prev_high = max(c["high"] for c in window)
    prev_low  = min(c["low"]  for c in window)

    bullish_sweep = (
        any(c["low"] < prev_low for c in last3) and
        last3[-1]["close"] > prev_low
    )
    bearish_sweep = (
        any(c["high"] > prev_high for c in last3) and
        last3[-1]["close"] < prev_high
    )
    return {"bullish_sweep": bullish_sweep, "bearish_sweep": bearish_sweep}


def detect_choch(candles_1m: list[dict], direction: str) -> bool:
    """
    كسر هيكل السعر CHoCH على فريم 1 دقيقة.
    buy  → آخر شمعة تُغلق فوق أعلى نقطة في الـ 5 شمعات السابقة.
    sell → آخر شمعة تُغلق تحت أدنى نقطة في الـ 5 شمعات السابقة.
    """
    if len(candles_1m) < 10:
        return False
    recent = candles_1m[-10:]
    last   = recent[-1]
    prev5  = recent[-6:-1]
    if not prev5:
        return False
    if direction == "buy":
        return last["close"] > max(c["high"] for c in prev5)
    if direction == "sell":
        return last["close"] < min(c["low"] for c in prev5)
    return False


# ─────────────────────────────────────────────
# إدارة المخاطر وحساب الحجم
# ─────────────────────────────────────────────

def calculate_lot_size(balance: float, risk_pct: float,
                       sl_distance: float, pip_value: float,
                       min_lot: float, lot_digits: int) -> float:
    """
    حجم اللوت = (رصيد × ريسك%) / (مسافة SL × قيمة النقطة)
    """
    if sl_distance <= 0 or pip_value <= 0:
        return min_lot
    risk_amount = balance * risk_pct
    lot = risk_amount / (sl_distance * pip_value)
    return max(round(lot, lot_digits), min_lot)


# ─────────────────────────────────────────────
# المحرك الرئيسي للتحليل
# ─────────────────────────────────────────────

def analyze_asset(symbol: str, info: dict) -> dict | None:
    """
    تحليل كامل للأصل وفق منهجية SMC بخمس خطوات.
    يُعيد إشارة كاملة أو None إذا لم تكتمل الشروط.
    """
    log.info(f"[SCAN] ▶ تحليل {info['display']} ...")

    # ── جلب الشمعات من Twelve Data ──────────────────────
    # نستخدم 4h بدلاً من 240min — Twelve يدعمها مباشرةً
    candles_4h  = fetch_candles(symbol, "4h",    limit=250)
    candles_1h  = fetch_candles(symbol, "1h",    limit=250)
    candles_15m = fetch_candles(symbol, "15min", limit=150)
    candles_5m  = fetch_candles(symbol, "5min",  limit=80)
    candles_1m  = fetch_candles(symbol, "1min",  limit=30)

    if not all([candles_4h, candles_1h, candles_15m, candles_5m, candles_1m]):
        log.warning(f"[SCAN] {info['display']}: بيانات غير كافية")
        return None

    current_price = candles_5m[-1]["close"]

    # ── 1. فلتر الاتجاه الكلي: EMA 200 على 1H و4H ───────
    ema200_1h = calc_ema([c["close"] for c in candles_1h], 200)
    ema200_4h = calc_ema([c["close"] for c in candles_4h], 200)

    last_ema_1h = next((v for v in reversed(ema200_1h) if v is not None), None)
    last_ema_4h = next((v for v in reversed(ema200_4h) if v is not None), None)

    if last_ema_1h is None or last_ema_4h is None:
        log.info(f"[SCAN] {info['display']}: EMA200 غير كافية")
        return None

    trend_1h = "up" if candles_1h[-1]["close"] > last_ema_1h else "down"
    trend_4h = "up" if candles_4h[-1]["close"] > last_ema_4h else "down"

    if trend_1h != trend_4h:
        log.info(f"[SCAN] {info['display']}: تعارض الاتجاه (1H={trend_1h}, 4H={trend_4h})")
        return None

    bias = "buy" if trend_1h == "up" else "sell"

    # ── 2. مناطق الدخول SMC على 15M ──────────────────────
    obs  = detect_order_blocks(candles_15m)
    fvgs = detect_fvg(candles_15m)

    ob_zones  = obs["bullish"]  if bias == "buy" else obs["bearish"]
    fvg_zones = fvgs["bullish"] if bias == "buy" else fvgs["bearish"]

    in_ob  = price_in_zone(current_price, ob_zones)
    in_fvg = price_in_zone(current_price, fvg_zones)

    if not in_ob and not in_fvg:
        log.info(f"[SCAN] {info['display']}: السعر خارج OB/FVG")
        return None

    zone_type = "Order Block" if in_ob else "Fair Value Gap"

    # ── 3. تأكيد الدخول: Liquidity Sweep (5M) + CHoCH (1M)
    sweeps = detect_liquidity_sweep(candles_5m)

    if bias == "buy"  and not sweeps["bullish_sweep"]:
        log.info(f"[SCAN] {info['display']}: لم يتم صيد السيولة الهابطة (BUY)")
        return None
    if bias == "sell" and not sweeps["bearish_sweep"]:
        log.info(f"[SCAN] {info['display']}: لم يتم صيد السيولة الصاعدة (SELL)")
        return None

    if not detect_choch(candles_1m, bias):
        log.info(f"[SCAN] {info['display']}: لم يتأكد CHoCH على 1M")
        return None

    # ── 4. إدارة المخاطر (ATR ديناميكي) ─────────────────
    atr = calc_atr(candles_15m, period=14)
    if atr <= 0:
        log.warning(f"[SCAN] {info['display']}: ATR = 0")
        return None

    sl_mult = 1.5   # SL = 1.5 × ATR
    tp_mult = 3.0   # TP = 3.0 × ATR  →  R:R = 1:2

    if bias == "buy":
        sl = round(current_price - sl_mult * atr, 5)
        tp = round(current_price + tp_mult * atr, 5)
    else:
        sl = round(current_price + sl_mult * atr, 5)
        tp = round(current_price - tp_mult * atr, 5)

    sl_distance = abs(current_price - sl)
    lot_size    = calculate_lot_size(
        ACCOUNT_BALANCE, RISK_PERCENT,
        sl_distance, info["pip_value"],
        info["min_lot"], info["lot_digits"],
    )
    rr_ratio = round(abs(tp - current_price) / sl_distance, 2)

    log.info(f"[SCAN] ✅ إشارة: {info['display']} {bias.upper()} @ {current_price}")

    return {
        "symbol":    info["display"],
        "name":      info["name"],
        "bias":      bias,
        "entry":     round(current_price, 5),
        "sl":        sl,
        "tp":        tp,
        "lot":       lot_size,
        "rr":        rr_ratio,
        "atr":       round(atr, 5),
        "zone_type": zone_type,
        "trend_1h":  trend_1h,
        "trend_4h":  trend_4h,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }


# ─────────────────────────────────────────────
# تنسيق رسالة التلجرام
# ─────────────────────────────────────────────

def format_signal(sig: dict) -> str:
    direction = "🟢 شراء  (BUY)" if sig["bias"] == "buy" else "🔴 بيع  (SELL)"
    t_emoji   = "📈" if sig["trend_1h"] == "up" else "📉"
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 <b>إشارة تداول جديدة</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 <b>الأداة :</b> {sig['symbol']}  —  {sig['name']}\n"
        f"📌 <b>الاتجاه:</b> {direction}\n\n"
        f"💰 <b>سعر الدخول :</b>  <code>{sig['entry']}</code>\n"
        f"🛑 <b>وقف الخسارة (SL):</b>  <code>{sig['sl']}</code>\n"
        f"🎯 <b>الهدف (TP) :</b>  <code>{sig['tp']}</code>\n\n"
        f"📦 <b>حجم اللوت :</b> {sig['lot']}  <i>(ريسك 1%)</i>\n"
        f"⚖️ <b>نسبة R:R  :</b> 1 : {sig['rr']}\n\n"
        "─────────────────────────\n"
        "🔍 <b>تفاصيل التحليل</b>\n"
        f"{t_emoji} الاتجاه الكلي : {sig['trend_1h'].upper()}  (1H & 4H)\n"
        f"📍 منطقة الدخول : {sig['zone_type']}\n"
        "💧 صيد السيولة  : ✅  مؤكد (5M)\n"
        "🔄 CHoCH         : ✅  مؤكد (1M)\n"
        f"📐 ATR(14)       : {sig['atr']}\n"
        "─────────────────────────\n"
        f"🕐 <i>{sig['timestamp']}</i>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━"
    )


# ─────────────────────────────────────────────
# أوامر التلجرام
# ─────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 <b>مستكشف الأسواق الذكي</b>  |  Twelve Data\n\n"
        "/scan   — فحص فوري لجميع الأصول\n"
        "/status — حالة البوت والإعدادات\n"
        "/help   — شرح المنهجية",
        parse_mode="HTML",
    )


async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 جاري فحص الأسواق... قد يستغرق دقيقة أو دقيقتين.")
    found = 0
    for symbol, info in ASSETS.items():
        try:
            sig = await asyncio.to_thread(analyze_asset, symbol, info)
            if sig:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=format_signal(sig),
                    parse_mode="HTML",
                )
                found += 1
            await asyncio.sleep(1.5)   # تجنب تجاوز حد الـ API
        except Exception as e:
            log.error(f"[CMD_SCAN] خطأ في {symbol}: {e}")

    reply = f"✅ تم إرسال {found} إشارة." if found else "⏳ لا توجد إشارات مكتملة الشروط حالياً."
    await update.message.reply_text(reply)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"✅ <b>البوت يعمل</b>  |  Twelve Data\n\n"
        f"💵 رصيد الحساب : <code>{ACCOUNT_BALANCE:,.0f} $</code>\n"
        f"⚠️ ريسك / صفقة : 1%\n"
        f"🔄 فترة الفحص   : كل {SCAN_INTERVAL // 60} دقيقة\n"
        f"📊 الأصول       : {', '.join(i['display'] for i in ASSETS.values())}",
        parse_mode="HTML",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>منهجية التحليل (SMC)</b>\n\n"
        "1️⃣ <b>فلتر الاتجاه :</b> EMA200 على 1H و4H\n"
        "2️⃣ <b>مناطق SMC  :</b> Order Blocks + FVG على 15M\n"
        "3️⃣ <b>التأكيد    :</b> Liquidity Sweep (5M) + CHoCH (1M)\n"
        "4️⃣ <b>إدارة مخاطر:</b> SL = ATR×1.5 | TP = ATR×3  →  R:R 1:2\n"
        "5️⃣ <b>حجم اللوت  :</b> محسوب على ريسك 1% من الرصيد\n\n"
        "⚙️ <b>متغيرات البيئة المطلوبة</b>\n"
        "• <code>TELEGRAM_TOKEN</code>\n"
        "• <code>CHAT_ID</code>\n"
        "• <code>TWELVE_KEY</code>  (من twelvedata.com)\n"
        "• <code>ACCOUNT_BALANCE</code>  (افتراضي: 10000)\n"
        "• <code>SCAN_INTERVAL</code>  (افتراضي: 300 ثانية)",
        parse_mode="HTML",
    )


# ─────────────────────────────────────────────
# الفحص الدوري التلقائي
# ─────────────────────────────────────────────

async def scheduled_scan(context: ContextTypes.DEFAULT_TYPE):
    log.info("[SCHEDULER] ▶ بدء الفحص الدوري...")
    for symbol, info in ASSETS.items():
        try:
            sig = await asyncio.to_thread(analyze_asset, symbol, info)
            if sig:
                await context.bot.send_message(
                    chat_id=CHAT_ID,
                    text=format_signal(sig),
                    parse_mode="HTML",
                )
            await asyncio.sleep(1.5)
        except Exception as e:
            log.error(f"[SCHEDULER] خطأ في {symbol}: {e}")
    log.info("[SCHEDULER] ✅ انتهى الفحص الدوري")


# ─────────────────────────────────────────────
# نقطة الإدخال الرئيسية
# ─────────────────────────────────────────────

def main():
    log.info("🚀 تشغيل مستكشف الأسواق الذكي — Twelve Data")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("scan",   cmd_scan))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("help",   cmd_help))

    app.job_queue.run_repeating(
        scheduled_scan,
        interval=SCAN_INTERVAL,
        first=30,
    )

    log.info(f"✅ البوت جاهز — فحص كل {SCAN_INTERVAL // 60} دقيقة")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main(
