#!/usr/bin/env python3
"""
Enhanced Documentation Fetcher Script
This version can optionally fetch real content from the internet
"""

import os
import sys
import time
import argparse
from pathlib import Path

# Try to import optional web scraping dependencies
try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    print("Note: requests and beautifulsoup4 not available. Using offline mode only.")

class EnhancedDocumentationFetcher:
    def __init__(self, base_dir="Reading Now", use_web=False):
        self.base_dir = Path(base_dir)
        self.use_web = use_web and WEB_SCRAPING_AVAILABLE
        
        if self.use_web:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            })
        
        # URL sources for web scraping
        self.web_sources = {
            'CSS': {
                'theory': 'https://developer.mozilla.org/en-US/docs/Web/CSS',
                'usage': 'https://www.w3schools.com/css/css_intro.asp',
                'examples': 'https://css-tricks.com/snippets/',
            },
            'HTML': {
                'theory': 'https://developer.mozilla.org/en-US/docs/Web/HTML',
                'usage': 'https://www.w3schools.com/html/html_intro.asp',
                'examples': 'https://www.w3schools.com/html/html_examples.asp',
            },
            'Javascript': {
                'theory': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide',
                'usage': 'https://www.w3schools.com/js/js_intro.asp',
                'examples': 'https://www.w3schools.com/js/js_examples.asp',
            },
            'Python': {
                'theory': 'https://docs.python.org/3/tutorial/',
                'usage': 'https://docs.python.org/3/library/',
                'examples': 'https://docs.python.org/3/tutorial/examples.html',
            },
            'SQL': {
                'theory': 'https://www.w3schools.com/sql/sql_intro.asp',
                'usage': 'https://www.w3schools.com/sql/',
                'examples': 'https://www.w3schools.com/sql/sql_examples.asp',
            },
            'Docker': {
                'theory': 'https://docs.docker.com/get-started/overview/',
                'usage': 'https://docs.docker.com/get-started/',
                'examples': 'https://docs.docker.com/samples/',
            },
            'git': {
                'theory': 'https://git-scm.com/about',
                'usage': 'https://git-scm.com/docs',
                'examples': 'https://git-scm.com/docs/gittutorial',
            }
        }
    
    def fetch_web_content(self, url, max_length=8000):
        """Fetch content from a URL."""
        if not self.use_web:
            return None
            
        try:
            print(f"    Fetching from: {url}")
            time.sleep(1)  # Be respectful
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            
            # Extract main content
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if main_content:
                text = main_content.get_text()
            else:
                text = soup.get_text()
            
            # Clean up text
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            clean_text = '\n'.join(lines)
            
            # Limit length
            if len(clean_text) > max_length:
                clean_text = clean_text[:max_length] + f"\n\n... (Content truncated. Full version at: {url})"
            
            return clean_text
            
        except Exception as e:
            print(f"    Warning: Failed to fetch {url}: {e}")
            return None
    
    def create_content(self, subject, doc_type):
        """Create content for a specific document type."""
        
        # Try to fetch web content first if enabled
        web_content = None
        if self.use_web and subject in self.web_sources and doc_type in self.web_sources[subject]:
            url = self.web_sources[subject][doc_type]
            web_content = self.fetch_web_content(url)
            
            if web_content:
                header = f"# {subject} - {doc_type.title()}\n"
                header += f"Source: {url}\n"
                header += f"Fetched: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                return header + web_content
        
        # Fallback to generated content
        if doc_type == 'theory':
            return f"""# {subject} - Theory and Concepts

## Overview
{subject} is an important technology/concept in modern software development.

## Fundamental Principles
- Core concepts and terminology
- Theoretical foundations
- Design principles and philosophy
- Historical context and evolution

## Architecture and Design
- How {subject} works internally
- System architecture and components
- Design patterns and methodologies
- Integration with other technologies

## Standards and Best Practices
- Industry standards and specifications
- Coding conventions and guidelines
- Performance considerations
- Security best practices

## Academic and Research Context
- Theoretical computer science foundations
- Related research areas
- Academic papers and publications
- Future trends and developments

## Further Reading
- Official documentation and specifications
- Academic textbooks and papers
- Industry publications and blogs
- Community resources and tutorials

Created: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

        elif doc_type == 'usage':
            return f"""# {subject} - Practical Usage Guide

## Getting Started
- Installation and setup procedures
- System requirements and dependencies
- Initial configuration steps
- Environment setup and preparation

