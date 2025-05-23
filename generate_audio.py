#!/usr/bin/env python3
"""
Podcast Audio Generator
Converts text-based podcast scripts to audio using Google Text-to-Speech
"""

import os
import tempfile
import re
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

# Google TTS imports (optional)
try:
    from google.cloud import texttospeech
    HAS_GOOGLE_TTS = True
except ImportError:
    HAS_GOOGLE_TTS = False

# Audio processing imports (optional)
try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False

class PodcastAudioGenerator:
    def __init__(self):
        self.temp_dir = None
        self.tts_client = None
        
        # Voice configuration for HOST and GUEST
        self.voice_config = {
            "HOST": {
                "name": "en-US-Wavenet-D",  # Male voice for host
                "language_code": "en-US",
                "gender": "MALE"
            },
            "GUEST": {
                "name": "en-US-Wavenet-F",  # Female voice for guest
                "language_code": "en-US", 
                "gender": "FEMALE"
            }
        }

    def initialize_tts_client(self) -> bool:
        """Initialize the TTS client after credentials are set up."""
        if not HAS_GOOGLE_TTS:
            print("Error: google-cloud-texttospeech package not installed.")
            print("Please install: pip install google-cloud-texttospeech")
            return False
            
        try:
            self.tts_client = texttospeech.TextToSpeechClient()
            print("Google TTS client initialized successfully")
            return True
        except Exception as e:
            print(f"Error: Could not initialize Google TTS client: {e}")
            print("Please check your Google Cloud credentials.")
            self.tts_client = None
            return False

    def parse_podcast_script(self, script_path: str) -> List[Dict]:
        """Parse the podcast script to extract HOST and GUEST segments."""
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        segments = []
        
        # Split by **HOST:** and **GUEST:** markers
        pattern = r'\*\*(HOST|GUEST):\*\*\s*(.*?)(?=\*\*(HOST|GUEST):\*\*|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            speaker = match[0]
            text = match[1].strip()
            
            # Clean up text - remove markdown headers and extra whitespace
            text = re.sub(r'^#+\s.*$', '', text, flags=re.MULTILINE)  # Remove headers
            text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)   # Remove dividers
            text = re.sub(r'\s+', ' ', text)                          # Normalize whitespace
            text = text.strip()
            
            if text and len(text) > 10:  # Only include substantial content
                segments.append({
                    "speaker": speaker,
                    "text": text
                })
        
        return segments

    def generate_audio_segment(self, text: str, voice_config: Dict, output_path: str) -> bool:
        """Generate audio for a single text segment using Google TTS."""
        if not self.tts_client:
            print("Error: Google TTS client not available")
            return False
        
        try:
            # Create synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Create voice selection
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_config["language_code"],
                name=voice_config["name"]
            )
            
            # Create audio config
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.95,  # Slightly slower for clarity
                pitch=0.0,
                volume_gain_db=0.0
            )
            
            # Perform TTS request
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Write audio to file
            with open(output_path, 'wb') as f:
                f.write(response.audio_content)
            
            return True
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            return False

    def generate_podcast_audio(self, script_path: str, output_path: str) -> str:
        """Generate audio podcast from the script file."""
        if not HAS_GOOGLE_TTS:
            print("Error: google-cloud-texttospeech package not installed.")
            print("Please install: pip install google-cloud-texttospeech")
            return None
            
        if not HAS_PYDUB:
            print("Error: pydub is not available.")
            print("Please install: pip install pydub")
            return None

        # Try to initialize TTS client now that credentials should be set up
        if not self.tts_client:
            if not self.initialize_tts_client():
                return None
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp())
        print(f"Working directory: {self.temp_dir}")
        
        # Parse the script
        print("Parsing podcast script...")
        segments = self.parse_podcast_script(script_path)
        print(f"Found {len(segments)} segments")
        
        if not segments:
            print("No segments found in script!")
            return None
        
        # Process each segment
        temp_files = []
        max_chars = 5000  # Google TTS limit
        
        for i, segment in enumerate(tqdm(segments, desc="Generating audio")):
            speaker = segment["speaker"]
            text = segment["text"]
            
            voice_config = self.voice_config.get(speaker)
            if not voice_config:
                print(f"Warning: No voice configured for speaker '{speaker}', skipping")
                continue
            
            print(f"\nProcessing {speaker}: {len(text)} characters")
            
            # Split long text into chunks
            if len(text) > max_chars:
                sentences = re.split(r'(?<=[.!?])\s+', text)
                chunks = []
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) < max_chars:
                        current_chunk += " " + sentence if current_chunk else sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
                
                if current_chunk:
                    chunks.append(current_chunk)
            else:
                chunks = [text]
            
            # Generate audio for each chunk
            for j, chunk in enumerate(chunks):
                output_file = self.temp_dir / f"segment_{i:04d}_{j:02d}.mp3"
                
                success = self.generate_audio_segment(chunk, voice_config, str(output_file))
                if success and output_file.exists():
                    temp_files.append(output_file)
                    print(f"  Generated chunk {j+1}/{len(chunks)}")
                else:
                    print(f"  Failed to generate chunk {j+1}/{len(chunks)}")
        
        # Combine all audio files
        print(f"\nCombining {len(temp_files)} audio segments...")
        combined = AudioSegment.empty()
        
        for temp_file in tqdm(temp_files, desc="Combining segments"):
            try:
                segment = AudioSegment.from_mp3(str(temp_file))
                combined += segment
                # Add pause between segments
                combined += AudioSegment.silent(duration=500)  # 0.5 second pause
            except Exception as e:
                print(f"Error combining file {temp_file}: {e}")
        
        # Export final podcast
        print(f"Exporting podcast to {output_path}...")
        combined.export(output_path, format="mp3", bitrate="192k")
        
        # Clean up temp files
        for temp_file in temp_files:
            try:
                temp_file.unlink()
            except:
                pass
        
        # Remove temp directory
        try:
            self.temp_dir.rmdir()
        except:
            pass
        
        duration_minutes = len(combined) / 1000 / 60
        print(f"\nPodcast generated successfully!")
        print(f"File: {output_path}")
        print(f"Duration: {duration_minutes:.1f} minutes")
        
        return output_path

