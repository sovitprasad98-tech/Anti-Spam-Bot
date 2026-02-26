from telegram import Update
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, ChatMemberHandler, CommandHandler, filters
from http.server import BaseHTTPRequestHandler
import json, os, asyncio, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    start_command, stats_command, help_command, reset_command,
    anti_spam_system, button_callback, track_member_updates, BOT_TOKEN
)

async def process_update(update_data):
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stats", stats_command, filters=filters.ChatType.GROUPS))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset_command, filters=filters.ChatType.GROUPS))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, anti_spam_system))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(ChatMemberHandler(track_member_updates, ChatMemberHandler.CHAT_MEMBER))
    
    await app.initialize()
    update = Update.de_json(update_data, app.bot)
    await app.process_update(update)
    await app.shutdown()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        update_data = json.loads(body.decode('utf-8'))
        asyncio.run(process_update(update_data))
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running!')
