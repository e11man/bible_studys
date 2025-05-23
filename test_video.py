#!/usr/bin/env python3
"""
Test script for video generation functionality
"""

import os
import tempfile
from generate_video import PodcastVideoGenerator
from PIL import Image

def create_test_image(filename="test_image.jpg"):
    """Create a simple test image."""
    # Create a simple colored image
    img = Image.new('RGB', (1280, 720), color=(70, 130, 180))  # Steel blue
    img.save(filename, 'JPEG')
    return filename

def create_test_audio(filename="test_audio.mp3"):
    """Create a simple test audio file (just return existing if available)."""
    # For this test, we'll assume you have an existing audio file
    # or you can create a silent one using moviepy
    try:
        from moviepy import AudioClip
        
        def make_frame(t):
            return [0.1 * (440 * 2 * 3.14159 * t) % 1]  # Simple sine wave
        
        audio = AudioClip(make_frame, duration=5, fps=22050)  # 5 second test audio
        audio.write_audiofile(filename, verbose=False, logger=None)
        audio.close()
        return filename
    except:
        print("Could not create test audio - you'll need an existing MP3 file")
        return None

def test_video_generation():
    """Test the video generation functionality."""
    print("Testing video generation...")
    
    generator = PodcastVideoGenerator()
    
    # Create test files
    print("Creating test image...")
    image_path = create_test_image()
    
    print("Creating test audio...")
    audio_path = create_test_audio()
    
    if not audio_path:
        print("Skipping test - no audio file available")
        return False
    
    output_path = "test_output_video.mp4"
    
    def progress_callback(progress, message):
        print(f"[{progress:3d}%] {message}")
    
    try:
        print("\nStarting video generation test...")
        success = generator.generate_video(
            audio_path,
            image_path,
            output_path,
            "Test Video",
            progress_callback
        )
        
        if success and os.path.exists(output_path):
            print(f"\n✅ Video generation test successful!")
            print(f"Output file: {output_path}")
            
            # Show file info
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"File size: {file_size:.2f} MB")
            
            return True
        else:
            print("\n❌ Video generation test failed!")
            return False
            
    except Exception as e:
        print(f"\n❌ Video generation test failed with error: {e}")
        return False
    
    finally:
        # Cleanup
        for file in [image_path, audio_path]:
            if file and os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass

if __name__ == "__main__":
    test_video_generation() 