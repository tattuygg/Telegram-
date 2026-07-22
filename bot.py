from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
import httpx
import base64
import logging
import urllib.parse
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8828859126:AAEDie5-nNIVZbr7Xrkb8w7u-9xEdOFXc0U"

async def generate_image_pollinations(prompt: str) -> dict:
    """
    Generate image using Pollinations AI with proper error handling
    """
    try:
        # URL encode the prompt properly
        encoded_prompt = urllib.parse.quote(prompt.strip())
        
        # Pollinations API endpoint
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        
        logger.info(f"Generating image for: {prompt}")
        
        # Fetch with proper headers and timeout
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                # Successfully got image
                img_data = response.content
                
                if len(img_data) > 100:  # Check if we got actual image data
                    b64 = base64.b64encode(img_data).decode()
                    logger.info(f"✅ Image generated successfully! Size: {len(img_data)} bytes")
                    return {"ok": True, "data": b64}
                else:
                    logger.warning("Received data too small, likely not an image")
                    return {"ok": False, "error": "Invalid image data"}
            else:
                logger.error(f"API returned status {response.status_code}")
                return {"ok": False, "error": f"API error: {response.status_code}"}
                
    except asyncio.TimeoutError:
        logger.error("Request timeout")
        return {"ok": False, "error": "Generation timeout - try simpler prompt"}
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e}")
        return {"ok": False, "error": str(e)[:100]}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    msg = """🎨 **TANJUAFLIX AI Bot** 🤖

Send me any description and I'll generate an AI image!

Examples:
• A cat sitting on the moon
• Sunset over mountains
• Futuristic city
• Beautiful garden

Just send text and wait 20-60 seconds!"""
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    prompt = update.message.text.strip()
    
    # Validate prompt
    if len(prompt) < 3:
        await update.message.reply_text("❌ Prompt too short! Min 3 characters")
        return
    
    if len(prompt) > 500:
        await update.message.reply_text("❌ Prompt too long! Max 500 characters")
        return
    
    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action=ChatAction.TYPING
    )
    
    # Send status message
    status_msg = await update.message.reply_text(
        f"🎨 **Generating:** {prompt}\n\n⏳ Wait 20-60 seconds..."
    )
    
    try:
        # Generate image
        result = await generate_image_pollinations(prompt)
        
        if result["ok"]:
            # Decode and send image
            img_data = base64.b64decode(result["data"])
            
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_data,
                caption=f"✅ **Generated:** {prompt}",
                parse_mode="Markdown"
            )
            
            # Delete status message
            try:
                await status_msg.delete()
            except:
                pass
            
            logger.info(f"✅ Image sent successfully")
        else:
            # Show error
            error_msg = result.get("error", "Unknown error")
            await status_msg.edit_text(
                f"❌ **Generation Failed**\n\n{error_msg}\n\n💡 Try a simpler prompt"
            )
    
    except Exception as e:
        logger.error(f"Send error: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)[:80]}")

# Create application
app = Application.builder().token(TOKEN).build()

# Add handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == "__main__":
    logger.info("🤖 TANJUAFLIX AI Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
