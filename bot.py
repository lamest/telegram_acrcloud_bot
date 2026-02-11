"""
Telegram Music Recognition Bot using ACRCloud
Works in any group. Messages starting with code word trigger recognition.
"""

import os
import logging
import tempfile
import re
import subprocess
from pathlib import Path

import yaml
from telegram import Update, Message
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

from acrcloud.extrtools import recognize

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class Config:
    """Configuration manager with environment variable support."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.data = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from YAML file with environment variable overrides."""
        if not Path(self.config_path).exists():
            return {}

        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f) or {}

        # Override with environment variables if set
        env_mappings = {
            "TELEGRAM_TOKEN": ("telegram", "token"),
            "CODE_WORD": ("telegram", "code_word"),
            "ACR_HOST": ("acrcloud", "host"),
            "ACR_ACCESS_KEY": ("acrcloud", "access_key"),
            "ACR_ACCESS_SECRET": ("acrcloud", "access_secret"),
            "SUPPORTED_FORMATS": ("recognition", "supported_formats"),
            "MAX_FILE_SIZE": ("recognition", "max_file_size"),
        }

        for env_key, path in env_mappings.items():
            value = os.environ.get(env_key)
            if value is not None:
                section, key = path
                if section not in data:
                    data[section] = {}
                # Handle list format for SUPPORTED_FORMATS
                if key == "supported_formats":
                    value = [v.strip() for v in value.split(",")]
                # Handle int format for MAX_FILE_SIZE
                elif key == "max_file_size":
                    value = int(value)
                data[section][key] = value

        return data

    @property
    def telegram_token(self) -> str:
        return self.data["telegram"]["token"]

    @property
    def code_word(self) -> str:
        return self.data["telegram"]["code_word"]

    @property
    def acr_host(self) -> str:
        return self.data["acrcloud"]["host"]

    @property
    def acr_access_key(self) -> str:
        return self.data["acrcloud"]["access_key"]

    @property
    def acr_access_secret(self) -> str:
        return self.data["acrcloud"]["access_secret"]

    @property
    def supported_formats(self) -> list:
        return self.data["recognition"]["supported_formats"]

    @property
    def max_file_size(self) -> int:
        return self.data["recognition"]["max_file_size"]


class ACRMusicRecognizer:
    """ACRCloud music recognition service."""

    def __init__(self, config: Config):
        self.config = config

    def recognize(self, file_path: str) -> dict:
        """Recognize music from audio/video file."""
        try:
            result = recognize(
                host=self.config.acr_host,
                access_key=self.config.acr_access_key,
                access_secret=self.config.acr_access_secret,
                audio_file_path=file_path,
            )
            return result
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            return {"status": {"msg": "Error", "code": 500}, "error": str(e)}

    def format_result(self, result: dict) -> str:
        """Format recognition result for display."""
        if result.get("status", {}).get("code") != 0:
            error_msg = result.get("status", {}).get("msg", "Unknown error")
            return f"❌ Recognition failed: {error_msg}"

        metadata = result.get("metadata", {})
        if not metadata:
            return "❌ No music found in the file."

        music_info = metadata.get("music", [])
        if not music_info:
            return "❌ No music found in the file."

        track = music_info[0]
        output = []

        if track.get("title"):
            output.append(f"🎵 *{track['title']}*")

        if track.get("artists"):
            artists = ", ".join(a.get("name", "") for a in track["artists"])
            if artists:
                output.append(f"👤 *Artist:* {artists}")

        if track.get("album"):
            output.append(f"💿 *Album:* {track['album'].get('name', 'Unknown')}")

        if track.get("release_date"):
            output.append(f"📅 *Released:* {track['release_date']}")

        if metadata.get("genres"):
            genres = ", ".join(g.get("name", "") for g in metadata["genres"])
            if genres:
                output.append(f"🏷️ *Genre:* {genres}")

        return "\n".join(output) if output else "❌ Could not identify the track."

    def extract_audio_from_video(self, video_path: str) -> str:
        """Extract audio from video file using ffmpeg."""
        audio_path = video_path + ".audio.ogg"

        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", video_path,
                    "-vn",
                    "-acodec", "libopus",
                    "-b:a", "128k",
                    "-ar", "44100",
                    audio_path
                ],
                check=True,
                capture_output=True
            )
            return audio_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            raise RuntimeError("Failed to extract audio from video")

    def trim_audio_to_10s_middle(self, audio_path: str) -> str:
        """Trim audio to 10 seconds from the middle. If shorter, return as-is."""
        trimmed_path = audio_path + ".trimmed.ogg"

        try:
            # Get audio duration
            duration_result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    audio_path
                ],
                capture_output=True,
                text=True
            )
            duration = float(duration_result.stdout.strip())

            if duration <= 10:
                # Audio is already 10 seconds or less, just copy it
                subprocess.run(
                    ["ffmpeg", "-y", "-i", audio_path, "-c", "copy", trimmed_path],
                    check=True,
                    capture_output=True
                )
            else:
                # Calculate start time for 10-second segment from middle
                start_time = (duration - 10) / 2
                subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-ss", str(start_time),
                        "-i", audio_path,
                        "-t", "10",
                        "-c", "copy",
                        trimmed_path
                    ],
                    check=True,
                    capture_output=True
                )

            return trimmed_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg trim error: {e.stderr.decode() if e.stderr else str(e)}")
            # Return original if trimming fails
            return audio_path


