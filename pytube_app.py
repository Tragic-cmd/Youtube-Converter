from flask import Flask, request, jsonify, send_file, render_template
import os
import uuid
import time
from flask_cors import CORS
from pytube import YouTube
import re

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Create a directory to store downloads
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Fix for pytube issues
def patch_pytube():
    """Apply various patches for pytube issues"""
    try:
        # Fix for regex issue - common pytube problem
        from pytube import cipher
        old_method = cipher.get_initial_function_name
        
        def new_method(js):
            try:
                return old_method(js)
            except:
                # Try with a more relaxed pattern if the default fails
                function_patterns = [
                    r'(?:\b[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*)([\w$]+)(?:[\s(])',
                    r'(?:\b[a-zA-Z0-9$]{2}\s*&&\s*[a-zA-Z0-9$]{2}\.set\([^,]+\s*,\s*)([\w$]+)(?:[\s(])',
                    r'(?:\bm\.set\([^,]+\s*,\s*)([\w$]+)'
                ]
                
                for pattern in function_patterns:
                    regex = re.compile(pattern)
                    function_match = regex.search(js)
                    if function_match:
                        return function_match.group(1)
                
                raise Exception("Could not find initial function name")
        
        cipher.get_initial_function_name = new_method
        
        return True
    except Exception as e:
        print(f"Failed to patch pytube: {str(e)}")
        return False

# Try to apply patches
patch_pytube()

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
        # Apply patches again for this request
        patch_pytube()
        
        # Generate a unique ID for this download
        unique_id = str(uuid.uuid4())
        output_path = os.path.join(DOWNLOAD_FOLDER, unique_id)
        
        # Create the output directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        # Create YouTube object with various retries
        attempt = 0
        max_attempts = 3
        youtube_object = None
        
        while attempt < max_attempts:
            try:
                youtube_object = YouTube(youtube_url)
                break
            except Exception as e:
                attempt += 1
                if attempt >= max_attempts:
                    raise e
                time.sleep(1)  # Wait before retrying
        
        if not youtube_object:
            return jsonify({'error': 'Failed to process YouTube URL'}), 400
            
        video_title = youtube_object.title
        
        if output_format == 'mp3':
            # Try multiple audio stream options
            audio_stream = None
            # First try audio only
            try:
                audio_stream = youtube_object.streams.filter(only_audio=True).first()
            except:
                pass
            
            # If that fails, try any audio
            if not audio_stream:
                try:
                    audio_stream = youtube_object.streams.filter(progressive=True).first()
                except:
                    pass
                    
            if not audio_stream:
                return jsonify({'error': 'No audio stream found for this video'}), 400
                
            downloaded_file = audio_stream.download(output_path=output_path)
            
            # Convert to MP3 (just rename the file)
            base, _ = os.path.splitext(downloaded_file)
            mp3_file = base + '.mp3'
            os.rename(downloaded_file, mp3_file)
            
            file_path = mp3_file
            file_name = f"{video_title}.mp3"
        else:  # mp4
            # Try multiple video options
            video_stream = None
            
            try:
                # Try progressive streams first (audio and video together)
                video_stream = youtube_object.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            except:
                pass
                
            if not video_stream:
                try:
                    # Try any mp4 stream
                    video_stream = youtube_object.streams.filter(file_extension='mp4').first()
                except:
                    pass
                
            if not video_stream:
                try:
                    # Try any video stream
                    video_stream = youtube_object.streams.first()
                except:
                    pass
                    
            if not video_stream:
                return jsonify({'error': 'No video stream found for this video'}), 400
                
            downloaded_file = video_stream.download(output_path=output_path)
            
            file_path = downloaded_file
            file_name = f"{video_title}.mp4"
        
        # Create a download token
        download_token = str(uuid.uuid4())
        
        # Store the file info
        app.config[download_token] = {
            'file_path': file_path,
            'file_name': file_name,
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
