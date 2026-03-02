# 🚀 Video Automation Tool - Complete Setup Guide

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: 10GB free space minimum
- **Python**: 3.9 or higher
- **FFmpeg**: Latest stable version

## 🔧 Step-by-Step Installation

### 1. Install FFmpeg

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
ffmpeg -version  # Verify installation
```

#### macOS
```bash
brew install ffmpeg
ffmpeg -version  # Verify installation
```

#### Windows (with WSL)
```bash
# In WSL terminal
sudo apt-get update
sudo apt-get install -y ffmpeg
```

### 2. Clone and Setup Project

```bash
# Clone repository
git clone <your-repo-url>
cd video-automation-tool

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

**Required Variables:**
```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHANNEL_ID=@your_channel_username
```

### 4. Setup Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start chat** and send `/newbot`
3. **Follow prompts**:
   - Enter bot name
   - Enter bot username (must end in 'bot')
4. **Copy the token** provided
5. **Add bot to your channel**:
   - Open your channel
   - Add member → Search bot username → Add as admin
   - Give permission to send messages

### 5. Get Channel ID

**Method 1: Using Bot API**
```bash
# Replace <TOKEN> with your bot token
curl https://api.telegram.org/bot<TOKEN>/getUpdates

# Look for "chat":{"id":-100xxxxxxxxxx
# Channel ID is -100xxxxxxxxxx
```

**Method 2: Using @userinfobot**
1. Forward a message from your channel to @userinfobot
2. It will reply with the channel ID

### 6. Run the Application

```bash
# Development mode
python backend/main.py

# Or with explicit host/port
python backend/main.py --host 0.0.0.0 --port 8000
```

**Access the web interface:** http://localhost:8000

## 🚂 Railway Deployment (Free Hosting)

### Step 1: Prepare Repository

```bash
# Ensure all files are committed
git add .
git commit -m "Ready for Railway deployment"
git push origin main
```

### Step 2: Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub
3. Verify email

### Step 3: Deploy Project

1. **New Project** → **Deploy from GitHub repo**
2. **Select your repository**
3. Railway will **auto-detect Dockerfile**

### Step 4: Add Environment Variables

1. Go to **Project** → **Variables**
2. **Add variables**:
   ```
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHANNEL_ID=@your_channel
   DEBUG=false
   ```

### Step 5: Deploy

1. Railway will **auto-deploy**
2. Wait for build to complete (2-5 minutes)
3. Click on the **generated domain** to access

### Step 6: Verify Deployment

```bash
# Check health endpoint
curl https://your-app.railway.app/api/health

# Should return:
# {"status":"ok","version":"1.0.0",...}
```

## 🎨 Customization

### Adding Custom Bengali Fonts

1. **Download Bengali fonts**:
   - Noto Sans Bengali
   - Hind Siliguri
   - Baloo Da 2

2. **Place in fonts/ directory**:
   ```bash
   mkdir -p fonts
   cp ~/Downloads/*.ttf fonts/
   ```

3. **Update environment**:
   ```env
   SUBTITLE_FONT=Your Font Name
   ```

### Changing Subtitle Style

Edit `backend/subtitle_processor.py`:

```python
style = SubtitleStyle(
    font_name="Your Font",
    font_size=32,
    primary_color="&H00FFFFFF",  # White
    outline_color="&H00000000",  # Black
    outline=3.0,  # Thicker outline
)
```

### Quality Presets

| Preset | CRF | Use Case |
|--------|-----|----------|
| low | 28 | Fast processing, smaller size |
| medium | 23 | Balanced quality |
| high | 18 | Best quality (recommended) |
| ultra | 16 | Maximum quality, larger size |

## 🔍 Troubleshooting

### Common Issues

#### 1. FFmpeg Not Found
```bash
# Check if installed
which ffmpeg

# If not found, reinstall:
sudo apt-get install ffmpeg  # Linux
brew install ffmpeg          # Mac
```

#### 2. Bengali Font Shows Boxes
```bash
# Install Bengali fonts
sudo apt-get install fonts-noto fonts-noto-cjk

# Or download manually:
wget https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansBengali/NotoSansBengali-Regular.ttf
```

#### 3. Telegram Upload Fails
- Check bot token is correct
- Ensure bot is channel admin
- Verify channel ID format

#### 4. M3U8 Download Fails
- Some sites require headers/cookies
- Update scraper with site-specific headers
- Check if stream is geo-restricted

#### 5. Railway Build Fails
```bash
# Check logs in Railway dashboard
# Common fixes:
- Ensure Dockerfile is correct
- Check requirements.txt syntax
- Verify no missing dependencies
```

### Debug Mode

```bash
# Enable debug logging
DEBUG=true python backend/main.py
```

### Check Logs

```bash
# Local logs
 tail -f logs/app.log

# Railway logs
# Go to Railway dashboard → Deployments → View Logs
```

## 📊 Performance Optimization

### For Large Files (1GB+)

1. **Use high memory plan** on Railway
2. **Enable swap**:
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

3. **Process in chunks** (future feature)

### Speed Up Processing

```env
# Use faster preset (lower quality)
VIDEO_QUALITY=medium

# Lower CRF for faster encoding
# Edit video_encoder.py
```

## 🔒 Security Best Practices

1. **Never commit .env file**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use strong bot token**
   - Regenerate if compromised: @BotFather → /revoke

3. **Restrict channel access**
   - Make channel private
   - Only add trusted admins

4. **Monitor usage**
   - Set up logging
   - Track API calls

## 🔄 Updating the Application

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r backend/requirements.txt --upgrade

# Restart application
# (Ctrl+C then python backend/main.py)
```

## 🆘 Getting Help

### Resources
- **GitHub Issues**: Report bugs
- **Telegram**: @your_support_channel
- **Documentation**: This README

### Debug Information

When reporting issues, include:
1. Error message
2. Steps to reproduce
3. Environment details (OS, Python version)
4. Relevant logs

---

**Happy Automating! 🎬**