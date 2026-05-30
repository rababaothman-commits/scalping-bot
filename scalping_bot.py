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
    main()
