from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = "8439703370:AAEvukwiKYdxmHMMZRFalz5NaSxONKY6U00"
ADMIN_USERNAME = "@tingadmin24"

PRICES = {
    "Instagram": [280,510,920,1330,2150,4000,7600,11100,14400,17500,20400,23100,25600,27900,30000],
    "TikTok": [260,480,870,1260,2050,3800,7200,10500,13600,16500,19200,21700,24100,26300,28500],
    "YouTube": [300,560,1000,1450,2350,4300,8100,11800,15300,18500,21600,24500,27200,29800,32000],
    "Facebook": [250,470,850,1230,2000,3700,7000,10200,13200,16000,18700,21100,23400,25600,27500],
    "Twitter": [270,500,900,1300,2100,3900,7400,10800,14000,17000,19800,22400,24900,27300,29500],
    "Telegram": [350,650,1200,1750,2800,5200,9800,14300,18500,22500,26400,30000,33500,37000,40000],
}
QUANTITIES = ["500","1K","2K","3K","5K","10K","20K","30K","40K","50K","60K","70K","80K","90K","100K"]
ICONS = {"Instagram":"📸","TikTok":"🎵","YouTube":"▶️","Facebook":"📘","Twitter":"🐦","Telegram":"✈️"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💰 PRICE LIST", callback_data="platforms"), InlineKeyboardButton("🛒 ORDER", callback_data="order")], [InlineKeyboardButton("👨‍💻 ADMIN", url="https://t.me/tingadmin24")]]
    text = ("👑 𝗢𝗙𝗙𝗜𝗖𝗜𝗔𝗟 𝗕𝗢𝗢𝗦𝗧 𝗔𝗗𝗠𝗜𝗡 🔥\n\n👋 Welcome to our Social Media Boosting Service!\n\n🚀 Available Services:\n📸 Instagram • 🎵 TikTok • ▶️ YouTube\n📘 Facebook • 🐦 Twitter • ✈️ Telegram\n\n💎 Fast & Easy Service\n📞 Support: @tingadmin24\n\n👇 Price দেখতে PRICE LIST চাপুন:")
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_platforms(query):
    keyboard = [[InlineKeyboardButton("📸 Instagram",callback_data="p_Instagram"),InlineKeyboardButton("🎵 TikTok",callback_data="p_TikTok")],[InlineKeyboardButton("▶️ YouTube",callback_data="p_YouTube"),InlineKeyboardButton("📘 Facebook",callback_data="p_Facebook")],[InlineKeyboardButton("🐦 Twitter",callback_data="p_Twitter"),InlineKeyboardButton("✈️ Telegram",callback_data="p_Telegram")],[InlineKeyboardButton("🛒 ORDER NOW",callback_data="order")]]
    await query.edit_message_text("💎 𝗦𝗘𝗟𝗘𝗖𝗧 𝗬𝗢𝗨𝗥 𝗣𝗟𝗔𝗧𝗙𝗢𝗥𝗠\n\nনিচের যেকোনো Platform নির্বাচন করুন 👇", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_prices(query, platform):
    keyboard=[]; row=[]
    for quantity,price in zip(QUANTITIES,PRICES[platform]):
        row.append(InlineKeyboardButton(f"{quantity} — ৳{price}",callback_data=f"buy_{platform}_{quantity}"))
        if len(row)==2: keyboard.append(row); row=[]
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton("⬅️ BACK",callback_data="platforms"),InlineKeyboardButton("🛒 ORDER",callback_data="order")])
    text=f"{ICONS[platform]} 𝗣𝗥𝗜𝗖𝗘 — {platform.upper()}\n\n🔥 Followers / Subscribers\n👇 আপনার প্রয়োজনীয় Quantity নির্বাচন করুন:\n\n💎 Premium Service • Fast Delivery"
    await query.edit_message_text(text,reply_markup=InlineKeyboardMarkup(keyboard))

async def selected_price(query, platform, quantity):
    price=PRICES[platform][QUANTITIES.index(quantity)]
    keyboard=[[InlineKeyboardButton("🛒 ORDER NOW",callback_data="order")],[InlineKeyboardButton("⬅️ BACK TO PRICE",callback_data=f"p_{platform}")]]
    text=f"{ICONS[platform]} 𝗦𝗘𝗟𝗘𝗖𝗧𝗘𝗗 𝗦𝗘𝗥𝗩𝗜𝗖𝗘\n\n📱 Platform: {platform}\n👥 Quantity: {quantity}\n💰 Price: ৳{price}\n\n🛒 অর্ডার করতে আপনার Profile/Page Link পাঠান।\n\n👨‍💻 Admin: {ADMIN_USERNAME}"
    await query.edit_message_text(text,reply_markup=InlineKeyboardMarkup(keyboard))

async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query=update.callback_query; await query.answer()
    text=("🛒 𝗢𝗥𝗗𝗘𝗥 𝗡𝗢𝗪 🔥\n\nঅর্ডার করতে পাঠান:\n\n1️⃣ Platform\n2️⃣ Service\n3️⃣ Quantity\n4️⃣ Your Link/Username\n\n📌 Example:\nInstagram — Followers — 1K\nLink: @username\n\n👨‍💻 Admin: @tingadmin24")
    await query.edit_message_text(text)

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message=update.message.text.lower().strip()
    if "price" in message or "প্রাইস" in message or "দাম" in message or "মূল্য" in message:
        keyboard=[[InlineKeyboardButton("📸 Instagram",callback_data="p_Instagram"),InlineKeyboardButton("🎵 TikTok",callback_data="p_TikTok")],[InlineKeyboardButton("▶️ YouTube",callback_data="p_YouTube"),InlineKeyboardButton("📘 Facebook",callback_data="p_Facebook")],[InlineKeyboardButton("🐦 Twitter",callback_data="p_Twitter"),InlineKeyboardButton("✈️ Telegram",callback_data="p_Telegram")]]
        await update.message.reply_text("💰 𝗣𝗥𝗜𝗖𝗘 𝗟𝗜𝗦𝗧 🔥\n\nযে Platform-এর দাম দেখতে চান, সেটিতে ক্লিক করুন 👇",reply_markup=InlineKeyboardMarkup(keyboard))
    elif "order" in message or "অর্ডার" in message:
        await update.message.reply_text("🛒 𝗢𝗥𝗗𝗘𝗥 𝗡𝗢𝗪 🔥\n\nPlatform + Service + Quantity + Link পাঠান।\n\n👨‍💻 Admin: @tingadmin24")
    elif "payment" in message or "পেমেন্ট" in message:
        await update.message.reply_text("💳 Payment information জানতে Admin-এর সাথে যোগাযোগ করুন:\n\n@tingadmin24")
    else:
        await update.message.reply_text("👋 আপনার মেসেজটি পেয়েছি। ❤️\n\n💰 Price List লিখুন\n🛒 Order লিখুন\n💳 Payment লিখুন\n\n👨‍💻 Admin: @tingadmin24")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query=update.callback_query; await query.answer(); data=query.data
    if data=="platforms": await show_platforms(query)
    elif data=="order": await order(update,context)
    elif data.startswith("p_"): await show_prices(query,data[2:])
    elif data.startswith("buy_"):
        parts=data.split("_"); await selected_price(query,parts[1],parts[2])

def main():
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,auto_reply))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__=="__main__": main()
