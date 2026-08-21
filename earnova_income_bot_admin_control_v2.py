import os
import sqlite3
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8974496982"))
DB = "earnova.db"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

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

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Balance", callback_data="balance"),
         InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("📝 Tasks", callback_data="tasks"),
         InlineKeyboardButton("👥 Referral", callback_data="ref")],
        [InlineKeyboardButton("🚀 BF / VIP", callback_data="bf"),
         InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("📊 Statistics", callback_data="stats"),
         InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = user(update.effective_user.id, update.effective_user.username)
    # Referral: /start REF_USER_ID
    if context.args:
        try:
            ref = int(context.args[0])
            if ref != u[0] and u[3] == 0:
                cur.execute("SELECT user_id FROM users WHERE user_id=?", (ref,))
                if cur.fetchone():
                    reward = float(setting("ref_reward"))
                    cur.execute("UPDATE users SET ref_by=?, balance=balance+? WHERE user_id=?",
                                (ref,reward,u[0]))
                    cur.execute("UPDATE users SET refs=refs+1, balance=balance+? WHERE user_id=?",
                                (reward,ref))
                    conn.commit()
        except ValueError:
            pass
    await update.message.reply_text(
        "🌟 *Earnova Income Bot*\n\n"
        "🎁 Welcome bonus: *20 ৳*\n"
        "💰 Earn from tasks and referrals.\n"
        "🚀 BF/VIP can increase your earning rate.\n"
        "💸 Withdraw through bKash, Nagad, Rocket, Binance or Mobile Recharge.",
        parse_mode="Markdown", reply_markup=menu()
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💸 Pending Withdrawals", callback_data="apending")],
        [InlineKeyboardButton("👥 Users", callback_data="ausers"),
         InlineKeyboardButton("📊 Stats", callback_data="astats")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="asettings")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="abroadcast")]
    ])
    await update.message.reply_text("🛠 *Earnova Admin Panel*", parse_mode="Markdown", reply_markup=kb)

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    u = user(uid, q.from_user.username)

    if q.data == "balance":
        await q.edit_message_text(f"💰 Balance: *{u[2]:.2f} ৳*", parse_mode="Markdown",
                                  reply_markup=menu())
    elif q.data == "profile":
        await q.edit_message_text(
            f"👤 *Profile*\n\nID: `{uid}`\nBalance: *{u[2]:.2f} ৳*\n"
            f"Referrals: *{u[4]}*\nBF Level: *{u[5]}*",
            parse_mode="Markdown", reply_markup=menu())
    elif q.data == "ref":
        me = await context.bot.get_me()
        link = f"https://t.me/{me.username}?start={uid}"
        await q.edit_message_text(
            f"👥 *Referral Program*\n\n"
            f"Per referral: *{setting('ref_reward')} ৳*\n"
            f"Your link:\n`{link}`", parse_mode="Markdown", reply_markup=menu())
    elif q.data == "tasks":
        cur.execute("SELECT id,title,reward,url FROM tasks WHERE active=1 ORDER BY id DESC")
        rows = cur.fetchall()
        if not rows:
            await q.edit_message_text("📝 এখন কোনো task নেই।", reply_markup=menu())
            return
        kb = [[InlineKeyboardButton(f"📝 {r[1]} — {r[2]}৳", callback_data=f"task:{r[0]}")] for r in rows]
        await q.edit_message_text("📝 *Available Tasks*", parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(kb))
    elif q.data.startswith("task:"):
        tid = int(q.data.split(":")[1])
        cur.execute("SELECT title,reward,url FROM tasks WHERE id=? AND active=1", (tid,))
        r = cur.fetchone()
        if not r:
            await q.edit_message_text("Task unavailable.", reply_markup=menu())
            return
        # This demo credits on button press. For real ad/task verification,
        # connect a verified provider before crediting users.
        cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (r[1],uid))
        conn.commit()
        await q.edit_message_text(f"✅ Task completed!\n💰 +{r[1]} ৳", reply_markup=menu())
    elif q.data == "bf":
        kb=[]
        for i in range(1,6):
            price, rate = setting(f"bf{i}").split(",")
            kb.append([InlineKeyboardButton(f"BF {i} — {price}৳ | +{rate}%", callback_data=f"bfbuy:{i}")])
        await q.edit_message_text("🚀 *BF / VIP Packages*\nChoose a package:",
                                  parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data.startswith("bfbuy:"):
        level = int(q.data.split(":")[1])
        price, rate = setting(f"bf{level}").split(",")
        price = float(price)
        cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        bal = cur.fetchone()[0]
        if bal < price:
            await q.edit_message_text(
                f"❌ Balance কম।\nPrice: {price:.0f} ৳\nYour balance: {bal:.2f} ৳",
                reply_markup=menu())
        else:
            cur.execute("UPDATE users SET balance=balance-?, bf_level=? WHERE user_id=?",
                        (price,level,uid))
            conn.commit()
            await q.edit_message_text(
                f"🎉 BF {level} activated!\nExtra earning rate: +{rate}%",
                reply_markup=menu())
    elif q.data == "withdraw":
        kb = [[InlineKeyboardButton(x, callback_data=f"wd:{x}")]
              for x in ["bKash","Nagad","Rocket","Binance","Mobile Recharge"]]
        await q.edit_message_text(
            f"💸 *Withdraw*\nMinimum: {setting('min_withdraw')} ৳\nSelect method:",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data.startswith("wd:"):
        method = q.data[3:]
        context.user_data["withdraw_method"] = method
        await q.edit_message_text(
            f"💸 {method}\n\nএখন amount এবং account/number পাঠাও এভাবে:\n"
            "`500 01XXXXXXXXX`\n\nBinance হলে UID/Pay ID দিতে পারো।",
            parse_mode="Markdown")
    elif q.data == "help":
        await q.edit_message_text(
            "ℹ️ *Help*\n\n"
            "📝 Tasks → task করে আয়\n"
            "👥 Referral → বন্ধু invite করে আয়\n"
            "🚀 BF/VIP → earning rate বাড়াতে পারো\n"
            "💸 Withdraw → payment method বেছে request পাঠাও\n\n"
            "⚠️ BF/VIP optional; withdraw approval admin-এর মাধ্যমে হয়।",
            parse_mode="Markdown", reply_markup=menu())

    # Admin callbacks
    if uid == ADMIN_ID and q.data == "adminhome":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💸 Pending Withdrawals", callback_data="apending")],
            [InlineKeyboardButton("👥 Users", callback_data="ausers"),
             InlineKeyboardButton("📊 Stats", callback_data="astats")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="asettings")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="abroadcast")]
        ])
        await q.edit_message_text("🛠 *Earnova Admin Panel*", parse_mode="Markdown", reply_markup=kb)
        return

    elif uid == ADMIN_ID and q.data == "apending":
        cur.execute("SELECT id,user_id,amount,method,account FROM withdrawals WHERE status='pending' ORDER BY id")
        rows=cur.fetchall()
        if not rows:
            await q.edit_message_text("✅ No pending withdrawals.", reply_markup=admin_kb())
        else:
            text="💸 *Pending Withdrawals*\n\n"
            kb=[]
            for r in rows:
                text += f"#{r[0]} | {r[1]} | {r[2]:.2f}৳ | {r[3]} | {r[4]}\n"
                kb.append([InlineKeyboardButton(f"✅ Approve #{r[0]}", callback_data=f"approve:{r[0]}"),
                           InlineKeyboardButton(f"❌ Reject #{r[0]}", callback_data=f"reject:{r[0]}")])
            await q.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(kb))
    elif uid == ADMIN_ID and q.data.startswith("approve:"):
        wid=int(q.data.split(":")[1])
        cur.execute("UPDATE withdrawals SET status='approved' WHERE id=? AND status='pending'",(wid,))
        conn.commit()
        await q.edit_message_text(f"✅ Withdrawal #{wid} approved.\nম্যানুয়ালি payment পাঠিয়ে দাও।",
                                  reply_markup=admin_kb())
    elif uid == ADMIN_ID and q.data.startswith("reject:"):
        wid=int(q.data.split(":")[1])
        cur.execute("SELECT user_id,amount FROM withdrawals WHERE id=? AND status='pending'",(wid,))
        r=cur.fetchone()
        if r:
            cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?",(r[1],r[0]))
            cur.execute("UPDATE withdrawals SET status='rejected' WHERE id=?",(wid,))
            conn.commit()
        await q.edit_message_text(f"❌ Withdrawal #{wid} rejected and balance refunded.",
                                  reply_markup=admin_kb())
    elif uid == ADMIN_ID and q.data == "ausers":
        cur.execute("SELECT COUNT(*), COALESCE(SUM(balance),0) FROM users")
        c,b=cur.fetchone()
        await q.edit_message_text(f"👥 Users: {c}\n💰 Total balance: {b:.2f} ৳",
                                  reply_markup=admin_kb())
    elif uid == ADMIN_ID and q.data == "astats":
        cur.execute("SELECT COUNT(*) FROM withdrawals WHERE status='pending'")
        p=cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tasks WHERE active=1")
        t=cur.fetchone()[0]
        await q.edit_message_text(f"📊 Pending withdrawals: {p}\n📝 Active tasks: {t}",
                                  reply_markup=admin_kb())
    elif uid == ADMIN_ID and q.data == "asettings":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Minimum Withdraw", callback_data="set_min"),
             InlineKeyboardButton("👥 Referral Reward", callback_data="set_ref")],
            [InlineKeyboardButton("📝 Add Task", callback_data="set_task")],
            [InlineKeyboardButton("📋 Task List", callback_data="set_tasks")],
            [InlineKeyboardButton("🔙 Admin Panel", callback_data="adminhome")]
        ])
        await q.edit_message_text(
            f"⚙️ *SETTINGS*\n\n"
            f"💳 Minimum Withdraw: {setting('min_withdraw')} ৳\n"
            f"👥 Referral Reward: {setting('ref_reward')} ৳",
            parse_mode="Markdown", reply_markup=kb)
    elif uid == ADMIN_ID and q.data == "set_min":
        context.user_data["admin_input"] = "min"
        await q.edit_message_text(
            "💳 নতুন Minimum Withdraw amount পাঠাও।\nউদাহরণ: `100`\n\n/cancel",
            parse_mode="Markdown", reply_markup=admin_kb())
    elif uid == ADMIN_ID and q.data == "set_ref":
        context.user_data["admin_input"] = "ref"
        await q.edit_message_text(
            "👥 নতুন Referral Reward পাঠাও।\nউদাহরণ: `10`\n\n/cancel",
            parse_mode="Markdown", reply_markup=admin_kb())
    elif uid == ADMIN_ID and q.data == "set_task":
        context.user_data["admin_input"] = "task"
        await q.edit_message_text(
            "📝 Task এভাবে পাঠাও:\n`Task Name | Reward | URL`\n\nউদাহরণ:\n`Join Channel | 5 | https://t.me/example`\n\n/cancel",
            parse_mode="Markdown", reply_markup=admin_kb())
    elif uid == ADMIN_ID and q.data == "set_tasks":
        cur.execute("SELECT id,title,reward,active FROM tasks ORDER BY id DESC")
        rows = cur.fetchall()
        if not rows:
            await q.edit_message_text("📋 কোনো Task নেই।", reply_markup=admin_kb())
        else:
            text = "📋 *TASK LIST*\n\n"
            kb = []
            for tid, title, reward, active in rows:
                text += f"#{tid} — {title} — {reward}৳ — {'🟢 ON' if active else '🔴 OFF'}\n"
                kb.append([InlineKeyboardButton(
                    f"{'🔴 OFF' if active else '🟢 ON'} #{tid}",
                    callback_data=f"toggle_task:{tid}")])
            kb.append([InlineKeyboardButton("🔙 Admin Panel", callback_data="adminhome")])
            await q.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(kb))
    elif uid == ADMIN_ID and q.data.startswith("toggle_task:"):
        tid = int(q.data.split(":")[1])
        cur.execute("UPDATE tasks SET active=CASE WHEN active=1 THEN 0 ELSE 1 END WHERE id=?", (tid,))
        conn.commit()
        await q.edit_message_text("✅ Task status changed.", reply_markup=admin_kb())
    elif uid == ADMIN_ID and q.data == "abroadcast":
        context.user_data["broadcast"]=True
        await q.edit_message_text("📢 এখন broadcast message পাঠাও।")

