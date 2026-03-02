"""
Utility functions for Video Automation Tool
"""
import os
import re
import hashlib
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def generate_task_id() -> str:
    """Generate unique task ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
    return f"task_{timestamp}_{random_hash}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200] + ext
    return filename.strip()


def format_file_size(size_bytes: int) -> str:
    """Format bytes to human readable"""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
        
    return f"{size:.2f} {units[unit_index]}"


def format_duration(seconds: float) -> str:
    """Format seconds to HH:MM:SS"""
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def estimate_output_size(input_size: int, quality: str = "high") -> int:
    """Estimate output file size based on quality"""
    multipliers = {
        "low": 0.5,
        "medium": 0.8,
        "high": 1.0,
        "ultra": 1.5
    }
    multiplier = multipliers.get(quality, 1.0)
    return int(input_size * multiplier)


def clean_temp_files(temp_dir: str, max_age_hours: int = 24):
    """Clean old temporary files"""
    temp_path = Path(temp_dir)
    if not temp_path.exists():
        return
        
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
    cleaned = 0
    
    for file_path in temp_path.rglob("*"):
        if file_path.is_file():
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff_time:
                    file_path.unlink()
                    cleaned += 1
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}: {e}")
                
    logger.info(f"Cleaned {cleaned} old files from {temp_dir}")


async def run_with_timeout(coro, timeout: float = 300):
    """Run coroutine with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise Exception(f"Operation timed out after {timeout} seconds")


def parse_video_url(url: str) -> Dict[str, Any]:
    """Parse and analyze video URL"""
    result = {
        'url': url,
        'type': 'unknown',
        'domain': '',
        'is_m3u8': False,
        'is_mp4': False,
        'is_embed': False,
    }
    
    # Check for m3u8
    if '.m3u8' in url.lower():
        result['is_m3u8'] = True
        result['type'] = 'm3u8'
        
    # Check for mp4
    if '.mp4' in url.lower():
        result['is_mp4'] = True
        result['type'] = 'mp4'
        
    # Check for embed
    if 'embed' in url.lower() or 'iframe' in url.lower():
        result['is_embed'] = True
        result['type'] = 'embed'
        
    # Extract domain
    from urllib.parse import urlparse
    parsed = urlparse(url)
    result['domain'] = parsed.netloc
    
    return result


def detect_bengali_text(text: str) -> bool:
    """Detect if text contains Bengali characters"""
    bengali_range = range(0x0980, 0x09FF + 1)
    return any(ord(char) in bengali_range for char in text)


def fix_bengali_spacing(text: str) -> str:
    """Fix spacing issues in Bengali text"""
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    # Fix punctuation spacing
    text = re.sub(r'\s+([।,;:!?])', r'\1', text)
    # Fix quote spacing
    text = re.sub(r'"\s+', '"', text)
    text = re.sub(r'\s+"', '"', text)
    return text.strip()


def merge_subtitle_entries(entries: List[Dict], min_gap_ms: int = 100) -> List[Dict]:
    """Merge subtitle entries that are too close together"""
    if not entries:
        return entries
        
    merged = [entries[0]]
    
    for entry in entries[1:]:
        last = merged[-1]
        gap = entry['start'] - last['end']
        
        if gap < min_gap_ms and last['text'] == entry['text']:
            # Merge entries
            last['end'] = entry['end']
        else:
            merged.append(entry)
            
    return merged


def validate_telegram_config(token: str, channel_id: str) -> Dict[str, Any]:
    """Validate Telegram configuration"""
    result = {'valid': False, 'errors': []}
    
    if not token:
        result['errors'].append("TELEGRAM_BOT_TOKEN is required")
    elif ':' not in token:
        result['errors'].append("Invalid bot token format")
        
    if not channel_id:
        result['errors'].append("TELEGRAM_CHANNEL_ID is required")
    elif not (channel_id.startswith('@') or channel_id.startswith('-100')):
        result['errors'].append("Channel ID should start with @ or -100")
        
    result['valid'] = len(result['errors']) == 0
    return result


def create_progress_tracker(total_steps: int):
    """Create progress tracker for multi-step operations"""
    current_step = 0
    step_weights = []
    
    def set_step_weights(weights: List[float]):
        nonlocal step_weights
        step_weights = weights
        
    def advance(message: str = ""):
        nonlocal current_step
        current_step += 1
        progress = int((current_step / total_steps) * 100)
        return {
            'step': current_step,
            'total': total_steps,
            'progress': progress,
            'message': message
        }
        
    def get_progress():
        if step_weights and current_step < len(step_weights):
            weighted_sum = sum(step_weights[:current_step])
            total_weight = sum(step_weights)
            progress = int((weighted_sum / total_weight) * 100)
        else:
            progress = int((current_step / total_steps) * 100)
        return progress
        
    return {
        'advance': advance,
        'get_progress': get_progress,
        'set_step_weights': set_step_weights
    }


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int = 10, period: float = 60.0):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        
    async def acquire(self):
        """Acquire rate limit slot"""
        now = datetime.now().timestamp()
        
        # Remove old calls
        self.calls = [c for c in self.calls if now - c < self.period]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                return await self.acquire()
                
        self.calls.append(now)
        
    def is_allowed(self) -> bool:
        """Check if call is allowed without waiting"""
        now = datetime.now().timestamp()
        self.calls = [c for c in self.calls if now - c < self.period]
        return len(self.calls) < self.max_calls


# Common user agents for scraping
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]


def get_random_user_agent() -> str:
    """Get random user agent"""
    import random
    return random.choice(USER_AGENTS)