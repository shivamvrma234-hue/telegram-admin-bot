import telebot
from telebot import types
import sqlite3
import time

import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
OWNER_ID = 7568268218

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


# =========================================================
# DATABASE
# =========================================================

DB_FILE = "bot.db"


def db_connect():
    return sqlite3.connect(DB_FILE)


def setup_database():
    conn = db_connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            user_id INTEGER PRIMARY KEY,
            role TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


setup_database()


# =========================================================
# ROLE SYSTEM
# =========================================================

ROLE_POWER = {
    "owner": 4,
    "moderator": 3,
    "manager": 2,
    "helper": 1,
    "user": 0
}


def role(user_id):
    # Owner is always owner
    if user_id == OWNER_ID:
        return "owner"

    conn = db_connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT role FROM staff WHERE user_id = ?",
        (user_id,)
    )

    result = cur.fetchone()

    conn.close()

    if result:
        return result[0]

    return "user"


def add_staff(user_id, staff_role):
    conn = db_connect()
    cur = conn.cursor()

    cur.execute(
        "INSERT OR REPLACE INTO staff (user_id, role) VALUES (?, ?)",
        (user_id, staff_role)
    )

    conn.commit()
    conn.close()


def remove_staff(user_id):
    conn = db_connect()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM staff WHERE user_id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()


# =========================================================
# GET TARGET USER
# USE BY REPLYING TO A MESSAGE
# =========================================================

def get_target(message):

    if message.reply_to_message:
        return message.reply_to_message.from_user

    return None


# =========================================================
# CHECK STAFF
# =========================================================

def is_staff(user_id):
    return role(user_id) in [
        "owner",
        "moderator",
        "manager",
        "helper"
    ]


def is_group(message):
    return message.chat.type in ["group", "supergroup"]


# =========================================================
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):

    bot.reply_to(
        message,
        "🤖 <b>Group Management Bot</b>\n\n"
        "Bot is online.\n\n"
        "Use /help to see commands."
    )


# =========================================================
# HELP
# =========================================================

@bot.message_handler(commands=["help"])
def help_command(message):

    text = """
🤖 <b>GROUP MANAGEMENT BOT</b>

👑 <b>Owner</b>
• Everything

🛡️ <b>Moderator</b>
• Ban
• Unban
• Mute
• Unmute
• Delete
• Purge
• Promote
• Demote

🔧 <b>Manager</b>
• Ban
• Unban
• Mute
• Unmute
• Delete
• Purge
• Demote

🧹 <b>Helper</b>
• Ban
• Unban
• Mute
• Unmute
• Delete

<b>Commands</b>

/promote
/demote
/ban
/unban
/mute
/unmute
/del
/purge
/delban
/id
/admins

Reply to a user's message when using moderation commands.
"""

    bot.reply_to(message, text)


# =========================================================
# ID
# =========================================================

@bot.message_handler(commands=["id"])
def get_id(message):

    user = get_target(message)

    if user:
        bot.reply_to(
            message,
            f"🆔 <b>User ID:</b> <code>{user.id}</code>"
        )
    else:
        bot.reply_to(
            message,
            f"🆔 <b>Your ID:</b> <code>{message.from_user.id}</code>"
        )


# =========================================================
# ADD MODERATOR
# OWNER ONLY
# =========================================================

@bot.message_handler(commands=["addmod"])
def add_moderator(message):

    if message.from_user.id != OWNER_ID:
        return

    user = get_target(message)

    if not user:
        bot.reply_to(
            message,
            "Reply to a user's message with /addmod"
        )
        return

    if user.id == OWNER_ID:
        bot.reply_to(
            message,
            "❌ Owner is already the Owner."
        )
        return

    add_staff(user.id, "moderator")

    bot.reply_to(
        message,
        f"🛡️ <b>{user.first_name}</b> is now a Moderator."
    )


# =========================================================
# ADD MANAGER
# OWNER / MODERATOR
# =========================================================