def admin_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="adminhome")]])

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    text=update.message.text.strip()

    if uid == ADMIN_ID:
        action = context.user_data.get("admin_input")
        if text.lower() == "/cancel":
            context.user_data.pop("admin_input", None)
            await update.message.reply_text("❌ Cancelled.", reply_markup=admin_kb())
            return
        if action == "min":
            try:
                value = float(text)
                if value <= 0: raise ValueError
                set_setting("min_withdraw", value)
                context.user_data.pop("admin_input", None)
                await update.message.reply_text(f"✅ Minimum Withdraw set to {value:g} ৳", reply_markup=admin_kb())
            except:
                await update.message.reply_text("❌ শুধু সঠিক সংখ্যা দাও। উদাহরণ: 100")
            return
        if action == "ref":
            try:
                value = float(text)
                if value < 0: raise ValueError
                set_setting("ref_reward", value)
                context.user_data.pop("admin_input", None)
                await update.message.reply_text(f"✅ Referral Reward set to {value:g} ৳", reply_markup=admin_kb())
            except:
                await update.message.reply_text("❌ শুধু সঠিক সংখ্যা দাও। উদাহরণ: 10")
            return
        if action == "task":
            parts = [x.strip() for x in text.split("|", 2)]
            if len(parts) != 3:
                await update.message.reply_text("❌ Format: Task Name | Reward | URL")
                return
            try:
                reward = float(parts[1])
                cur.execute("INSERT INTO tasks(title,reward,url,active) VALUES(?,?,?,1)",
                            (parts[0], reward, parts[2]))
                conn.commit()
                context.user_data.pop("admin_input", None)
                await update.message.reply_text("✅ Task added successfully.", reply_markup=admin_kb())
            except:
                await update.message.reply_text("❌ Reward সঠিক সংখ্যা হতে হবে।")
            return

    if uid == ADMIN_ID and context.user_data.pop("broadcast",False):
        cur.execute("SELECT user_id FROM users")
        ids=[r[0] for r in cur.fetchall()]
        sent=0
        for x in ids:
            try:
                await context.bot.send_message(x, text)
                sent+=1
            except Exception:
                pass
        await update.message.reply_text(f"📢 Broadcast sent: {sent}")
        return

    method=context.user_data.get("withdraw_method")
    if method:
        parts=text.split(maxsplit=1)
        if len(parts)!=2:
            await update.message.reply_text("Format: 500 01XXXXXXXXX")
            return
        try:
            amount=float(parts[0])
        except:
            await update.message.reply_text("Amount ঠিকভাবে দাও।")
            return
        account=parts[1]
        u=user(uid, update.effective_user.username)
        minimum=float(setting("min_withdraw"))
        if amount < minimum:
            await update.message.reply_text(f"Minimum withdraw {minimum:.0f} ৳")
            return
        if amount > u[2]:
            await update.message.reply_text("❌ পর্যাপ্ত balance নেই।")
            return
        cur.execute("UPDATE users SET balance=balance-? WHERE user_id=?",(amount,uid))
        cur.execute("""INSERT INTO withdrawals(user_id,amount,method,account,created_at)
                       VALUES(?,?,?,?,?)""",
                    (uid,amount,method,account,datetime.utcnow().isoformat()))
        conn.commit()
        context.user_data.pop("withdraw_method",None)
        await update.message.reply_text("✅ Withdraw request submitted.\nAdmin review করবে।",
                                        reply_markup=menu())
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"💸 New Withdraw\nUser: {uid}\nAmount: {amount:.2f} ৳\nMethod: {method}\nAccount: {account}\nUse /admin"
            )
        except Exception:
            pass

async def setmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: return await update.message.reply_text("Use /setmin 100")
    set_setting("min_withdraw", context.args[0])
    await update.message.reply_text("✅ Minimum withdraw updated.")

async def setref(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: return await update.message.reply_text("Use /setref 10")
    set_setting("ref_reward", context.args[0])
    await update.message.reply_text("✅ Referral reward updated.")

async def addtask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    raw=update.message.text.replace("/addtask ","",1)
    parts=raw.split("|")
    if len(parts)!=3:
        return await update.message.reply_text("Use /addtask Title|Reward|URL")
    title,reward,url=parts
    cur.execute("INSERT INTO tasks(title,reward,url) VALUES(?,?,?)",(title,float(reward),url))
    conn.commit()
    await update.message.reply_text("✅ Task added.")

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("setmin", setmin))
    app.add_handler(CommandHandler("setref", setref))
    app.add_handler(CommandHandler("addtask", addtask))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    print("Earnova bot running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
