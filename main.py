from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
import httpx
import base64
import urllib.parse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8828859126:AAEDie5-nNIVZbr7Xrkb8w7u-9xEdOFXc0U"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎨 Send me any text and I'll generate an AI image!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    
    if len(prompt) < 3 or len(prompt) > 500:
        await update.message.reply_text("❌ Prompt must be 3-500 characters")
        return
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    msg = await update.message.reply_text(f"🎨 Generating: {prompt}\n⏳ Wait 15-45 seconds...")
    
    try:
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&model=flux"
        
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url, follow_redirects=True)
        
        if resp.status_code == 200:
            img = base64.b64encode(resp.content).decode()
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=base64.b64decode(img),
                caption=f"✅ {prompt}"
            )
            await msg.delete()
        else:
            await msg.edit_text("❌ Generation failed. Try again!")
    except Exception as e:
        await msg.edit_text(f"❌ Error: {str(e)[:50]}")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    logger.info("Bot started!")
    app.run_polling()
