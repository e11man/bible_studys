#!/usr/bin/env python3
"""
Video Generator for Bible Podcast
Converts MP3 audio files to MP4 videos with static background images for YouTube upload
"""

import os
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm

# Video processing imports (optional)
try:
    from moviepy import AudioFileClip, ImageClip, CompositeVideoClip
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False

# Image processing imports (optional)
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

class PodcastVideoGenerator:
    def __init__(self):
        self.temp_dir = None
        
        # Video configuration for YouTube optimization
        self.video_config = {
            "resolution": (1280, 720),  # 720p for faster processing
            "fps": 24,  # Lower FPS for faster rendering
            "audio_bitrate": "128k",  # Good quality audio
            "video_codec": "libx264",
            "audio_codec": "aac",
            "preset": "ultrafast",  # Fastest encoding preset
            "crf": 28  # Higher CRF for smaller file size
        }

    def get_available_audio_files(self, directory: str = "output") -> List[Dict]:
        """Get list of available MP3 files for video conversion."""
        audio_files = []
        
        if not os.path.exists(directory):
            return audio_files
        
        # Recursively search for MP3 files in output directory
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.mp3'):
                    full_path = os.path.join(root, file)
                    try:
                        # Get file info
                        stat = os.stat(full_path)
                        file_size = stat.st_size
                        
                        # Try to get audio duration
                        duration = None
                        if HAS_MOVIEPY:
                            try:
                                with AudioFileClip(full_path) as audio:
                                    duration = audio.duration
                            except:
                                pass
                        
                        audio_files.append({
                            "filename": file,
                            "path": full_path,
                            "relative_path": os.path.relpath(full_path, directory),
                            "size": file_size,
                            "size_mb": round(file_size / (1024 * 1024), 2),
                            "duration": duration,
                            "duration_str": f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "Unknown"
                        })
                    except Exception as e:
                        print(f"Error processing {full_path}: {e}")
        
        # Also search in current directory for any MP3 files
        try:
            for file in os.listdir('.'):
                if file.lower().endswith('.mp3'):
                    full_path = os.path.abspath(file)
                    try:
                        stat = os.stat(full_path)
                        file_size = stat.st_size
                        
                        duration = None
                        if HAS_MOVIEPY:
                            try:
                                with AudioFileClip(full_path) as audio:
                                    duration = audio.duration
                            except:
                                pass
                        
                        # Avoid duplicates
                        if not any(af["path"] == full_path for af in audio_files):
                            audio_files.append({
                                "filename": file,
                                "path": full_path,
                                "relative_path": file,
                                "size": file_size,
                                "size_mb": round(file_size / (1024 * 1024), 2),
                                "duration": duration,
                                "duration_str": f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else "Unknown"
                            })
                    except Exception as e:
                        print(f"Error processing {full_path}: {e}")
        except Exception as e:
            print(f"Error scanning current directory: {e}")
        
        # Sort by creation time (newest first)
        audio_files.sort(key=lambda x: os.path.getctime(x["path"]), reverse=True)
        return audio_files

    def validate_image(self, image_path: str) -> tuple:
        """Validate background image file."""
        if not os.path.exists(image_path):
            return False, "Image file does not exist"
        
        if not HAS_PIL:
            return False, "PIL (Pillow) library not available for image processing"
        
        try:
            with Image.open(image_path) as img:
                # Check if it's a valid image
                img.verify()
                
                # Reopen for getting info (verify() closes the file)
                with Image.open(image_path) as img:
                    width, height = img.size
                    format_name = img.format
                    
                    # Check file size (limit to 50MB)
                    file_size = os.path.getsize(image_path)
                    if file_size > 50 * 1024 * 1024:
                        return False, "Image file too large (max 50MB)"
                    
                    return True, f"Valid image: {width}x{height}, {format_name} format"
                    
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"

    def prepare_background_image(self, image_path: str, target_resolution: tuple) -> str:
        """Prepare background image by resizing and optimizing for video."""
        if not HAS_PIL:
            return image_path  # Return original if PIL not available
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to target resolution while maintaining aspect ratio
                img.thumbnail(target_resolution, Image.Resampling.LANCZOS)
                
                # Create new image with exact target dimensions and center the resized image
                background = Image.new('RGB', target_resolution, (0, 0, 0))  # Black background
                
                # Calculate position to center the image
                x = (target_resolution[0] - img.size[0]) // 2
                y = (target_resolution[1] - img.size[1]) // 2
                
                background.paste(img, (x, y))
                
                # Save optimized image
                optimized_path = image_path.replace(Path(image_path).suffix, '_optimized.jpg')
                background.save(optimized_path, 'JPEG', quality=85, optimize=True)
                
                return optimized_path
                
        except Exception as e:
            print(f"Error optimizing image: {e}")
            return image_path  # Return original on error

    def generate_video(self, audio_path: str, image_path: str, output_path: str, 
                      title: str = "", progress_callback=None) -> bool:
        """Generate MP4 video from MP3 audio and background image."""
        
        if not HAS_MOVIEPY:
            raise Exception("moviepy library not available. Install with: pip install moviepy")
        
        if not HAS_PIL:
            raise Exception("PIL library not available. Install with: pip install Pillow")
        
        try:
            # Update progress
            if progress_callback:
                progress_callback(10, "Loading audio file...")
            
            # Load audio
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            if progress_callback:
                progress_callback(20, "Preparing background image...")
            
            # Prepare and optimize background image
            optimized_image_path = self.prepare_background_image(image_path, self.video_config["resolution"])
            
            if progress_callback:
                progress_callback(30, "Creating video clip...")
            
            # Create image clip with duration matching audio
            image_clip = ImageClip(optimized_image_path, duration=duration)
            
            if progress_callback:
                progress_callback(40, "Combining audio and video...")
            
            # Combine audio and video using with_audio method
            video_clip = image_clip.with_audio(audio_clip)
            
            if progress_callback:
                progress_callback(50, "Starting video export (this may take a while)...")
            
            # Export video with simplified settings for better compatibility
            video_clip.write_videofile(
                output_path,
                fps=self.video_config["fps"],
                codec='libx264',
                audio_codec='aac'
            )
            
            if progress_callback:
                progress_callback(90, "Cleaning up temporary files...")
            
            # Clean up
            audio_clip.close()
            image_clip.close()
            video_clip.close()
            
            # Remove optimized image if it was created
            if optimized_image_path != image_path and os.path.exists(optimized_image_path):
                try:
                    os.remove(optimized_image_path)
                except:
                    pass
            
            if progress_callback:
                progress_callback(100, "Video generation completed!")
            
            return True
            
        except Exception as e:
            print(f"Error generating video: {e}")
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            return False

    def get_video_info(self, video_path: str) -> Dict:
        """Get information about generated video file."""
        if not os.path.exists(video_path):
            return {}
        
        try:
            stat = os.stat(video_path)
            file_size = stat.st_size
            
            info = {
                "filename": os.path.basename(video_path),
                "path": video_path,
                "size": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "duration": None,
                "duration_str": "Unknown"
            }
            
            # Try to get video duration
            if HAS_MOVIEPY:
                try:
                    with AudioFileClip(video_path) as audio:
                        duration = audio.duration
                        info["duration"] = duration
                        info["duration_str"] = f"{int(duration // 60)}:{int(duration % 60):02d}"
                except:
                    pass
            
            return info
            
        except Exception as e:
            print(f"Error getting video info: {e}")
            return {}

