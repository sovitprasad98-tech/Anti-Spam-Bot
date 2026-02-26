from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup, ChatMemberUpdated
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ChatMemberHandler, CommandHandler, filters, ContextTypes
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import os

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8565945940:AAHfwADWZnO7QvVIKPZ-6TDEgCUGQZ-bVZA")

# Configuration
WARNING_THRESHOLD = 2       # 2 same messages in 30s = Warning
MUTE_THRESHOLD = 3          # 3 same messages in 30s = Mute
TIME_WINDOW = 30            # 30 seconds - STRICT TIME WINDOW
MUTE_DURATION_HOURS = 2     # 2 hours mute
WARNING_DELETE_TIME = 20    # Warning auto-delete after 20s
MUTE_MSG_DELETE_TIME = 60   # Mute message auto-delete after 60s

DEVELOPER_CREDIT = "\n\n💎 *Developed by SovitX*"

# User tracking with timestamp-based logic
user_spam_data = defaultdict(lambda: {
    'messages': [],          # List of {text, time, message_id}
    'muted': False,
    'warned': False,
    'mute_count': 0,
    'warning_count': 0,
    'last_violation': None
})

# Bot statistics
bot_stats = {
    'total_warnings': 0,
    'total_mutes': 0,
    'total_bans': 0,
    'messages_deleted': 0,
    'start_time': datetime.now()
}


def escape_markdown(text):
    """Escape Markdown V2 special characters"""
    if not text:
        return ""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = str(text).replace(char, f'\\{char}')
    return text


