"""
Web Scraper Module - Extracts video sources and subtitles from streaming sites
"""
import re
import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)

class VideoScraper:
    """Advanced scraper for extracting video sources from streaming sites"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=30))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def fetch_page(self, url: str) -> str:
        """Fetch page content with retry logic"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"Failed to fetch {url}: Status {response.status}")
                    return ""
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return ""
            
    def extract_iframes(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """Extract all iframe sources from HTML"""
        soup = BeautifulSoup(html, 'lxml')
        iframes = []
        
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if src:
                full_url = urljoin(base_url, src)
                iframes.append({
                    'url': full_url,
                    'width': iframe.get('width', ''),
                    'height': iframe.get('height', ''),
                    'id': iframe.get('id', ''),
                    'class': iframe.get('class', [''])[0] if iframe.get('class') else ''
                })
                
        logger.info(f"Found {len(iframes)} iframes")
        return iframes
        
    def extract_m3u8_links(self, html: str, base_url: str) -> List[Dict[str, Any]]:
        """Extract M3U8/HLS stream links from HTML and scripts"""
        m3u8_links = []
        
        # Pattern 1: Direct m3u8 URLs in HTML
        patterns = [
            r'https?://[^\s"\'<>]+\.m3u8(?:\?[^\s"\'<>]*)?',
            r'["\']([^"\']*master[^"\']*\.m3u8[^"\']*)["\']',
            r'["\']([^"\']*playlist[^"\']*\.m3u8[^"\']*)["\']',
            r'["\']([^"\']*index[^"\']*\.m3u8[^"\']*)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if match.startswith('http'):
                    m3u8_links.append({
                        'url': match,
                        'type': 'direct',
                        'quality': self._detect_quality(match)
                    })
                    
        # Pattern 2: JSON encoded sources
        json_patterns = [
            r'sources\s*:\s*(\[[^\]]+\])',
            r'"sources"\s*:\s*(\[[^\]]+\])',
            r'videoSrc\s*=\s*(\[[^\]]+\])',
            r'playlist\s*:\s*(\[[^\]]+\])',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                try:
                    sources = json.loads(match)
                    if isinstance(sources, list):
                        for source in sources:
                            if isinstance(source, dict):
                                src = source.get('file', source.get('src', ''))
                                if src and '.m3u8' in src:
                                    full_url = urljoin(base_url, src)
                                    m3u8_links.append({
                                        'url': full_url,
                                        'type': 'json_source',
                                        'quality': source.get('label', self._detect_quality(src)),
                                        'default': source.get('default', False)
                                    })
                except json.JSONDecodeError:
                    continue
                    
        # Pattern 3: JavaScript variables
        js_patterns = [
            r'var\s+source\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'var\s+videoUrl\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'var\s+streamUrl\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                full_url = urljoin(base_url, match)
                m3u8_links.append({
                    'url': full_url,
                    'type': 'js_variable',
                    'quality': self._detect_quality(match)
                })
                
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in m3u8_links:
            if link['url'] not in seen:
                seen.add(link['url'])
                unique_links.append(link)
                
        logger.info(f"Found {len(unique_links)} M3U8 links")
        return unique_links
        
    def extract_mp4_links(self, html: str, base_url: str) -> List[Dict[str, Any]]:
        """Extract direct MP4 video links"""
        mp4_links = []
        
        patterns = [
            r'https?://[^\s"\'<>]+\.mp4(?:\?[^\s"\'<>]*)?',
            r'["\']([^"\']*video[^"\']*\.mp4[^"\']*)["\']',
            r'<source[^>]+src=["\']([^"\']+\.mp4[^"\']*)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if match.startswith('http'):
                    mp4_links.append({
                        'url': match,
                        'type': 'direct',
                        'quality': self._detect_quality(match)
                    })
                    
        # Check for video tags
        soup = BeautifulSoup(html, 'lxml')
        for video in soup.find_all('video'):
            src = video.get('src', '')
            if src and src.endswith('.mp4'):
                full_url = urljoin(base_url, src)
                mp4_links.append({
                    'url': full_url,
                    'type': 'video_tag',
                    'quality': 'unknown'
                })
                
            # Check source tags inside video
            for source in video.find_all('source'):
                src = source.get('src', '')
                if src and src.endswith('.mp4'):
                    full_url = urljoin(base_url, src)
                    mp4_links.append({
                        'url': full_url,
                        'type': 'source_tag',
                        'quality': source.get('label', source.get('res', 'unknown'))
                    })
                    
        # Remove duplicates
        seen = set()
        unique_links = []
        for link in mp4_links:
            if link['url'] not in seen:
                seen.add(link['url'])
                unique_links.append(link)
                
        logger.info(f"Found {len(unique_links)} MP4 links")
        return unique_links
        
    def extract_subtitles(self, html: str, base_url: str) -> List[Dict[str, Any]]:
        """Extract subtitle links (SRT, VTT, ASS) in various languages"""
        subtitles = []
        
        # Language patterns
        lang_patterns = {
            'english': ['english', 'eng', 'en'],
            'korean': ['korean', 'kor', 'ko', 'kr'],
            'japanese': ['japanese', 'jpn', 'ja', 'jp'],
            'chinese': ['chinese', 'chi', 'zh', 'cn'],
            'bangla': ['bangla', 'bengali', 'ben', 'bn'],
        }
        
        # Pattern 1: Direct subtitle URLs
        subtitle_patterns = [
            r'https?://[^\s"\'<>]+\.(?:srt|vtt|ass)(?:\?[^\s"\'<>]*)?',
            r'["\']([^"\']*subtitle[^"\']*\.(?:srt|vtt|ass)[^"\']*)["\']',
            r'["\']([^"\']*caption[^"\']*\.(?:srt|vtt|ass)[^"\']*)["\']',
        ]
        
        for pattern in subtitle_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                if match.startswith('http'):
                    lang = self._detect_language(match, lang_patterns)
                    subtitles.append({
                        'url': match,
                        'format': match.split('.')[-1].split('?')[0],
                        'language': lang,
                        'type': 'direct'
                    })
                    
        # Pattern 2: JSON subtitle tracks
        json_patterns = [
            r'tracks\s*:\s*(\[[^\]]+\])',
            r'"tracks"\s*:\s*(\[[^\]]+\])',
            r'subtitles\s*:\s*(\[[^\]]+\])',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                try:
                    tracks = json.loads(match)
                    if isinstance(tracks, list):
                        for track in tracks:
                            if isinstance(track, dict):
                                src = track.get('file', track.get('src', ''))
                                if src:
                                    full_url = urljoin(base_url, src)
                                    lang = track.get('language', track.get('lang', 'unknown'))
                                    label = track.get('label', '')
                                    subtitles.append({
                                        'url': full_url,
                                        'format': src.split('.')[-1].split('?')[0] if '.' in src else 'vtt',
                                        'language': self._normalize_language(lang, label),
                                        'label': label,
                                        'type': 'json_track',
                                        'default': track.get('default', False)
                                    })
                except json.JSONDecodeError:
                    continue
                    
        # Pattern 3: track tags in HTML
        soup = BeautifulSoup(html, 'lxml')
        for track in soup.find_all('track'):
            src = track.get('src', '')
            if src:
                full_url = urljoin(base_url, src)
                lang = track.get('srclang', track.get('lang', 'unknown'))
                label = track.get('label', '')
                subtitles.append({
                    'url': full_url,
                    'format': src.split('.')[-1].split('?')[0] if '.' in src else 'vtt',
                    'language': self._normalize_language(lang, label),
                    'label': label,
                    'type': 'track_tag',
                    'kind': track.get('kind', 'subtitles')
                })
                
        # Remove duplicates
        seen = set()
        unique_subs = []
        for sub in subtitles:
            if sub['url'] not in seen:
                seen.add(sub['url'])
                unique_subs.append(sub)
                
        logger.info(f"Found {len(unique_subs)} subtitle tracks")
        return unique_subs
        
    def _detect_quality(self, url: str) -> str:
        """Detect video quality from URL"""
        quality_patterns = [
            (r'1080[pi]', '1080p'),
            (r'720[pi]', '720p'),
            (r'480[pi]', '480p'),
            (r'360[pi]', '360p'),
            (r'240[pi]', '240p'),
            (r'4k|2160[pi]', '4K'),
        ]
        
        url_lower = url.lower()
        for pattern, quality in quality_patterns:
            if re.search(pattern, url_lower):
                return quality
        return 'unknown'
        
    def _detect_language(self, text: str, patterns: Dict) -> str:
        """Detect language from URL or text"""
        text_lower = text.lower()
        for lang, keywords in patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return lang
        return 'unknown'
        
    def _normalize_language(self, code: str, label: str = '') -> str:
        """Normalize language code to full name"""
        lang_map = {
            'en': 'english', 'eng': 'english', 'english': 'english',
            'ko': 'korean', 'kor': 'korean', 'kr': 'korean', 'korean': 'korean',
            'ja': 'japanese', 'jp': 'japanese', 'jpn': 'japanese', 'japanese': 'japanese',
            'zh': 'chinese', 'chi': 'chinese', 'cn': 'chinese', 'chinese': 'chinese',
            'bn': 'bangla', 'ben': 'bangla', 'bangla': 'bangla', 'bengali': 'bangla',
        }
        
        combined = f"{code} {label}".lower()
        for key, value in lang_map.items():
            if key in combined:
                return value
        return code
        
    async def analyze_page(self, url: str) -> Dict[str, Any]:
        """Complete page analysis - extracts all video sources"""
        logger.info(f"Analyzing page: {url}")
        
        html = await self.fetch_page(url)
        if not html:
            return {'error': 'Failed to fetch page'}
            
        result = {
            'source_url': url,
            'iframes': self.extract_iframes(html, url),
            'm3u8_links': self.extract_m3u8_links(html, url),
            'mp4_links': self.extract_mp4_links(html, url),
            'subtitles': self.extract_subtitles(html, url),
        }
        
        # If iframes found, also check iframe content
        if result['iframes']:
            logger.info(f"Checking {len(result['iframes'])} iframes for additional sources...")
            for iframe in result['iframes'][:3]:  # Limit to first 3 iframes
                iframe_html = await self.fetch_page(iframe['url'])
                if iframe_html:
                    iframe_m3u8 = self.extract_m3u8_links(iframe_html, iframe['url'])
                    iframe_mp4 = self.extract_mp4_links(iframe_html, iframe['url'])
                    iframe_subs = self.extract_subtitles(iframe_html, iframe['url'])
                    
                    result['m3u8_links'].extend(iframe_m3u8)
                    result['mp4_links'].extend(iframe_mp4)
                    result['subtitles'].extend(iframe_subs)
                    
        # Remove duplicates after iframe processing
        seen_m3u8 = set()
        result['m3u8_links'] = [x for x in result['m3u8_links'] if not (x['url'] in seen_m3u8 or seen_m3u8.add(x['url']))]
        
        seen_mp4 = set()
        result['mp4_links'] = [x for x in result['mp4_links'] if not (x['url'] in seen_mp4 or seen_mp4.add(x['url']))]
        
        seen_subs = set()
        result['subtitles'] = [x for x in result['subtitles'] if not (x['url'] in seen_subs or seen_subs.add(x['url']))]
        
        logger.info(f"Analysis complete. Found {len(result['m3u8_links'])} M3U8, {len(result['mp4_links'])} MP4, {len(result['subtitles'])} subtitles")
        
        return result


# Standalone function for quick use
async def scrape_video_sources(url: str) -> Dict[str, Any]:
    """Quick function to scrape video sources from a URL"""
    async with VideoScraper() as scraper:
        return await scraper.analyze_page(url)