@bot.message_handler(commands=["addmanager"])
def add_manager(message):

    r = role(message.from_user.id)

    if r not in ["owner", "moderator"]:
        return

    user = get_target(message)

    if not user:
        bot.reply_to(
            message,
            "Reply to a user's message with /addmanager"
        )
        return

    if user.id == OWNER_ID:
        bot.reply_to(
            message,
            "❌ Cannot change Owner."
        )
        return

    add_staff(user.id, "manager")

    bot.reply_to(
        message,
        f"🔧 <b>{user.first_name}</b> is now a Manager."
    )


# =========================================================
# ADD HELPER
# OWNER / MODERATOR / MANAGER
# =========================================================

@bot.message_handler(commands=["addhelper"])
def add_helper(message):

    r = role(message.from_user.id)

    if r not in ["owner", "moderator", "manager"]:
        return

    user = get_target(message)

    if not user:
        bot.reply_to(
            message,
            "Reply to a user's message with /addhelper"
        )
        return

    if user.id == OWNER_ID:
        bot.reply_to(
            message,
            "❌ Cannot change Owner."
        )
        return

    add_staff(user.id, "helper")

    bot.reply_to(
        message,
        f"🧹 <b>{user.first_name}</b> is now a Helper."
    )


# =========================================================
# REMOVE STAFF
# OWNER ONLY
# =========================================================

@bot.message_handler(commands=["removestaff"])
def remove_staff_command(message):

    if message.from_user.id != OWNER_ID:
        return

    user = get_target(message)

    if not user:
        bot.reply_to(
            message,
            "Reply to a staff member's message with /removestaff"
        )
        return

    if user.id == OWNER_ID:
        bot.reply_to(
            message,
            "❌ Cannot remove Owner."
        )
        return

    remove_staff(user.id)

    bot.reply_to(
        message,
        f"✅ <b>{user.first_name}</b> removed from staff."
    )


# =========================================================
# PROMOTE GROUP ADMIN
# OWNER / MODERATOR
# =========================================================

@bot.message_handler(commands=["promote"])
def promote(message):

    r = role(message.from_user.id)

    if r not in ["owner", "moderator"]:
        return

    if not is_group(message):
        bot.reply_to(
            message,
            "❌ This command only works in groups."
        )
        return

    user = get_target(message)

    if not user:
        bot.reply_to(
            message,
            "Reply to a user's message with /promote"
        )
        return

    if user.id == OWNER_ID:
        bot.reply_to(
            message,
            "❌ Owner does not need promotion."
        )
        return

    try:

        bot.promote_chat_member(
            message.chat.id,
            user.id,

            can_change_info=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_delete_messages=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_manage_video_chats=True,
            can_manage_topics=True,
            can_promote_members=True,
        )

        bot.reply_to(
            message,
            f"👑 <b>{user.first_name}</b> promoted to group admin."
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ <b>Could not promote.</b>\n<code>{e}</code>"
        )


# =========================================================
# DEMOTE GROUP ADMIN
# OWNER / MODERATOR / MANAGER
# =========================================================

@bot.message_handler(commands=["demote"])
def demote(message):

    r = role(message.from_user.id)

    if r not in ["owner", "moderator", "manager"]:
        return

    if not is_group(message):
        bot.reply_to(
            message,
            "❌ This command only works in groups."
        )
        return

    user = get_target(message)

    if not user:
        bot.reply_to(
            message,
            "Reply to an admin's message with /demote"
        )
        return

    if user.id == OWNER_ID:
        bot.reply_to(
            message,
            "❌ Cannot demote Owner."
        )
        return

    try:

        bot.promote_chat_member(
            message.chat.id,
            user.id,

            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_manage_video_chats=False,
            can_manage_topics=False,
            can_promote_members=False
        )

        bot.reply_to(
            message,
            f"✅ <b>{user.first_name}</b> demoted."
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ <b>Could not demote.</b>\n<code>{e}</code>"
        )


# =========================================================
# DELETE MESSAGE
# ALL STAFF
# =========================================================

