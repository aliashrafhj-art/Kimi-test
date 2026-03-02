# 🏗️ Video Automation Tool - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Web UI    │  │  WebSocket  │  │   Progress Tracking     │  │
│  │  (React)    │◄─┤  (Real-time)├─►│      (Logs)             │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────────┘  │
└─────────┼────────────────────────────────────────────────────────┘
          │ HTTP/WebSocket
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API Layer                             │    │
│  │  /api/extract-sources  /api/download  /api/burn        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────┬─────────────┼─────────────┬─────────────────┐  │
│  ▼             ▼             ▼             ▼                 ▼  │
│ ┌────────┐  ┌────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│ │Scraper │  │Download│  │ Subtitle │  │  Video   │  │Telegram│ │
│ │Module  │  │ Module │  │ Processor│  │ Encoder  │  │Upload  │ │
│ └───┬────┘  └───┬────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│     │           │            │             │            │      │
│     ▼           ▼            ▼             ▼            ▼      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FFmpeg + Python Libraries                    │  │
│  │     aiohttp, beautifulsoup4, python-telegram-bot         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SERVICES                            │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────────┐   │
│  │  Streaming │  │  Telegram  │  │      File System         │   │
│  │   Sites    │  │    API     │  │   (/tmp, downloads)      │   │
│  └────────────┘  └────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Module Breakdown

### 1. Scraper Module (`scraper.py`)

**Purpose**: Extract video sources from streaming sites

**Key Features**:
- Async HTTP requests with retry logic
- Iframe detection and parsing
- M3U8 playlist extraction
- MP4 direct link detection
- Subtitle discovery (multi-language)

**Algorithms**:
- Regex pattern matching for URLs
- HTML parsing with BeautifulSoup
- JSON parsing for embedded sources
- Recursive iframe checking

**Output**:
```python
{
    "iframes": [{"url": "...", "width": "..."}],
    "m3u8_links": [{"url": "...", "quality": "1080p"}],
    "mp4_links": [{"url": "...", "quality": "720p"}],
    "subtitles": [{"url": "...", "language": "english"}]
}
```

### 2. Downloader Module (`downloader.py`)

**Purpose**: Download videos from various sources

**Key Features**:
- M3U8 stream downloading with segment merging
- Direct MP4 download with progress
- Concurrent segment downloads
- Resume capability (planned)

**Algorithms**:
- M3U8 playlist parsing
- Parallel segment download
- FFmpeg concat for merging
- Progress tracking via callbacks

**Performance**:
- Chunk size: 8KB for downloads
- Concurrent segments: 5 (configurable)
- Timeout: 30 seconds per segment

### 3. Subtitle Processor (`subtitle_processor.py`)

**Purpose**: Process Bengali subtitles with proper rendering

**Key Features**:
- SRT/VTT to ASS conversion
- Bengali Unicode normalization
- যুক্তবর্ণ (combined character) fixing
- Netflix-style styling

**Algorithms**:
- Unicode NFC normalization
- Character sequence correction
- ASS format generation
- Font fallback handling

**Bengali Font Handling**:
```python
BENGALI_FONTS = [
    "Noto Sans Bengali",    # Primary
    "Hind Siliguri",         # Fallback 1
    "Baloo Da 2",            # Fallback 2
    # ... more fallbacks
]
```

### 4. Video Encoder (`video_encoder.py`)

**Purpose**: Burn subtitles into video using FFmpeg

**Key Features**:
- Hardware-accelerated encoding (if available)
- Multiple quality presets
- Progress tracking
- Subtitle style application

**FFmpeg Command Structure**:
```bash
ffmpeg -i input.mp4 -vf subtitles=subtitle.ass -c:v libx264 -crf 18 output.mp4
```

**Quality Presets**:
| Preset | CRF | Speed | Size |
|--------|-----|-------|------|
| low | 28 | Fast | Small |
| medium | 23 | Medium | Medium |
| high | 18 | Slow | Large |
| ultra | 16 | Slowest | Largest |

### 5. Telegram Uploader (`telegram_uploader.py`)

**Purpose**: Upload videos to Telegram channel

