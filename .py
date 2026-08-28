import os
import sqlite3
import telebot
from telebot import types

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Put YOUR Telegram user ID here.
# You can get it by messaging @userinfobot on Telegram.
OWNER_ID = 7568268218

DB = "bot.db"

# =========================
# DATABASE
# =========================

db = sqlite3.connect(DB, check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS bot_admins (
    user_id INTEGER PRIMARY KEY,
    role TEXT NOT NULL
)
""")

db.commit()


def add_admin(user_id, role):
    cur.execute(
        "INSERT OR REPLACE INTO bot_admins (user_id, role) VALUES (?, ?)",
        (user_id, role)
    )
    db.commit()


def remove_admin(user_id):
    cur.execute(
        "DELETE FROM bot_admins WHERE user_id = ?",
        (user_id,)
    )
    db.commit()


def get_role(user_id):
    if user_id == OWNER_ID:
        return "owner"

    cur.execute(
        "SELECT role FROM bot_admins WHERE user_id = ?",
        (user_id,)
    )

    row = cur.fetchone()

    return row[0] if row else None


# =========================
# PERMISSIONS
# =========================

ROLE_LEVEL = {
    "helper": 1,
    "manager": 2,
    "moderator": 3,
    "owner": 4
}


def is_bot_admin(user_id):
    return get_role(user_id) is not None


def has_role(user_id, role):
    current = get_role(user_id)

    if not current:
        return False

    return ROLE_LEVEL[current] >= ROLE_LEVEL[role]


def is_group(message):
    return message.chat.type in ["group", "supergroup"]


def reply(message, text):
    try:
        bot.reply_to(message, text)
    except Exception as e:
        print("Reply error:", e)


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    role = get_role(message.from_user.id)

    if role:
        reply(
            message,
            f"👋 Welcome!\n\n"
            f"🤖 <b>Group Management Bot</b>\n"
            f"Your role: <b>{role.upper()}</b>\n\n"
            f"Use /help to see commands."
        )
    else:
        reply(
            message,
            "👋 Hello!\n\n"
            "I am a group management bot.\n"
            "Use me in a group where I am an administrator."
        )


# =========================
# HELP
# =========================

@bot.message_handler(commands=["help"])
def help_command(message):
    role = get_role(message.from_user.id)

    if not role:
        reply(message, "❌ You are not authorized to use management commands.")
        return

    text = """
<b>🤖 GROUP MANAGEMENT BOT</b>

<b>🛡️ Moderation</b>

/ban - Reply to a user's message
/unban - Reply to a user's message
/mute - Reply to a user's message
/unmute - Reply to a user's message
/kick - Reply to a user's message

<b>🗑️ Messages</b>

/del - Delete replied message
/purge - Delete replied message and messages after it
/delban - Delete message and ban the user

<b>👤 Information</b>

/id - Get user/chat ID
/role - Show your role
/admins - Show bot staff

<b>👑 Staff</b>

/addmod - Add moderator
/addmanager - Add manager
/addhelper - Add helper
/removestaff - Remove staff member

Only the Owner can add/remove bot staff.
"""

    reply(message, text)


# =========================
# ROLE
# =========================

@bot.message_handler(commands=["role"])
def role_command(message):
    role = get_role(message.from_user.id)

    if not role:
        reply(message, "❌ You don't have a bot role.")
        return

    reply(message, f"👤 Your role: <b>{role.upper()}</b>")


# =========================
# ID
# =========================

@bot.message_handler(commands=["id"])
def id_command(message):
    text = (
        f"👤 Your ID: <code>{message.from_user.id}</code>\n"
        f"💬 Chat ID: <code>{message.chat.id}</code>"
    )

    if message.reply_to_message:
        text += (
            f"\n\n🎯 Replied user's ID: "
            f"<code>{message.reply_to_message.from_user.id}</code>"
        )

    reply(message, text)


# =========================
# STAFF LIST
# =========================

@bot.message_handler(commands=["admins"])
def admins_command(message):
    if not is_bot_admin(message.from_user.id):
        reply(message, "❌ Unauthorized.")
        return

    cur.execute("SELECT user_id, role FROM bot_admins ORDER BY role")

    rows = cur.fetchall()

    text = "👑 <b>BOT STAFF</b>\n\n"

    text += f"Owner: <code>{OWNER_ID}</code>\n"

    if rows:
        for user_id, role in rows:
            text += f"• <code>{user_id}</code> — {role.upper()}\n"
    else:
        text += "\nNo additional staff."

    reply(message, text)


# =========================
# GET TARGET USER
# =========================

def get_target(message):
    if not message.reply_to_message:
        reply(
            message,
            "❌ Reply to the user's message with this command."
        )
        return None

    return message.reply_to_message.from_user


# =========================
# BAN
# =========================

@bot.message_handler(commands=["ban"])
def ban_command(message):
    if not has_role(message.from_user.id, "helper"):
        reply(message, "❌ You don't have permission.")
        return

    if not is_group(message):
        reply(message, "❌ Use this command inside a group.")
        return

    user = get_target(message)

    if not user:
        return

    try:
        bot.ban_chat_member(message.chat.id, user.id)

        reply(
            message,
            f"🔨 <b>{user.first_name}</b> has been banned."
        )

    except Exception as e:
        reply(message, f"❌ Couldn't ban user.\n<code>{e}</code>")


# =========================
# UNBAN
# =========================

@bot.message_handler(commands=["unban"])
def unban_command(message):
    if not has_role(message.from_user.id, "helper"):
        reply(message, "❌ You don't have permission.")
        return

    user = get_target(message)

    if not user:
        return

    try:
        bot.unban_chat_member(
            message.chat.id,
            user.id,
            only_if_banned=True
        )

        reply(
            message,
            f"✅ <b>{user.first_name}</b> has been unbanned."
        )

    except Exception as e:
        reply(message, f"❌ Couldn't unban user.\n<code>{e}</code>")


# =========================
# MUTE
# =========================

@bot.message_handler(commands=["mute"])
def mute_command(message):
    if not has_role(message.from_user.id, "helper"):
        reply(message, "❌ You don't have permission.")
        return

    user = get_target(message)

    if not user:
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

        reply(
            message,
            f"🔇 <b>{user.first_name}</b> has been muted."
        )

    except Exception as e:
        reply(message, f"❌ Couldn't mute user.\n<code>{e}</code>")


# =========================
# UNMUTE
# =========================

@bot.message_handler(commands=["unmute"])
def unmute_command(message):
    if not has_role(message.from_user.id, "helper"):
        reply(message, "❌ You don't have permission.")
        return

    user = get_target(message)

    if not user:
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

        reply(
            message,
            f"🔊 <b>{user.first_name}</b> has been unmuted."
        )

    except Exception as e:
        reply(message, f"❌ Couldn't unmute user.\n<code>{e}</code>")


# =========================
# KICK
# =========================

@bot.message_handler(commands=["kick"])
def kick_command(message):
    if not has_role(message.from_user.id, "helper"):
        reply(message, "❌ You don't have permission.")
        return

    user = get_target(message)

    if not user:
        return

    try:
        bot.ban_chat_member(message.chat.id, user.id)
        bot.unban_chat_member(message.chat.id, user.id)

        reply(
            message,
            f"👢 <b>{user.first_name}</b> has been kicked."
        )

    except Exception as e:
        reply(message, f"❌ Couldn't kick user.\n<code>{e}</code>")


# =========================
# DELETE
# =========================

@bot.message_handler(commands=["del"])
def delete_command(message):
    if not has_role(message.from_user.id, "helper"):
        reply(message, "❌ You don't have permission.")
        return

    if not message.reply_to_message:
        reply(message, "❌ Reply to a message.")
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
        print("Delete error:", e)


# =========================
# DELBAN
# =========================

@bot.message_handler(commands=["delban"])
def delban_command(message):
    if not has_role(message.from_user.id, "helper"):
        reply(message, "❌ You don't have permission.")
        return

    user = get_target(message)

    if not user:
        return

    try:
        if message.reply_to_message:
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

    except Exception as e:
        reply(message, f"❌ Delban failed.\n<code>{e}</code>")


# =========================
# ADD STAFF
# =========================

def add_staff(message, role):
    if message.from_user.id != OWNER_ID:
        reply(message, "❌ Only the Owner can manage bot staff.")
        return

    user = get_target(message)

    if not user:
        return

    if user.id == OWNER_ID:
        reply(message, "❌ That user is already the Owner.")
        return

    add_admin(user.id, role)

    reply(
        message,
        f"✅ <b>{user.first_name}</b> is now "
        f"<b>{role.upper()}</b>."
    )


@bot.message_handler(commands=["addmod"])
def addmod(message):
    add_staff(message, "moderator")


@bot.message_handler(commands=["addmanager"])
def addmanager(message):
    add_staff(message, "manager")


@bot.message_handler(commands=["addhelper"])
def addhelper(message):
    add_staff(message, "helper")


# =========================
# REMOVE STAFF
# =========================

@bot.message_handler(commands=["removestaff"])
def removestaff(message):
    if message.from_user.id != OWNER_ID:
        reply(message, "❌ Only the Owner can remove staff.")
        return

    user = get_target(message)

    if not user:
        return

    if user.id == OWNER_ID:
        reply(message, "❌ You cannot remove the Owner.")
        return

    remove_admin(user.id)

    reply(
        message,
        f"✅ <b>{user.first_name}</b> has been removed from bot staff."
    )


# =========================
# PROMOTE
# =========================

@bot.message_handler(commands=["promote"])
def promote_command(message):
    if not has_role(message.from_user.id, "moderator"):
        reply(message, "❌ Only Moderators/Owner can promote users.")
        return

    user = get_target(message)

    if not user:
        return

    try:
        bot.promote_chat_member(
            message.chat.id,
            user.id,
            can_change_info=False,
            can_post_messages=True,
            can_edit_messages=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_manage_video_chats=True
        )

        reply(
            message,
            f"⬆️ <b>{user.first_name}</b> has been promoted."
        )

    except Exception as e:
        reply(message, f"❌ Couldn't promote.\n<code>{e}</code>")


# =========================
# DEMOTE
# =========================

@bot.message_handler(commands=["demote"])
def demote_command(message):
    if not has_role(message.from_user.id, "moderator"):
        reply(message, "❌ Only Moderators/Owner can demote users.")
        return

    user = get_target(message)

    if not user:
        return

    try:
        bot.promote_chat_member(
            message.chat.id,
            user.id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_manage_video_chats=False
        )

        reply(
            message,
            f"⬇️ <b>{user.first_name}</b> has been demoted."
        )

    except Exception as e:
        reply(message, f"❌ Couldn't demote.\n<code>{e}</code>")


# =========================
# PURGE
# =========================

@bot.message_handler(commands=["purge"])
def purge_command(message):
    if not has_role(message.from_user.id, "manager"):
        reply(message, "❌ Only Managers/Moderators/Owner can purge.")
        return

    if not message.reply_to_message:
        reply(message, "❌ Reply to the first message to purge from.")
        return

    start_id = message.reply_to_message.message_id
    end_id = message.message_id

    deleted = 0

    for msg_id in range(start_id, end_id + 1):
        try:
            bot.delete_message(message.chat.id, msg_id)
            deleted += 1
        except Exception:
            pass

    try:
        bot.send_message(
            message.chat.id,
            f"🧹 Deleted <b>{deleted}</b> messages."
        )
    except Exception:
        pass


# =========================
# UNKNOWN COMMAND
# =========================

@bot.message_handler(commands=["owner"])
def owner_command(message):
    reply(
        message,
        f"👑 Owner ID: <code>{OWNER_ID}</code>"
    )


# =========================
# START BOT
# =========================

print("================================")
print("🟢 TELEGRAM BOT STARTED")
print("================================")

bot.infinity_polling(
    timeout=60,
    long_polling_timeout=60
)
