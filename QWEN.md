# Telegram Music Recognition Bot - QWEN.md

## Project Overview

A **Telegram bot** that recognizes audio and video music using the **ACRCloud API**. The bot works exclusively in **group chats** and requires authorization with a code word before it can process media files.

### Key Technologies
- **Language:** Python
- **Telegram API:** `python-telegram-bot>=20.0`
- **Music Recognition:** `acrcloud_extr_tools>=1.0.0`
- **Configuration:** `PyYAML>=6.0`
- **Environment Variables:** `python-dotenv>=1.0.0`

---

## Building and Running

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the Bot
```bash
python bot.py
```

### Configuration
Edit `config.yaml` with your credentials:
- Telegram bot token from @BotFather
- ACRCloud access key and secret
- Authorization code word

Alternatively, use environment variables:
- `TELEGRAM_TOKEN`
- `CODE_WORD`
- `ACR_ACCESS_KEY`
- `ACR_ACCESS_SECRET`
- `CONFIG_PATH`

---

## Architecture

### Core Classes

| Class | Purpose |
|-------|---------|
| `Config` | Loads and provides access to `config.yaml` settings |
| `ACRMusicRecognizer` | Handles ACRCloud API integration and result formatting |
| `MusicBot` | Main bot logic: message handling, file processing, authorization |

### Data Flow
1. Message received → Check if in group chat
2. Validate message starts with code word
3. Extract audio/video file from message or reply
4. Check file format and size limits
5. Download file to temporary storage
6. Send to ACRCloud for recognition
7. Format and return results
8. Clean up temporary files

---

## Development Conventions

### Code Style
- **Logging:** Use `logging` module with `logger.error()` and `logger.info()`
- **Type Hints:** Present in function signatures (e.g., `config_path: str = "config.yaml"`)
- **Async/Await:** Used for Telegram API calls
- **Class Structure:** Organized with single-responsibility classes

### Error Handling
- `try...except` blocks with proper exception logging
- Graceful cleanup in `finally` blocks
- Dedicated `error_handler` method for unhandled exceptions

### File Operations
- Temporary files created with `tempfile.NamedTemporaryFile`
- Automatic cleanup with `os.unlink()` in `finally` block

### Configuration Management
- YAML-based configuration with property accessors
- Environment variable overrides supported

---

## Supported Formats

| Type | Formats |
|------|---------|
| Audio | MP3, WAV, FLAC, M4A, OGG, AAC, WMA |
| Video | MP4, AVI, MKV, MOV |
| Other | Voice messages |

**Constraints:**
- Maximum file size: 20MB
- Must start with code word to trigger recognition

---

## Usage Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize the bot |
| `/help` | Display help message |
| `<code_word> [audio/video]` | Trigger recognition (code word + media file) |

**Note:** There is no `/auth` command. The bot uses a code word prefix system instead.

---

## Quick Reference

| File | Purpose |
|------|---------|
| `bot.py` | Main application entry point |
| `config.yaml` | Configuration settings |
| `requirements.txt` | Python dependencies |
| `README.md` | User documentation |
