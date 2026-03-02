"""
Video Encoder Module - Burns Bengali subtitles into video with Netflix style
Uses FFmpeg with proper font rendering for Bengali text
"""
import os
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import logging
import shutil

logger = logging.getLogger(__name__)

class VideoEncoder:
    """
    Video encoder that burns subtitles with proper Bengali font support
    """
    
    def __init__(self, font_dir: str = "./fonts"):
        self.font_dir = Path(font_dir)
        self.font_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_path = self._find_ffmpeg()
        self.ffprobe_path = self._find_ffprobe()
        
    def _find_ffmpeg(self) -> str:
        """Find FFmpeg executable"""
        ffmpeg = shutil.which('ffmpeg')
        if ffmpeg:
            return ffmpeg
        # Common paths
        for path in ['/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/opt/homebrew/bin/ffmpeg']:
            if os.path.exists(path):
                return path
        raise Exception("FFmpeg not found. Please install FFmpeg.")
        
    def _find_ffprobe(self) -> str:
        """Find FFprobe executable"""
        ffprobe = shutil.which('ffprobe')
        if ffprobe:
            return ffprobe
        for path in ['/usr/bin/ffprobe', '/usr/local/bin/ffprobe', '/opt/homebrew/bin/ffprobe']:
            if os.path.exists(path):
                return path
        raise Exception("FFprobe not found. Please install FFmpeg.")
        
    async def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video information using FFprobe"""
        cmd = [
            self.ffprobe_path,
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,duration,bit_rate',
            '-show_entries', 'format=duration,size,bit_rate',
            '-of', 'json',
            video_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                import json
                data = json.loads(stdout.decode())
                return {
                    'width': data.get('streams', [{}])[0].get('width', 0),
                    'height': data.get('streams', [{}])[0].get('height', 0),
                    'duration': float(data.get('format', {}).get('duration', 0)),
                    'size': int(data.get('format', {}).get('size', 0)),
                    'bitrate': int(data.get('format', {}).get('bit_rate', 0)),
                }
            else:
                logger.error(f"FFprobe error: {stderr.decode()}")
                return {}
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {}
            
    async def burn_subtitles(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str,
        font_name: str = "Noto Sans Bengali",
        font_size: int = 28,
        subtitle_style: str = "netflix",
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        quality: str = "high"
    ) -> str:
        """
        Burn subtitles into video with Netflix-style Bengali rendering
        
        Args:
            video_path: Input video file path
            subtitle_path: ASS subtitle file path
            output_path: Output video file path
            font_name: Bengali font name
            font_size: Subtitle font size
            subtitle_style: 'netflix', 'minimal', or 'classic'
            progress_callback: Progress callback function
            quality: 'low', 'medium', 'high', or 'ultra'
        """
        
        logger.info(f"Starting subtitle burn: {video_path} + {subtitle_path} -> {output_path}")
        
        if progress_callback:
            progress_callback(0, 100, "Preparing video encoding...")
            
        # Verify files exist
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not os.path.exists(subtitle_path):
            raise FileNotFoundError(f"Subtitle file not found: {subtitle_path}")
            
        # Get video info
        video_info = await self.get_video_info(video_path)
        duration = video_info.get('duration', 0)
        
        # Build FFmpeg command based on style
        vf_filters = self._build_video_filters(subtitle_path, font_name, font_size, subtitle_style)
        
        # Quality presets
        quality_presets = {
            'low': {
                'video_codec': 'libx264',
                'preset': 'ultrafast',
                'crf': '28',
                'audio_codec': 'aac',
                'audio_bitrate': '96k',
            },
            'medium': {
                'video_codec': 'libx264',
                'preset': 'fast',
                'crf': '23',
                'audio_codec': 'aac',
                'audio_bitrate': '128k',
            },
            'high': {
                'video_codec': 'libx264',
                'preset': 'medium',
                'crf': '18',
                'audio_codec': 'aac',
                'audio_bitrate': '192k',
            },
            'ultra': {
                'video_codec': 'libx265',
                'preset': 'slow',
                'crf': '16',
                'audio_codec': 'aac',
                'audio_bitrate': '256k',
            }
        }
        
        preset = quality_presets.get(quality, quality_presets['high'])
        
        # Build command
        cmd = [
            self.ffmpeg_path,
            '-y',  # Overwrite output
            '-i', video_path,
            '-vf', vf_filters,
            '-c:v', preset['video_codec'],
            '-preset', preset['preset'],
            '-crf', preset['crf'],
            '-c:a', preset['audio_codec'],
            '-b:a', preset['audio_bitrate'],
            '-movflags', '+faststart',  # Web optimization
            '-pix_fmt', 'yuv420p',  # Compatibility
        ]
        
        # Add progress tracking
        cmd.extend(['-progress', 'pipe:1', '-nostats'])
        
        cmd.append(output_path)
        
        if progress_callback:
            progress_callback(5, 100, "Starting FFmpeg encoding...")
            
        logger.info(f"FFmpeg command: {' '.join(cmd)}")
        
        # Run FFmpeg with progress tracking
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Parse progress
            last_progress = 5
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                    
                line = line.decode('utf-8', errors='ignore').strip()
                
                # Parse progress
                if line.startswith('out_time_ms='):
                    time_ms = int(line.split('=')[1])
                    if duration > 0:
                        progress = min(95, 5 + int((time_ms / 1000000 / duration) * 90))
                        if progress > last_progress:
                            last_progress = progress
                            if progress_callback:
                                progress_callback(progress, 100, f"Encoding video: {progress}%")
                                
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')[-500:]
                logger.error(f"FFmpeg encoding failed: {error_msg}")
                raise Exception(f"FFmpeg encoding failed: {error_msg}")
                
            if progress_callback:
                progress_callback(100, 100, "Encoding complete")
                
            logger.info(f"Subtitle burn complete: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error during encoding: {e}")
            raise
            
    def _build_video_filters(
        self, 
        subtitle_path: str, 
        font_name: str, 
        font_size: int,
        style: str
    ) -> str:
        """Build FFmpeg video filter for subtitles"""
        
        # Escape subtitle path for FFmpeg
        escaped_subtitle = subtitle_path.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'")
        
        # Font directory for subtitle rendering
        font_dir = str(self.font_dir).replace('\\', '/')
        
        if style == 'netflix':
            # Netflix-style: Bold, with outline, positioned at bottom
            vf = (
                f"subtitles={escaped_subtitle}:"
                f"fontsdir={font_dir}:"
                f"force_style='"
                f"FontName={font_name},"
                f"FontSize={font_size},"
                f"PrimaryColour=&H00FFFFFF,""
                f"SecondaryColour=&H000000FF,"
                f"OutlineColour=&H00000000,"
                f"BackColour=&H80000000,"
                f"Bold=1,"
                f"Italic=0,"
                f"Underline=0,"
                f"StrikeOut=0,"
                f"ScaleX=100,"
                f"ScaleY=100,"
                f"Spacing=0,"
                f"Angle=0,"
                f"BorderStyle=1,"
                f"Outline=2.5,"
                f"Shadow=0.5,"
                f"Alignment=2,"
                f"MarginL=60,"
                f"MarginR=60,"
                f"MarginV=60,"
                f"Encoding=0'"
            )
        elif style == 'minimal':
            # Minimal style: Clean, simple
            vf = (
                f"subtitles={escaped_subtitle}:"
                f"fontsdir={font_dir}:"
                f"force_style='"
                f"FontName={font_name},"
                f"FontSize={font_size},"
                f"PrimaryColour=&H00FFFFFF,"
                f"OutlineColour=&H00000000,"
                f"Outline=1,"
                f"Shadow=0,"
                f"Alignment=2,"
                f"MarginV=40'"
            )
        elif style == 'classic':
            # Classic yellow subtitles
            vf = (
                f"subtitles={escaped_subtitle}:"
                f"fontsdir={font_dir}:"
                f"force_style='"
                f"FontName={font_name},"
                f"FontSize={font_size},"
                f"PrimaryColour=&H00FFFF00,""
                f"OutlineColour=&H00000000,"
                f"Outline=2,"
                f"Shadow=1,"
                f"Alignment=2,"
                f"MarginV=50'"
            )
        else:
            # Default
            vf = f"subtitles={escaped_subtitle}:fontsdir={font_dir}"
            
        return vf
        
    async def add_burned_subtitle_simple(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """
        Simple subtitle burning with default settings
        """
        return await self.burn_subtitles(
            video_path=video_path,
            subtitle_path=subtitle_path,
            output_path=output_path,
            subtitle_style="netflix",
            progress_callback=progress_callback,
            quality="high"
        )
        
    async def convert_to_mp4(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """Convert any video to MP4 format"""
        
        cmd = [
            self.ffmpeg_path,
            '-y',
            '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-pix_fmt', 'yuv420p',
            '-progress', 'pipe:1',
            '-nostats',
            output_path
        ]
        
        logger.info(f"Converting to MP4: {input_path} -> {output_path}")
        
        if progress_callback:
            progress_callback(0, 100, "Starting conversion...")
            
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Simple progress (no duration parsing)
        if progress_callback:
            progress_callback(50, 100, "Converting...")
            
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"Conversion failed: {stderr.decode()[-500:]}")
            
        if progress_callback:
            progress_callback(100, 100, "Conversion complete")
            
        return output_path


# Standalone function
async def burn_subtitles_to_video(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    **kwargs
) -> str:
    """Quick function to burn subtitles"""
    encoder = VideoEncoder()
    return await encoder.burn_subtitles(video_path, subtitle_path, output_path, **kwargs)