**Key Features**:
- Large file support (up to 2GB)
- Progress tracking
- Caption formatting (HTML)
- Thumbnail support

**Upload Methods**:
- Small files (<50MB): Direct upload
- Large files: Streaming upload with chunks

### 6. Web Interface (`main.py`)

**Purpose**: Provide web UI and API endpoints

**Key Features**:
- FastAPI framework
- WebSocket for real-time logs
- RESTful API design
- CORS enabled

**Endpoints**:
```
GET  /                    → Web UI
WS   /ws                  → Real-time logs
POST /api/extract-sources → Extract video sources
POST /api/download        → Download video
POST /api/process-subtitle → Convert subtitle
POST /api/burn-subtitles  → Burn subtitles
POST /api/upload-telegram → Upload to Telegram
POST /api/full-automation → Complete workflow
GET  /api/health          → Health check
```

## Data Flow

### Full Automation Workflow

```
1. User provides episode URL
        ↓
2. Scraper extracts sources
   - M3U8/MP4 links
   - Subtitle links
        ↓
3. Downloader fetches video
   - Segments (if M3U8)
   - Direct download (if MP4)
        ↓
4. Subtitle processor converts
   - SRT/VTT → ASS
   - Applies Netflix style
        ↓
5. Video encoder burns subtitles
   - FFmpeg processing
   - Progress tracking
        ↓
6. Telegram uploader sends
   - Large file handling
   - Caption formatting
        ↓
7. User receives notification
```

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **HTTP Client**: aiohttp (async)
- **HTML Parsing**: BeautifulSoup4 + lxml
- **Video Processing**: FFmpeg-python
- **Telegram**: python-telegram-bot
- **Configuration**: pydantic-settings

### Frontend
- **Framework**: Vanilla JS (embedded in FastAPI)
- **Styling**: Custom CSS (dark theme)
- **Real-time**: WebSocket API
- **Icons**: Emoji

### Infrastructure
- **Container**: Docker
- **Hosting**: Railway (free tier)
- **Storage**: Ephemeral (/tmp)
- **Process**: Single worker (can scale)

## Security Considerations

### Input Validation
- URL validation
- File path sanitization
- Size limits
- Timeout handling

### Secrets Management
- Environment variables
- No hardcoded tokens
- .env file in .gitignore

### Rate Limiting
- Per-IP limits (to be implemented)
- Concurrent task limits
- Download speed limits (optional)

## Scalability

### Current Limitations (Free Tier)
- Memory: 512MB-1GB
- Disk: 5GB ephemeral
- Network: Shared
- CPU: Shared

### Optimization Strategies
1. **Chunked processing** for large files
2. **Queue system** for multiple tasks
3. **External storage** (S3) for files
4. **CDN** for delivery

### Future Improvements
- Redis for task queue
- Celery for distributed processing
- Multiple worker instances
- GPU acceleration for encoding

## Error Handling

### Retry Logic
```python
max_retries = 3
backoff_factor = 2  # 1s, 2s, 4s
```

### Graceful Degradation
- If Telegram fails → Save locally
- If subtitle burn fails → Return raw video
- If download fails → Try alternative sources

### Logging
- Structured JSON logs
- Log rotation
- Error tracking (Sentry integration planned)

## Performance Metrics

### Benchmarks (Estimated)

| Operation | Time (720p) | Time (1080p) |
|-----------|-------------|--------------|
| Extract sources | 2-5s | 2-5s |
| Download (1GB) | 2-5min | 5-10min |
| Process subtitle | 1-2s | 1-2s |
| Burn subtitles | 5-10min | 15-30min |
| Telegram upload | 5-15min | 20-40min |
| **Total** | **15-30min** | **45-90min** |

### Bottlenecks
1. **Video encoding** (CPU intensive)
2. **Network download** (bandwidth limited)
3. **Telegram upload** (API rate limited)

### Optimization Ideas
- Use hardware encoding (NVENC, QuickSync)
- Parallel downloads
- Compress before upload
- Use Telegram Bot API local server

---

**Architecture Version**: 1.0.0  
**Last Updated**: 2024