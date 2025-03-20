# YouTube to MP3/MP4 Converter

A web application that allows users to convert YouTube videos to either MP3 (audio) or MP4 (video) format. This project uses Flask for the backend API and vanilla JavaScript for the frontend interface, providing a simple and intuitive way to download YouTube content.

## Table of Contents

1. [Installation](https://github.com/Tragic-cmd/Youtube-Converter#installation)
2. [Usage]
3. [Features]
4. [Contributing]
5. [License]
6. [Contact]

## Installation

### Prerequisites

- Python 3.6 or higher
- FFmpeg installed on your system
- yt-dlp installed on your system

### Setup Steps

```bash
# Clone the repository
git clone https://github.com/your-username/youtube-converter.git

# Navigate into the project directory
cd youtube-converter

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required dependencies
pip install flask flask-cors

# Install yt-dlp if not already installed
pip install yt-dlp

# Install FFmpeg if not already installed
# On Ubuntu/Debian: sudo apt-get install ffmpeg
# On macOS with Homebrew: brew install ffmpeg
# On Windows: Download from https://ffmpeg.org/download.html

# Update FFmpeg path in app.py to match your installation
# Line 19: FFMPEG_PATH = '/path/to/your/ffmpeg'
```

## Usage

1. Start the Flask server:

```bash
python app.py
```

2. Open your web browser and navigate to `http://localhost:5000`
    
3. Enter a YouTube URL in the input field
    
4. Select your desired format (MP3 or MP4)
    
5. Click the "Convert Now" button
    
6. Once conversion is complete, click the "Download" button to save your file
    

### API Endpoints

If you want to integrate with the API directly:

```
POST /api/convert
```

- Request body: `{ "url": "youtube-url", "format": "mp3" or "mp4" }`
- Response: `{ "success": true, "download_token": "token", "title": "video-title", "format": "mp3" or "mp4" }`

```
GET /api/download/<token>
```

- Returns the converted file as a download

## Features

- Convert YouTube videos to MP3 (audio) or MP4 (video) formats
- Simple and intuitive user interface
- High-quality conversion using FFmpeg
- No registration required
- Unlimited conversions
- Fast processing speed
- Supports all YouTube videos
- Automatic cleanup of downloaded files after 1 hour
- Responsive design works on desktop and mobile devices

## Contributing

Contributions are welcome! Here's how you can contribute:

1. Fork the repository
2. Create your feature branch: `git checkout -b feature-branch-name`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature-branch-name`
5. Open a pull request

### Development Guidelines

- Test your changes thoroughly
- Update documentation as needed

## License

This project is licensed under the MIT License - see the [LICENSE](https://claude.ai/chat/LICENSE) file for details.

## Contact

If you have any questions or suggestions, feel free to reach out:

- GitHub: [Tragic-cmd](https://github.com/Tragic-cmd)

---

**Note**: This application is for educational purposes only. Please respect YouTube's terms of service and copyright laws when using this tool.