def setup_google_credentials(credentials_path: str = None):
    """Set up Google Cloud credentials for TTS."""
    if credentials_path and os.path.exists(credentials_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(credentials_path)
        print(f"Using Google Cloud credentials from: {os.path.abspath(credentials_path)}")
        return True
    else:
        print("Google Cloud credentials file not found or not provided")
        print("Set GOOGLE_APPLICATION_CREDENTIALS environment variable or provide credentials file")
        return False

def get_script_files():
    """Get list of available podcast script files."""
    script_files = []
    for file in Path('.').glob('*.txt'):
        if 'script' in file.name.lower():
            script_files.append(file.name)
    return script_files

def main():
    print("="*60)
    print("PODCAST AUDIO GENERATOR")
    print("="*60)
    
    # Check for Google Cloud credentials
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("\nGoogle Cloud credentials not found in environment.")
        creds_file = input("Enter path to Google Cloud credentials JSON file (or press Enter to skip): ").strip()
        if creds_file:
            if not setup_google_credentials(creds_file):
                print("Failed to set up credentials. Exiting.")
                return
        else:
            print("No credentials provided. Make sure GOOGLE_APPLICATION_CREDENTIALS is set.")
            return
    else:
        print(f"Using credentials from: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")
    
    # Get available script files
    script_files = get_script_files()
    
    if script_files:
        print(f"\nFound {len(script_files)} script files:")
        for i, file in enumerate(script_files, 1):
            print(f"  {i}. {file}")
        
        while True:
            try:
                choice = input(f"\nSelect script file (1-{len(script_files)}) or enter custom path: ").strip()
                
                # Check if it's a number (selecting from list)
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(script_files):
                        script_path = script_files[index]
                        break
                    else:
                        print("Invalid selection. Please try again.")
                        continue
                except ValueError:
                    # It's a custom path
                    if os.path.exists(choice):
                        script_path = choice
                        break
                    else:
                        print(f"File '{choice}' not found. Please try again.")
                        continue
            except KeyboardInterrupt:
                print("\nExiting...")
                return
    else:
        # No script files found, ask for path
        script_path = input("\nEnter path to podcast script file: ").strip()
        if not os.path.exists(script_path):
            print(f"Error: Script file '{script_path}' not found.")
            return
    
    # Get output filename
    default_output = script_path.replace('.txt', '_podcast.mp3').replace('_script', '')
    output_path = input(f"\nEnter output audio filename [{default_output}]: ").strip()
    if not output_path:
        output_path = default_output
    
    # Generate the audio
    print(f"\nInput script: {script_path}")
    print(f"Output audio: {output_path}")
    print("\n" + "="*50)
    print("GENERATING AUDIO PODCAST")
    print("="*50)
    
    generator = PodcastAudioGenerator()
    
    try:
        audio_file = generator.generate_podcast_audio(script_path, output_path)
        if audio_file:
            print(f"\n🎉 Audio podcast generated successfully: {audio_file}")
        else:
            print("\n❌ Failed to generate audio podcast")
    except Exception as e:
        print(f"\n❌ Error generating audio: {e}")

if __name__ == "__main__":
    main() 