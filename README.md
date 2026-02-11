# Telegram Music Recognition Bot

A Telegram bot that recognizes audio and video music using ACRCloud. Works only in group chats and requires authorization with a code word.

## Features

- 🎵 Music recognition for audio/video files
- 🔒 Group-only mode with code word authorization
- 📁 Supports multiple formats: MP3, WAV, FLAC, M4A, MP4, AVI, MKV, MOV, OGG, AAC, WMA
- 🐳 Docker support for easy deployment

## Quick Start with Docker

### 1. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
TELEGRAM_TOKEN=your_bot_token_here
ACR_ACCESS_KEY=your_acr_key_here
ACR_ACCESS_SECRET=your_acr_secret_here
CODE_WORD=music123
```

### 2. Launch with Docker Compose

```bash
docker compose up -d
```

The bot will automatically build and start in detached mode.

## Manual Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the Bot

Edit `config.yaml` with your settings:

```yaml
telegram:
  token: "YOUR_TELEGRAM_BOT_TOKEN"  # Get from @BotFather
  code_word: "music123"  # Your secret code word

acrcloud:
  host: "identify-us-west-2.acrcloud.com"
  access_key: "YOUR_ACR_ACCESS_KEY"
  access_secret: "YOUR_ACR_ACCESS_SECRET"
```

### 3. Get ACRCloud Credentials

1. Sign up at [ACRCloud](https://www.acrcloud.com/)
2. Create a new project
3. Get your access key and secret

### 4. Get Telegram Bot Token

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Use `/newbot` to create a new bot
3. Copy the token

### 5. Run the Bot

```bash
python bot.py
```

## Usage

### In Telegram Groups:

1. Add the bot to your group
2. Send `/auth <code_word>` to authorize (e.g., `/auth music123`)
3. Send an audio or video file
4. The bot will recognize and display music information

### Commands:

- `/start` - Start the bot
- `/auth <code>` - Authorize the group (required before use)
- `/help` - Show help message

## Supported Formats

- Audio: MP3, WAV, FLAC, M4A, OGG, AAC, WMA
- Video: MP4, AVI, MKV, MOV
- Voice messages

## Environment Variables

You can also use environment variables instead of config.yaml:

| Variable | Description |
|----------|-------------|
| TELEGRAM_TOKEN | Telegram bot token |
| CODE_WORD | Authorization code word |
| ACR_ACCESS_KEY | ACRCloud access key |
| ACR_ACCESS_SECRET | ACRCloud access secret |
| CONFIG_PATH | Path to config.yaml |