## Basic Operations
- Essential commands and operations
- Common workflows and procedures
- Basic configuration options
- Fundamental usage patterns

## Intermediate Usage
- Advanced features and capabilities
- Configuration customization
- Integration with development tools
- Workflow optimization techniques

## Advanced Techniques
- Expert-level features and options
- Performance tuning and optimization
- Automation and scripting
- Custom extensions and plugins

## Troubleshooting
- Common issues and solutions
- Error messages and debugging
- Performance problems
- Compatibility considerations

## Best Practices
- Recommended workflows
- Code organization and structure
- Team collaboration guidelines
- Maintenance and updates

## Tools and Utilities
- Related development tools
- IDE integrations and plugins
- Testing and debugging utilities
- Monitoring and analysis tools

Created: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

        else:  # examples
            return f"""# {subject} - Examples and Code Samples

## Basic Examples

### Example 1: Hello World
```
# Basic {subject} example - Getting started
# This demonstrates the simplest possible use case

# Initialize or setup
{self._generate_sample_code(subject, 'basic')}
```

### Example 2: Configuration
```
# Basic configuration example
# Shows how to set up {subject} for typical use

{self._generate_sample_code(subject, 'config')}
```

## Intermediate Examples

### Example 3: Real-world Application
```
# Practical example showing common usage patterns
# Includes error handling and best practices

{self._generate_sample_code(subject, 'practical')}
```

### Example 4: Data Processing
```
# Example showing data manipulation or processing
# Demonstrates intermediate concepts

{self._generate_sample_code(subject, 'data')}
```

## Advanced Examples

### Example 5: Performance Optimization
```
# Advanced example focusing on performance
# Shows optimization techniques and best practices

{self._generate_sample_code(subject, 'performance')}
```

### Example 6: Integration Example
```
# Shows how to integrate {subject} with other technologies
# Demonstrates advanced integration patterns

{self._generate_sample_code(subject, 'integration')}
```

## Complex Use Cases

### Example 7: Production Setup
```
# Production-ready configuration and usage
# Includes monitoring, logging, and error handling

{self._generate_sample_code(subject, 'production')}
```

### Example 8: Custom Extension
```
# Example of extending or customizing {subject}
# Shows advanced customization techniques

{self._generate_sample_code(subject, 'custom')}
```

## Additional Resources
- Official example repositories
- Community-contributed samples
- Interactive tutorials and demos
- Sample projects and templates
- Code playgrounds and sandboxes

Created: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

    def _generate_sample_code(self, subject, example_type):
        """Generate appropriate sample code based on subject and type."""
        
        code_templates = {
            'CSS': {
                'basic': '/* Basic CSS styling */\nbody {\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 20px;\n}',
                'config': '/* CSS variables and configuration */\n:root {\n    --primary-color: #007bff;\n    --font-size: 16px;\n}',
                'practical': '/* Responsive design example */\n.container {\n    max-width: 1200px;\n    margin: 0 auto;\n}\n\n@media (max-width: 768px) {\n    .container { padding: 10px; }\n}',
            },
            'Javascript': {
                'basic': '// Basic JavaScript example\nconsole.log("Hello, World!");\n\n// Variables and functions\nconst greeting = (name) => {\n    return `Hello, ${name}!`;\n};',
                'config': '// Configuration object\nconst config = {\n    apiUrl: "https://api.example.com",\n    timeout: 5000,\n    retries: 3\n};',
                'practical': '// Async/await example\nasync function fetchData(url) {\n    try {\n        const response = await fetch(url);\n        return await response.json();\n    } catch (error) {\n        console.error("Error:", error);\n    }\n}',
            },
            'Python': {
                'basic': '# Basic Python example\nprint("Hello, World!")\n\n# Function definition\ndef greet(name):\n    return f"Hello, {name}!"',
                'config': '# Configuration using environment variables\nimport os\n\nCONFIG = {\n    "database_url": os.getenv("DATABASE_URL"),\n    "debug": os.getenv("DEBUG", "False").lower() == "true"\n}',
                'practical': '# File processing example\nwith open("data.txt", "r") as file:\n    for line in file:\n        processed = line.strip().upper()\n        print(processed)',
            }
        }
        
        # Return specific template or generic placeholder
        if subject in code_templates and example_type in code_templates[subject]:
            return code_templates[subject][example_type]
        else:
            return f'# {subject} {example_type} example\n# Placeholder for {subject} code\n# Refer to official documentation for actual examples'

    def create_links_file(self, subject):
        """Create comprehensive links file."""
        content = f"""# {subject} - Comprehensive Resource Links

