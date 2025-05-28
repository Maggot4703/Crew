#!/usr/bin/env python3
"""
Script to save the chat summary to a file
"""

chat_content = """
# Chat Export - May 28, 2025

## Guide Creation and Text-to-Speech Tool Development

### User Request:
Create comprehensive guides for various languages/tools, saving them as "use-[language].txt" files with detailed examples and usage information. Currently working on creating guides for Tcl, Markdown (.md), Docker, and Docker Hub.

Additionally, create a file to read out contents of a selected "use-" file to be read out loud.

### Completed Work:

#### Comprehensive Guides Created:
1. **Markdown Guide** (`use-Markdown.txt`) - A comprehensive guide covering basic and advanced Markdown syntax, different flavors, best practices, popular editors, tools and resources.

2. **Docker Guide** (`use-Docker.txt`) - A detailed guide covering Docker installation, basic commands, Dockerfile creation, Docker Compose, container orchestration, data management, networking, security best practices, debugging and resources.

3. **Docker Hub Guide** (`use-DockerHub.txt`) - A comprehensive guide covering Docker Hub features, account management, working with images, repository management, automated builds, organizations and teams, security features, webhooks, best practices, troubleshooting and alternatives.

4. **Tcl Guide** (`use-Tcl.txt`) - Previously completed comprehensive guide covering Tcl programming language.

#### Text-to-Speech Tools Developed:
1. **GUI Version** (`read_use_file.py`) - A graphical user interface for selecting and reading use files, with features like file preview, speed/volume control, and text preprocessing for better speech quality.

2. **Command Line Version** (`read_use_file_cli.py`) - A command-line utility for quickly accessing and reading use files by name or number.

3. **Shell Script Helper** (`read_use.sh`) - A simple bash script for the easiest possible access to reading any use file.

All tools include duplicate file handling, text preprocessing for better speech quality, and user-friendly interfaces. A detailed README file (`USE_FILE_READER_README.md`) provides usage instructions for all utilities.

### Usage Examples:
```bash
# GUI version
./read_use_file.py

# Command line version
./read_use_file_cli.py --file Docker
./read_use_file_cli.py --rate 180 --file Markdown

# Shell script 
./read_use.sh Docker
```

These tools automatically find and read aloud any of the use-* guides, making them accessible even when unable to read the screen directly, and will install any required dependencies automatically.

### Key Features of Text-to-Speech Tools:

1. **GUI Interface** with:
   - File browser with preview functionality
   - Adjustable reading speed and volume controls
   - Start/stop control buttons
   - Text preprocessing for better TTS quality

2. **Command-line Interface** with:
   - File listing capabilities
   - File selection by name or number
   - Speed adjustment options
   - Simple, scriptable access

3. **Preprocessing Features**:
   - Removes code blocks and formats them appropriately for speech
   - Handles markdown formatting elements
   - Properly formats lists and headers
   - Makes URLs and special characters more speech-friendly

4. **Automatic Dependency Installation**:
   - Detects if pyttsx3 is installed
   - Automatically installs it if missing
   - Provides clear error messages

### Directory Structure:
- `read_use_file.py` - GUI application
- `read_use_file_cli.py` - Command-line utility
- `read_use.sh` - Convenience shell script
- `USE_FILE_READER_README.md` - Documentation for all tools

### Implementation Details:

#### Text Pre-processing for Better TTS
```python
def preprocess_text_for_speech(text):
    """Preprocess text to make it more suitable for TTS."""
    # Remove markdown headers (#)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove code blocks
    text = re.sub(r'```.*?```', ' Code block omitted. ', text, flags=re.DOTALL)
    
    # Remove inline code
    text = re.sub(r'`.*?`', ' Code omitted. ', text)
    
    # Replace bullet points
    text = re.sub(r'^[\*\-\+]\s+', '• ', text, flags=re.MULTILINE)
    
    # Handle numbered lists
    text = re.sub(r'^\d+\.\s+', 'Number. ', text, flags=re.MULTILINE)
    
    # Replace URLs with placeholders
    text = re.sub(r'https?://\S+', ' URL link. ', text)
    
    return text.strip()
```

#### Duplicate File Handling
```python
def find_use_files():
    """Find all use-*.txt files in the current directory and subdirectories"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    use_files = []
    
    # Track filenames to avoid duplicates
    filenames_seen = set()
    
    for root, _, _ in os.walk(base_dir):
        files = glob.glob(os.path.join(root, "use-*.txt"))
        for file_path in files:
            filename = os.path.basename(file_path)
            if filename not in filenames_seen:
                use_files.append(file_path)
                filenames_seen.add(filename)
    
    return sorted(use_files)
```

### Conclusion:
All requested guides have been created and a comprehensive set of text-to-speech tools has been developed to make the guides accessible through audio. The tools are designed to be user-friendly, handle edge cases gracefully, and provide a good listening experience even for technical content.
"""

# Write the content to chat.txt
with open('chat.txt', 'w') as f:
    f.write(chat_content)

print("Chat content has been saved to chat.txt")