def reset_user_data(user_id):
    """Reset user spam tracking data"""
    if user_id in user_spam_data:
        del user_spam_data[user_id]
        logger.info(f"🔄 Data reset for user ID: {user_id}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - Different response for private vs group"""
    
    # PRIVATE CHAT - Setup Instructions
    if update.effective_chat.type == "private":
        setup_text = (
            f"👋 *Welcome to Anti\\-Spam Bot\\!*\n"
            f"💎 *Developed by SovitX*\n"
            f"{'='*40}\n\n"
            f"🤖 *I'm a powerful spam protection bot\\!*\n\n"
            f"📋 *SETUP INSTRUCTIONS*\n\n"
            f"*Step 1:* Add me to your group\n"
            f"└─ Click on my profile → Add to Group\n\n"
            f"*Step 2:* Make me Admin\n"
            f"└─ Go to Group Info → Administrators\n"
            f"└─ Add me as admin\n\n"
            f"*Step 3:* Give me these permissions:\n"
            f"├─ ✅ Delete Messages\n"
            f"├─ ✅ Ban Users\n"
            f"└─ ✅ Restrict Members\n\n"
            f"*Step 4:* Done\\! 🎉\n"
            f"└─ I'll automatically protect your group\\!\n\n"
            f"{'='*40}\n\n"
            f"⚡ *BOOM\\! I'm ready to protect\\!*\n\n"
            f"🛡️ *What I do:*\n"
            f"├─ Detect spam automatically\n"
            f"├─ Warn spammers\n"
            f"├─ Mute repeat offenders\n"
            f"└─ Keep your group clean\\!\n\n"
            f"💡 *Type /help in your group for commands\\!*\n\n"
            f"🌟 _Protecting communities 24/7_"
        )
        
        await update.message.reply_text(setup_text, parse_mode='MarkdownV2')
        logger.info(f"Setup instructions sent to user {update.effective_user.id}")
        return
    
    # GROUP CHAT - Bot Status
    uptime = datetime.now() - bot_stats['start_time']
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)
    
    status_text = (
        f"🔥 *ULTIMATE ANTI\\-SPAM BOT*\n"
        f"💎 *Developed by SovitX*\n"
        f"{'='*40}\n\n"
        f"📊 *BOT STATUS*\n"
        f"├─ ✅ Status: *Online & Active*\n"
        f"├─ ⏱ Uptime: *{hours}h {minutes}m*\n"
        f"└─ 🔥 Power: *MAXIMUM*\n\n"
        f"📈 *PROTECTION STATS*\n"
        f"├─ ⚠️ Warnings Issued: *{bot_stats['total_warnings']}*\n"
        f"├─ 🔴 Users Muted: *{bot_stats['total_mutes']}*\n"
        f"├─ 🚫 Users Banned: *{bot_stats['total_bans']}*\n"
        f"└─ 🗑️ Spam Deleted: *{bot_stats['messages_deleted']}*\n\n"
        f"⚙️ *DETECTION SETTINGS*\n"
        f"├─ Warning: *{WARNING_THRESHOLD} same messages*\n"
        f"├─ Mute: *{MUTE_THRESHOLD} same messages*\n"
        f"├─ Time Window: *{TIME_WINDOW} seconds*\n"
        f"└─ Mute Duration: *{MUTE_DURATION_HOURS} hours*\n\n"
        f"🛡️ *ACTIVE FEATURES*\n"
        f"├─ 🚨 Smart spam detection\n"
        f"├─ ⚠️ Two\\-level warning system\n"
        f"├─ 🔴 Automatic mute system\n"
        f"├─ 🚫 Admin ban controls\n"
        f"├─ 🔓 Admin unmute controls\n"
        f"├─ 🔄 Auto\\-reset on leave/join\n"
        f"└─ 📊 Real\\-time monitoring\n\n"
        f"👮 *ADMIN COMMANDS*\n"
        f"├─ `/stats` \\- View detailed statistics\n"
        f"├─ `/reset` \\- Reset user warnings\n"
        f"└─ `/help` \\- Get help\n\n"
        f"{'='*40}\n"
        f"🌟 *Your group is protected 24/7\\!*"
    )
    
    await update.message.reply_text(status_text, parse_mode='MarkdownV2')


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin statistics command"""
    chat_id = update.effective_chat.id
    
    try:
        chat_admins = await context.bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in chat_admins]
        
        if update.effective_user.id not in admin_ids:
            await update.message.reply_text("❌ Only admins can view statistics!")
            return
        
        uptime = datetime.now() - bot_stats['start_time']
        
        stats_text = (
            f"📊 *DETAILED STATISTICS*\n"
            f"💎 *Developed by SovitX*\n"
            f"{'='*40}\n\n"
            f"⏱ *Bot Runtime*\n"
            f"└─ {int(uptime.total_seconds() // 3600)}h {int((uptime.total_seconds() % 3600) // 60)}m\n\n"
            f"📈 *Actions Taken*\n"
            f"├─ Warnings Issued: *{bot_stats['total_warnings']}*\n"
            f"├─ Users Muted: *{bot_stats['total_mutes']}*\n"
            f"├─ Users Banned: *{bot_stats['total_bans']}*\n"
            f"└─ Messages Deleted: *{bot_stats['messages_deleted']}*\n\n"
            f"👥 *Active Monitoring*\n"
            f"└─ Tracked Users: *{len(user_spam_data)}*\n\n"
            f"🛡️ *Protection Level*\n"
            f"└─ *MAXIMUM SECURITY*\n\n"
            f"⚙️ *Current Settings*\n"
            f"├─ Time Window: *{TIME_WINDOW}s*\n"
            f"├─ Warning at: *{WARNING_THRESHOLD} messages*\n"
            f"└─ Mute at: *{MUTE_THRESHOLD} messages*\n\n"
            f"{'='*40}\n"
            f"✨ *Protecting your community\\!*"
        )
        
        await update.message.reply_text(stats_text, parse_mode='MarkdownV2')
        
    except Exception as e:
        logger.error(f"Stats command error: {e}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help information"""
    help_text = (
        f"📖 *HELP \\- ANTI\\-SPAM BOT*\n"
        f"💎 *Developed by SovitX*\n"
        f"{'='*40}\n\n"
        f"🤖 *HOW IT WORKS*\n"
        f"The bot monitors all messages automatically\\.\n"
        f"It tracks repeated messages within a time window\\.\n\n"
        f"⚠️ *WARNING SYSTEM*\n"
        f"├─ {WARNING_THRESHOLD} same messages in {TIME_WINDOW}s → Warning\n"
        f"├─ User gets notified\n"
        f"└─ Warning auto\\-deletes after {WARNING_DELETE_TIME}s\n\n"
        f"🔴 *MUTE SYSTEM*\n"
        f"├─ {MUTE_THRESHOLD} same messages in {TIME_WINDOW}s → Mute\n"
        f"├─ User muted for {MUTE_DURATION_HOURS}h\n"
        f"├─ Spam messages deleted\n"
        f"└─ Auto\\-unmute after duration\n\n"
        f"⏱ *TIME WINDOW LOGIC*\n"
        f"_Only messages within {TIME_WINDOW} seconds are counted\\._\n"
        f"_If more than {TIME_WINDOW}s passes, counter resets\\._\n\n"
        f"👮 *ADMIN COMMANDS*\n"
        f"├─ `/start` \\- Bot status\n"
        f"├─ `/stats` \\- View statistics\n"
        f"├─ `/reset` \\- Reset user \\(reply to msg\\)\n"
        f"└─ `/help` \\- This help message\n\n"
        f"🛡️ *ADMIN CONTROLS*\n"
        f"When user is muted, admins see:\n"
        f"├─ 🔓 Unmute \\- Remove mute instantly\n"
        f"└─ 🚫 Ban \\- Permanently ban user\n\n"
        f"🔄 *AUTO\\-RESET TRIGGERS*\n"
        f"User gets fresh start when:\n"
        f"├─ They leave and rejoin group\n"
        f"├─ Admin unmutes them\n"
        f"├─ Auto\\-unmute completes\n"
        f"└─ Admin uses /reset command\n\n"
        f"{'='*40}\n"
        f"💡 *Bot needs admin permissions to work\\!*"
    )
    
    await update.message.reply_text(help_text, parse_mode='MarkdownV2')


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin reset command"""
    chat_id = update.effective_chat.id
    admin_id = update.effective_user.id
    
    try:
        chat_admins = await context.bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in chat_admins]
        
        if admin_id not in admin_ids:
            await update.message.reply_text("❌ Only admins can use this command!")
            return
        
        if update.message.reply_to_message:
            target_user_id = update.message.reply_to_message.from_user.id
            target_username = update.message.reply_to_message.from_user.first_name
        else:
            await update.message.reply_text(
                "ℹ️ *Usage:* Reply to user's message and type `/reset`",
                parse_mode='MarkdownV2'
            )
            return
        
        reset_user_data(target_user_id)
        
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True
            )
        )
        
        admin_name = update.effective_user.first_name
        
        await update.message.reply_text(
            f"✅ *User Reset Successfully\\!*\n\n"
            f"👤 User: {escape_markdown(target_username)}\n"
            f"👮 By Admin: {escape_markdown(admin_name)}\n"
            f"🔄 All warnings cleared\n"
            f"✨ Fresh start granted\\!",
            parse_mode='MarkdownV2'
        )
        
        logger.info(f"Admin {admin_name} reset user {target_username}")
        
    except Exception as e:
        logger.error(f"Reset command error: {e}")


async def track_member_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Track member joins/leaves for auto-reset"""
    result = update.chat_member
    
    if result is None:
        return
    
    user_id = result.new_chat_member.user.id
    username = result.new_chat_member.user.first_name
    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status
    
    # User left - reset data
    if old_status in ["member", "restricted"] and new_status in ["left", "kicked"]:
        reset_user_data(user_id)
        logger.info(f"👋 {username} left - data cleared")
    
    # User joined - fresh start
    elif old_status in ["left", "kicked"] and new_status == "member":
        reset_user_data(user_id)
        logger.info(f"👋 {username} joined - fresh start")


