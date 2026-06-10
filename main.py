#!/usr/bin/env python3
"""
TANJUAFLIX AI - Telegram Bot
Simple image generation bot using Pollinations AI
"""

import logging
import base64
import urllib.parse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
import httpx

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8828859126:AAEDie5-nNIVZbr7Xrkb8w7u-9xEdOFXc0U"
POLLINATIONS_URL = "https://image.pollinations.ai/prompt"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    msg = """🎨 **TANJUAFLIX AI Bot** 🤖

Welcome! Send me any text and I'll generate an AI image.

Examples:
- "A cat sitting on moon"
- "Sunset over ocean"
- "Futuristic city"

Just send text and wait 15-45 seconds!"""
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    msg = """📖 **Help**

Just send any description and I'll generate an image!

Tips:
✅ Be descriptive
✅ Use adjectives
✅ Specify style

Example: "A beautiful sunset over mountains, oil painting style"

Generation takes 15-45 seconds."""
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def generate_image(prompt: str) -> dict:
    """Generate image from Pollinations API"""
    try:
        encoded = urllib.parse.quote(prompt.strip())
        url = f"{POLLINATIONS_URL}/{encoded}?width=512&height=512&model=flux"
        
        logger.info(f"Generating: {prompt}")
        
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url, follow_redirects=True)
            
            if resp.status_code == 200:
                b64 = base64.b64encode(resp.content).decode()
                return {"ok": True, "data": b64, "size": len(resp.content)}
            else:
                return {"ok": False, "error": f"API error: {resp.status_code}"}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"ok": False, "error": str(e)}

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    
    prompt = update.message.text.strip()
    
    if len(prompt) < 3:
        await update.message.reply_text("❌ Prompt too short! Min 3 characters.")
        return
    
    if len(prompt) > 500:
        await update.message.reply_text("❌ Prompt too long! Max 500 characters.")
        return
    
    # Show typing
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    
    # Send status
    status = await update.message.reply_text(f"🎨 Generating: *{prompt}*\n\n⏳ Wait 15-45 seconds...", parse_mode="Markdown")
    
    try:
        result = await generate_image(prompt)
        
        if not result["ok"]:
            await status.edit_text(f"❌ Error: {result['error']}\n\n💡 Try simpler prompt")
            return
        
        # Send image
        img_data = base64.b64decode(result["data"])
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=img_data,
            caption=f"✅ Generated: *{prompt}*",
            parse_mode="Markdown"
        )
        
        # Delete status
        try:
            await status.delete()
        except:
            pass
        
        logger.info(f"✅ Success! Size: {result['size']} bytes")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await status.edit_text(f"❌ Error: {str(e)[:100]}")

def main():
    """Start bot"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("🤖 Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
