# TANJUAFLIX AI - Telegram Bot

Generate AI images directly from Telegram using TANJUAFLIX AI!

## Features

✨ **AI Image Generation**
- Generate images from text descriptions
- Multiple image sizes (512x512, 768x768, 1024x1024)
- Flux AI model for high-quality images

🚀 **Easy to Use**
- Just send a text description
- Bot generates image automatically
- No complex commands needed

⚡ **Fast & Reliable**
- Powered by Manus AI API
- Fallback to Pollinations API
- 10-30 second generation time

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Edit `.env` file with your settings:
```
BOT_TOKEN=your_bot_token_here
MANUS_API_URL=https://api.manus.im
MANUS_API_KEY=your_api_key_here
```

### 3. Run the Bot
```bash
python bot.py
```

## Usage

### Commands
- `/start` - Start the bot and see welcome message
- `/help` - Get help and tips
- `/settings` - Adjust image settings

### Generate Images
Simply send any text description:
- "A cat sitting on a moon"
- "Futuristic city at sunset"
- "Beautiful landscape with mountains"

## API Integration

### Manus API
- Primary image generation service
- Requires API key
- High quality, fast generation

### Pollinations API
- Fallback service
- No API key required
- Good quality images

## Deployment

### Local Deployment
```bash
python bot.py
```

### Docker Deployment
```bash
docker build -t tanjuaflix-bot .
docker run -e BOT_TOKEN=your_token tanjuaflix-bot
```

### Railway Deployment
1. Push to GitHub
2. Connect Railway to repository
3. Set environment variables
4. Deploy

## Configuration

### Image Sizes
- 256x256 - Fast, lower quality
- 512x512 - Balanced (default)
- 768x768 - High quality
- 1024x1024 - Maximum quality

### Models
- flux - Default model
- flux-pro - Professional quality
- stable-diffusion - Alternative model

## Troubleshooting

### Bot not responding
- Check bot token is correct
- Verify internet connection
- Check logs for errors

### Images not generating
- Try simpler prompt
- Check API keys
- Verify API service is running

### Slow generation
- This is normal (10-30 seconds)
- Larger images take longer
- Try smaller size first

## Support

For issues or questions:
1. Check the help command: `/help`
2. Review the README
3. Check bot logs for errors

## License

MIT License - Feel free to use and modify!

## Credits

- Built with python-telegram-bot
- Powered by Manus AI & Pollinations API
- TANJUAFLIX AI Project
