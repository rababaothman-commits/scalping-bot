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
        return 
