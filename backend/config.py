"""
Configuration settings for Video Automation Tool
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Video Automation Tool"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Paths
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp/video-automation")
    DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "/tmp/video-automation/downloads")
    FONT_DIR: str = os.getenv("FONT_DIR", "./fonts")
    
    # Telegram Settings
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHANNEL_ID: str = os.getenv("TELEGRAM_CHANNEL_ID", "")
    
    # Redis (for Celery)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Video Processing
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2"))
    VIDEO_QUALITY: str = os.getenv("VIDEO_QUALITY", "720p")
    
    # Subtitle Settings
    SUBTITLE_FONT: str = os.getenv("SUBTITLE_FONT", "Noto Sans Bengali")
    SUBTITLE_FONT_SIZE: int = int(os.getenv("SUBTITLE_FONT_SIZE", "24"))
    SUBTITLE_COLOR: str = os.getenv("SUBTITLE_COLOR", "#FFFFFF")
    SUBTITLE_OUTLINE_COLOR: str = os.getenv("SUBTITLE_OUTLINE_COLOR", "#000000")
    SUBTITLE_OUTLINE_WIDTH: int = int(os.getenv("SUBTITLE_OUTLINE_WIDTH", "2"))
    
    class Config:
        env_file = ".env"

settings = Settings()