def main():
    """Command line interface for video generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate MP4 video from podcast audio")
    parser.add_argument("--audio", required=True, help="Path to MP3 audio file")
    parser.add_argument("--image", required=True, help="Path to background image")
    parser.add_argument("--output", help="Output MP4 file path")
    parser.add_argument("--title", help="Video title")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.audio):
        print(f"Error: Audio file '{args.audio}' not found")
        return
    
    if not os.path.exists(args.image):
        print(f"Error: Image file '{args.image}' not found")
        return
    
    # Generate output filename if not provided
    if not args.output:
        audio_name = Path(args.audio).stem
        args.output = f"{audio_name}_video.mp4"
    
    print("="*60)
    print("BIBLE PODCAST VIDEO GENERATOR")
    print("="*60)
    print(f"Audio: {args.audio}")
    print(f"Image: {args.image}")
    print(f"Output: {args.output}")
    print("="*60)
    
    generator = PodcastVideoGenerator()
    
    # Validate image
    is_valid, message = generator.validate_image(args.image)
    print(f"Image validation: {message}")
    
    if not is_valid:
        print("Aborting due to image validation failure.")
        return
    
    # Progress callback
    def progress_callback(progress, message):
        print(f"[{progress:3d}%] {message}")
    
    # Generate video
    success = generator.generate_video(
        args.audio, 
        args.image, 
        args.output,
        args.title or "",
        progress_callback
    )
    
    if success:
        print(f"\n🎉 Video generated successfully: {args.output}")
        
        # Show video info
        info = generator.get_video_info(args.output)
        if info:
            print(f"Duration: {info['duration_str']}")
            print(f"File size: {info['size_mb']} MB")
    else:
        print("\n❌ Video generation failed")

if __name__ == "__main__":
    main()