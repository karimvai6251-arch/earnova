import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

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
    chat_id TEXT,
    active INTEGER DEFAULT 1
);
""")
conn.commit()

defaults = {
    "min_withdraw": "100",
    "ref_reward": "10",
    "daily_bonus": "5",
    "payment_methods": "bKash, Nagad, Rocket, Binance",
}
for k, v in defaults.items():
    cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k,v))
conn.commit()

def setting(key):
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    return row[0] if row else ""

def set_setting(key, value):
    cur.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key,str(value)))
    conn.commit()

def user(uid, username=None):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO users(user_id,username,balance,created_at) VALUES(?,?,20,?)",
            (uid, username or "", datetime.utcnow().isoformat())
        )
        conn.commit()
        cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
        row = cur.fetchone()
    elif username is not None:
        cur.execute("UPDATE users SET username=? WHERE user_id=?", (username,uid))
        conn.commit()
    return row

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 EARN", callback_data="tasks"), InlineKeyboardButton("👥 REFER", callback_data="ref")],
        [InlineKeyboardButton("🎁 BONUS", callback_data="bonus"), InlineKeyboardButton("💳 WITHDRAW", callback_data="withdraw")],
        [InlineKeyboardButton("👤 PROFILE", callback_data="profile"), InlineKeyboardButton("💎 VIP / BF", callback_data="vip")],
        [InlineKeyboardButton("🏆 LEADERBOARD", callback_data="leaderboard"), InlineKeyboardButton("🆘 SUPPORT", callback_data="support")]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 STATS", callback_data="astats"), InlineKeyboardButton("👥 USERS", callback_data="ausers")],
        [InlineKeyboardButton("📋 TASKS", callback_data="atasks"), InlineKeyboardButton("💳 WITHDRAW", callback_data="apending")],
        [InlineKeyboardButton("💰 REFERRAL", callback_data="aset_ref"), InlineKeyboardButton("🎁 BONUS", callback_data="aset_bonus")],
        [InlineKeyboardButton("📢 BROADCAST", callback_data="abroadcast"), InlineKeyboardButton("⚙️ SETTINGS", callback_data="asettings")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = user(update.effective_user.id, update.effective_user.username)
    if context.args:
        try:
            ref = int(context.args[0])
            if ref != u[0] and u[3] == 0:
                cur.execute("SELECT user_id FROM users WHERE user_id=?", (ref,))
                if cur.fetchone():
                    reward = float(setting("ref_reward"))
                    cur.execute("UPDATE users SET ref_by=?, balance=balance+? WHERE user_id=?", (ref,reward,u[0]))
                    cur.execute("UPDATE users SET refs=refs+1, balance=balance+? WHERE user_id=?", (reward,ref))
                    conn.commit()
        except ValueError:
            pass

    await update.message.reply_text(
        "💰 Earn from available tasks\n👥 Referral rewards\n🎁 Daily bonus\n💳 Easy withdrawals\n💎 VIP/BF Benefits\n\n👇 Menu থেকে নির্বাচন করুন।",
        reply_markup=main_menu()
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("👑 ADMIN PANEL", reply_markup=admin_menu())

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    u = user(uid, q.from_user.username)

    if q.data == "home":
        await q.edit_message_text("👇 Menu থেকে নির্বাচন করুন।", reply_markup=main_menu())

    elif q.data == "tasks":
        cur.execute("SELECT id, title, reward FROM tasks WHERE active=1 ORDER BY id DESC")
        rows = cur.fetchall()
        if not rows:
            await q.edit_message_text("📝 বর্তমানে কোনো Task উপলব্ধ নেই।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="home")]]))
            return
        kb = [[InlineKeyboardButton(f"🎯 {r[1]} (+{r[2]}৳)", callback_data=f"task:{r[0]}")] for r in rows]
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data="home")])
        await q.edit_message_text("📝 Available Tasks:", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data.startswith("task:"):
        tid = int(q.data.split(":")[1])
        cur.execute("SELECT title, reward, url FROM tasks WHERE id=? AND active=1", (tid,))
        r = cur.fetchone()
        if not r:
            await q.edit_message_text("❌ Task পাওয়া যায়নি।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="tasks")]]))
            return
        kb = [
            [InlineKeyboardButton("🔗 Open Channel / Task", url=r[2])],
            [InlineKeyboardButton("✅ Check Joined Status", callback_data=f"checktask:{tid}")],
            [InlineKeyboardButton("⬅️ Back", callback_data="tasks")]
        ]
        await q.edit_message_text(f"📌 Task: {r[0]}\n💰 Reward: {r[1]} ৳\n\nউপরের লিংকে জয়েন করার পর Check এ চাপুন।", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data.startswith("checktask:"):
        tid = int(q.data.split(":")[1])
        cur.execute("SELECT title, reward, chat_id FROM tasks WHERE id=?", (tid,))
        r = cur.fetchone()
        
        is_member = True
        if r and r[2]:
            try:
                member = await context.bot.get_chat_member(chat_id=r[2], user_id=uid)
                if member.status not in ['member', 'administrator', 'creator']:
                    is_member = False
            except Exception:
                is_member = False

        if is_member and r:
            cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (r[1], uid))
            conn.commit()
            await q.edit_message_text(f"🎉 Task Completed!\n💰 +{r[1]} ৳ যোগ করা হয়েছে।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="tasks")]]))
        else:
            await q.answer("❌ আপনি এখনো জয়েন করেননি! আগে চ্যানেলে জয়েন করুন।", show_alert=True)

    elif q.data == "ref":
        me = await context.bot.get_me()
        link = f"https://t.me/{me.username}?start={uid}"
        await q.edit_message_text(f"👥 Refer and Earn\nPer Referral: {setting('ref_reward')} ৳\n\nYour Referral Link:\n`{link}`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="home")]]))

    elif q.data == "withdraw":
        raw = setting("payment_methods") or "bKash, Nagad, Rocket, Binance"
        methods = [x.strip() for x in raw.split(",") if x.strip()]
        kb = [[InlineKeyboardButton(f"💳 {x}", callback_data=f"wd:{x}")] for x in methods]
        kb.append([InlineKeyboardButton("⬅️ Back", callback_data="home")])
        await q.edit_message_text(f"💳 Withdraw Portal\nMinimum: {setting('min_withdraw')} ৳\nYour Balance: {u[2]:.2f} ৳\n\nমেথড নির্বাচন করুন:", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data.startswith("wd:"):
        method = q.data[3:]
        context.user_data["withdraw_method"] = method
        await q.edit_message_text(f"💳 {method} Withdraw\n\nটাকা তুলতে Amount এবং Account No এভাবে লিখে মেসেজ দিন:\n`500 017XXXXXXXX`", parse_mode="Markdown")

    elif q.data == "profile":
        await q.edit_message_text(f"👤 USER PROFILE\n\nID: `{uid}`\nBalance: {u[2]:.2f} ৳\nReferrals: {u[4]}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="home")]]))

    # ADMIN PANEL CONTROL
    if uid == ADMIN_ID:
        if q.data == "adminhome":
            await q.edit_message_text("👑 ADMIN PANEL", reply_markup=admin_menu())
        elif q.data == "apending":
            cur.execute("SELECT id, user_id, amount, method, account FROM withdrawals WHERE status='pending'")
            rows = cur.fetchall()
            if not rows:
                await q.edit_message_text("💳 PENDING WITHDRAWALS\n\nকোনো রিকোয়েস্ট নেই।", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin", callback_data="adminhome")]]))
            else:
                text = "💳 PENDING WITHDRAWALS:\n\n"
                kb = []
                for r in rows:
                    text += f"#{r[0]} | User: {r[1]} | {r[2]}৳ | {r[3]} ({r[4]})\n"
                    kb.append([InlineKeyboardButton(f"✅ Approve #{r[0]}", callback_data=f"app:{r[0]}"), InlineKeyboardButton(f"❌ Reject #{r[0]}", callback_data=f"rej:{r[0]}")])
                kb.append([InlineKeyboardButton("⬅️ Admin", callback_data="adminhome")])
                await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
        elif q.data == "atasks":
            context.user_data["admin_input"] = "task"
            await q.edit_message_text(
                "📝 ADD TASK\n\nএভাবে লিখে পাঠান:\n`Task Title | Reward | URL | @channel_username`\n\nউদাহরণ:\n`Join Channel | 5 | https://t.me/example | @example`",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin", callback_data="adminhome")]])
            )

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    if uid == ADMIN_ID and context.user_data.get("admin_input") == "task":
        parts = [x.strip() for x in text.split("|")]
        if len(parts) == 4:
            try:
                reward = float(parts[1])
                cur.execute("INSERT INTO tasks(title, reward, url, chat_id, active) VALUES(?,?,?,?,1)", (parts[0], reward, parts[2], parts[3]))
                conn.commit()
                context.user_data.pop("admin_input", None)
                await update.message.reply_text("✅ Task added successfully!", reply_markup=admin_menu())
                return
            except Exception:
                pass
        await update.message.reply_text("❌ ফরম্যাট সঠিক হয়নি! আবার সঠিক ফরম্যাটে দিন।")
        return

    method = context.user_data.get("withdraw_method")
    if method:
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            try:
                amount = float(parts[0])
                account = parts[1]
                u = user(uid)
                if amount >= float(setting("min_withdraw")) and amount <= u[2]:
                    cur.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (amount, uid))
                    cur.execute("INSERT INTO withdrawals(user_id, amount, method, account, created_at) VALUES(?,?,?,?,?)", (uid, amount, method, account, datetime.utcnow().isoformat()))
                    conn.commit()
                    context.user_data.pop("withdraw_method", None)
                    await update.message.reply_text("✅ Withdraw request submitted!", reply_markup=main_menu())
                    return
            except Exception:
                pass
        await update.message.reply_text("❌ ভুল তথ্য দিয়েছেন। সঠিক উদাহরণ: `500 017XXXXXXXX`", parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    print("Earnova Bot Started...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
