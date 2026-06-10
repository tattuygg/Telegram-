"""
TANJUAFLIX AI - Telegram Bot
Generate AI images directly from Telegram
"""

import logging
import os
import asyncio
import base64
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

# Manus API Configuration
MANUS_API_URL = os.getenv("MANUS_API_URL", "https://api.manus.im")
MANUS_API_KEY = os.getenv("MANUS_API_KEY", "")

# Fallback to Pollinations API
POLLINATIONS_API_URL = "https://image.pollinations.ai/prompt"

# Store user sessions
user_sessions = {}

class ImageGenerator:
    """Handle image generation with multiple backends"""
    
    @staticmethod
    async def generate_with_manus(prompt: str, width: int = 512, height: int = 512) -> dict:
        """Generate image using Manus API"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{MANUS_API_URL}/v1/images/generations",
                    json={
                        "prompt": prompt,
                        "width": width,
                        "height": height,
                        "model": "flux-pro",
                        "n": 1,
                    },
                    headers={
                        "Authorization": f"Bearer {MANUS_API_KEY}",
                        "Content-Type": "application/json",
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    image_url = data.get("data", [{}])[0].get("url")
                    if image_url:
                        return {"success": True, "url": image_url, "source": "manus"}
        except Exception as e:
            logger.warning(f"Manus API error: {e}")
        
        return {"success": False, "source": "manus"}
    
    @staticmethod
    async def generate_with_pollinations(prompt: str, width: int = 512, height: int = 512) -> dict:
        """Generate image using Pollinations API"""
        try:
            # Build Pollinations URL
            url = f"{POLLINATIONS_API_URL}/{prompt}?width={width}&height={height}&model=flux"
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    # Encode image as base64
                    image_base64 = base64.b64encode(response.content).decode('utf-8')
                    return {
                        "success": True,
                        "base64": image_base64,
                        "source": "pollinations"
                    }
        except Exception as e:
            logger.warning(f"Pollinations API error: {e}")
        
        return {"success": False, "source": "pollinations"}
    
    @staticmethod
    async def generate(prompt: str, width: int = 512, height: int = 512) -> dict:
        """Generate image with fallback mechanism"""
        # Try Manus first
        result = await ImageGenerator.generate_with_manus(prompt, width, height)
        if result["success"]:
            return result
        
        # Fallback to Pollinations
        result = await ImageGenerator.generate_with_pollinations(prompt, width, height)
        return result


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command handler"""
    welcome_message = """
🎨 **TANJUAFLIX AI Bot** 🤖

Welcome! I can generate AI images from your text prompts.

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
⏱️ Image generation takes 10-30 seconds
📊 Max 10 requests per minute
🎯 Keep prompts under 500 characters

Need more help? Use /settings to adjust preferences.
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
        f"🎨 Generating image for: *{prompt}*\n\n⏳ This may take 10-30 seconds...",
        parse_mode="Markdown"
    )
    
    try:
        # Generate image
        logger.info(f"User {user_id} requested: {prompt}")
        
        result = await ImageGenerator.generate(prompt)
        
        if not result["success"]:
            await status_message.edit_text(
                "❌ Failed to generate image. Please try again later.\n\n"
                "💡 Tip: Try a simpler prompt"
            )
            return
        
        # Send image
        if result["source"] == "manus":
            # Send from URL
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=result["url"],
                caption=f"✅ Generated: *{prompt}*",
                parse_mode="Markdown"
            )
        else:
            # Send from base64
            image_data = base64.b64decode(result["base64"])
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=image_data,
                caption=f"✅ Generated: *{prompt}*",
                parse_mode="Markdown"
            )
        
        # Delete status message
        await status_message.delete()
        
        logger.info(f"Image generated successfully for user {user_id}")
        
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
        "Select preferred image size:",
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
    logger.info("🤖 TANJUAFLIX AI Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
