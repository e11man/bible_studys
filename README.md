# Bible Podcast Generator - Complete Web Application

A powerful web application that transforms Bible passages and theological commentary into professional podcast scripts, audio, and videos.

## ✨ Features

- **📖 Scripture Reading**: Generate podcast scripts directly from Bible passages
- **📝 Commentary Integration**: Process theological commentary into structured podcast content
- **🎵 Audio Generation**: Convert scripts to professional dual-voice audio using Google Cloud TTS
- **🎬 Video Creation**: Generate YouTube-ready videos with background images
- **🌐 Web Interface**: Beautiful, modern web UI for easy content creation
- **📱 Mobile Responsive**: Works perfectly on all device sizes

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** with virtual environment
2. **Google Cloud Text-to-Speech API** credentials (for audio generation)
3. **Bible JSON files** in the `bibles/` directory

### Installation

1. **Clone or navigate to your project directory**
   ```bash
   cd ~/Documents/bible_study
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask requests google-cloud-texttospeech pydub tqdm moviepy pillow
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Open your browser**
   ```
   http://localhost:5001
   ```

## 📋 Usage Guide

### 1. Generate Scripture-Only Podcasts

1. Select a Bible translation (ESV or NKJV)
2. Enter passage (e.g., "Genesis 1-3", "Psalms 1-5", "Matthew 5-7")
3. Leave commentary field empty
4. Click "Generate Podcast Script"

### 2. Generate Commentary-Based Podcasts

1. Select Bible translation
2. Enter passage
3. Paste theological commentary in the expected format:
   ```
   Section 1: Genesis 1:1-5 - Creation Begins
   Your commentary content here...
   
   Section 2: Genesis 1:6-10 - The Firmament
   More commentary content...
   ```
4. Click "Generate Podcast Script"

### 3. Create Audio Podcasts

1. After generating a script, click "Generate Audio"
2. Wait for processing (can take several minutes)
3. Download the MP3 file when complete

### 4. Create Video Content

1. Generate audio first
2. Click "Create Video" in the audio result section
3. Upload a background image (1280px width minimum)
4. Add optional title
5. Click "Generate Video"
6. Download MP4 when complete

## 🔧 Configuration

### Google Cloud Setup

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create new project or select existing

2. **Enable Text-to-Speech API**
   - Navigate to APIs & Services > Library
   - Search for "Cloud Text-to-Speech API"
   - Click Enable

3. **Create Service Account**
   - Go to IAM & Admin > Service Accounts
   - Create new service account
   - Download JSON key file

4. **Configure Credentials**
   - Place JSON file in project root as `majestic-bounty-455918-f1-fb3e5e5fef3d.json`
   - Or use the web interface to set custom path

### Bible Data

Place Bible JSON files in `bibles/` directory:
- `ESV_bible.json`
- `NKJV_bible.json`

Format: `{book_name: {chapter: {verse: "text"}}}`

## 🎯 Script Format

Generated scripts use this format:

```markdown
# Passage Podcast Script
# Translation with Commentary
# Generated from Commentary/Reading

---

## Section 1: Genesis 1:1-5

**HOST:**
Now let's turn to Genesis 1:1-5:

"In the beginning God created..."

**GUEST:**
Commentary or continued reading...

---
```

- **HOST**: Introduces passages, reads scripture
- **GUEST**: Provides commentary or continues reading
- Clear section breaks for easy editing

## 📁 File Structure

```
bible_study/
├── main.py                 # Main Flask application
├── bible.py               # Scripture processing engine
├── generate_audio.py      # Audio generation module
├── generate_video.py      # Video creation module
├── templates/
│   └── index.html         # Web interface
├── bibles/
│   ├── ESV_bible.json     # Bible translations
│   └── NKJV_bible.json
├── output/                # Generated content
├── uploads/               # Uploaded images
└── majestic-bounty-*.json # Google Cloud credentials
```

## 🎵 Audio Features

- **Dual Voice**: HOST (male) and GUEST (female) speakers
- **High Quality**: 192kbps MP3 output
- **Natural Pacing**: Optimized speaking rate and pauses
- **Professional**: Google Cloud TTS with Wavenet voices

## 🎬 Video Features

- **YouTube Ready**: 720p MP4 output
- **Custom Backgrounds**: Upload your own images
- **Optimized**: Fast encoding with H.264
- **Automatic**: Perfect audio synchronization

## 🔍 Troubleshooting

### Common Issues

1. **"Script generation failed"**
   - Check passage format (e.g., "Genesis 1-3")
   - Verify Bible translation is available
   - Ensure commentary follows expected format

2. **"Audio generation not available"**
   - Check Google Cloud credentials
   - Verify TTS API is enabled
   - Install: `pip install google-cloud-texttospeech pydub`

3. **"Video generation not available"**
   - Install: `pip install moviepy pillow`
   - Check image format (JPG, PNG supported)
   - Ensure image is at least 1280px wide

### Debug Mode

The application runs in debug mode by default. Check terminal for detailed logs:
- 🔍 Commentary processing
- ✓ Successful operations
- ❌ Error details
- 📊 Progress updates

## 🌟 Tips for Best Results

### Scripture Reading
- Use complete chapters for natural flow
- Multiple chapters work well (e.g., "Psalms 1-5")
- Short books can be done entirely (e.g., "Philemon 1")

### Commentary
- Follow the section format exactly
- Include verse references that exist in your Bible translation
- Keep sections reasonably sized (not too long)

### Audio
- Scripts with 2000-4000 words produce 10-20 minute podcasts
- HOST/GUEST alternation creates engaging dialogue
- Pauses between sections provide natural breaks

### Video
- Use high-resolution images (1920x1080 recommended)
- Landscape orientation works best
- Religious artwork, nature scenes, or simple backgrounds are effective

## 📞 Support

If you encounter issues:

1. Check the terminal/console for error messages
2. Verify all dependencies are installed
3. Ensure Bible JSON files are properly formatted
4. Test with a simple passage first (e.g., "Genesis 1")

## 🎉 Example Workflow

1. **Quick Test**: Generate "Psalms 23" with NKJV
2. **Audio Test**: Create audio from the generated script
3. **Video Test**: Upload a simple background image and create video
4. **Full Project**: Generate longer passages with commentary

The application is designed to be intuitive - most features work with just a few clicks! 