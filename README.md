# 🎬 Video Automation Tool

একটি শক্তিশালী পাইথন অটোমেশন টুলস যা ভিডিও প্রসেসিং এর সম্পূর্ণ workflow অটোমেট করে - ওয়েব স্ক্র্যাপিং থেকে শুরু করে টেলিগ্রাম আপলোড পর্যন্ত।

## ✨ Features

### 🔍 Smart Web Scraping
- **Iframe Detection**: অটোমেটিক iframe থেকে ভিডিও সোর্স বের করে
- **M3U8 Extraction**: HLS stream links সনাক্ত করে
- **MP4 Detection**: Direct video links খুঁজে পায়
- **Subtitle Discovery**: ইংরেজি, কোরিয়ান, জাপানি সাবটাইটেল অটো-ডিটেক্ট

### ⬇️ Advanced Downloader
- **M3U8 Streams**: HLS playlist থেকে ভিডিও ডাউনলোড
- **Progress Tracking**: রিয়েল-টাইম ডাউনলোড প্রোগ্রেস
- **Resume Support**: বড় ফাইলের জন্য resume capability
- **Quality Selection**: অটোমেটিক best quality সিলেকশন

### 📝 Bengali Subtitle Processor
- **Netflix Style**: স্টাইলিশ বাংলা সাবটাইটেল ফরম্যাট
- **Font Fix**: যুক্তবর্ণ এবং ব্রোকেন ক্যারেক্টার ঠিক করে
- **Unicode Normalize**: সঠিক বাংলা রেন্ডারিং
- **ASS Format**: Advanced SubStation Alpha সাপোর্ট

### 🔥 Video Encoder
- **FFmpeg Powered**: প্রফেশনাল গ্রেড ভিডিও এনকোডিং
- **Hardcode Subtitles**: স্থায়ী সাবটাইটেল বার্নিং
- **Multiple Styles**: Netflix, Minimal, Classic স্টাইল
- **Quality Presets**: Low, Medium, High, Ultra quality

### 📤 Telegram Integration
- **Large File Support**: 2GB পর্যন্ত ফাইল আপলোড
- **Progress Tracking**: আপলোড প্রোগ্রেস দেখা যায়
- **Caption Support**: HTML ফরম্যাটেড ক্যাপশন
- **Channel Upload**: অটোমেটিক চ্যানেলে আপলোড

### 🌐 Web Interface
- **Real-time Logs**: WebSocket দিয়ে লাইভ লগ
- **Progress Bars**: ভিজ্যুয়াল প্রোগ্রেস ইন্ডিকেটর
- **Responsive UI**: মোবাইল ফ্রেন্ডলি ডিজাইন
- **Dark Theme**: আধুনিক ডার্ক থিম

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone <repo-url>
cd video-automation-tool

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Install FFmpeg (if not installed)
# Ubuntu/Debian: sudo apt-get install ffmpeg
# Mac: brew install ffmpeg
# Windows: choco install ffmpeg

# Setup environment variables
cp .env.example .env
# Edit .env with your Telegram bot token

# Run the application
python backend/main.py
```

### Railway Deployment (Free)

1. **Fork/Clone** this repository to your GitHub

2. **Create Railway Account**: https://railway.app

3. **New Project** → Deploy from GitHub repo

4. **Add Environment Variables**:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHANNEL_ID=@your_channel
   ```

5. **Deploy** - Railway অটোমেটিক Dockerfile ব্যবহার করবে

## 📖 Usage Guide

### Step 1: Extract Video Sources

```bash
curl -X POST http://localhost:8000/api/extract-sources \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/episode-1"}'
```

Response:
```json
{
  "iframes": [...],
  "m3u8_links": [{"url": "...", "quality": "1080p"}],
  "mp4_links": [...],
  "subtitles": [{"url": "...", "language": "english"}]
}
```

### Step 2: Download Video

```bash
curl -X POST http://localhost:8000/api/download \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/video.m3u8",
    "url_type": "m3u8",
    "filename": "episode_01.mp4"
  }'
```

### Step 3: Process Subtitle

