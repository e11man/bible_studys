#!/usr/bin/env python3
"""
Flask Web GUI for Bible Podcast Generator - SINGLE FILE VERSION
Provides a user-friendly interface for generating Bible podcast scripts and audio
Save this file as 'app.py' and run with: python app.py
"""

import os
import json
import tempfile
import threading
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import uuid

# Import your existing classes
from bible import PodcastScriptGenerator
try:
    from generate_audio import PodcastAudioGenerator
    HAS_AUDIO_GENERATION = True
except ImportError:
    HAS_AUDIO_GENERATION = False

app = Flask(__name__)
app.secret_key = 'bible-podcast-generator-secret-key-change-this'  # Change this to a random secret key

# Global dictionary to track job progress
job_progress = {}

# Default Google Cloud credentials path
DEFAULT_CREDENTIALS_PATH = 'majestic-bounty-455918-f1-fb3e5e5fef3d.json'



class WebPodcastGenerator:
    def __init__(self):
        self.generator = PodcastScriptGenerator()
        self.audio_generator = PodcastAudioGenerator() if HAS_AUDIO_GENERATION else None
        
    def get_available_versions(self):
        """Get list of available Bible versions."""
        return self.generator.get_available_versions()
    
    def validate_passage(self, version, passage):
        """Validate Bible passage."""
        if not self.generator.load_bible_version(version):
            return False, f"Could not load Bible version: {version}"
        
        if not self.generator.validate_passage(passage):
            return False, f"Invalid passage: {passage}"
        
        return True, "Valid passage"
    
    def generate_script(self, job_id, version, passage, commentary_text=None, output_dir="output"):
        """Generate podcast script with progress tracking."""
        try:
            # Update progress
            job_progress[job_id] = {"status": "initializing", "progress": 0, "message": "Loading Bible version..."}
            
            # Load Bible version
            if not self.generator.load_bible_version(version):
                job_progress[job_id] = {"status": "error", "progress": 0, "message": f"Failed to load Bible version: {version}"}
                return
            
            job_progress[job_id] = {"status": "processing", "progress": 20, "message": "Validating passage..."}
            
            # Validate passage
            if not self.generator.validate_passage(passage):
                job_progress[job_id] = {"status": "error", "progress": 0, "message": f"Invalid passage: {passage}"}
                return
            
            job_progress[job_id] = {"status": "processing", "progress": 40, "message": "Generating podcast script..."}
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            safe_passage = passage.replace(' ', '_').replace(':', '-')
            timestamp = int(time.time())
            
            if commentary_text and commentary_text.strip():
                # Commentary-based generation
                script_filename = os.path.join(output_dir, f"commentary_{safe_passage}_{version}_{timestamp}.txt")
                job_progress[job_id] = {"status": "processing", "progress": 60, "message": "Processing commentary..."}
                
                # Write commentary to temporary file
                temp_commentary = os.path.join(output_dir, f"temp_commentary_{timestamp}.txt")
                with open(temp_commentary, 'w', encoding='utf-8') as f:
                    f.write(commentary_text)
                
                job_progress[job_id] = {"status": "processing", "progress": 80, "message": "Generating commentary-based script..."}
                output_file = self.generator.generate_commentary_based_script(commentary_text, script_filename)
                
                # Clean up temp file
                try:
                    os.remove(temp_commentary)
                except:
                    pass
            else:
                # Direct Bible reading
                script_filename = os.path.join(output_dir, f"{safe_passage}_{version}_{timestamp}_script.txt")
                job_progress[job_id] = {"status": "processing", "progress": 60, "message": "Reading Bible passages..."}
                output_file = self.generator.generate_podcast_script_from_passage(passage, script_filename)
            
            job_progress[job_id] = {"status": "processing", "progress": 95, "message": "Finalizing script..."}
            
            if output_file and os.path.exists(output_file):
                print(f"✓ Script generation completed: {output_file}")  # Debug log
                job_progress[job_id] = {
                    "status": "completed", 
                    "progress": 100, 
                    "message": "Script generated successfully!",
                    "output_file": output_file,
                    "filename": os.path.basename(output_file)
                }
                print(f"✓ Progress updated to completed for job {job_id}")  # Debug log
            else:
                print(f"❌ Script generation failed: {output_file}")  # Debug log
                job_progress[job_id] = {"status": "error", "progress": 0, "message": "Failed to generate script"}
                
        except Exception as e:
            job_progress[job_id] = {"status": "error", "progress": 0, "message": f"Error: {str(e)}"}
    
    def generate_audio(self, job_id, script_path, output_dir="output"):
        """Generate audio from script with progress tracking."""
        try:
            if not HAS_AUDIO_GENERATION:
                job_progress[job_id] = {"status": "error", "progress": 0, "message": "Audio generation not available - missing dependencies"}
                return
            
            job_progress[job_id] = {"status": "processing", "progress": 10, "message": "Initializing audio generation..."}
            
            # Check Google Cloud credentials
            if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
                job_progress[job_id] = {"status": "error", "progress": 0, "message": "Google Cloud credentials not configured"}
                return
            
            job_progress[job_id] = {"status": "processing", "progress": 20, "message": "Setting up TTS client..."}
            
            # Initialize TTS client
            if not self.audio_generator.initialize_tts_client():
                job_progress[job_id] = {"status": "error", "progress": 0, "message": "Failed to initialize TTS client"}
                return
            
            job_progress[job_id] = {"status": "processing", "progress": 30, "message": "Parsing script..."}
            
            # Generate output filename
            script_name = Path(script_path).stem
            audio_filename = os.path.join(output_dir, f"{script_name}_podcast.mp3")
            
            job_progress[job_id] = {"status": "processing", "progress": 40, "message": "Generating audio (this may take several minutes)..."}
            
            # Generate audio
            output_file = self.audio_generator.generate_podcast_audio(script_path, audio_filename)
            
            if output_file and os.path.exists(output_file):
                job_progress[job_id] = {
                    "status": "completed", 
                    "progress": 100, 
                    "message": "Audio generated successfully!",
                    "output_file": output_file,
                    "filename": os.path.basename(output_file)
                }
            else:
                job_progress[job_id] = {"status": "error", "progress": 0, "message": "Failed to generate audio"}
                
        except Exception as e:
            job_progress[job_id] = {"status": "error", "progress": 0, "message": f"Error: {str(e)}"}

