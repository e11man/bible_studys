#!/usr/bin/env python3

from bible import PodcastScriptGenerator
import os

def create_enhanced_psalm_script():
    """
    Create an enhanced script that combines theological commentary with direct Bible reading.
    """
    generator = PodcastScriptGenerator()
    
    # Load NKJV Bible data
    if not generator.load_bible_version("NKJV"):
        print("Failed to load NKJV Bible data")
        return None
    
    print("Creating enhanced Psalm 1-13 script...")
    
    # First, generate the commentary-based script for Psalms 1-2
    with open('theological_commentary_psalms_1-40.txt', 'r') as f:
        commentary_text = f.read()
    
    commentary_script = generator.generate_commentary_based_script(
        commentary_text, 
        "temp_commentary_script.txt"
    )
    
    # Now generate direct Bible reading for Psalms 3-13
    direct_script = generator.generate_podcast_script_from_passage(
        "Psalm 3-13", 
        "temp_direct_script.txt"
    )
    
    # Combine both scripts
    combined_lines = []
    combined_lines.append("# Enhanced Psalm 1-13 Podcast Script")
    combined_lines.append("# NKJV Translation with Theological Commentary")
    combined_lines.append("# Combined Commentary-Based and Direct Reading")
    combined_lines.append("")
    combined_lines.append("---")
    combined_lines.append("")
    
    # Add commentary-based sections (Psalms 1-2)
    if commentary_script and os.path.exists(commentary_script):
        with open(commentary_script, 'r') as f:
            commentary_content = f.read()
        
        # Skip the header and add the content
        commentary_lines = commentary_content.split('\n')
        in_content = False
        for line in commentary_lines:
            if line.strip() == "---" and not in_content:
                in_content = True
                continue
            if in_content:
                combined_lines.append(line)
    
    # Add direct reading sections (Psalms 3-13)
    if direct_script and os.path.exists(direct_script):
        with open(direct_script, 'r') as f:
            direct_content = f.read()
        
        # Skip the header and add the content
        direct_lines = direct_content.split('\n')
        in_content = False
        for line in direct_lines:
            if line.strip() == "---" and not in_content:
                in_content = True
                continue
            if in_content:
                combined_lines.append(line)
    
    # Write the combined script
    output_file = "output/enhanced_Psalm_1-13_NKJV_commentary_script.txt"
    os.makedirs("output", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(combined_lines))
    
    # Clean up temporary files
    if os.path.exists("temp_commentary_script.txt"):
        os.remove("temp_commentary_script.txt")
    if os.path.exists("temp_direct_script.txt"):
        os.remove("temp_direct_script.txt")
    
    print(f"Enhanced script created: {output_file}")
    print("Structure:")
    print("  - Psalms 1-2: Detailed theological commentary")
    print("  - Psalms 3-13: Direct Bible reading with natural transitions")
    
    return output_file

if __name__ == "__main__":
    create_enhanced_psalm_script() 