```bash
curl -X POST http://localhost:8000/api/process-subtitle \
  -H "Content-Type: application/json" \
  -d '{"subtitle_path": "/tmp/subtitle.srt"}'
```

### Step 4: Burn Subtitles

```bash
curl -X POST http://localhost:8000/api/burn-subtitles \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "/tmp/video.mp4",
    "subtitle_path": "/tmp/subtitle.ass",
    "subtitle_style": "netflix"
  }'
```

### Full Automation (All Steps)

```bash
curl -X POST http://localhost:8000/api/full-automation \
  -H "Content-Type: application/json" \
  -d '{
    "source_url": "https://example.com/episode-1",
    "bangla_subtitle_path": "/tmp/bangla.srt",
    "output_name": "My_Video",
    "upload_to_telegram": true
  }'
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | Required |
| `TELEGRAM_CHANNEL_ID` | Channel username or ID | Required |
| `TEMP_DIR` | Temporary files directory | `/tmp/video-automation` |
| `DOWNLOAD_DIR` | Downloaded files directory | `/tmp/downloads` |
| `MAX_CONCURRENT_DOWNLOADS` | Max parallel downloads | `2` |
| `VIDEO_QUALITY` | Default video quality | `720p` |
| `SUBTITLE_FONT` | Bengali font name | `Noto Sans Bengali` |

### Telegram Bot Setup

1. **Create Bot**: Message @BotFather, send `/newbot`
2. **Get Token**: Copy the provided token
3. **Add to Channel**: Add bot to your channel as admin
4. **Get Channel ID**: 
   - Forward a message from channel to @userinfobot
   - Or use: `https://api.telegram.org/bot<TOKEN>/getUpdates`

## 🎨 Subtitle Styles

### Netflix Style (Recommended)
- White text with black outline
- Bottom center alignment
- Bold font
- Semi-transparent background box

### Minimal Style
- Clean white text
- Thin outline
- Simple design

### Classic Style
- Yellow subtitles
- Black outline
- Traditional look

## 🛠️ Advanced Features

### Custom Font Support

Place your Bengali fonts in `fonts/` directory:
- NotoSansBengali.ttf
- HindSiliguri.ttf
- BalooDa2.ttf

### WebSocket Real-time Logs

Connect to `ws://localhost:8000/ws` for live updates:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.message);
};
```

### Progress Tracking

All endpoints return progress updates via WebSocket:
```json
{
  "type": "progress",
  "task_id": "...",
  "step": "download",
  "progress": 45,
  "total": 100,
  "message": "Downloading: 45%"
}
```

## 🐛 Troubleshooting

### Bengali Font Issues

If বক্স বক্স দেখা যায়:
1. Ensure Bengali fonts are installed
2. Check `fonts/` directory
3. Verify FONT_DIR environment variable

### FFmpeg Not Found

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# Mac
brew install ffmpeg

# Windows
choco install ffmpeg
```

### Telegram Upload Fails

1. Check bot token is correct
2. Ensure bot is channel admin
3. Verify channel ID format (use @username or -100xxx)

### Large File Issues

Railway's free tier has limitations:
- Disk: ~5GB ephemeral
- Memory: 512MB-1GB
- For large files, use external storage

## 📁 Project Structure

```
video-automation-tool/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── scraper.py           # Web scraping
│   ├── downloader.py        # Video download
│   ├── subtitle_processor.py # Bengali subtitle processing
│   ├── video_encoder.py     # FFmpeg encoding
│   └── telegram_uploader.py # Telegram integration
├── fonts/                   # Bengali fonts
├── Dockerfile               # Container config
├── railway.toml            # Railway deployment
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## 🔒 Security Notes

- Never commit `.env` file
- Use strong Telegram bot token
- Restrict channel access
- Monitor disk usage on Railway
- Don't expose sensitive endpoints

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📜 License

MIT License - Free for personal and commercial use.

## 🙏 Credits

- FFmpeg: Video processing
- FastAPI: Web framework
- python-telegram-bot: Telegram integration
- Noto Fonts: Bengali font support

---

**Made with ❤️ for Bengali video enthusiasts**