# Initialize the generator
web_generator = WebPodcastGenerator()

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/api/versions')
def get_versions():
    """Get available Bible versions."""
    versions = web_generator.get_available_versions()
    return jsonify({"versions": versions})

@app.route('/api/validate', methods=['POST'])
def validate_passage():
    """Validate Bible passage."""
    data = request.json
    version = data.get('version')
    passage = data.get('passage')
    
    is_valid, message = web_generator.validate_passage(version, passage)
    return jsonify({"valid": is_valid, "message": message})

@app.route('/api/generate', methods=['POST'])
def generate_script():
    """Generate podcast script."""
    data = request.json
    version = data.get('version')
    passage = data.get('passage')
    commentary = data.get('commentary', '')
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Create output directory
    output_dir = os.path.join("output", job_id)
    os.makedirs(output_dir, exist_ok=True)
    
    # Start generation in background thread
    thread = threading.Thread(
        target=web_generator.generate_script, 
        args=(job_id, version, passage, commentary, output_dir)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"job_id": job_id})

@app.route('/api/generate-audio', methods=['POST'])
def generate_audio():
    """Generate audio from script."""
    data = request.json
    script_path = data.get('script_path')
    
    if not script_path or not os.path.exists(script_path):
        return jsonify({"error": "Script file not found"}), 400
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Get output directory from script path
    output_dir = os.path.dirname(script_path)
    
    # Start audio generation in background thread
    thread = threading.Thread(
        target=web_generator.generate_audio, 
        args=(job_id, script_path, output_dir)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"job_id": job_id})

@app.route('/api/progress/<job_id>')
def get_progress(job_id):
    """Get job progress."""
    progress = job_progress.get(job_id, {"status": "not_found", "progress": 0, "message": "Job not found"})
    print(f"📊 Progress check for {job_id}: {progress.get('status', 'unknown')} - {progress.get('progress', 0)}%")  # Debug log
    return jsonify(progress)

@app.route('/api/download/<path:filename>')
def download_file(filename):
    """Download generated file."""
    # Security: only allow downloads from output directory
    if not filename.startswith('output/'):
        return "Access denied", 403
    
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True, download_name=os.path.basename(filename))
    else:
        return "File not found", 404

@app.route('/api/config/audio', methods=['GET', 'POST'])
def audio_config():
    """Configure audio generation settings."""
    if request.method == 'GET':
        # Set default credentials if not already set
        if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = DEFAULT_CREDENTIALS_PATH
            
        return jsonify({
            "has_audio_generation": HAS_AUDIO_GENERATION,
            "has_credentials": bool(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')),
            "credentials_path": os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', DEFAULT_CREDENTIALS_PATH)
        })
    
    elif request.method == 'POST':
        data = request.json
        credentials_path = data.get('credentials_path', DEFAULT_CREDENTIALS_PATH)
        
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.abspath(credentials_path)
            return jsonify({"success": True, "message": "Credentials path set successfully"})
        else:
            return jsonify({"success": False, "message": "Credentials file not found"}), 400

if __name__ == '__main__':
    # Create output directory
    os.makedirs('output', exist_ok=True)
    
    print("="*60)
    print("BIBLE PODCAST GENERATOR - WEB GUI")
    print("="*60)
    print(f"Available Bible versions: {web_generator.get_available_versions()}")
    print(f"Audio generation available: {HAS_AUDIO_GENERATION}")
    print(f"Google Cloud credentials: {'✓' if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') else '✗'}")
    print("\nStarting Flask server...")
    print("Access the application at: http://localhost:5001")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5001)