"""
TANJUAFLIX AI - Telegram Bot
Generate AI images directly from Telegram
"""

import logging
import os
import asyncio
import base64
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction
import httpx
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token
BOT_TOKEN = "8828859126:AAEDie5-nNIVZbr7Xrkb8w7u-9xEdOFXc0U"

# Pollinations API Configuration
POLLINATIONS_API_URL = "https://image.pollinations.ai/prompt"

# Store user sessions
user_sessions = {}

class ImageGenerator:
    """Handle image generation with Pollinations AI"""
    
    @staticmethod
    async def generate_image(prompt: str, width: int = 512, height: int = 512, model: str = "flux") -> dict:
        """Generate image using Pollinations API"""
        try:
            # Build Pollinations URL with proper encoding
            encoded_prompt = urllib.parse.quote(prompt.strip())
            url = f"{POLLINATIONS_API_URL}/{encoded_prompt}?width={width}&height={height}&model={model}"
            
            logger.info(f"Generating image with prompt: {prompt}")
            logger.info(f"URL: {url}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, follow_redirects=True)
                
                logger.info(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    # Encode image as base64
                    image_base64 = base64.b64encode(response.content).decode('utf-8')
                    return {
                        "success": True,
                        "base64": image_base64,
                        "size": len(response.content),
                        "prompt": prompt
                    }
                else:
                    logger.error(f"API error: {response.status_code}")
                    return {"success": False, "error": f"API returned {response.status_code}"}
                    
        except asyncio.TimeoutError:
            logger.error("Request timeout")
            return {"success": False, "error": "Request timeout - image generation took too long"}
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return {"success": False, "error": str(e)}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler"""
    welcome_message = """
🎨 **TANJUAFLIX AI Bot** 🤖

Welcome! I can generate AI images from your text prompts using Pollinations AI.

**How to use:**
1. Just send me any text description
2. I'll generate an AI image based on your description
3. The image will be sent to you

**Examples:**
- "A cat sitting on a moon"
- "Futuristic city at sunset"
- "Elephant dancing in the rain"

**Commands:**
/start - Show this message
/help - Get help
/settings - Adjust image settings

Let's create some amazing images! 🚀
    """
    
    await update.message.reply_text(
        welcome_message,
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command handler"""
    help_text = """
📖 **Help & Guide**

**Basic Usage:**
Send any text and I'll generate an image!

**Image Settings:**
- Default size: 512x512
- Supported sizes: 256, 512, 768, 1024
- Model: Flux (AI image generation)

**Tips:**
✅ Be descriptive: "A red cat with blue eyes sitting on a golden chair"
✅ Use adjectives: "beautiful, stunning, detailed, realistic"
✅ Specify style: "oil painting, digital art, 3D render"
✅ Add mood: "dark, bright, moody, cheerful"

**Example prompts:**
- "A serene landscape with mountains and lake at sunset"
- "Cyberpunk city street with neon lights"
- "Cute robot playing with flowers"

**Limitations:**
⏱️ Image generation takes 15-45 seconds
📊 Max 10 requests per minute
🎯 Keep prompts under 500 characters

**Troubleshooting:**
- If image doesn't generate, try a simpler prompt
- Avoid offensive or NSFW content
- Use /settings to adjust image size

Need more help? Use /help again or try a different prompt!
    """
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages and generate images"""
    
    user_id = update.effective_user.id
    prompt = update.message.text.strip()
    
    # Validate prompt
    if not prompt or len(prompt) < 3:
        await update.message.reply_text(
            "❌ Please provide a proper description for the image.\n\n"
            "Example: 'A beautiful sunset over the ocean'"
        )
        return
    
    if len(prompt) > 500:
        await update.message.reply_text(
            "❌ Prompt is too long! Keep it under 500 characters."
        )
        return
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    
    # Send generating message
    status_message = await update.message.reply_text(
        f"🎨 Generating image for: *{prompt}*\n\n⏳ This may take 15-45 seconds...",
        parse_mode="Markdown"
    )
    
    try:
        # Generate image
        logger.info(f"User {user_id} requested: {prompt}")
        
        result = await ImageGenerator.generate_image(prompt)
        
        if not result["success"]:
            error_msg = result.get("error", "Unknown error")
            await status_message.edit_text(
                f"❌ Failed to generate image: {error_msg}\n\n"
                "💡 Tip: Try a simpler prompt or wait a moment and try again"
            )
            return
        
        # Send image from base64
        try:
            image_data = base64.b64decode(result["base64"])
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_data,
                caption=f"✅ Generated: *{prompt}*\n\nSize: {result['size']} bytes",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            await update.message.reply_text(
                f"❌ Error sending image: {str(e)[:100]}"
            )
            return
        
        # Delete status message
        try:
            await status_message.delete()
        except:
            pass
        
        logger.info(f"Image generated successfully for user {user_id}. Size: {result['size']} bytes")
        
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        await status_message.edit_text(
            f"❌ Error: {str(e)[:100]}\n\n"
            "Please try again with a different prompt."
        )


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Settings command"""
    keyboard = [
        [
            InlineKeyboardButton("512x512", callback_data="size_512"),
            InlineKeyboardButton("768x768", callback_data="size_768"),
        ],
        [
            InlineKeyboardButton("1024x1024", callback_data="size_1024"),
            InlineKeyboardButton("Back", callback_data="back"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚙️ **Image Settings**\n\n"
        "Select preferred image size:\n\n"
        "💡 Larger sizes take longer to generate",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


def main() -> None:
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("settings", settings_command))
    
    # Message handler for all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    logger.info("🤖 TANJUAFLIX AI Bot started with Pollinations AI!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
