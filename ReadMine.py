#!/usr/bin/env python3
"""
ReadMine.py - Comprehensive Documentation Scraper

Fetches documentation (theory, usage, examples) for subjects in read_books.txt
from w3schools, MDN, and other major programming sites, organized into
beginner, intermediate, and advanced levels. Outputs text files and an HTML
index for each subject under the base directory. Supports resume via progress
log and uses existing .venv when available.
"""
import os
import sys
import time
import json
import logging
import argparse
import random
import subprocess
from pathlib import Path
from datetime import datetime

# Try to import web scraping deps
try:
    import requests
    from bs4 import BeautifulSoup
    import html2text
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    # Attempt to use .venv for missing web scraping dependencies
    VENV_PATH = Path(__file__).parent / '.venv'
    if VENV_PATH.exists():
        pip_exe = VENV_PATH / 'bin' / 'pip'
        subprocess.run([str(pip_exe), 'install', 'requests', 'beautifulsoup4', 'html2text'], check=False)
        try:
            import requests
            from bs4 import BeautifulSoup
            import html2text
            WEB_SCRAPING_AVAILABLE = True
        except ImportError:
            pass

# Constants
DEFAULT_BASE_DIR = Path("/home/me/BACKUP/PROJECTS/Crew/Reading Now")
PROGRESS_FILE = Path("readmine_progress.json")
SUBJECTS_FILE = Path("read_books.txt")
CONTENT_TYPES = ["theory", "usage", "examples"]
LEVELS = ["beginner", "intermediate", "advanced"]
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
    'Mozilla/5.0 (X11; Linux x86_64)...'
]

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ReadMine")

class DocumentationFetcher:
    def __init__(self, base_dir=DEFAULT_BASE_DIR, use_web=True, delay=3):
        self.base_dir = Path(base_dir)
        self.use_web = use_web and WEB_SCRAPING_AVAILABLE
        self.delay = delay
        self.progress = self._load_progress()
        if self.use_web:
            self.session = requests.Session()
            self.url_cache = {}
            self._set_user_agent()

    def _set_user_agent(self):
        self.session.headers.update({'User-Agent': random.choice(USER_AGENTS)})

    def _load_progress(self):
        if PROGRESS_FILE.exists():
            try:
                return json.loads(PROGRESS_FILE.read_text())
            except:
                pass
        return {'completed': [], 'last_run': None}

    def _save_progress(self):
        self.progress['last_run'] = datetime.now().isoformat()
        PROGRESS_FILE.write_text(json.dumps(self.progress, indent=2))

    def _mkdir(self, path):
        path.mkdir(parents=True, exist_ok=True)

    def _fetch(self, url):
        if not self.use_web:
            return f"Web disabled: {url}"
        if url in self.url_cache:
            return self.url_cache[url]
        try:
            self._set_user_agent()
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in ['script','style','header','footer','nav','aside']:
                for el in soup.select(tag): el.decompose()
            text = html2text.HTML2Text().handle(str(soup))
            self.url_cache[url] = text[:12000]
            time.sleep(self.delay)
            return self.url_cache[url]
        except Exception as e:
            logger.warning(f"Fetch failed {url}: {e}")
            return ''

    def _load_subjects(self):
        lines = SUBJECTS_FILE.read_text().splitlines()
        return [l for l in lines if l and not l.strip().startswith(('#','//'))]

    def get_urls(self, subject, level, ctype):
        """
        Generate prioritized list of URLs for a subject, level, and content type
        """
        urls = []
        if ctype == 'theory':
            urls = [
                f"https://www.w3schools.com/search/search.php?search={subject}",
                f"https://developer.mozilla.org/en-US/search?q={subject}"
            ]
        elif ctype == 'usage':
            urls = [
                f"https://www.w3schools.com/search/search.php?search={subject}+usage",
                f"https://stackoverflow.com/questions/tagged/{subject.lower()}"
            ]
        elif ctype == 'examples':
            urls = [
                f"https://www.w3schools.com/search/search.php?search={subject}+examples",
                f"https://www.programiz.com/search/{subject}"
            ]
        # can extend with more sources if needed
        return urls

    def create_content(self, subject, level, ctype):
        # Try web sources first
        if self.use_web:
            urls = self.get_urls(subject, level, ctype)
            for url in urls:
                text = self._fetch(url)
                if text and not text.startswith('Failed to fetch'):
                    return text
        # Fallback detailed stub
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        urls = self.get_urls(subject, level, ctype)
        if ctype == 'theory':
            content = f"# {subject} - {level.capitalize()} Theory Concepts\n"
            content += f"Generated stub content for {subject} {level} theory.\n\n"
            content += "## Further Reading\n"
            for u in urls:
                content += f"- {u}\n"
        elif ctype == 'usage':
            content = f"# {subject} - {level.capitalize()} Usage Guide\n"
            content += f"Generated stub content for {subject} {level} usage instructions.\n\n"
            content += "## Further Reading\n"
            for u in urls:
                content += f"- {u}\n"
        elif ctype == 'examples':
            content = f"# {subject} - {level.capitalize()} Examples\n"
            # include five placeholder examples
            for i in range(1, 6):
                content += (
                    f"\n## Example {i}\n" \
                    "```python\n" \
                    f"# Example {i} for {subject} at {level} level\n" \
                    "print('Example code goes here')\n" \
                    "```\n"
                )
            content += "\n## Further Examples Sources\n"
            for u in urls:
                content += f"- {u}\n"
        else:
            content = f"# {subject} - {level.capitalize()} {ctype.capitalize()}\n"
            content += "Generated placeholder.\n"
        content += f"\nGenerated on: {now}\n"
        return content

    def process(self):
        # Ensure base directory exists
        self._mkdir(self.base_dir)
        subjects = self._load_subjects()
        for subj in subjects:
            logger.info(f"Processing subject: {subj}")
            subj_dir = self.base_dir / subj
            self._mkdir(subj_dir)
            index_links = []
            for lvl in LEVELS:
                lvl_dir = subj_dir / lvl
                self._mkdir(lvl_dir)
                for ct in CONTENT_TYPES:
                    urls = self.get_urls(subj, lvl, ct)
                    fname = lvl_dir / f"{ct}.txt"
                    content = self.create_content(subj, lvl, ct)
                    if fname.exists():
                        # append updates to existing file
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        with fname.open('a') as f:
                            f.write(f"\n\n==== Update on: {timestamp} ====\n")
                            f.write(content)
                    else:
                        fname.write_text(content)
                    # write separate links file with raw URLs for further reading
                    (lvl_dir / f"{ct}_links.txt").write_text("\n".join(urls))
                    index_links.append(f'<a href="{lvl}/{ct}.txt">{lvl.capitalize()} {ct.capitalize()}</a>')
            # write HTML index with hyperlinks
            html = "<html><body>\n" + "<br/>\n".join(index_links) + "\n</body></html>"
            (subj_dir / "index.html").write_text(html)
        # Record progress (append unique)
        self.progress['completed'] = list(dict.fromkeys(self.progress['completed'] + [subj]))
        self._save_progress()

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-web', action='store_true')
    parser.add_argument('--delay', type=int, default=3)
    args = parser.parse_args()
    fetcher = DocumentationFetcher(use_web=not args.no_web, delay=args.delay)
    fetcher.process()
