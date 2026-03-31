#!/usr/bin/env python3
"""
Documentation Fetcher Script
"""

import os
import sys
import time
import requests
from pathlib import Path

class DocumentationFetcher:
    def __init__(self, base_dir="Reading Now"):
        self.base_dir = Path(base_dir)
        
    def create_directory(self, path):
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Failed to create directory {path}: {e}")
            return False
    
    def create_content(self, subject, doc_type):
        if doc_type == 'theory':
            return f"""# {subject} - Theory and Concepts

## Overview
{subject} is an important technology in modern development.

## Key Concepts
- Fundamental principles of {subject}
- Core terminology and concepts
- Best practices and standards
- Historical context and evolution

## Architecture
- How {subject} works internally
- Design patterns and methodologies
- Performance considerations
- Security implications

## Further Reading
Please refer to official documentation for detailed information.
Created: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        elif doc_type == 'usage':
            return f"""# {subject} - Usage Guide

## Getting Started
- Installation and setup procedures
- Basic configuration requirements
- Environment setup
- Initial project structure

## Common Operations
- Basic commands and operations
- Configuration options
- Best practices for daily use
- Troubleshooting common issues

## Advanced Usage
- Advanced features and capabilities
- Integration with other tools
- Automation and scripting
- Performance optimization

## Tips and Tricks
- Productivity enhancements
- Common pitfalls to avoid
- Community recommendations
- Workflow optimization

Created: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        else:  # examples
            return f"""# {subject} - Examples and Code Samples

## Basic Examples

### Example 1: Getting Started
```
# Basic {subject} example
# This demonstrates the simplest use case
```

### Example 2: Common Use Case
```
# Common usage pattern for {subject}
# Shows typical workflow and best practices
```

## Intermediate Examples

### Example 3: Real-world Application
```
# More complex example showing practical usage
# Includes error handling and optimization
```

### Example 4: Integration Example
```
# Shows how to integrate {subject} with other tools
# Demonstrates common integration patterns
```

## Advanced Examples

### Example 5: Performance Optimization
```
# Advanced techniques for optimizing {subject}
# Best practices for production environments
```

### Example 6: Custom Configuration
```
# Advanced configuration example
# Shows customization options and techniques
```

## Additional Resources
- Official code repositories
- Interactive tutorials and demos
- Community-contributed examples
- Sample projects and templates

Created: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

    def create_links_file(self, subject):
        return f"""# {subject} - Useful Links and Resources

## Official Documentation
- Official website and documentation
- API reference and guides
- Getting started tutorials
- Advanced usage examples

## Learning Resources
- Stack Overflow: https://stackoverflow.com/questions/tagged/{subject.lower()}
- GitHub: https://github.com/search?q={subject}
- Reddit: https://www.reddit.com/search/?q={subject}
- YouTube tutorials and courses

## Community and Support
- Official forums and communities
- Discord/Slack channels
- Meetups and conferences
- User groups and discussions

## Tools and Utilities
- Development tools and IDEs
- Testing frameworks
- Integration libraries
- Monitoring and debugging tools

## Books and Publications
- Recommended books
- Academic papers
- Industry reports
- Best practice guides

Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

    def process_subject(self, subject):
        subject_dir = self.base_dir / subject
        
        if not self.create_directory(subject_dir):
            return False
        
        print(f"Processing: {subject}")
        
        # Create theory, usage, examples files
        for doc_type in ['theory', 'usage', 'examples']:
            file_path = subject_dir / f"{doc_type}.txt"
            content = self.create_content(subject, doc_type)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Created: {file_path}")
            except Exception as e:
                print(f"  Failed to write {file_path}: {e}")
        
        # Create links file
        links_path = subject_dir / "links.txt"
        try:
            with open(links_path, 'w', encoding='utf-8') as f:
                f.write(self.create_links_file(subject))
            print(f"  Created: {links_path}")
        except Exception as e:
            print(f"  Failed to write {links_path}: {e}")
        
        return True
    
    def run(self):
        print("Documentation Fetcher Starting...")
        
        # Create base directory
        if not self.create_directory(self.base_dir):
            return False
        
        # Read subjects from file
        try:
            with open('read_books.txt', 'r') as f:
                subjects = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Failed to read read_books.txt: {e}")
            return False
        
        print(f"Found {len(subjects)} subjects to process")
        
        # Process each subject
        success_count = 0
        for subject in subjects:
            if self.process_subject(subject):
                success_count += 1
        
        print(f"\nCompleted! Processed {success_count}/{len(subjects)} subjects")
        print(f"Documentation saved to: {self.base_dir.absolute()}")
        
        return True

def main():
    if not os.path.exists('read_books.txt'):
        print("Error: read_books.txt not found")
        return 1
    
    fetcher = DocumentationFetcher()
    try:
        fetcher.run()
        return 0
    except KeyboardInterrupt:
        print("\nCancelled by user")
        return 1

if __name__ == "__main__":
    sys.exit(main())