async def anti_spam_system(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main spam detection engine with strict 30-second time window logic.
    
    LOGIC EXPLANATION:
    1. Store each message with timestamp
    2. Remove messages older than 30 seconds
    3. Count only messages within the 30-second window
    4. Take action based on count
    """
    if not update.message or not update.message.text:
        return
    
    user_id = update.message.from_user.id
    username = update.message.from_user.first_name
    user_handle = update.message.from_user.username or "no_username"
    message_text = update.message.text.strip().lower()
    chat_id = update.message.chat_id
    chat_title = update.message.chat.title or "Unknown Group"
    current_time = datetime.now()
    message_id = update.message.message_id
    
    # If user is muted, delete their message immediately
    if user_spam_data[user_id]['muted']:
        try:
            await update.message.delete()
            bot_stats['messages_deleted'] += 1
            logger.info(f"🗑️ Deleted message from muted user: {username}")
            return
        except:
            return
    
    # Add current message to tracking list
    user_spam_data[user_id]['messages'].append({
        'text': message_text,
        'time': current_time,
        'message_id': message_id
    })
    
    # CRITICAL: Remove messages older than 30 seconds (TIME_WINDOW)
    # This ensures we ONLY count messages within the time window
    cutoff_time = current_time - timedelta(seconds=TIME_WINDOW)
    user_spam_data[user_id]['messages'] = [
        msg for msg in user_spam_data[user_id]['messages']
        if msg['time'] > cutoff_time
    ]
    
    # Count ONLY same messages within the 30-second window
    same_messages = [
        msg for msg in user_spam_data[user_id]['messages']
        if msg['text'] == message_text
    ]
    
    spam_count = len(same_messages)
    
    logger.debug(f"User {username}: {spam_count} same messages in last {TIME_WINDOW}s")
    
    # ACTION 1: WARNING (2 same messages within 30s)
    if spam_count == WARNING_THRESHOLD and not user_spam_data[user_id]['warned']:
        logger.warning(f"⚠️ WARNING! {username} | {chat_title} | Count: {spam_count}")
        
        try:
            user_spam_data[user_id]['warning_count'] += 1
            user_spam_data[user_id]['warned'] = True
            bot_stats['total_warnings'] += 1
            
            safe_username = escape_markdown(username)
            safe_handle = escape_markdown(user_handle)
            
            warning_text = (
                f"⚠️ *SPAM WARNING\\!*\n\n"
                f"🚨 User: [{safe_username}](tg://user?id={user_id})\n"
                f"🆔 Username: @{safe_handle}\n\n"
                f"📛 *VIOLATION DETECTED*\n"
                f"├─ Repeated message: *{spam_count} times*\n"
                f"├─ Within: *{TIME_WINDOW} seconds*\n"
                f"└─ Warning \\#{user_spam_data[user_id]['warning_count']}\n\n"
                f"🚫 *STOP SPAMMING IMMEDIATELY\\!*\n"
                f"⚡ One more spam = *INSTANT MUTE*\n\n"
                f"🔴 Do not repeat messages\\!\n"
                f"You will be muted if you continue\\!"
                f"{DEVELOPER_CREDIT}"
            )
            
            warning_msg = await update.message.reply_text(
                text=warning_text,
                parse_mode='MarkdownV2'
            )
            
            # Auto-delete warning after configured time
            context.application.job_queue.run_once(
                delete_message,
                when=WARNING_DELETE_TIME,
                data={'chat_id': chat_id, 'message_id': warning_msg.message_id}
            )
            
            logger.info(f"✅ Warning sent to {username}")
            
        except Exception as e:
            logger.error(f"Warning error: {e}")
    
    # ACTION 2: MUTE (3 same messages within 30s)
    elif spam_count >= MUTE_THRESHOLD:
        logger.error(f"🔴 MUTING! {username} | {chat_title} | Count: {spam_count}")
        
        try:
            mute_until = current_time + timedelta(hours=MUTE_DURATION_HOURS)
            
            # Mute user with restricted permissions
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_polls=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                    can_invite_users=False
                ),
                until_date=mute_until
            )
            
            # Delete all spam messages
            deleted_count = 0
            for msg in same_messages:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg['message_id'])
                    deleted_count += 1
                    bot_stats['messages_deleted'] += 1
                except:
                    pass
            
            # Update user data
            user_spam_data[user_id]['mute_count'] += 1
            user_spam_data[user_id]['muted'] = True
            user_spam_data[user_id]['warned'] = False
            user_spam_data[user_id]['messages'] = []
            user_spam_data[user_id]['last_violation'] = current_time
            
            bot_stats['total_mutes'] += 1
            mute_count = user_spam_data[user_id]['mute_count']
            
            safe_username = escape_markdown(username)
            safe_handle = escape_markdown(user_handle)
            
            # Admin control buttons
            keyboard = [
                [
                    InlineKeyboardButton("🔓 Unmute", callback_data=f"unmute_{user_id}"),
                    InlineKeyboardButton("🚫 Ban", callback_data=f"ban_{user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # ENGLISH MUTE MESSAGE
            mute_text = (
                f"🔴 *USER MUTED\\!*\n\n"
                f"👤 *Name:* [{safe_username}](tg://user?id={user_id})\n"
                f"🆔 *Username:* @{safe_handle}\n"
                f"🔢 *User ID:* `{user_id}`\n\n"
                f"📛 *REASON*\n"
                f"├─ *Attempted to spam the group*\n"
                f"├─ Same message: *{spam_count} times*\n"
                f"├─ Within: *{TIME_WINDOW} seconds*\n"
                f"└─ Messages deleted: *{deleted_count}*\n\n"
                f"⏱ *MUTE DETAILS*\n"
                f"├─ Duration: *{MUTE_DURATION_HOURS} hours*\n"
                f"├─ Until: *{escape_markdown(mute_until.strftime('%d %b, %I:%M %p'))}*\n"
                f"└─ Total violations: *{mute_count}*\n\n"
                f"🚫 *COMMUNITY MESSAGE*\n"
                f"_This user tried to spam the group\\._\n"
                f"_They have been muted for this behavior\\._\n"
                f"_Please do not repeat this behavior\\!_\n\n"
                f"👮 *ADMIN CONTROLS*\n"
                f"Only admins can use the buttons below\\."
                f"{DEVELOPER_CREDIT}"
            )
            
            mute_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=mute_text,
                parse_mode='MarkdownV2',
                reply_markup=reply_markup
            )
            
            # Schedule mute message deletion
            context.application.job_queue.run_once(
                delete_message,
                when=MUTE_MSG_DELETE_TIME,
                data={'chat_id': chat_id, 'message_id': mute_msg.message_id}
            )
            
            # Schedule auto-unmute
            context.application.job_queue.run_once(
                auto_unmute_user,
                when=timedelta(hours=MUTE_DURATION_HOURS),
                data={
                    'user_id': user_id,
                    'chat_id': chat_id,
                    'username': username
                }
            )
            
            logger.info(f"✅ {username} muted until {mute_until.strftime('%I:%M %p')}")
            
        except Exception as e:
            logger.error(f"Mute error: {e}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin button clicks (Unmute/Ban)"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat_id
    admin_id = query.from_user.id
    
    try:
        # Verify admin status
        chat_admins = await context.bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in chat_admins]
        
        if admin_id not in admin_ids:
            await query.answer("❌ Only admins can use these controls!", show_alert=True)
            return
        
        action, user_id = query.data.split('_')
        user_id = int(user_id)
        admin_name = query.from_user.first_name
        
        # UNMUTE ACTION
        if action == "unmute":
            await context.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_invite_users=True
                )
            )
            
            reset_user_data(user_id)
            
            safe_admin = escape_markdown(admin_name)
            
            await query.edit_message_text(
                text=f"✅ *USER UNMUTED\\!*\n\n"
                     f"👮 *Unmuted by:* Admin {safe_admin}\n"
                     f"🔄 *Status:* All warnings cleared\\!\n"
                     f"✨ *Fresh start granted\\!*\n"
                     f"⚠️ Please follow group rules\\!"
                     f"{DEVELOPER_CREDIT}",
                parse_mode='MarkdownV2'
            )
            
            logger.info(f"✅ Admin {admin_name} unmuted user {user_id}")
        
        # BAN ACTION
        elif action == "ban":
            await context.bot.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id
            )
            
            bot_stats['total_bans'] += 1
            reset_user_data(user_id)
            
            safe_admin = escape_markdown(admin_name)
            
            await query.edit_message_text(
                text=f"🚫 *USER PERMANENTLY BANNED\\!*\n\n"
                     f"👮 *Banned by:* Admin {safe_admin}\n"
                     f"⚠️ *Reason:* Spam violation\n"
                     f"🔴 *Status:* Permanently removed from group\\!\n\n"
                     f"_User has been kicked and cannot rejoin\\._"
                     f"{DEVELOPER_CREDIT}",
                parse_mode='MarkdownV2'
            )
            
            logger.info(f"🚫 Admin {admin_name} banned user {user_id}")
        
    except Exception as e:
        logger.error(f"Button callback error: {e}")
        await query.answer(f"❌ Error: {str(e)}", show_alert=True)


async def delete_message(context: ContextTypes.DEFAULT_TYPE):
    """Delete scheduled messages (warnings/mute announcements)"""
    try:
        await context.bot.delete_message(
            chat_id=context.job.data['chat_id'],
            message_id=context.job.data['message_id']
        )
        logger.info("🗑️ Scheduled message deleted")
    except:
        pass


async def auto_unmute_user(context: ContextTypes.DEFAULT_TYPE):
    """Automatically unmute user after mute duration"""
    job_data = context.job.data
    user_id = job_data['user_id']
    chat_id = job_data['chat_id']
    username = job_data['username']
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True
            )
        )
        
        reset_user_data(user_id)
        
        logger.info(f"✅ Auto-unmuted: {username}")
        
        safe_username = escape_markdown(username)
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🔓 *AUTO UNMUTE NOTIFICATION*\n\n"
                 f"👤 {safe_username} has been unmuted\\!\n"
                 f"🔄 Fresh start granted\\!\n"
                 f"⚠️ Please follow group rules\\!"
                 f"{DEVELOPER_CREDIT}",
            parse_mode='MarkdownV2'
        )
        
    except Exception as e:
        logger.error(f"Auto-unmute error: {e}")


def main():
    """Initialize and start the bot"""
    print("\n" + "="*60)
    print("🔥 ULTIMATE ANTI-SPAM BOT v3.1 (ENGLISH)")
    print("💎 Developed by SovitX")
    print("="*60)
    print("\n⚙️  Configuration:")
    print(f"   ├─ ⚠️  Warning: {WARNING_THRESHOLD} same messages")
    print(f"   ├─ 🔴 Mute: {MUTE_THRESHOLD} same messages")
    print(f"   ├─ ⏱  Time Window: {TIME_WINDOW} seconds (STRICT)")
    print(f"   ├─ 🔒 Mute Duration: {MUTE_DURATION_HOURS} hours")
    print(f"   ├─ 🗑️  Warning Delete: {WARNING_DELETE_TIME}s")
    print(f"   └─ 🗑️  Mute Msg Delete: {MUTE_MSG_DELETE_TIME}s")
    print("\n🎯 Logic:")
    print(f"   └─ Messages counted ONLY within {TIME_WINDOW}s window")
    print(f"      If message is older than {TIME_WINDOW}s, it's ignored")
    print("\n🎯 Features:")
    print("   ├─ ✅ Pure English messages")
    print("   ├─ ✅ Private /start with setup guide")
    print("   ├─ ✅ Strict 30-second time window")
    print("   ├─ ✅ 2-level warning system")
    print("   ├─ ✅ Ban + Unmute buttons")
    print("   ├─ ✅ Real-time statistics")
    print("   └─ ✅ Auto reset on leave/join")
    print("\n🚀 Starting ultimate protection...\n")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Commands
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("stats", stats_command, filters=filters.ChatType.GROUPS))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("reset", reset_command, filters=filters.ChatType.GROUPS))
        
        # Message handler for spam detection
        application.add_handler(
            MessageHandler(
                filters.TEXT & filters.ChatType.GROUPS,
                anti_spam_system
            )
        )
        
        # Button callback handler
        application.add_handler(
            CallbackQueryHandler(button_callback)
        )
        
        # Member tracking handler
        application.add_handler(
            ChatMemberHandler(track_member_updates, ChatMemberHandler.CHAT_MEMBER)
        )
        
        print("✅ Bot started successfully!")
        print("🛡️  Protection: ACTIVE")
        print("👀 Monitoring: ALL GROUPS")
        print("⏱  Time Window: STRICT 30s")
        print("🔥 Power: MAXIMUM")
        print("\n" + "="*60)
        print("📊 LIVE LOGS:\n")
        
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")


if __name__ == '__main__':
    main()