@bot.message_handler(commands=["del"])
def delete_message(message):

    r = role(message.from_user.id)

    if r not in [
        "owner",
        "moderator",
        "manager",
        "helper"
    ]:
        return

    if not message.reply_to_message:
        bot.reply_to(
            message,
            "Reply to a message with /del"
        )
        return

    try:

        bot.delete_message(
            message.chat.id,
            message.reply_to_message.message_id
        )

        bot.delete_message(
            message.chat.id,
            message.message_id
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ Could not delete.\n<code>{e}</code>"
        )


# =========================================================
# BAN
# ALL STAFF
# =========================================================

@bot.message_handler(commands=["ban"])
def ban(message):

    r = role(message.from_user.id)

    if r not in [
        "owner",
        "moderator",
        "manager",
        "helper"
    ]:
        return

    if not is_group(message):
        return

    user = get_target(message)

    if not user:
        bot.reply_to(
            message,
            "Reply to a user's message with /ban"
        )
        return

    if user.id == OWNER_ID:
        bot.reply_to(
            message,
            "❌ Cannot ban Owner."
        )
        return

    try:

        bot.ban_chat_member(
            message.chat.id,
            user.id
        )

        bot.reply_to(
            message,
            f"🚫 <b>{user.first_name}</b> banned."
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ <b>Could not ban.</b>\n<code>{e}</code>"
        )


# =========================================================
# UNBAN
# ALL STAFF
# =========================================================

@bot.message_handler(commands=["unban"])
def unban(message):

    r = role(message.from_user.id)

    if r not in [
        "owner",
        "moderator",
        "manager",
        "helper"
    ]:
        return

    if not is_group(message):
        return

    user = get_target(message)

    if not user:
        bot.reply_to(
            message,
            "Reply to a user's message with /unban"
        )
        return

    try:

        bot.unban_chat_member(
            message.chat.id,
            user.id,
            only_if_banned=True
        )

        bot.reply_to(
            message,
            f"✅ <b>{user.first_name}</b> unbanned."
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ <b>Could not unban.</b>\n<code>{e}</code>"
        )


# =========================================================
# MUTE
# ALL STAFF
# =========================================================

@bot.message_handler(commands=["mute"])
def mute(message):

    r = role(message.from_user.id)

    if r not in [
        "owner",
        "moderator",
        "manager",
        "helper"
    ]:
        return

    if not is_group(message):
        return

    user = get_target(message)

    if not user:
        bot.reply_to(
            message,
            "Reply to a user's message with /mute"
        )
        return

    if user.id == OWNER_ID:
        bot.reply_to(
            message,
            "❌ Cannot mute Owner."
        )
        return

    try:

        permissions = types.ChatPermissions(
            can_send_messages=False
        )

        bot.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions=permissions
        )

        bot.reply_to(
            message,
            f"🔇 <b>{user.first_name}</b> muted."
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ <b>Could not mute.</b>\n<code>{e}</code>"
        )


# =========================================================
# UNMUTE
# ALL STAFF
# =========================================================

@bot.message_handler(commands=["unmute"])
def unmute(message):

    r = role(message.from_user.id)

    if r not in [
        "owner",
        "moderator",
        "manager",
        "helper"
    ]:
        return

    if not is_group(message):
        return

    user = get_target(message)

    if not user:
        bot.reply_to(
            message,
            "Reply to a muted user's message with /unmute"
        )
        return

    try:

        permissions = types.ChatPermissions(
            can_send_messages=True,
            can_send_audios=True,
            can_send_documents=True,
            can_send_photos=True,
            can_send_videos=True,
            can_send_video_notes=True,
            can_send_voice_notes=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )

        bot.restrict_chat_member(
            message.chat.id,
            user.id,
            permissions=permissions
        )

        bot.reply_to(
            message,
            f"🔊 <b>{user.first_name}</b> unmuted."
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ <b>Could not unmute.</b>\n<code>{e}</code>"
        )


