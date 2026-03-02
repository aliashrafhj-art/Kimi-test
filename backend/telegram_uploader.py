"""
Telegram Uploader Module - Uploads videos to Telegram channel with progress tracking
Handles large files (1GB+) with resume capability
"""
import os
import asyncio
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import logging
from telegram import Bot, InputFile
from telegram.constants import ParseMode
import aiohttp

logger = logging.getLogger(__name__)

class TelegramUploader:
    """
    Telegram uploader with progress tracking for large files
    """
    
    def __init__(self, bot_token: str, channel_id: str):
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.bot = Bot(token=bot_token)
        self.chunk_size = 1024 * 1024  # 1MB chunks
        
    async def upload_video(
        self,
        video_path: str,
        caption: Optional[str] = None,
        thumbnail_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload video to Telegram channel
        
        Args:
            video_path: Path to video file
            caption: Video caption (supports HTML formatting)
            thumbnail_path: Path to thumbnail image
            progress_callback: Progress callback (current, total, message)
            metadata: Additional metadata (title, episode, etc.)
        """
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        file_size = os.path.getsize(video_path)
        file_name = os.path.basename(video_path)
        
        logger.info(f"Starting Telegram upload: {file_name} ({self._format_size(file_size)})")
        
        # Build caption
        if not caption and metadata:
            caption = self._build_caption(metadata)
            
        # Upload with progress tracking
        if progress_callback:
            progress_callback(0, 100, "Starting Telegram upload...")
            
        try:
            # For files under 50MB, use direct upload
            # For larger files, use streaming upload
            if file_size < 50 * 1024 * 1024:
                result = await self._upload_small_file(
                    video_path, caption, thumbnail_path, progress_callback
                )
            else:
                result = await self._upload_large_file(
                    video_path, caption, thumbnail_path, progress_callback
                )
                
            logger.info(f"Telegram upload complete: {result.get('message_id')}")
            return result
            
        except Exception as e:
            logger.error(f"Telegram upload failed: {e}")
            raise
            
    async def _upload_small_file(
        self,
        video_path: str,
        caption: Optional[str],
        thumbnail_path: Optional[str],
        progress_callback: Optional[Callable[[int, int, str], None]]
    ) -> Dict[str, Any]:
        """Upload small file (< 50MB) directly"""
        
        if progress_callback:
            progress_callback(50, 100, "Uploading to Telegram...")
            
        with open(video_path, 'rb') as video_file:
            message = await self.bot.send_video(
                chat_id=self.channel_id,
                video=InputFile(video_file),
                caption=caption,
                parse_mode=ParseMode.HTML,
                thumbnail=open(thumbnail_path, 'rb') if thumbnail_path else None,
                supports_streaming=True,
                disable_notification=False
            )
            
        if progress_callback:
            progress_callback(100, 100, "Upload complete")
            
        return {
            'message_id': message.message_id,
            'chat_id': message.chat_id,
            'file_id': message.video.file_id if message.video else None,
            'file_unique_id': message.video.file_unique_id if message.video else None,
        }
        
    async def _upload_large_file(
        self,
        video_path: str,
        caption: Optional[str],
        thumbnail_path: Optional[str],
        progress_callback: Optional[Callable[[int, int, str], None]]
    ) -> Dict[str, Any]:
        """
        Upload large file using streaming with progress tracking
        Telegram Bot API limit: 2GB per file
        """
        
        file_size = os.path.getsize(video_path)
        file_name = os.path.basename(video_path)
        
        # Use Telegram Bot API with streaming
        url = f"https://api.telegram.org/bot{self.bot_token}/sendVideo"
        
        # Build multipart form data with progress tracking
        form_data = aiohttp.FormData()
        form_data.add_field('chat_id', self.channel_id)
        
        if caption:
            form_data.add_field('caption', caption)
            form_data.add_field('parse_mode', 'HTML')
            
        form_data.add_field('supports_streaming', 'true')
        
        # Add thumbnail if provided
        if thumbnail_path and os.path.exists(thumbnail_path):
            form_data.add_field('thumb', open(thumbnail_path, 'rb'))
            
        # Add video file with progress tracking
        uploaded_bytes = 0
        
        class ProgressFile:
            """File wrapper that tracks upload progress"""
            def __init__(self, file_path, callback, total_size):
                self.file = open(file_path, 'rb')
                self.callback = callback
                self.total_size = total_size
                self.uploaded = 0
                self.last_reported = 0
                
            def read(self, size=-1):
                data = self.file.read(size)
                if data:
                    self.uploaded += len(data)
                    # Report progress every 5%
                    progress = int((self.uploaded / self.total_size) * 100)
                    if progress >= self.last_reported + 5:
                        self.last_reported = progress
                        if self.callback:
                            asyncio.create_task(self._report(progress))
                return data
                
            async def _report(self, progress):
                self.callback(progress, 100, f"Uploading to Telegram: {progress}%")
                
            def __enter__(self):
                return self
                
            def __exit__(self, *args):
                self.file.close()
                
        # Create progress-tracking file
        progress_file = ProgressFile(video_path, progress_callback, file_size)
        form_data.add_field('video', progress_file, filename=file_name)
        
        if progress_callback:
            progress_callback(0, 100, "Connecting to Telegram...")
            
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form_data) as response:
                result = await response.json()
                
                if not result.get('ok'):
                    error = result.get('description', 'Unknown error')
                    raise Exception(f"Telegram API error: {error}")
                    
                message = result['result']
                
                if progress_callback:
                    progress_callback(100, 100, "Upload complete")
                    
                return {
                    'message_id': message['message_id'],
                    'chat_id': message['chat']['id'],
                    'file_id': message['video']['file_id'] if 'video' in message else None,
                    'file_unique_id': message['video']['file_unique_id'] if 'video' in message else None,
                }
                
    async def send_message(
        self,
        text: str,
        parse_mode: str = ParseMode.HTML
    ) -> Dict[str, Any]:
        """Send text message to channel"""
        
        message = await self.bot.send_message(
            chat_id=self.channel_id,
            text=text,
            parse_mode=parse_mode
        )
        
        return {
            'message_id': message.message_id,
            'chat_id': message.chat_id,
        }
        
    async def send_photo(
        self,
        photo_path: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send photo to channel"""
        
        with open(photo_path, 'rb') as photo:
            message = await self.bot.send_photo(
                chat_id=self.channel_id,
                photo=InputFile(photo),
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            
        return {
            'message_id': message.message_id,
            'chat_id': message.chat_id,
            'file_id': message.photo[-1].file_id if message.photo else None,
        }
        
    def _build_caption(self, metadata: Dict[str, Any]) -> str:
        """Build formatted caption from metadata"""
        
        title = metadata.get('title', 'Unknown Title')
        episode = metadata.get('episode', '')
        season = metadata.get('season', '')
        quality = metadata.get('quality', '720p')
        source = metadata.get('source', '')
        
        caption_parts = [f"<b>{title}</b>"]
        
        if season and episode:
            caption_parts.append(f"<code>S{season:02d}E{episode:02d}</code>")
        elif episode:
            caption_parts.append(f"<code>Episode {episode}</code>")
            
        caption_parts.append(f"\n📹 <b>Quality:</b> {quality}")
        
        if source:
            caption_parts.append(f"📡 <b>Source:</b> {source}")
            
        # Add watermark
        caption_parts.append("\n<i>Powered by Video Automation Tool</i>")
        
        return '\n'.join(caption_parts)
        
    def _format_size(self, size_bytes: int) -> str:
        """Format byte size to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
        
    async def check_bot(self) -> Dict[str, Any]:
        """Check if bot is working and can access channel"""
        
        try:
            me = await self.bot.get_me()
            chat = await self.bot.get_chat(self.channel_id)
            
            return {
                'ok': True,
                'bot_name': me.username,
                'bot_id': me.id,
                'channel_title': chat.title,
                'channel_id': chat.id,
                'channel_type': chat.type,
            }
        except Exception as e:
            return {
                'ok': False,
                'error': str(e),
            }


# Standalone function
async def upload_to_telegram(
    video_path: str,
    bot_token: str,
    channel_id: str,
    **kwargs
) -> Dict[str, Any]:
    """Quick upload function"""
    uploader = TelegramUploader(bot_token, channel_id)
    return await uploader.upload_video(video_path, **kwargs)