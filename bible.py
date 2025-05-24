import requests
import re
import time
import os
import json
from pathlib import Path
from typing import List, Tuple, Dict
from tqdm import tqdm

class PodcastScriptGenerator:
    def __init__(self):
        # Bible data will be loaded dynamically
        self.bible_data = None
        self.bible_version = None
        self.bible_books = []
        
        # Initialize TTS capabilities
        self.temp_dir = None
        self.tts_client = None
        # Don't initialize TTS client here - do it later when credentials are available
        
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

    def load_bible_version(self, version: str) -> bool:
        """Load Bible data from JSON file."""
        version_upper = version.upper()
        json_file = f"bibles/{version_upper}_bible.json"
        
        if not os.path.exists(json_file):
            print(f"Error: Bible file '{json_file}' not found.")
            return False
        
        try:
            print(f"Loading {version_upper} Bible data...")
            with open(json_file, 'r', encoding='utf-8') as f:
                self.bible_data = json.load(f)
            
            self.bible_version = version_upper
            self.bible_books = list(self.bible_data.keys())
            print(f"Successfully loaded {version_upper} with {len(self.bible_books)} books")
            return True
            
        except Exception as e:
            print(f"Error loading Bible data: {e}")
            return False

    def get_available_versions(self) -> List[str]:
        """Get list of available Bible versions."""
        bibles_dir = Path("bibles")
        if not bibles_dir.exists():
            return []
        
        versions = []
        for file in bibles_dir.glob("*_bible.json"):
            version = file.stem.replace("_bible", "")
            versions.append(version)
        
        return versions

    def prompt_user_selection(self) -> Tuple[str, str]:
        """Prompt user for Bible version and passage selection."""
        # Get available versions
        available_versions = self.get_available_versions()
        
        if not available_versions:
            print("Error: No Bible JSON files found in 'bibles' directory.")
            print("Expected files like: ESV_bible.json, NKJV_bible.json")
            return None, None
        
        # Prompt for Bible version
        print("\nAvailable Bible versions:")
        for i, version in enumerate(available_versions, 1):
            print(f"  {i}. {version}")
        
        while True:
            try:
                choice = input(f"\nSelect Bible version (1-{len(available_versions)}): ").strip()
                index = int(choice) - 1
                if 0 <= index < len(available_versions):
                    selected_version = available_versions[index]
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a number.")
        
        # Load the selected version
        if not self.load_bible_version(selected_version):
            return None, None
        
        # Show available books
        print(f"\nAvailable books in {selected_version}:")
        books_per_line = 6
        for i in range(0, len(self.bible_books), books_per_line):
            book_line = self.bible_books[i:i+books_per_line]
            print("  " + ", ".join(book_line))
        
        # Prompt for passage
        print(f"\nEnter passage in format: 'BookName StartChapter-EndChapter'")
        print("Examples:")
        print("  Genesis 1-3")
        print("  Job 35-42") 
        print("  Psalms 1-5")
        print("  Matthew 5-7")
        
        while True:
            passage = input("\nEnter passage: ").strip()
            if self.validate_passage(passage):
                return selected_version, passage
            else:
                print("Invalid passage format. Please try again.")

    def validate_passage(self, passage: str) -> bool:
        """Validate the passage format and check if it exists in the Bible data."""
        try:
            # Parse passage like "Genesis 1-3"
            parts = passage.split()
            if len(parts) < 2:
                print("Error: Please include both book name and chapter range.")
                return False
            
            # Handle multi-word book names
            if len(parts) > 2:
                book_name = " ".join(parts[:-1])
                chapter_range = parts[-1]
            else:
                book_name, chapter_range = parts
            
            # Check if book exists
            if book_name not in self.bible_data:
                print(f"Error: Book '{book_name}' not found.")
                print(f"Available books: {', '.join(self.bible_books[:10])}...")
                return False
            
            # Parse chapter range
            if '-' in chapter_range:
                start_ch, end_ch = chapter_range.split('-')
                start_chapter = int(start_ch)
                end_chapter = int(end_ch)
            else:
                start_chapter = end_chapter = int(chapter_range)
            
            # Check if chapters exist
            book_data = self.bible_data[book_name]
            available_chapters = [int(ch) for ch in book_data.keys()]
            
            if start_chapter not in available_chapters:
                print(f"Error: Chapter {start_chapter} not found in {book_name}.")
                print(f"Available chapters: {min(available_chapters)}-{max(available_chapters)}")
                return False
            
            if end_chapter not in available_chapters:
                print(f"Error: Chapter {end_chapter} not found in {book_name}.")
                print(f"Available chapters: {min(available_chapters)}-{max(available_chapters)}")
                return False
            
            if start_chapter > end_chapter:
                print("Error: Start chapter cannot be greater than end chapter.")
                return False
            
            return True
            
        except ValueError:
            print("Error: Invalid chapter number format.")
            return False
        except Exception as e:
            print(f"Error validating passage: {e}")
            return False

    def parse_passage_input(self, passage: str) -> Dict:
        """Parse user passage input like 'Genesis 1-3' into components."""
        parts = passage.split()
        
        # Handle multi-word book names
        if len(parts) > 2:
            book_name = " ".join(parts[:-1])
            chapter_range = parts[-1]
        else:
            book_name, chapter_range = parts
        
        # Parse chapter range
        if '-' in chapter_range:
            start_ch, end_ch = chapter_range.split('-')
            start_chapter = int(start_ch)
            end_chapter = int(end_ch)
        else:
            start_chapter = end_chapter = int(chapter_range)
        
        return {
            'book': book_name,
            'start_chapter': start_chapter,
            'end_chapter': end_chapter
        }

    def get_chapter_text(self, book: str, chapter: int) -> str:
        """Get all verses from a chapter as continuous text."""
        if not self.bible_data or book not in self.bible_data:
            return f"[Book '{book}' not available]"
        
        chapter_str = str(chapter)
        if chapter_str not in self.bible_data[book]:
            return f"[Chapter {chapter} not available in {book}]"
        
        verses = self.bible_data[book][chapter_str]
        verse_texts = []
        
        # Get all verses in order
        for verse_num in sorted(verses.keys(), key=int):
            verse_text = verses[verse_num]
            # Clean up Unicode characters
            verse_text = verse_text.replace('\u201c', '"').replace('\u201d', '"')
            verse_texts.append(verse_text)
        
        return ' '.join(verse_texts)

    def extract_verse_references(self, commentary_text: str) -> List[Tuple[str, str, str]]:
        """
        Extract verse references and their corresponding commentary sections.
        Returns list of tuples: (verse_reference, section_title, commentary)
        """
        sections = []
        
        # Split by sections looking for pattern: "Section X: BookName Chapter:Verse-Verse - Title"
        lines = commentary_text.split('\n')
        current_section = None
        current_commentary = []
        
        for line in lines:
            line = line.strip()
            
            # Check if this is a section header - now handles any book name
            # Pattern matches: "Section 1: Genesis 1:1-5 - Title" or "Section 1: 1 Chronicles 2:1-10 - Title"
            section_match = re.match(r'Section \d+: ((?:\d+\s+)?[A-Za-z]+(?:\s+[A-Za-z]+)*\s+\d+:\d+-\d+) - (.+)', line)
            if section_match:
                # Save previous section if it exists
                if current_section:
                    verse_ref, section_title = current_section
                    commentary = '\n'.join(current_commentary).strip()
                    if commentary:
                        sections.append((verse_ref, section_title, commentary))
                
                # Start new section
                current_section = (section_match.group(1), section_match.group(2))
                current_commentary = []
                
            elif current_section and line and not line.startswith('Chapter') and not line.startswith('Theological'):
                # Add to current commentary (skip chapter headers and main title)
                current_commentary.append(line)
        
        # Don't forget the last section
        if current_section:
            verse_ref, section_title = current_section
            commentary = '\n'.join(current_commentary).strip()
            if commentary:
                sections.append((verse_ref, section_title, commentary))
        
        return sections

    def extract_theological_commentary_sections(self, commentary_text: str) -> List[Tuple[str, str, str]]:
        """
        Extract sections from theological commentary that's organized by chapters and subsections.
        Handles format like:
        ## Chapter 1: The Two Ways - Foundation of Wisdom
        ### Section 1: Psalm 1:1-3 - The Blessed Man's Character
        
        Returns list of tuples: (verse_reference, section_title, commentary)
        """
        sections = []
        lines = commentary_text.split('\n')
        current_chapter = None
        current_section = None
        current_commentary = []
        
        for line in lines:
            line = line.strip()
            
            # Check for chapter headers: ## Chapter X: BookName Chapter - Title
            chapter_match = re.match(r'## Chapter \d+: (.+)', line)
            if chapter_match:
                current_chapter = chapter_match.group(1)
                continue
            
            # Check for section headers: ### Section X: BookName Chapter:Verse-Verse - Title
            section_match = re.match(r'### Section \d+: ((?:\d+\s+)?[A-Za-z]+(?:\s+[A-Za-z]+)*\s+\d+:\d+-\d+) - (.+)', line)
            if section_match:
                # Save previous section if it exists
                if current_section:
                    verse_ref, section_title = current_section
                    commentary = '\n'.join(current_commentary).strip()
                    if commentary:
                        sections.append((verse_ref, section_title, commentary))
                
                # Start new section
                current_section = (section_match.group(1), section_match.group(2))
                current_commentary = []
                
            elif current_section and line and not line.startswith('#'):
                # Add to current commentary (skip headers but include bold markdown)
                current_commentary.append(line)
        
        # Don't forget the last section
        if current_section:
            verse_ref, section_title = current_section
            commentary = '\n'.join(current_commentary).strip()
            if commentary:
                sections.append((verse_ref, section_title, commentary))
        
        return sections
    
    def clean_commentary(self, commentary: str) -> str:
        """Clean up the commentary text for better podcast reading."""
        # Remove any remaining formatting artifacts
        commentary = re.sub(r'\s+', ' ', commentary)
        
        # Add proper spacing after colons for better reading flow
        commentary = re.sub(r'Author\'s Intent:', '\n\nAuthor\'s Intent:', commentary)
        commentary = re.sub(r'Original Audience Understanding:', '\n\nOriginal Audience Understanding:', commentary)
        commentary = re.sub(r'Universal Application:', '\n\nUniversal Application:', commentary)
        
        return commentary.strip()
    
    def parse_verse_reference(self, verse_reference: str) -> dict:
        """
        Parse verse reference like "Job 35:1-8" or "1 Chronicles 2:1-10" into components for Bible lookup.
        Returns dict with book, chapter, start_verse, end_verse
        """
        # Match pattern like "Job 35:1-8" or "1 Chronicles 2:1-10" or "Song of Solomon 3:1-5"
        # This handles numbered books (1 Kings), multi-word books (Song of Solomon), etc.
        match = re.match(r'((?:\d+\s+)?[A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(\d+):(\d+)-(\d+)', verse_reference)
        if match:
            book_name, chapter, start_verse, end_verse = match.groups()
            
            # Find the correct book name in the loaded Bible data (case-insensitive)
            if self.bible_data:
                for bible_book in self.bible_data.keys():
                    if bible_book.lower() == book_name.lower():
                        book_name = bible_book  # Use the exact case from JSON
                        break
            
            return {
                'book': book_name,
                'chapter': int(chapter),
                'start_verse': int(start_verse),
                'end_verse': int(end_verse)
            }
        return None
    
    def fetch_bible_verse(self, verse_reference: str, max_retries: int = 3) -> str:
        """
        Fetch Bible verse from loaded Bible data.
        """
        parsed = self.parse_verse_reference(verse_reference)
        if not parsed:
            return f"[Could not parse reference: {verse_reference}]"
        
        book = parsed['book']
        chapter = parsed['chapter']
        start_verse = parsed['start_verse']
        end_verse = parsed['end_verse']
        
        # Check if we have the book
        if book not in self.bible_data:
            return f"[Book '{book}' not available in database]"
        
        # Check if we have the chapter
        chapter_str = str(chapter)
        if chapter_str not in self.bible_data[book]:
            return f"[Chapter {chapter} not available for {book}]"
        
        verses_text = []
        chapter_data = self.bible_data[book][chapter_str]
        
        print(f"  Fetching {self.bible_version} verses from database...")
        
        for verse_num in range(start_verse, end_verse + 1):
            verse_str = str(verse_num)
            if verse_str in chapter_data:
                verse_text = chapter_data[verse_str]
                # Clean up Unicode characters
                verse_text = verse_text.replace('\u201c', '"').replace('\u201d', '"')
                verses_text.append(verse_text)
            else:
                verses_text.append("[Verse not available]")
        
        if verses_text:
            return ' '.join(verses_text)
        else:
            return f"[No verses found for {verse_reference}]"

    def fetch_bible_verse_fallback(self, verse_reference: str, max_retries: int = 3) -> str:
        """
        This method is no longer needed since we use JSON data,
        but keeping it for compatibility. It now just calls the main method.
        """
        return self.fetch_bible_verse(verse_reference, max_retries)
    
    def get_manual_verse_placeholder(self, verse_reference: str) -> str:
        """
        Provide a placeholder for manual verse insertion.
        This is useful when APIs don't have the selected version or are unavailable.
        """
        return f"[MANUAL INSERT: {verse_reference} from {self.bible_version} - Replace this with the actual verse text]"
    
    def generate_podcast_script_from_passage(self, passage: str, output_file: str = None) -> str:
        """
        Generate a podcast script directly from a Bible passage (no commentary needed).
        
        Args:
            passage: The passage to read (e.g., "Genesis 1-3")
            output_file: Output filename (optional)
        """
        if not self.bible_data:
            print("Error: No Bible data loaded.")
            return None
        
        # Parse the passage
        parsed = self.parse_passage_input(passage)
        book = parsed['book']
        start_chapter = parsed['start_chapter']
        end_chapter = parsed['end_chapter']
        
        # Set default output filename
        if not output_file:
            safe_passage = passage.replace(' ', '_').replace(':', '-')
            output_file = f"{safe_passage}_{self.bible_version}_podcast_script.txt"
        
        print(f"Generating podcast script for {passage} ({self.bible_version})...")
        
        script_lines = []
        script_lines.append(f"# {passage} Podcast Script")
        script_lines.append(f"# {self.bible_version} Translation")
        script_lines.append(f"# Generated Bible Reading")
        script_lines.append("")
        script_lines.append("---")
        script_lines.append("")
        
        # Process each chapter
        for chapter in range(start_chapter, end_chapter + 1):
            print(f"Processing {book} chapter {chapter}...")
            
            # Get the chapter text
            chapter_text = self.get_chapter_text(book, chapter)
            
            if "[Chapter" in chapter_text or "[Book" in chapter_text:
                print(f"Warning: Could not load {book} {chapter}")
                continue
            
            # Add chapter header
            script_lines.append(f"## {book} Chapter {chapter}")
            script_lines.append("")
            
            # Host introduces the chapter
            script_lines.append("**HOST:**")
            script_lines.append(f"Now let's turn to {book} chapter {chapter} from the {self.bible_version}:")
            script_lines.append("")
            
            # Split long chapters into manageable segments for reading
            max_chars_per_segment = 2000  # Reasonable length for audio
            
            if len(chapter_text) <= max_chars_per_segment:
                # Short chapter - read in one segment
                script_lines.append("**GUEST:**")
                script_lines.append(f'"{chapter_text}"')
                script_lines.append("")
            else:
                # Long chapter - split into multiple segments
                sentences = re.split(r'(?<=[.!?])\s+', chapter_text)
                segments = []
                current_segment = ""
                
                for sentence in sentences:
                    if len(current_segment) + len(sentence) < max_chars_per_segment:
                        current_segment += " " + sentence if current_segment else sentence
                    else:
                        if current_segment:
                            segments.append(current_segment)
                        current_segment = sentence
                
                if current_segment:
                    segments.append(current_segment)
                
                # Alternate between HOST and GUEST for long chapters
                for i, segment in enumerate(segments):
                    speaker = "HOST" if i % 2 == 0 else "GUEST"
                    script_lines.append(f"**{speaker}:**")
                    script_lines.append(f'"{segment}"')
                    script_lines.append("")
            
            script_lines.append("---")
            script_lines.append("")
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_lines))
        
        print(f"Podcast script generated successfully: {output_file}")
        print(f"Chapters processed: {start_chapter}-{end_chapter}")
        print(f"Bible version: {self.bible_version}")
        
        return output_file

    def generate_podcast_script(self, commentary_text: str = None, output_file: str = "podcast_script.txt", use_api: bool = True):
        """
        Generate the complete podcast script. Now supports both commentary-based and direct Bible reading.
        
        Args:
            commentary_text: Optional commentary text (if None, generates direct Bible reading)
            output_file: Output filename
            use_api: This parameter is kept for compatibility but no longer used
        """
        if commentary_text:
            # Original commentary-based generation (updated to use loaded Bible data)
            return self.generate_commentary_based_script(commentary_text, output_file)
        else:
            # Direct Bible passage reading (no commentary)
            print("No commentary provided. This method requires either commentary text or use generate_podcast_script_from_passage() directly.")
            return None

    def generate_commentary_based_script(self, commentary_text: str, output_file: str):
        """Generate script from commentary text (original functionality)."""
        print("Extracting sections from commentary...")
        
        # Check if commentary text is meaningful
        if not commentary_text or len(commentary_text.strip()) < 20:
            print("Commentary text is empty or too short for processing.")
            return None
            
        # Try the standard verse reference format first
        sections = self.extract_verse_references(commentary_text)
        
        # If no sections found, try the theological commentary format
        if not sections:
            print("Standard format not found, trying theological commentary format...")
            sections = self.extract_theological_commentary_sections(commentary_text)
        
        if not sections:
            print("No sections found. Commentary might not be in the expected format.")
            print("Expected formats:")
            print("  1. 'Section X: BookName Chapter:Verse-Verse - Title'")
            print("  2. '### Section X: BookName Chapter:Verse-Verse - Title'")
            return None
        
        print(f"Found {len(sections)} sections. Generating script...")
        
        script_lines = []
        script_lines.append("# Commentary Podcast Script")
        script_lines.append(f"# {self.bible_version} Translation with Commentary")
        script_lines.append("# Generated from Commentary")
        script_lines.append("")
        script_lines.append("---")
        script_lines.append("")
        
        for i, (verse_ref, section_title, commentary) in enumerate(sections, 1):
            print(f"Processing section {i}/{len(sections)}: {verse_ref}")
            
            # Add section header for reference
            script_lines.append(f"## Section {i}: {verse_ref} - {section_title}")
            script_lines.append("")
            
            # Clean up commentary
            clean_commentary = self.clean_commentary(commentary)
            
            # Fetch Bible verse from loaded database
            print(f"  Fetching verse: {verse_ref}")
            bible_verse = self.fetch_bible_verse(verse_ref)
            
            # Host reads the verse
            script_lines.append("**HOST:**")
            script_lines.append(f"Now let's turn to {verse_ref}:")
            script_lines.append("")
            script_lines.append(f'"{bible_verse}"')
            script_lines.append("")
            
            # Guest reads the commentary
            script_lines.append("**GUEST:**")
            script_lines.append(clean_commentary)
            script_lines.append("")
            script_lines.append("---")
            script_lines.append("")
        
        try:
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(script_lines))
            
            print(f"Podcast script generated successfully: {output_file}")
            print(f"Total sections processed: {len(sections)}")
            print(f"Bible version: {self.bible_version}")
                
            return output_file
        except Exception as e:
            print(f"Error writing script file: {e}")
            return None

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

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Bible podcast script")
    parser.add_argument("--commentary-file", help="Optional commentary file to use instead of direct Bible reading")
    parser.add_argument("--passage", help="Bible passage to read (e.g., 'Genesis 1-3') - overrides interactive mode")
    parser.add_argument("--version", help="Bible version (ESV or NKJV) - overrides interactive mode")
    
    args = parser.parse_args()
    
    # Initialize the generator
    generator = PodcastScriptGenerator()
    
    # Get Bible version and passage
    if args.version and args.passage:
        # Command line mode
        selected_version = args.version
        selected_passage = args.passage
        
        # Load the Bible version
        if not generator.load_bible_version(selected_version):
            print(f"Failed to load Bible version: {selected_version}")
            return
        
        # Validate the passage
        if not generator.validate_passage(selected_passage):
            print(f"Invalid passage: {selected_passage}")
            return
    else:
        # Interactive mode
        print("="*60)
        print("BIBLE PODCAST GENERATOR")
        print("="*60)
        
        selected_version, selected_passage = generator.prompt_user_selection()
        
        if not selected_version or not selected_passage:
            print("Failed to get valid Bible version and passage.")
            return
    
    print(f"\nSelected: {selected_passage} ({selected_version})")
    
    # Check if commentary file is provided or if we should use default commentary.txt for Job
    commentary_text = None
    if args.commentary_file:
        try:
            with open(args.commentary_file, 'r', encoding='utf-8') as f:
                commentary_text = f.read()
            print(f"Loaded commentary from: {args.commentary_file}")
        except FileNotFoundError:
            print(f"Error: Commentary file '{args.commentary_file}' not found.")
            return
        except Exception as e:
            print(f"Error reading commentary file: {e}")
            return
    else:
        # Check if this is a Job passage and commentary.txt exists
        if selected_passage.lower().startswith('job') and os.path.exists('commentary.txt'):
            try:
                with open('commentary.txt', 'r', encoding='utf-8') as f:
                    commentary_text = f.read()
                print("Automatically loaded commentary from commentary.txt")
            except Exception as e:
                print(f"Warning: Could not load default commentary.txt: {e}")
    
    # Generate the podcast script
    print("\n" + "="*50)
    print("GENERATING PODCAST SCRIPT")
    print("="*50)
    
    if commentary_text:
        # Commentary-based generation
        print("Generating commentary-based podcast script...")
        script_filename = f"commentary_{selected_version}_podcast_script.txt"
        output_file = generator.generate_commentary_based_script(commentary_text, script_filename)
    else:
        # Direct Bible reading
        print("Generating direct Bible reading script...")
        output_file = generator.generate_podcast_script_from_passage(selected_passage)
    
    if not output_file:
        print("Failed to generate podcast script.")
        return
    
    print(f"\nPodcast script has been saved to: {output_file}")
    print(f"Bible version: {selected_version}")
    print(f"Passage: {selected_passage}")
    
    print("\nScript format:")
    print("- HOST introduces chapters/sections")
    print("- GUEST reads Bible text/commentary")
    print("- Clear section breaks for easy editing")
    
    print(f"\nTo generate audio from this script, run:")
    print(f"python3 generate_audio.py")

if __name__ == "__main__":
    main()