# =========================================================
# PURGE
# ALL STAFF
# =========================================================

@bot.message_handler(commands=["purge"])
def purge(message):

    r = role(message.from_user.id)

    if r not in [
        "owner",
        "moderator",
        "manager"
    ]:
        return

    if not message.reply_to_message:
        bot.reply_to(
            message,
            "Reply to the first message you want to delete with /purge"
        )
        return

    try:

        chat_id = message.chat.id
        start_id = message.reply_to_message.message_id
        end_id = message.message_id

        deleted = 0

        for msg_id in range(start_id, end_id + 1):

            try:

                bot.delete_message(
                    chat_id,
                    msg_id
                )

                deleted += 1

            except Exception:
                pass

        bot.send_message(
            chat_id,
            f"🧹 Deleted <b>{deleted}</b> messages."
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ <b>Purge failed.</b>\n<code>{e}</code>"
        )


# =========================================================
# DELBAN
# DELETE REPLIED MESSAGE + BAN USER
# ALL STAFF
# =========================================================

@bot.message_handler(commands=["delban"])
def delban(message):

    r = role(message.from_user.id)

    if r not in [
        "owner",
        "moderator",
        "manager",
        "helper"
    ]:
        return

    if not is_group(message):
        return

    if not message.reply_to_message:
        bot.reply_to(
            message,
            "Reply to a user's message with /delban"
        )
        return

    user = message.reply_to_message.from_user

    if user.id == OWNER_ID:
        bot.reply_to(
            message,
            "❌ Cannot ban Owner."
        )
        return

    try:

        bot.delete_message(
            message.chat.id,
            message.reply_to_message.message_id
        )

        bot.ban_chat_member(
            message.chat.id,
            user.id
        )

        bot.delete_message(
            message.chat.id,
            message.message_id
        )

        bot.send_message(
            message.chat.id,
            f"🚫 <b>{user.first_name}</b> banned."
        )

    except Exception as e:

        bot.reply_to(
            message,
            f"❌ <b>Delban failed.</b>\n<code>{e}</code>"
        )


# =========================================================
# SHOW STAFF LIST
# OWNER / MODERATOR / MANAGER
# =========================================================

@bot.message_handler(commands=["staff"])
def staff_list(message):

    r = role(message.from_user.id)

    if r not in [
        "owner",
        "moderator",
        "manager"
    ]:
        return

    conn = db_connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id, role FROM staff ORDER BY role"
    )

    rows = cur.fetchall()

    conn.close()

    text = "👥 <b>BOT STAFF</b>\n\n"

    text += f"👑 Owner: <code>{OWNER_ID}</code>\n"

    if not rows:
        text += "\nNo additional staff."
    else:

        for user_id, staff_role in rows:

            emoji = {
                "moderator": "🛡️",
                "manager": "🔧",
                "helper": "🧹"
            }.get(staff_role, "👤")

            text += (
                f"{emoji} {staff_role.title()}: "
                f"<code>{user_id}</code>\n"
            )

    bot.reply_to(message, text)


# =========================================================
# BOT INFO
# =========================================================

@bot.message_handler(commands=["myrole"])
def myrole(message):

    r = role(message.from_user.id)

    emoji = {
        "owner": "👑",
        "moderator": "🛡️",
        "manager": "🔧",
        "helper": "🧹",
        "user": "👤"
    }.get(r, "👤")

    bot.reply_to(
        message,
        f"{emoji} Your role: <b>{r.title()}</b>"
    )


# =========================================================
# ERROR-SAFE POLLING
# =========================================================

print("======================================")
print("🤖 TELEGRAM MANAGEMENT BOT")
print("======================================")
print("🟢 BOT STARTED")
print("📱 Open Telegram and send /start")
print("======================================")

while True:
    try:
        bot.infinity_polling(
            timeout=30,
            long_polling_timeout=30,
            skip_pending=True
        )
    except Exception as e:
        print("Polling error:")
        print(e)
        time.sleep(5)