class MusicBot:
    """Telegram music recognition bot."""

    def __init__(self, config: Config):
        self.config = config
        self.recognizer = ACRMusicRecognizer(config)

    def is_group_chat(self, update: Update) -> bool:
        """Check if the message is from a group/supergroup."""
        chat = update.effective_chat
        return chat and chat.type in ["group", "supergroup"]

    def starts_with_code_word(self, text: str) -> bool:
        """Check if message text starts with code word."""
        if not text:
            return False
        pattern = rf"^{re.escape(self.config.code_word)}\b"
        return bool(re.match(pattern, text.strip(), re.IGNORECASE))

    def get_file_from_message(self, message: Message):
        """Get file from message or its reply."""
        # Check direct attachments
        if message.audio:
            return message.audio, message.audio.file_name
        if message.voice:
            return message.voice, "voice.ogg"
        if message.video:
            return message.video, message.video.file_name
        if message.document:
            return message.document, message.document.file_name
        return None, None

    def get_file_info(self, message: Message):
        """Get file info from message or its replied-to message."""
        # First check current message
        file, file_name = self.get_file_from_message(message)
        if file:
            return file, file_name

        # Then check replied-to message
        if message.reply_to_message:
            file, file_name = self.get_file_from_message(message.reply_to_message)
            if file:
                return file, file_name

        return None, None

    def is_supported_file(self, file_name: str, mime_type: str) -> bool:
        """Check if file format is supported."""
        # Check by mime type
        if mime_type:
            supported_mime = ["audio/", "video/"]
            if any(mime_type.startswith(prefix) for prefix in supported_mime):
                return True

        # Check by extension
        if file_name:
            ext = Path(file_name).suffix.lower()
            if ext in self.config.supported_formats:
                return True

        return False

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages starting with code word."""
        if not self.is_group_chat(update):
            return

        message = update.message
        if not message:
            return

        text = message.text or message.caption or ""

        # Check if message starts with code word
        if not self.starts_with_code_word(text):
            return

        # Get file from message or reply
        file, file_name = self.get_file_info(message)
        if not file:
            await message.reply_text("❌ Please attach an audio/video file or reply to one with the code word.")
            return

        # Check mime type and format
        mime_type = getattr(file, "mime_type", "") or ""
        if not self.is_supported_file(file_name or "", mime_type):
            await message.reply_text(
                f"❌ Unsupported format.\nSupported: {', '.join(self.config.supported_formats)}"
            )
            return

        # Check file size
        file_size = getattr(file, "file_size", 0) or 0
        if file_size > self.config.max_file_size:
            await message.reply_text(
                f"❌ File too large. Maximum: {self.config.max_file_size // (1024 * 1024)}MB"
            )
            return

        # Send processing message
        processing_msg = await message.reply_text("🔍 Recognizing...")

        tmp_path = None
        audio_path = None
        try:
            # Determine extension
            ext = Path(file_name or "file").suffix if file_name else ".tmp"
            if not ext or ext == ".tmp":
                ext = ".ogg" if "ogg" in mime_type.lower() else ".tmp"

            # Download file
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                tmp_path = tmp_file.name

            bot = context.bot
            file_id = file.file_id
            new_file = await bot.get_file(file_id)
            await new_file.download_to_drive(tmp_path)

            # Extract audio from video if needed
            if mime_type.startswith("video/"):
                audio_path = self.recognizer.extract_audio_from_video(tmp_path)
            else:
                audio_path = tmp_path

            # Trim to 10 seconds from middle if needed
            trimmed_path = self.recognizer.trim_audio_to_10s_middle(audio_path)
            result = self.recognizer.recognize(trimmed_path)

            # Clean up trimmed file
            if trimmed_path != audio_path and os.path.exists(trimmed_path):
                try:
                    os.unlink(trimmed_path)
                except:
                    pass

            # Send result
            response_text = self.recognizer.format_result(result)
            await processing_msg.edit_text(response_text, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error: {e}")
            await processing_msg.edit_text(f"❌ Error: {str(e)}")
        finally:
            # Cleanup
            for path in [tmp_path, audio_path]:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except:
                        pass

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"Exception: {context.error}")

    def run(self):
        """Start the bot."""
        app = Application.builder().token(self.config.telegram_token).build()

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.add_error_handler(self.error_handler)

        logger.info("Starting bot...")
        app.run_polling()


def main():
    """Main entry point."""
    config_path = os.environ.get("CONFIG_PATH", "config.yaml")
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        print("Error: config.yaml not found.")
        return

    config = Config(config_path)
    bot = MusicBot(config)
    bot.run()


if __name__ == "__main__":
    main()
