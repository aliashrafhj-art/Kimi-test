"""
Bangla Subtitle Processor - Netflix Style with Proper Font Rendering
Handles Bengali font issues, combined characters, and stylish rendering
"""
import os
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import logging
import unicodedata

logger = logging.getLogger(__name__)

@dataclass
class SubtitleStyle:
    """Netflix-style subtitle configuration"""
    font_name: str = "Noto Sans Bengali"
    font_size: int = 28
    primary_color: str = "&H00FFFFFF"  # White in ASS format (BGR)
    secondary_color: str = "&H000000FF"  # Blue
    outline_color: str = "&H00000000"  # Black
    back_color: str = "&H80000000"  # Semi-transparent black
    bold: int = 1
    italic: int = 0
    underline: int = 0
    strikeout: int = 0
    scale_x: float = 100.0
    scale_y: float = 100.0
    spacing: float = 0.0
    angle: float = 0.0
    border_style: int = 1  # 1=outline, 3=opaque box
    outline: float = 2.0
    shadow: float = 1.0
    alignment: int = 2  # 2=bottom center
    margin_l: int = 60
    margin_r: int = 60
    margin_v: int = 40
    encoding: int = 0  # UTF-8
    
    # Netflix specific
    netflix_box_enabled: bool = True
    netflix_box_color: str = "&H80000000"  # Semi-transparent black
    netflix_box_margin: int = 10
    netflix_line_spacing: float = 1.2


