import telebot
import csv
import threading
import random
import time
from datetime import datetime

# ========= CONFIG =========
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
ADMIN_ID = 123456789  # replace with your Telegram user ID
TRADE_LOG_FILE = "trade_history.csv"

bot = telebot.TeleBot(BOT_TOKEN)

# ========= GLOBALS =========
auto_trader_running = False
current_auto = {"symbol": None, "timeframes": [], "leverage": None}
trade_stats = {"wins": 0, "losses": 0, "profit_pct": 0.0}
daily_stats = {"wins": 0, "losses": 0, "profit_pct": 0.0}
weekly_stats = {"wins": 0, "losses": 0, "profit_pct": 0.0}

# ========= CSV INIT =========
def init_trade_log():
    try:
        with open(TRADE_LOG_FILE, mode="x", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Time", "Symbol", "Timeframes", "Outcome", "PnL%"])
    except FileExistsError:
        pass

def log_trade(symbol, timeframes, outcome, pnl):
    with open(TRADE_LOG_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol,
            ", ".join(timeframes),
            outcome,
            pnl
        ])

init_trade_log()

# ========= STAT UPDATER =========
def update_stats(outcome, pnl):
    global trade_stats, daily_stats, weekly_stats
    if outcome == "WIN":
        trade_stats["wins"] += 1
        daily_stats["wins"] += 1
        weekly_stats["wins"] += 1
    else:
        trade_stats["losses"] += 1
        daily_stats["losses"] += 1
        weekly_stats["losses"] += 1

    trade_stats["profit_pct"] += pnl
    daily_stats["profit_pct"] += pnl
    weekly_stats["profit_pct"] += pnl

# ========= AUTO TRADER =========
def auto_agree_trader(symbol, timeframes, leverage=10):
    global auto_trader_running, current_auto, trade_stats
    auto_trader_running = True
    current_auto = {"symbol": symbol, "timeframes": timeframes, "leverage": leverage}
    trade_stats = {"wins": 0, "losses": 0, "profit_pct": 0.0}

    bot.send_message(
        ADMIN_ID,
        f"✅ Auto-trader started\nPair: {symbol}\n"
        f"Timeframes: {', '.join(timeframes)}\nLeverage: {leverage}x"
    )

    while auto_trader_running:
        # TODO: Replace with real strategy checks
        trade_outcome = random.choice(["win", "loss"])
        if trade_outcome == "win":
            update_stats("WIN", 50)
            log_trade(symbol, timeframes, "WIN", "+50%")
        else:
            update_stats("LOSS", -5)
            log_trade(symbol, timeframes, "LOSS", "-5%")

        time.sleep(5)  # adjust frequency

# ========= REPORTS =========
def send_daily_report():
    global daily_stats
    bot.send_message(
        ADMIN_ID,
        f"📅 Daily Report:\n"
        f"Wins: {daily_stats['wins']}\n"
        f"Losses: {daily_stats['losses']}\n"
        f"Net PnL: {daily_stats['profit_pct']}%"
    )
    daily_stats = {"wins": 0, "losses": 0, "profit_pct": 0.0}
    threading.Timer(86400, send_daily_report).start()

def send_weekly_report():
    global weekly_stats
    bot.send_message(
        ADMIN_ID,
        f"📊 Weekly Report:\n"
        f"Wins: {weekly_stats['wins']}\n"
        f"Losses: {weekly_stats['losses']}\n"
        f"Net PnL: {weekly_stats['profit_pct']}%"
    )
    weekly_stats = {"wins": 0, "losses": 0, "profit_pct": 0.0}
    threading.Timer(604800, send_weekly_report).start()

# ========= COMMANDS =========
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🤖 Bot ready! Use /autoagree, /status, /history, /report")

@bot.message_handler(commands=['autoagree'])
def autoagree(message):
    try:
        parts = message.text.split()
        symbol = parts[1]
        timeframes = parts[2:-1] if len(parts) > 3 else parts[2:]
        leverage = int(parts[-1]) if parts[-1].endswith("x") else 10
        threading.Thread(target=auto_agree_trader, args=(symbol, timeframes, leverage)).start()
    except Exception as e:
        bot.reply_to(message, f"❌ Usage: /autoagree SYMBOL TF1 TF2 ... Leverage\nError: {e}")

@bot.message_handler(commands=['stopauto'])
def stopauto(message):
    global auto_trader_running
    auto_trader_running = False
    bot.reply_to(message, "🛑 Auto-trader stopped.")

@bot.message_handler(commands=['status'])
def status(message):
    if auto_trader_running:
        bot.reply_to(
            message,
            f"🤖 Auto-trader is RUNNING\n"
            f"Pair: {current_auto['symbol']}\n"
            f"Timeframes: {', '.join(current_auto['timeframes'])}\n"
            f"Leverage: {current_auto['leverage']}x\n\n"
            f"📊 Stats:\nWins: {trade_stats['wins']}\n"
            f"Losses: {trade_stats['losses']}\n"
            f"Net PnL: {trade_stats['profit_pct']}%"
        )
    else:
        bot.reply_to(message, "🛑 Auto-trader is NOT running.")

@bot.message_handler(commands=['history'])
def history(message):
    try:
        with open(TRADE_LOG_FILE, "rb") as file:
            bot.send_document(message.chat.id, file)
    except FileNotFoundError:
        bot.reply_to(message, "⚠️ No trade history file found yet.")

@bot.message_handler(commands=['report'])
def report(message):
    bot.reply_to(
        message,
        f"📊 Instant Report:\n\n"
        f"📅 Daily Stats:\nWins: {daily_stats['wins']} | Losses: {daily_stats['losses']} | PnL: {daily_stats['profit_pct']}%\n\n"
        f"📈 Weekly Stats:\nWins: {weekly_stats['wins']} | Losses: {weekly_stats['losses']} | PnL: {weekly_stats['profit_pct']}%\n\n"
        f"⚡ Session Total:\nWins: {trade_stats['wins']} | Losses: {trade_stats['losses']} | PnL: {trade_stats['profit_pct']}%"
    )

# ========= START BOT =========
send_daily_report()
send_weekly_report()
print("🤖 Bot running...")
bot.polling()
