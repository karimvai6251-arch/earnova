import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8610852982:AAH2-ousRJkyogQuibBpnuF39WF3PWaFsgs"
ADMIN_ID = 8974496982
BOT_USERNAME = "YOUR_BOT_USERNAME"

DB_NAME = "earn_bot.db"
REFERRAL_RATE = 10
DAILY_BONUS = 5
MIN_WITHDRAW = 50

def db():
    return sqlite3.connect(DB_NAME)

def init_db():
    con = db()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY, username TEXT, balance REAL DEFAULT 0,
        referral_earn REAL DEFAULT 0, referred_by INTEGER, joined_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, reward REAL,
        link TEXT, active INTEGER DEFAULT 1)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS withdrawals(
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL,
        method TEXT, account TEXT, status TEXT DEFAULT 'pending', created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS bonuses(
        user_id INTEGER PRIMARY KEY, last_claim TEXT)""")
    con.commit()
    con.close()

def add_user(user, referrer=None):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user.id,))
    if not cur.fetchone():
        cur.execute("""INSERT INTO users(user_id,username,referred_by,joined_at)
                       VALUES(?,?,?,?)""",
                    (user.id, user.username or "", referrer, datetime.now().isoformat()))
    con.commit()
    con.close()

def get_user(uid):
    con = db()
    row = con.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    con.close()
    return row

def change_balance(uid, amount):
    con = db()
    con.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, uid))
    con.commit()
    con.close()

def user_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💰 𝗘𝗔𝗥𝗡", callback_data="earn"),
            InlineKeyboardButton("👥 𝗥𝗘𝗙𝗘𝗥", callback_data="ref")
        ],
        [
            InlineKeyboardButton("🎁 𝗕𝗢𝗡𝗨𝗦", callback_data="bonus"),
            InlineKeyboardButton("💳 𝗪𝗜𝗧𝗛𝗗𝗥𝗔𝗪", callback_data="withdraw")
        ],
        [
            InlineKeyboardButton("👤 𝗣𝗥𝗢𝗙𝗜𝗟𝗘", callback_data="profile"),
            InlineKeyboardButton("💎 𝗩𝗜𝗣 / 𝗕𝗙", callback_data="vip")
        ],
        [
            InlineKeyboardButton("🏆 𝗟𝗘𝗔𝗗𝗘𝗥𝗕𝗢𝗔𝗥𝗗", callback_data="leaderboard"),
            InlineKeyboardButton("🆘 𝗦𝗨𝗣𝗣𝗢𝗥𝗧", callback_data="support")
        ]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 𝗦𝗧𝗔𝗧𝗦", callback_data="a_stats"),
            InlineKeyboardButton("👥 𝗨𝗦𝗘𝗥𝗦", callback_data="a_users")
        ],
        [
            InlineKeyboardButton("📋 𝗧𝗔𝗦𝗞𝗦", callback_data="a_tasks"),
            InlineKeyboardButton("💳 𝗪𝗜𝗧𝗛𝗗𝗥𝗔𝗪", callback_data="a_withdraw")
        ],
        [
            InlineKeyboardButton("💰 𝗥𝗘𝗙𝗘𝗥𝗥𝗔𝗟", callback_data="a_ref"),
            InlineKeyboardButton("🎁 𝗕𝗢𝗡𝗨𝗦", callback_data="a_bonus")
        ],
        [
            InlineKeyboardButton("📢 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧", callback_data="a_broadcast"),
            InlineKeyboardButton("⚙️ 𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦", callback_data="a_settings")
        ]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ref = None
    if context.args:
        try: ref = int(context.args[0])
        except ValueError: pass
    add_user(update.effective_user, ref)
    await update.message.reply_text(
        "👑 <b>WELCOME TO EARNOVA</b>\n\n"
        "💰 Earn from available tasks\n👥 Referral rewards\n"
        "🎁 Daily bonus\n💳 Withdraw\n💎 VIP/BF\n\n"
        "👇 Menu থেকে নির্বাচন করুন।",
        parse_mode="HTML", reply_markup=user_menu())

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Access Denied.")
        return
    await update.message.reply_text(
        "👑 <b>ADMIN PANEL</b>\n\nশুধু আপনার Admin ID এই panel ব্যবহার করতে পারবে।",
        parse_mode="HTML", reply_markup=admin_menu())

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data

    if d.startswith("a_") and q.from_user.id != ADMIN_ID:
        await q.edit_message_text("⛔ Access Denied.")
        return

    if d == "home":
        await q.edit_message_text("👑 <b>EARNOVA</b>\n\nMenu থেকে নির্বাচন করুন 👇",
                                  parse_mode="HTML", reply_markup=user_menu())
    elif d == "profile":
        u = get_user(q.from_user.id)
        await q.edit_message_text(
            f"👤 <b>MY PROFILE</b>\n\n🆔 ID: <code>{q.from_user.id}</code>"
            f"\n💰 Balance: ৳{u[2]:.2f}\n👥 Referral Earn: ৳{u[3]:.2f}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="home")]]))
    elif d == "ref":
        link = f"https://t.me/{BOT_USERNAME}?start={q.from_user.id}"
        await q.edit_message_text(
            f"👥 <b>REFERRAL</b>\n\n🔗 <code>{link}</code>\n\n💸 Rate: {REFERRAL_RATE}%",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="home")]]))
    elif d == "bonus":
        today = datetime.now().date().isoformat()
        con = db(); row = con.execute("SELECT last_claim FROM bonuses WHERE user_id=?", (q.from_user.id,)).fetchone()
        if row and row[0] == today:
            msg = "🎁 আজকের bonus ইতিমধ্যে নেওয়া হয়েছে।"
        else:
            change_balance(q.from_user.id, DAILY_BONUS)
            con.execute("INSERT OR REPLACE INTO bonuses(user_id,last_claim) VALUES(?,?)",
                        (q.from_user.id, today)); con.commit()
            msg = f"🎁 ৳{DAILY_BONUS} bonus যোগ হয়েছে।"
        con.close()
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="home")]]))
    elif d == "withdraw":
        u = get_user(q.from_user.id)
        await q.edit_message_text(
            f"💳 <b>WITHDRAW</b>\n\n💰 Balance: ৳{u[2]:.2f}\n📌 Minimum: ৳{MIN_WITHDRAW}\n\n"
            "Withdraw-এর জন্য Admin-এর সাথে যোগাযোগ করুন: @tingadmin24",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👑 Admin", url="https://t.me/tingadmin24")],
                [InlineKeyboardButton("⬅️ Back", callback_data="home")]]))
    elif d == "earn":
        con = db(); rows = con.execute("SELECT id,title,reward FROM tasks WHERE active=1").fetchall(); con.close()
        buttons = [[InlineKeyboardButton(f"📌 {r[1]} — ৳{r[2]}", callback_data=f"task_{r[0]}")] for r in rows]
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="home")])
        await q.edit_message_text("💰 <b>AVAILABLE TASKS</b>\n\nTask নির্বাচন করুন।" if rows else
                                   "💰 এখন কোনো active task নেই।",
                                   parse_mode="HTML", reply_markup=InlineKeyboardMarkup(buttons))
    elif d == "vip":
        await q.edit_message_text(
            "💎 <b>VIP / BF</b>\n\nAdmin Panel থেকে package settings নিয়ন্ত্রণ করা যাবে।\n"
            "⚠️ কোনো package guaranteed profit নয়.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="home")]]))
    elif d == "leaderboard":
        con=db(); rows=con.execute("SELECT user_id,balance FROM users ORDER BY balance DESC LIMIT 10").fetchall(); con.close()
        text="🏆 <b>LEADERBOARD</b>\n\n"
        for i,(uid,b) in enumerate(rows,1): text += f"{i}. {uid} — ৳{b:.2f}\n"
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="home")]]))
    elif d == "support":
        await q.edit_message_text("🆘 Support: @tingadmin24", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="home")]]))
    elif d == "admin_home":
        await q.edit_message_text("👑 <b>ADMIN PANEL</b>", parse_mode="HTML", reply_markup=admin_menu())
    elif d == "a_stats":
        con=db(); users=con.execute("SELECT COUNT(*) FROM users").fetchone()[0]; bal=con.execute("SELECT COALESCE(SUM(balance),0) FROM users").fetchone()[0]; wd=con.execute("SELECT COUNT(*) FROM withdrawals WHERE status='pending'").fetchone()[0]; con.close()
        await q.edit_message_text(f"📊 <b>STATISTICS</b>\n\n👥 Users: {users}\n💰 Balances: ৳{bal:.2f}\n💳 Pending withdrawals: {wd}",
                                  parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin", callback_data="admin_home")]]))
    elif d == "a_users":
        con=db(); rows=con.execute("SELECT user_id,username,balance FROM users ORDER BY joined_at DESC LIMIT 20").fetchall(); con.close()
        text="👥 <b>RECENT USERS</b>\n\n" + "\n".join(f"{x[0]} | @{x[1] or '-'} | ৳{x[2]:.2f}" for x in rows)
        await q.edit_message_text(text or "কোনো user নেই।", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin", callback_data="admin_home")]]))
    elif d == "a_tasks":
        await q.edit_message_text("📋 Tasks control: database ready. Add/edit/delete task buttons can be connected next.",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin", callback_data="admin_home")]]))
    elif d == "a_withdraw":
        con=db(); rows=con.execute("SELECT id,user_id,amount,method,account FROM withdrawals WHERE status='pending' ORDER BY id DESC LIMIT 20").fetchall(); con.close()
        text="💳 <b>PENDING WITHDRAWALS</b>\n\n" + "\n".join(f"#{x[0]} | {x[1]} | ৳{x[2]} | {x[3]} | {x[4]}" for x in rows)
        await q.edit_message_text(text or "কোনো pending withdrawal নেই।", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin", callback_data="admin_home")]]))
    elif d == "a_ref":
        await q.edit_message_text(f"👥 Referral Rate: {REFERRAL_RATE}%", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin", callback_data="admin_home")]]))
    elif d == "a_bonus":
        await q.edit_message_text(f"🎁 Daily Bonus: ৳{DAILY_BONUS}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin", callback_data="admin_home")]]))
    elif d == "a_broadcast":
        await q.edit_message_text("📢 Broadcast module ready for adding admin message input.",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin", callback_data="admin_home")]]))
    elif d == "a_settings":
        await q.edit_message_text(f"⚙️ Settings\n\nReferral: {REFERRAL_RATE}%\nDaily Bonus: ৳{DAILY_BONUS}\nMinimum Withdraw: ৳{MIN_WITHDRAW}",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Admin", callback_data="admin_home")]]))
    elif d.startswith("task_"):
        tid=int(d.split("_")[1]); con=db(); task=con.execute("SELECT title,reward FROM tasks WHERE id=? AND active=1",(tid,)).fetchone(); con.close()
        await q.edit_message_text(f"📌 {task[0]}\n💰 Reward: ৳{task[1]}\n\nTask verification প্রয়োজন।" if task else "Task পাওয়া যায়নি।",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Earn", callback_data="earn")]]))

def main():
    init_db()
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(callbacks))
    print("🤖 Earn Bot is running...")
    app.run_polling()

if __name__=="__main__":
    main()
