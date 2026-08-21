import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# আপনার প্রদান করা বট টোকেন এবং এডমিন আইডি
BOT_TOKEN = "8610852982:AAH2-ousRJkyogQuibBpnuF39WF3PWaFsgs"
ADMIN_ID = 8974496982
DB = "earnova.db"

conn = sqlite3.connect(DB, check_same_thread=False)
cur = conn.cursor()
cur.executescript("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance REAL DEFAULT 0,
    ref_by INTEGER DEFAULT 0,
    refs INTEGER DEFAULT 0,
    bf_level INTEGER DEFAULT 0,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS settings(
    key TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS withdrawals(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    method TEXT,
    account TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    reward REAL,
    url TEXT,
    active INTEGER DEFAULT 1
);
""")
conn.commit()

defaults = {
    "min_withdraw": "100",
    "ref_reward": "10",
    "task_reward": "5",
    "payment_methods": "bKash, Nagad, Rocket, Binance, Mobile Recharge",
    "bf1": "150,1.25",
    "bf2": "290,1.35",
    "bf3": "380,1.47",
    "bf4": "470,2.09",
    "bf5": "560,2.35",
}
for k, v in defaults.items():
    cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k,v))
conn.commit()

def setting(key):
    cur.execute("SELECT value FROM
