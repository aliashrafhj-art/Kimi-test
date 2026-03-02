"""
Video Downloader Module - Downloads M3U8 and MP4 with progress tracking
"""
import os
import asyncio
import aiohttp
import aiofiles
import m3u8
from typing import Callable, Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

class VideoDownloader:
    """Advanced video downloader with progress tracking"""
    
    def __init__(self, temp_dir: str = "/tmp/video-automation"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir = self.temp_dir / "downloads"
        self.downloads_dir.mkdir(exist_ok=True)
        self.segments_dir = self.temp_dir / "segments"
        self.segments_dir.mkdir(exist_ok=True)
        
    async def download_with_progress(
        self, 
        url: str, 
        output_path: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """Download file with progress tracking"""
        
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        if headers:
            default_headers.update(headers)
            
        try:
            async with aiohttp.ClientSession(headers=default_headers) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                        
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    async with aiofiles.open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress_callback and total_size > 0:
                                percentage = int((downloaded / total_size) * 100)
                                progress_callback(downloaded, total_size, f"Downloading: {percentage}%")
                                
            if progress_callback:
                progress_callback(downloaded, total_size, "Download complete")
                
            return output_path
            
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            raise
            
    async def download_m3u8(
        self, 
        m3u8_url: str, 
        output_filename: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        quality: str = "best"
    ) -> str:
        """Download M3U8 stream and convert to MP4"""
        
        logger.info(f"Starting M3U8 download: {m3u8_url}")
        
        if progress_callback:
            progress_callback(0, 100, "Fetching M3U8 playlist...")
            
        # Parse M3U8
        try:
            playlist = m3u8.load(m3u8_url)
        except Exception as e:
            logger.error(f"Failed to load M3U8: {str(e)}")
            raise
            
        # If master playlist, select best quality
        if playlist.is_variant:
            if progress_callback:
                progress_callback(5, 100, "Selecting best quality stream...")
                
            playlists = playlist.playlists
            if quality == "best":
                selected = max(playlists, key=lambda p: p.stream_info.bandwidth if p.stream_info.bandwidth else 0)
            elif quality == "worst":
                selected = min(playlists, key=lambda p: p.stream_info.bandwidth if p.stream_info.bandwidth else float('inf'))
            else:
                # Try to match resolution
                selected = playlists[0]
                for pl in playlists:
                    if pl.stream_info.resolution and quality in str(pl.stream_info.resolution):
                        selected = pl
                        break
                        
            stream_url = urljoin(m3u8_url, selected.uri)
            logger.info(f"Selected stream: {stream_url} (Bandwidth: {selected.stream_info.bandwidth})")
            
            # Load the selected stream
            playlist = m3u8.load(stream_url)
        else:
            stream_url = m3u8_url
            
        if not output_filename:
            output_filename = f"video_{asyncio.get_event_loop().time()}.mp4"
            
        output_path = self.downloads_dir / output_filename
        
        # Download segments
        segments = playlist.segments
        total_segments = len(segments)
        
        if total_segments == 0:
            raise Exception("No segments found in M3U8")
            
        logger.info(f"Downloading {total_segments} segments...")
        
        # Create segment download directory
        segment_dir = self.segments_dir / f"seg_{asyncio.get_event_loop().time()}"
        segment_dir.mkdir(exist_ok=True)
        
        # Download all segments
        downloaded_segments = []
        
        async with aiohttp.ClientSession() as session:
            for i, segment in enumerate(segments):
                segment_url = urljoin(stream_url, segment.uri)
                segment_file = segment_dir / f"segment_{i:05d}.ts"
                
                try:
                    async with session.get(segment_url) as response:
                        if response.status == 200:
                            async with aiofiles.open(segment_file, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    await f.write(chunk)
                            downloaded_segments.append(str(segment_file))
                            
                            progress = int(((i + 1) / total_segments) * 80)  # 80% for downloading
                            if progress_callback:
                                progress_callback(progress, 100, f"Downloading segments: {i+1}/{total_segments}")
                        else:
                            logger.warning(f"Failed to download segment {i}: HTTP {response.status}")
                            
                except Exception as e:
                    logger.error(f"Error downloading segment {i}: {str(e)}")
                    
        if not downloaded_segments:
            raise Exception("No segments were downloaded successfully")
            
        # Merge segments using FFmpeg
        if progress_callback:
            progress_callback(85, 100, "Merging segments...")
            
        await self._merge_segments_ffmpeg(downloaded_segments, str(output_path))
        
        # Cleanup segments
        if progress_callback:
            progress_callback(95, 100, "Cleaning up...")
            
        for seg_file in downloaded_segments:
            try:
                os.remove(seg_file)
            except:
                pass
        try:
            os.rmdir(segment_dir)
        except:
            pass
            
        if progress_callback:
            progress_callback(100, 100, "Download complete")
            
        logger.info(f"M3U8 download complete: {output_path}")
        return str(output_path)
        
    async def download_mp4(
        self, 
        mp4_url: str, 
        output_filename: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """Download direct MP4 file"""
        
        logger.info(f"Starting MP4 download: {mp4_url}")
        
        if not output_filename:
            parsed = urlparse(mp4_url)
            output_filename = os.path.basename(parsed.path) or f"video_{asyncio.get_event_loop().time()}.mp4"
            
        output_path = self.downloads_dir / output_filename
        
        await self.download_with_progress(
            mp4_url, 
            str(output_path), 
            progress_callback
        )
        
        logger.info(f"MP4 download complete: {output_path}")
        return str(output_path)
        
    async def _merge_segments_ffmpeg(self, segments: List[str], output_path: str):
        """Merge TS segments using FFmpeg"""
        
        # Create concat file list
        concat_file = self.temp_dir / f"concat_{asyncio.get_event_loop().time()}.txt"
        with open(concat_file, 'w') as f:
            for segment in segments:
                f.write(f"file '{segment}'\n")
                
        # Run FFmpeg
        cmd = [
            'ffmpeg',
            '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            output_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                raise Exception(f"FFmpeg failed with code {process.returncode}")
                
        finally:
            try:
                os.remove(concat_file)
            except:
                pass
                
    async def download_subtitle(
        self, 
        subtitle_url: str, 
        output_filename: Optional[str] = None
    ) -> str:
        """Download subtitle file"""
        
        if not output_filename:
            parsed = urlparse(subtitle_url)
            output_filename = os.path.basename(parsed.path) or f"subtitle_{asyncio.get_event_loop().time()}.vtt"
            
        output_path = self.downloads_dir / output_filename
        
        await self.download_with_progress(subtitle_url, str(output_path))
        
        logger.info(f"Subtitle download complete: {output_path}")
        return str(output_path)


# Standalone functions
async def download_video(url: str, url_type: str = "auto", **kwargs) -> str:
    """Quick download function"""
    downloader = VideoDownloader()
    
    if url_type == "m3u8" or url.endswith('.m3u8'):
        return await downloader.download_m3u8(url, **kwargs)
    elif url_type == "mp4" or url.endswith('.mp4'):
        return await downloader.download_mp4(url, **kwargs)
    else:
        # Auto-detect
        if '.m3u8' in url:
            return await downloader.download_m3u8(url, **kwargs)
        else:
            return await downloader.download_mp4(url, **kwargs)