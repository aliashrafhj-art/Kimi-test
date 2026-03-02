"""
Command Line Interface for Video Automation Tool
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Optional

from config import settings
from scraper import scrape_video_sources
from downloader import download_video
from subtitle_processor import process_bengali_subtitle
from video_encoder import burn_subtitles_to_video
from telegram_uploader import upload_to_telegram


def print_banner():
    """Print CLI banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           🎬 VIDEO AUTOMATION TOOL v1.0.0                    ║
║     Automated Video Processing with Bengali Subtitles       ║
╚══════════════════════════════════════════════════════════════╝
    """)


async def extract_command(url: str):
    """Extract video sources from URL"""
    print(f"🔍 Extracting sources from: {url}\n")
    
    result = await scrape_video_sources(url)
    
    print(f"\n✅ Extraction complete!\n")
    
    if result.get('iframes'):
        print(f"📺 Iframes found: {len(result['iframes'])}")
        for i, iframe in enumerate(result['iframes'][:3], 1):
            print(f"   {i}. {iframe['url'][:80]}...")
            
    if result.get('m3u8_links'):
        print(f"\n🎬 M3U8 Streams: {len(result['m3u8_links'])}")
        for i, link in enumerate(result['m3u8_links'][:5], 1):
            print(f"   {i}. [{link.get('quality', 'unknown')}] {link['url'][:80]}...")
            
    if result.get('mp4_links'):
        print(f"\n📁 MP4 Videos: {len(result['mp4_links'])}")
        for i, link in enumerate(result['mp4_links'][:5], 1):
            print(f"   {i}. [{link.get('quality', 'unknown')}] {link['url'][:80]}...")
            
    if result.get('subtitles'):
        print(f"\n📝 Subtitles: {len(result['subtitles'])}")
        for i, sub in enumerate(result['subtitles'][:5], 1):
            print(f"   {i}. [{sub.get('language', 'unknown')}] {sub['url'][:80]}...")


async def download_command(url: str, output: Optional[str] = None, url_type: str = "auto"):
    """Download video"""
    print(f"⬇️ Downloading: {url}\n")
    
    def progress(current, total, message):
        if total > 0:
            pct = int((current / total) * 100)
            bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
            print(f"\r[{bar}] {pct}% {message}", end='', flush=True)
        else:
            print(f"\r{message}", end='', flush=True)
            
    try:
        file_path = await download_video(url, url_type, filename=output, progress_callback=progress)
        print(f"\n\n✅ Download complete: {file_path}")
        return file_path
    except Exception as e:
        print(f"\n\n❌ Download failed: {e}")
        return None


async def subtitle_command(input_path: str, output: Optional[str] = None):
    """Process subtitle"""
    print(f"📝 Processing subtitle: {input_path}\n")
    
    try:
        output_path = process_bengali_subtitle(input_path, output)
        print(f"✅ Subtitle processed: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return None


async def burn_command(video: str, subtitle: str, output: str, style: str = "netflix"):
    """Burn subtitles into video"""
    print(f"🔥 Burning subtitles...")
    print(f"   Video: {video}")
    print(f"   Subtitle: {subtitle}")
    print(f"   Output: {output}")
    print(f"   Style: {style}\n")
    
    def progress(current, total, message):
        if total > 0:
            pct = int((current / total) * 100)
            bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
            print(f"\r[{bar}] {pct}% {message}", end='', flush=True)
            
    try:
        output_path = await burn_subtitles_to_video(
            video, subtitle, output,
            subtitle_style=style,
            progress_callback=progress
        )
        print(f"\n\n✅ Burn complete: {output_path}")
        return output_path
    except Exception as e:
        print(f"\n\n❌ Burn failed: {e}")
        return None


async def upload_command(video: str, caption: Optional[str] = None):
    """Upload to Telegram"""
    print(f"📤 Uploading to Telegram: {video}\n")
    
    if not settings.TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not configured")
        return
        
    def progress(current, total, message):
        if total > 0:
            pct = int((current / total) * 100)
            bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
            print(f"\r[{bar}] {pct}% {message}", end='', flush=True)
            
    try:
        result = await upload_to_telegram(
            video,
            settings.TELEGRAM_BOT_TOKEN,
            settings.TELEGRAM_CHANNEL_ID,
            caption=caption,
            progress_callback=progress
        )
        print(f"\n\n✅ Upload complete!")
        print(f"   Message ID: {result.get('message_id')}")
        print(f"   File ID: {result.get('file_id')}")
    except Exception as e:
        print(f"\n\n❌ Upload failed: {e}")


async def full_command(
    url: str,
    bangla_sub: Optional[str] = None,
    output: Optional[str] = None,
    upload: bool = True
):
    """Full automation"""
    print(f"🚀 Starting full automation...")
    print(f"   URL: {url}")
    if bangla_sub:
        print(f"   Bangla Subtitle: {bangla_sub}")
    print()
    
    # Step 1: Extract
    print("=" * 60)
    print("STEP 1/5: Extracting video sources...")
    print("=" * 60)
    sources = await scrape_video_sources(url)
    
    m3u8 = sources.get('m3u8_links', [])
    mp4 = sources.get('mp4_links', [])
    subs = sources.get('subtitles', [])
    
    print(f"✅ Found {len(m3u8)} M3U8, {len(mp4)} MP4, {len(subs)} subtitles\n")
    
    # Step 2: Download
    print("=" * 60)
    print("STEP 2/5: Downloading video...")
    print("=" * 60)
    
    video_url = None
    if m3u8:
        video_url = m3u8[0]['url']
    elif mp4:
        video_url = mp4[0]['url']
    else:
        print("❌ No video sources found")
        return
        
    video_path = await download_command(video_url, None, "auto")
    if not video_path:
        return
    print()
    
    # Step 3: Process subtitle
    print("=" * 60)
    print("STEP 3/5: Processing subtitle...")
    print("=" * 60)
    
    if bangla_sub and os.path.exists(bangla_sub):
        sub_path = await subtitle_command(bangla_sub)
    elif subs:
        from downloader import VideoDownloader
        downloader = VideoDownloader()
        sub_url = subs[0]['url']
        sub_path = await downloader.download_subtitle(sub_url)
        sub_path = await subtitle_command(sub_path)
    else:
        print("❌ No subtitles available")
        return
        
    if not sub_path:
        return
    print()
    
    # Step 4: Burn
    print("=" * 60)
    print("STEP 4/5: Burning subtitles...")
    print("=" * 60)
    
    if not output:
        output = f"final_{int(asyncio.get_event_loop().time())}.mp4"
    output_path = os.path.join(settings.DOWNLOAD_DIR, output)
    
    final_video = await burn_command(video_path, sub_path, output_path)
    if not final_video:
        return
    print()
    
    # Step 5: Upload
    if upload and settings.TELEGRAM_BOT_TOKEN:
        print("=" * 60)
        print("STEP 5/5: Uploading to Telegram...")
        print("=" * 60)
        await upload_command(final_video)
        print()
        
    print("=" * 60)
    print("🎉 FULL AUTOMATION COMPLETE!")
    print(f"📁 Output: {final_video}")
    print("=" * 60)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Video Automation Tool CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract sources
  python cli.py extract "https://example.com/episode-1"
  
  # Download video
  python cli.py download "https://example.com/video.m3u8" -o episode.mp4
  
  # Process subtitle
  python cli.py subtitle subtitle.srt -o subtitle.ass
  
  # Burn subtitles
  python cli.py burn video.mp4 subtitle.ass -o output.mp4 --style netflix
  
  # Upload to Telegram
  python cli.py upload output.mp4 -c "My video caption"
  
  # Full automation
  python cli.py full "https://example.com/episode-1" -b bangla.srt -o final.mp4
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract video sources')
    extract_parser.add_argument('url', help='Episode URL')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download video')
    download_parser.add_argument('url', help='Video URL')
    download_parser.add_argument('-o', '--output', help='Output filename')
    download_parser.add_argument('-t', '--type', default='auto', choices=['auto', 'm3u8', 'mp4'])
    
    # Subtitle command
    subtitle_parser = subparsers.add_parser('subtitle', help='Process subtitle')
    subtitle_parser.add_argument('input', help='Input subtitle file')
    subtitle_parser.add_argument('-o', '--output', help='Output file')
    
    # Burn command
    burn_parser = subparsers.add_parser('burn', help='Burn subtitles')
    burn_parser.add_argument('video', help='Video file')
    burn_parser.add_argument('subtitle', help='ASS subtitle file')
    burn_parser.add_argument('-o', '--output', required=True, help='Output file')
    burn_parser.add_argument('-s', '--style', default='netflix', choices=['netflix', 'minimal', 'classic'])
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload to Telegram')
    upload_parser.add_argument('video', help='Video file')
    upload_parser.add_argument('-c', '--caption', help='Caption text')
    
    # Full automation
    full_parser = subparsers.add_parser('full', help='Full automation')
    full_parser.add_argument('url', help='Episode URL')
    full_parser.add_argument('-b', '--bangla-sub', help='Bangla subtitle file')
    full_parser.add_argument('-o', '--output', help='Output filename')
    full_parser.add_argument('--no-upload', action='store_true', help='Skip Telegram upload')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    print_banner()
    
    if args.command == 'extract':
        asyncio.run(extract_command(args.url))
    elif args.command == 'download':
        asyncio.run(download_command(args.url, args.output, args.type))
    elif args.command == 'subtitle':
        asyncio.run(subtitle_command(args.input, args.output))
    elif args.command == 'burn':
        asyncio.run(burn_command(args.video, args.subtitle, args.output, args.style))
    elif args.command == 'upload':
        asyncio.run(upload_command(args.video, args.caption))
    elif args.command == 'full':
        asyncio.run(full_command(args.url, args.bangla_sub, args.output, not args.no_upload))


if __name__ == '__main__':
    main()