## Official Documentation
"""
        # Add web sources if available
        if subject in self.web_sources:
            for doc_type, url in self.web_sources[subject].items():
                content += f"- {doc_type.title()}: {url}\n"
        else:
            content += f"- Search for official {subject} documentation\n"
        
        content += f"""
## Learning Resources
- Stack Overflow: https://stackoverflow.com/questions/tagged/{subject.lower().replace(' ', '-')}
- GitHub: https://github.com/search?q={subject.replace(' ', '+')}
- Reddit: https://www.reddit.com/search/?q={subject.replace(' ', '+')}
- Dev.to: https://dev.to/search?q={subject.replace(' ', '%20')}

## Community and Support
- Official forums and discussion boards
- Discord/Slack community channels
- Meetups and local user groups
- Conferences and events
- Mailing lists and newsletters

## Tools and Development Environment
- IDEs and editors with {subject} support
- Linters and code formatters
- Testing frameworks and tools
- Debugging and profiling utilities
- Build tools and automation

## Tutorials and Courses
- Free online tutorials and guides
- Paid courses and certifications
- Interactive coding platforms
- Video tutorials and workshops
- Hands-on labs and exercises

## Books and Publications
- Recommended books for beginners
- Advanced reference materials
- Academic papers and research
- Industry white papers
- Technical blogs and articles

## Code Repositories and Examples
- Official example repositories
- Community projects and samples
- Awesome lists and curated resources
- Code snippets and gists
- Template repositories

## News and Updates
- Official blogs and announcements
- Release notes and changelogs
- Technology news websites
- Podcasts and video channels
- Twitter accounts and social media

Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}
Web scraping: {'Enabled' if self.use_web else 'Disabled'}
"""
        return content

    def create_directory(self, path):
        """Create directory with error handling."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {path}: {e}")
            return False

    def process_subject(self, subject):
        """Process a single subject and create documentation."""
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
                print(f"  ✓ Created: {doc_type}.txt")
            except Exception as e:
                print(f"  ✗ Failed to create {doc_type}.txt: {e}")
        
        # Create links file
        links_path = subject_dir / "links.txt"
        try:
            with open(links_path, 'w', encoding='utf-8') as f:
                f.write(self.create_links_file(subject))
            print(f"  ✓ Created: links.txt")
        except Exception as e:
            print(f"  ✗ Failed to create links.txt: {e}")
        
        return True

    def run(self, subjects_file="read_books.txt"):
        """Main execution method."""
        print("Enhanced Documentation Fetcher")
        print("=" * 50)
        print(f"Web scraping: {'Enabled' if self.use_web else 'Disabled'}")
        print(f"Output directory: {self.base_dir.absolute()}")
        print()
        
        # Create base directory
        if not self.create_directory(self.base_dir):
            return False
        
        # Read subjects
        try:
            with open(subjects_file, 'r') as f:
                subjects = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"Error reading {subjects_file}: {e}")
            return False
        
        print(f"Found {len(subjects)} subjects to process")
        print()
        
        # Process each subject
        success_count = 0
        for i, subject in enumerate(subjects, 1):
            print(f"[{i}/{len(subjects)}] ", end="")
            if self.process_subject(subject):
                success_count += 1
            print()
        
        print("=" * 50)
        print(f"Completed! Successfully processed {success_count}/{len(subjects)} subjects")
        print(f"Documentation saved to: {self.base_dir.absolute()}")
        
        return success_count == len(subjects)

def main():
    parser = argparse.ArgumentParser(description='Enhanced Documentation Fetcher')
    parser.add_argument('--web', action='store_true', help='Enable web scraping (requires requests and beautifulsoup4)')
    parser.add_argument('--output', '-o', default='Reading Now', help='Output directory (default: Reading Now)')
    parser.add_argument('--subjects', '-s', default='read_books.txt', help='Subjects file (default: read_books.txt)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.subjects):
        print(f"Error: {args.subjects} not found")
        return 1
    
    if args.web and not WEB_SCRAPING_AVAILABLE:
        print("Error: Web scraping requires 'requests' and 'beautifulsoup4' packages")
        print("Install with: pip install requests beautifulsoup4")
        return 1
    
    fetcher = EnhancedDocumentationFetcher(base_dir=args.output, use_web=args.web)
    
    try:
        success = fetcher.run(args.subjects)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