class BanglaSubtitleProcessor:
    """
    Processes Bengali subtitles with proper font handling
    Fixes: broken characters, combined letters (যুক্তবর্ণ), and encoding issues
    """
    
    # Bengali Unicode range
    BENGALI_RANGE = r'[\u0980-\u09FF]'
    
    # Common Bengali font list (prioritized)
    BENGALI_FONTS = [
        "Noto Sans Bengali",
        "Noto Sans Bengali UI",
        "Hind Siliguri",
        "Baloo Da 2",
        "Nikosh",
        "NikoshBAN",
        "Siyam Rupali",
        "SolaimanLipi",
        "Kalpurush",
        "AdorshoLipi",
        "Bangla",
        "Vrinda",
        "Arial Unicode MS",
    ]
    
    # Character fixes for common issues
    CHAR_FIXES = {
        # Fix broken combined characters
        '্য': '্য',
        '্র': '্র',
        '্ল': '্ল',
        '্ম': '্ম',
        '্ন': '্ন',
        '্প': '্প',
        '্ব': '্ব',
        '্ভ': '্ভ',
        '্স': '্স',
        '্ত': '্ত',
        '্দ': '্দ',
        '্ধ': '্ধ',
        '্ক': '্ক',
        '্গ': '্গ',
        '্ঘ': '্ঘ',
        '্চ': '্চ',
        '্ছ': '্ছ',
        '্জ': '্জ',
        '্ঝ': '্ঝ',
        '্ট': '্ট',
        '্ঠ': '্ঠ',
        '্ড': '্ড',
        '্ঢ': '্ঢ',
        '্ণ': '্ণ',
        '্থ': '্থ',
        '্ন': '্ন',
        '্প': '্প',
        '্ফ': '্ফ',
        '্ব': '্ব',
        '্ভ': '্ভ',
        '্ম': '্ম',
        '্য': '্য',
        '্র': '্র',
        '্ল': '্ল',
        '্শ': '্শ',
        '্ষ': '্ষ',
        '্স': '্স',
        '্হ': '্হ',
        '্ড়': 'ড়',
        '্ঢ়': 'ঢ়',
        '্য়': 'য়',
        '্ৎ': 'ৎ',
    }
    
    def __init__(self, font_dir: str = "./fonts"):
        self.font_dir = Path(font_dir)
        self.font_dir.mkdir(parents=True, exist_ok=True)
        self.style = SubtitleStyle()
        
    def fix_bengali_text(self, text: str) -> str:
        """
        Fix common Bengali text rendering issues
        - Normalizes Unicode
        - Fixes broken combined characters
        - Handles encoding issues
        """
        if not text:
            return text
            
        # Normalize Unicode (NFC - Canonical Decomposition followed by Canonical Composition)
        text = unicodedata.normalize('NFC', text)
        
        # Fix broken characters
        for broken, fixed in self.CHAR_FIXES.items():
            text = text.replace(broken, fixed)
            
        # Fix specific combined character sequences
        text = self._fix_juktoborno(text)
        
        # Fix spacing issues
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = text.strip()
        
        return text
        
    def _fix_juktoborno(self, text: str) -> str:
        """
        Fix যুক্তবর্ণ (combined Bengali characters)
        Ensures proper ordering of consonant + hasant + consonant
        """
        # Bengali consonants
        consonants = r'[কখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়রল]'
        hasant = '্'
        
        # Pattern: consonant + hasant + consonant (correct order)
        # Some systems output: hasant + consonant + consonant (wrong)
        
        # Fix common mis-ordered sequences
        patterns = [
            (f'{hasant}({consonants})({consonants})', r'\1{hasant}\2'),
        ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
            
        return text
        
    def detect_bengali(self, text: str) -> bool:
        """Check if text contains Bengali characters"""
        return bool(re.search(self.BENGALI_RANGE, text))
        
    def convert_srt_to_ass(
        self, 
        srt_path: str, 
        output_path: Optional[str] = None,
        style: Optional[SubtitleStyle] = None
    ) -> str:
        """
        Convert SRT to ASS with Netflix-style Bengali formatting
        """
        if not output_path:
            output_path = srt_path.replace('.srt', '.ass')
            
        if not style:
            style = self.style
            
        logger.info(f"Converting SRT to ASS: {srt_path} -> {output_path}")
        
        # Parse SRT
        subtitles = self._parse_srt(srt_path)
        
        # Generate ASS
        self._generate_ass(subtitles, output_path, style)
        
        return output_path
        
    def convert_vtt_to_ass(
        self, 
        vtt_path: str, 
        output_path: Optional[str] = None,
        style: Optional[SubtitleStyle] = None
    ) -> str:
        """
        Convert VTT to ASS with Netflix-style Bengali formatting
        """
        if not output_path:
            output_path = vtt_path.replace('.vtt', '.ass')
            
        if not style:
            style = self.style
            
        logger.info(f"Converting VTT to ASS: {vtt_path} -> {output_path}")
        
        # Parse VTT
        subtitles = self._parse_vtt(vtt_path)
        
        # Generate ASS
        self._generate_ass(subtitles, output_path, style)
        
        return output_path
        
    def _parse_srt(self, srt_path: str) -> List[Dict[str, Any]]:
        """Parse SRT file"""
        subtitles = []
        
        with open(srt_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            
        # Split by double newline
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # First line is index
                index = lines[0].strip()
                
                # Second line is timecode
                time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                if time_match:
                    start = self._srt_time_to_ass(time_match.group(1))
                    end = self._srt_time_to_ass(time_match.group(2))
                    
                    # Rest is text
                    text = '\n'.join(lines[2:])
                    text = self.fix_bengali_text(text)
                    
                    subtitles.append({
                        'index': index,
                        'start': start,
                        'end': end,
                        'text': text
                    })
                    
        return subtitles
        
    def _parse_vtt(self, vtt_path: str) -> List[Dict[str, Any]]:
        """Parse VTT file"""
        subtitles = []
        
        with open(vtt_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            
        # Remove WEBVTT header
        content = re.sub(r'^WEBVTT.*?\n', '', content, flags=re.DOTALL)
        
        # Parse cues
        cue_pattern = r'(?:\d+\n)?(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})[^\n]*\n(.*?)(?:\n\n|$)'
        matches = re.findall(cue_pattern, content, re.DOTALL)
        
        for i, (start, end, text) in enumerate(matches):
            text = text.strip()
            text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
            text = self.fix_bengali_text(text)
            
            subtitles.append({
                'index': str(i + 1),
                'start': self._vtt_time_to_ass(start),
                'end': self._vtt_time_to_ass(end),
                'text': text
            })
            
        return subtitles
        
    def _srt_time_to_ass(self, time_str: str) -> str:
        """Convert SRT time to ASS time"""
        # SRT: 00:00:00,000 -> ASS: 0:00:00.00
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return f"{hours}:{minutes:02d}:{seconds:05.2f}"
        
    def _vtt_time_to_ass(self, time_str: str) -> str:
        """Convert VTT time to ASS time"""
        # VTT: 00:00:00.000 -> ASS: 0:00:00.00
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return f"{hours}:{minutes:02d}:{seconds:05.2f}"
        
    def _generate_ass(self, subtitles: List[Dict], output_path: str, style: SubtitleStyle):
        """Generate ASS file with Netflix-style formatting"""
        
        # ASS Header with Netflix-style styling
        header = f"""[Script Info]
Title: Netflix Style Bengali Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Netflix,{style.font_name},{style.font_size},{style.primary_color},{style.secondary_color},{style.outline_color},{style.back_color},{style.bold},{style.italic},{style.underline},{style.strikeout},{style.scale_x},{style.scale_y},{style.spacing},{style.angle},{style.border_style},{style.outline},{style.shadow},{style.alignment},{style.margin_l},{style.margin_r},{style.margin_v},{style.encoding}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        with open(output_path, 'w', encoding='utf-8-sig') as f:
            f.write(header)
            
            for sub in subtitles:
                # Format text for ASS
                text = sub['text']
                
                # Add Netflix-style background box if enabled
                if style.netflix_box_enabled:
                    # Use \N for line breaks in ASS
                    text = text.replace('\n', '\\N')
                    
                # Escape special characters
                text = text.replace('{', '\\{')
                text = text.replace('}', '\\}')
                
                line = f"Dialogue: 0,{sub['start']},{sub['end']},Netflix,,0,0,0,,{text}\n"
                f.write(line)
                
        logger.info(f"ASS file generated: {output_path}")
        
    def create_netflix_style_ass(
        self, 
        subtitles: List[Dict[str, Any]], 
        output_path: str,
        font_name: str = "Noto Sans Bengali"
    ) -> str:
        """
        Create Netflix-style ASS subtitle from scratch
        """
        style = SubtitleStyle(
            font_name=font_name,
            font_size=32,
            primary_color="&H00FFFFFF",
            outline_color="&H00000000",
            back_color="&H80000000",
            bold=1,
            outline=2.5,
            shadow=0.5,
            border_style=1,
            alignment=2,
            margin_v=60
        )
        
        self._generate_ass(subtitles, output_path, style)
        return output_path
        
    def download_bengali_fonts(self):
        """Download popular Bengali fonts for proper rendering"""
        import urllib.request
        
        font_urls = {
            "NotoSansBengali-Regular.ttf": "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansBengali/NotoSansBengali-Regular.ttf",
            "HindSiliguri-Regular.ttf": "https://github.com/itfoundry/hind-siliguri/raw/master/products/HindSiliguri-Regular.ttf",
            "BalooDa2-Regular.ttf": "https://github.com/ektype/baloo-2/raw/master/fonts/BalooDa2-Regular.ttf",
        }
        
        downloaded = []
        for filename, url in font_urls.items():
            font_path = self.font_dir / filename
            if not font_path.exists():
                try:
                    logger.info(f"Downloading font: {filename}")
                    urllib.request.urlretrieve(url, str(font_path))
                    downloaded.append(str(font_path))
                except Exception as e:
                    logger.error(f"Failed to download {filename}: {e}")
                    
        return downloaded


# Standalone functions
def process_bengali_subtitle(
    input_path: str, 
    output_path: Optional[str] = None,
    font_name: str = "Noto Sans Bengali"
) -> str:
    """Quick function to process Bengali subtitle"""
    processor = BanglaSubtitleProcessor()
    
    if input_path.endswith('.srt'):
        return processor.convert_srt_to_ass(input_path, output_path)
    elif input_path.endswith('.vtt'):
        return processor.convert_vtt_to_ass(input_path, output_path)
    elif input_path.endswith('.ass'):
        # Just fix the text in existing ASS
        return input_path
    else:
        raise ValueError(f"Unsupported subtitle format: {input_path}")