from flask import Flask, request, jsonify, send_file, render_template
import os
import uuid
import time
import subprocess
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Create a directory to store downloads
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Set FFmpeg path - adjust this to your FFmpeg installation path
# Common paths:
# Windows: 'C:/ffmpeg/bin/ffmpeg.exe' 
# Mac/Linux: '/usr/bin/ffmpeg' or '/usr/local/bin/ffmpeg'
FFMPEG_PATH = '/usr/bin/ffmpeg'  # Change this to your FFmpeg path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/convert', methods=['POST'])
def convert():
    data = request.get_json()
    
    if not data or 'url' not in data or 'format' not in data:
        return jsonify({'error': 'Missing URL or format parameter'}), 400
    
    youtube_url = data['url']
    output_format = data['format'].lower()  # 'mp3' or 'mp4'
    
    if output_format not in ['mp3', 'mp4']:
        return jsonify({'error': 'Format must be mp3 or mp4'}), 400
    
    try:
        # Generate a unique ID for this download
        unique_id = str(uuid.uuid4())
        output_path = os.path.join(DOWNLOAD_FOLDER, unique_id)
        
        # Create the output directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # Define the output file path
        if output_format == 'mp3':
            output_file = os.path.join(output_path, f"{unique_id}.mp3")
            # Use yt-dlp to download as MP3
            command = [
                'yt-dlp',
                '-x',  # Extract audio
                '--audio-format', 'mp3',
                '--ffmpeg-location', FFMPEG_PATH,  # Specify FFmpeg path
                '-o', output_file,
                youtube_url
            ]
        else:  # mp4
            output_file = os.path.join(output_path, f"{unique_id}.mp4")
            # Use yt-dlp to download as MP4
            command = [
                'yt-dlp',
                '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                '--ffmpeg-location', FFMPEG_PATH,  # Specify FFmpeg path
                '-o', output_file,
                youtube_url
            ]
        
        # Execute the command
        process = subprocess.run(command, capture_output=True, text=True)
        
        if process.returncode != 0:
            raise Exception(f"yt-dlp error: {process.stderr}")
        
        # Get the video title
        title_command = ['yt-dlp', '--get-title', youtube_url]
        title_process = subprocess.run(title_command, capture_output=True, text=True)
        video_title = title_process.stdout.strip() if title_process.returncode == 0 else f"youtube-video-{unique_id}"
        
        # Create a download token
        download_token = str(uuid.uuid4())
        
        # Store the file info (in a real app, you'd use a database)
        app.config[download_token] = {
            'file_path': output_file,
            'file_name': f"{video_title}.{output_format}",
            'created_at': time.time()
        }
        
        return jsonify({
            'success': True,
            'download_token': download_token,
            'title': video_title,
            'format': output_format
        })
    
    except Exception as e:
        # Log the error for debugging
        print(f"Error converting video: {str(e)}")
        return jsonify({'error': f"Conversion failed: {str(e)}"}), 500

@app.route('/api/download/<token>', methods=['GET'])
def download(token):
    if token not in app.config:
        return jsonify({'error': 'Invalid or expired download token'}), 400
    
    file_info = app.config[token]
    
    # Check if file exists
    if not os.path.exists(file_info['file_path']):
        return jsonify({'error': 'File not found'}), 404
    
    # Send the file
    return send_file(
        file_info['file_path'],
        as_attachment=True,
        download_name=file_info['file_name']
    )

# Clean up old files
@app.before_request
def cleanup_old_files():
    current_time = time.time()
    tokens_to_remove = []
    
    for token, file_info in app.config.items():
        if isinstance(file_info, dict) and 'created_at' in file_info:
            # Remove files older than 1 hour
            if current_time - file_info['created_at'] > 3600:
                try:
                    os.remove(file_info['file_path'])
                    # Remove the directory if it's empty
                    dir_path = os.path.dirname(file_info['file_path'])
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                    tokens_to_remove.append(token)
                except:
                    pass
    
    for token in tokens_to_remove:
        del app.config[token]

if __name__ == '__main__':
    app.run(debug=True)
