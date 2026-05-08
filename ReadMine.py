#!/usr/bin/env python
"""Generate structured learning notes for subjects listed in read_books.txt."""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import urlparse


def _install_package(package: str) -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


try:
    import requests
except ImportError:
    _install_package("requests")
    import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    _install_package("beautifulsoup4")
    from bs4 import BeautifulSoup

try:
    import html2text
except ImportError:
    _install_package("html2text")
    import html2text


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_DIR = SCRIPT_DIR / "Reading Now"
DEFAULT_PROGRESS_FILE = SCRIPT_DIR / "readmine_progress.json"
DEFAULT_SUBJECTS_FILE = SCRIPT_DIR / "read_books.txt"
LEVELS = ("beginner", "intermediate", "advanced")
DEFAULT_OUTPUT_LEVELS = ("beginner",)
CONTENT_TYPES = ("theory", "usage", "examples")
KNOWN_SOURCES = {
    "custom",
    "docker-docs",
    "git-docs",
    "github-docs",
    "markdownguide",
    "mcp-docs",
    "mdn",
    "pandas-docs",
    "pillow-docs",
    "programiz",
    "python-docs",
    "sqlite-docs",
    "streamlit-docs",
    "tkdocs",
    "tcl-docs",
    "uv-docs",
    "w3schools",
}
LEVEL_CHAR_LIMITS = {
    "beginner": 4000,
    "intermediate": 6500,
    "advanced": 9000,
}
LEVEL_GUIDANCE = {
    "theory": {
        "beginner": "Focus on the core concepts, vocabulary, and what problem the topic solves.",
        "intermediate": "Explain how the moving parts fit together, when to choose them, and common tradeoffs.",
        "advanced": "Highlight edge cases, design constraints, internals, and failure modes.",
    },
    "usage": {
        "beginner": "Show the smallest reliable workflow to get productive quickly.",
        "intermediate": "Describe practical workflows, configuration choices, and debugging tips.",
        "advanced": "Emphasize scaling patterns, automation, performance, and operational concerns.",
    },
    "examples": {
        "beginner": "Prefer short examples with one concept at a time and explicit expected results.",
        "intermediate": "Combine multiple concepts into realistic tasks and show how to adapt them.",
        "advanced": "Use nuanced examples that surface edge cases, composition, and maintenance concerns.",
    },
}
SOURCE_SELECTORS = {
    "developer.mozilla.org": ["main article", "article", "main"],
    "www.w3schools.com": ["#main", ".w3-main", "main", "article"],
    "programiz.com": ["main", "article", ".main-wrapper", ".container"],
    "docs.python.org": ["main", ".body", ".document", "article"],
    "pandas.pydata.org": ["main", ".bd-main", "article"],
    "docs.streamlit.io": ["main", "article", ".sl-elements"],
    "docs.astral.sh": ["main", "article"],
    "docs.docker.com": ["main", "article"],
    "docs.github.com": ["main", "article"],
    "git-scm.com": ["article", ".content", "main"],
    "www.markdownguide.org": ["main", "article", ".content"],
    "modelcontextprotocol.io": ["main", "article"],
    "pillow.readthedocs.io": ["main", ".rst-content", "article"],
    "www.sqlite.org": ["main", ".content", "body"],
    "tkdocs.com": ["main", "article", ".content"],
    "www.tcl-lang.org": ["body"],
}
NOISE_SELECTORS = [
    "aside",
    "footer",
    "header",
    "nav",
    ".feedback",
    ".pagination",
    ".sidebar",
    ".toc",
]
DIRECT_SOURCE_MAP: dict[str, dict[str, str]] = {
    "css": {
        "mdn": "https://developer.mozilla.org/en-US/docs/Web/CSS",
        "w3schools": "https://www.w3schools.com/css/",
    },
    "databases": {
        "sqlite-docs": "https://www.sqlite.org/docs.html",
        "python-docs": "https://docs.python.org/3/library/sqlite3.html",
    },
    "docker": {
        "docker-docs": "https://docs.docker.com/get-started/docker-overview/",
    },
    "dockerhub": {
        "docker-docs": "https://docs.docker.com/docker-hub/",
    },
    "git": {
        "git-docs": "https://git-scm.com/doc",
        "github-docs": "https://docs.github.com/en/get-started/using-git/about-git",
    },
    "github": {
        "github-docs": "https://docs.github.com/en/get-started/start-your-journey/hello-world",
        "git-docs": "https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F",
    },
    "html": {
        "mdn": "https://developer.mozilla.org/en-US/docs/Web/HTML",
        "w3schools": "https://www.w3schools.com/html/",
    },
    "javascript": {
        "mdn": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
        "w3schools": "https://www.w3schools.com/js/",
    },
    "json": {
        "python-docs": "https://docs.python.org/3/library/json.html",
        "mdn": "https://developer.mozilla.org/en-US/docs/Glossary/JSON",
    },
    "markdown": {
        "markdownguide": "https://www.markdownguide.org/basic-syntax/",
        "github-docs": "https://docs.github.com/en/get-started/writing-on-github",
    },
    "mcp": {
        "mcp-docs": "https://modelcontextprotocol.io/introduction",
    },
    "pandas_dataframes": {
        "pandas-docs": "https://pandas.pydata.org/docs/user_guide/dsintro.html",
    },
    "pandas_guide": {
        "pandas-docs": "https://pandas.pydata.org/docs/getting_started/intro_tutorials/",
    },
    "pdfs": {
        "python-docs": "https://docs.python.org/3/library/pydoc.html",
    },
    "pil": {
        "pillow-docs": "https://pillow.readthedocs.io/en/stable/handbook/tutorial.html",
    },
    "sql": {
        "sqlite-docs": "https://www.sqlite.org/lang.html",
        "w3schools": "https://www.w3schools.com/sql/",
    },
    "start": {
        "github-docs": "https://docs.github.com/en/get-started/start-your-journey",
    },
    "streamlit": {
        "streamlit-docs": "https://docs.streamlit.io/get-started",
    },
    "tcl": {
        "tcl-docs": "https://www.tcl-lang.org/man/tcl/TclCmd/contents.htm",
    },
    "tkinter_guide": {
        "python-docs": "https://docs.python.org/3/library/tkinter.html",
        "tkdocs": "https://tkdocs.com/tutorial/",
    },
    "uv": {
        "uv-docs": "https://docs.astral.sh/uv/",
    },
    "vscode": {
        "github-docs": "https://code.visualstudio.com/docs",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_subject_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def split_csvish(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;,]", value) if item.strip()]


@dataclass(frozen=True)
class SubjectRequest:
    name: str
    source_preferences: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    urls: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def normalized_name(self) -> str:
        return normalize_subject_name(self.name)


@dataclass(frozen=True)
class SourceCandidate:
    source_name: str
    url: str
    description: str = ""


@dataclass
class FetchResult:
    source_name: str
    source_url: str
    extracted_text: str
    fetch_errors: list[str] = field(default_factory=list)


def parse_subject_line(line: str) -> Optional[SubjectRequest]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    parts = [part.strip() for part in stripped.split("|") if part.strip()]
    name = parts[0]
    source_preferences: list[str] = []
    tags: list[str] = []
    urls: list[str] = []
    metadata: dict[str, str] = {}

    for part in parts[1:]:
        if "=" in part:
            key, raw_value = [item.strip() for item in part.split("=", 1)]
            key = key.lower()
            if key in {"source", "sources"}:
                source_preferences.extend(split_csvish(raw_value))
            elif key in {"tag", "tags"}:
                tags.extend(split_csvish(raw_value))
            elif key in {"url", "urls"}:
                urls.extend(split_csvish(raw_value))
            else:
                metadata[key] = raw_value
            continue

        if part.startswith("http://") or part.startswith("https://"):
            urls.append(part)
        elif part.lower() in KNOWN_SOURCES:
            source_preferences.append(part.lower())
        else:
            tags.append(part)

    return SubjectRequest(
        name=name,
        source_preferences=tuple(
            dict.fromkeys(item.lower() for item in source_preferences)
        ),
        tags=tuple(dict.fromkeys(tags)),
        urls=tuple(dict.fromkeys(urls)),
        metadata=metadata,
    )


def load_subject_requests(path: Path) -> list[SubjectRequest]:
    requests_list: list[SubjectRequest] = []
    if not path.exists():
        return requests_list

    for line in path.read_text(encoding="utf-8").splitlines():
        request = parse_subject_line(line)
        if request:
            requests_list.append(request)
    return requests_list


def build_source_candidates(subject: SubjectRequest) -> list[SourceCandidate]:
    candidates: list[SourceCandidate] = []
    seen: set[tuple[str, str]] = set()

    def add_candidate(source_name: str, url: str, description: str = "") -> None:
        key = (source_name, url)
        if not url or key in seen:
            return
        seen.add(key)
        candidates.append(
            SourceCandidate(source_name=source_name, url=url, description=description)
        )

    for url in subject.urls:
        add_candidate("custom", url, "explicit subject URL")

    mapped_sources = DIRECT_SOURCE_MAP.get(subject.normalized_name, {})
    source_order = list(subject.source_preferences) or list(mapped_sources.keys())

    if not source_order:
        for token, source_name in (
            ("pandas", "pandas-docs"),
            ("python", "python-docs"),
            ("json", "python-docs"),
            ("docker", "docker-docs"),
            ("git", "git-docs"),
            ("github", "github-docs"),
            ("tkinter", "python-docs"),
            ("streamlit", "streamlit-docs"),
            ("markdown", "markdownguide"),
            ("sql", "sqlite-docs"),
            ("html", "mdn"),
            ("css", "mdn"),
            ("javascript", "mdn"),
            ("uv", "uv-docs"),
        ):
            if token in subject.normalized_name:
                source_order.append(source_name)

    for source_name in source_order:
        mapped_url = mapped_sources.get(source_name)
        if mapped_url:
            add_candidate(source_name, mapped_url, "direct documentation page")

    for source_name, mapped_url in mapped_sources.items():
        add_candidate(source_name, mapped_url, "direct documentation page")

    return candidates


def create_html_converter() -> html2text.HTML2Text:
    converter = html2text.HTML2Text()
    converter.body_width = 0
    converter.ignore_links = False
    converter.ignore_images = True
    converter.ignore_emphasis = False
    return converter


def extract_page_text(url: str, html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    parsed = urlparse(url)
    selectors = SOURCE_SELECTORS.get(parsed.netloc, ["main", "article", "body"])

    container = None
    for selector in selectors:
        container = soup.select_one(selector)
        if container is not None:
            break
    if container is None:
        container = soup.body or soup

    for selector in NOISE_SELECTORS:
        for node in container.select(selector):
            node.decompose()

    text = create_html_converter().handle(str(container))
    cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
    return cleaned


def render_reference_links(candidates: Iterable[SourceCandidate]) -> str:
    urls = [candidate.url for candidate in candidates]
    return "\n".join(dict.fromkeys(urls))


def format_readmine_summary(summary: dict[str, Any]) -> str:
    subject_count = summary.get("subjects_total", 0)
    generated = summary.get("generated", 0)
    skipped = summary.get("skipped", 0)
    failed = summary.get("failed", 0)
    stubbed = summary.get("stub_generated", 0)
    fetched = summary.get("fetched_generated", 0)
    output_dir = summary.get("output_dir", "")
    message = (
        f"ReadMine processed {subject_count} subject(s): "
        f"{generated} generated ({fetched} fetched, {stubbed} stub), "
        f"{skipped} skipped, {failed} failed."
    )
    if output_dir:
        message = f"{message} Output: {output_dir}"
    return message


class DocumentationFetcher:
    def __init__(
        self,
        use_web: bool = True,
        base_dir: Path = DEFAULT_BASE_DIR,
        progress_file: Path = DEFAULT_PROGRESS_FILE,
        subjects_file: Path = DEFAULT_SUBJECTS_FILE,
        force: bool = False,
        output_levels: tuple[str, ...] = DEFAULT_OUTPUT_LEVELS,
    ):
        self.use_web = use_web
        self.base_dir = Path(base_dir)
        self.progress_file = Path(progress_file)
        self.subjects_file = Path(subjects_file)
        self.force = force
        invalid_levels = [level for level in output_levels if level not in LEVELS]
        if invalid_levels:
            invalid = ", ".join(sorted(invalid_levels))
            raise ValueError(f"Unsupported ReadMine output level(s): {invalid}")
        self.output_levels = (
            tuple(dict.fromkeys(output_levels)) or DEFAULT_OUTPUT_LEVELS
        )
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.progress = self._load_progress()
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "ReadMine/2.0 (+https://github.com/Maggot4703/Notebooks)"}
        )
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    def _new_progress(self) -> dict[str, Any]:
        return {
            "version": 2,
            "completed": [],
            "completed_items": [],
            "last_run": None,
            "subjects": {},
            "items": {},
        }

    def _load_progress(self) -> dict[str, Any]:
        if not self.progress_file.exists():
            return self._new_progress()

        progress = json.loads(self.progress_file.read_text(encoding="utf-8"))
        normalized = self._new_progress()
        normalized.update(progress)
        normalized["version"] = 2
        normalized["completed"] = list(dict.fromkeys(progress.get("completed", [])))
        normalized["completed_items"] = list(
            dict.fromkeys(progress.get("completed_items", []))
        )
        raw_subjects = progress.get("subjects", {}) or {}
        normalized["subjects"] = {
            name: self._normalize_subject_progress(name, subject_progress)
            for name, subject_progress in raw_subjects.items()
            if isinstance(name, str)
        }
        normalized["items"] = progress.get("items", {}) or {}
        return normalized

    def _normalize_subject_progress(
        self, subject_name: str, subject_progress: Any
    ) -> dict[str, Any]:
        timestamp = utc_now()
        if not isinstance(subject_progress, dict):
            subject_progress = {}

        normalized = {
            "tags": list(subject_progress.get("tags", [])),
            "metadata": dict(subject_progress.get("metadata", {})),
            "completed_items": list(
                dict.fromkeys(subject_progress.get("completed_items", []))
            ),
            "failed_items": list(
                dict.fromkeys(subject_progress.get("failed_items", []))
            ),
            "items": dict(subject_progress.get("items", {})),
            "updated_at": subject_progress.get("updated_at", timestamp),
        }
        return normalized

    def save_progress(self) -> None:
        self.progress_file.write_text(
            json.dumps(self.progress, indent=2, sort_keys=True), encoding="utf-8"
        )

    def _item_key(self, subject: SubjectRequest, level: str, ctype: str) -> str:
        return f"{subject.normalized_name}::{level}::{ctype}"

    def _subject_dir(self, subject: SubjectRequest) -> Path:
        return self.base_dir / subject.name

    def _content_path(self, subject: SubjectRequest, level: str, ctype: str) -> Path:
        return self._subject_dir(subject) / level / f"{ctype}.txt"

    def _links_path(self, subject: SubjectRequest, level: str, ctype: str) -> Path:
        return self._subject_dir(subject) / level / f"{ctype}_links.txt"

    def _metadata_path(self, subject: SubjectRequest, level: str, ctype: str) -> Path:
        return self._subject_dir(subject) / level / f"{ctype}.meta.json"

    def _prune_unused_output_levels(self, subject: SubjectRequest) -> None:
        subject_dir = self._subject_dir(subject)
        for level in LEVELS:
            if level in self.output_levels:
                continue
            level_dir = subject_dir / level
            if level_dir.exists():
                shutil.rmtree(level_dir)

    def _prune_unused_progress_items(self, subject: SubjectRequest) -> None:
        active_levels = set(self.output_levels)
        active_item_keys = {
            self._item_key(subject, level, ctype)
            for level in self.output_levels
            for ctype in CONTENT_TYPES
        }

        for item_key, item_record in list(self.progress["items"].items()):
            if item_record.get("subject") != subject.name:
                continue
            if item_record.get("level") in active_levels:
                continue
            self.progress["items"].pop(item_key, None)
            self.progress["completed_items"] = [
                value for value in self.progress["completed_items"] if value != item_key
            ]

        subject_progress = self.progress["subjects"].get(subject.name)
        if not subject_progress:
            return

        subject_items = {
            item_key: item_record
            for item_key, item_record in subject_progress.get("items", {}).items()
            if item_key in active_item_keys
        }
        subject_progress["items"] = subject_items
        subject_progress["completed_items"] = [
            item_key
            for item_key in subject_progress.get("completed_items", [])
            if item_key in active_item_keys
        ]
        subject_progress["failed_items"] = [
            item_key
            for item_key in subject_progress.get("failed_items", [])
            if item_key in active_item_keys
        ]

    def _record_item(
        self,
        subject: SubjectRequest,
        level: str,
        ctype: str,
        *,
        status: str,
        output_path: Path,
        links_path: Path,
        metadata_path: Path,
        source_name: Optional[str] = None,
        source_url: Optional[str] = None,
        used_stub: bool = False,
        error: Optional[str] = None,
        fetch_errors: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        item_key = self._item_key(subject, level, ctype)
        timestamp = utc_now()
        item_record = {
            "subject": subject.name,
            "subject_key": subject.normalized_name,
            "level": level,
            "content_type": ctype,
            "status": status,
            "output_path": str(output_path),
            "links_path": str(links_path),
            "metadata_path": str(metadata_path),
            "source_name": source_name,
            "source_url": source_url,
            "used_stub": used_stub,
            "tags": list(subject.tags),
            "metadata": dict(subject.metadata),
            "error": error,
            "fetch_errors": fetch_errors or [],
            "updated_at": timestamp,
        }
        self.progress["items"][item_key] = item_record

        subject_progress = self.progress["subjects"].setdefault(
            subject.name,
            {
                "tags": list(subject.tags),
                "metadata": dict(subject.metadata),
                "completed_items": [],
                "failed_items": [],
                "items": {},
                "updated_at": timestamp,
            },
        )
        subject_progress = self._normalize_subject_progress(
            subject.name, subject_progress
        )
        self.progress["subjects"][subject.name] = subject_progress
        subject_progress["tags"] = list(subject.tags)
        subject_progress["metadata"] = dict(subject.metadata)
        subject_progress["items"][item_key] = item_record
        subject_progress["updated_at"] = timestamp

        completed_items = set(self.progress["completed_items"])
        subject_completed = set(subject_progress.get("completed_items", []))
        subject_failed = set(subject_progress.get("failed_items", []))

        if status in {"generated", "skipped"}:
            completed_items.add(item_key)
            subject_completed.add(item_key)
            subject_failed.discard(item_key)
        elif status == "failed":
            subject_failed.add(item_key)
            completed_items.discard(item_key)
            subject_completed.discard(item_key)

        self.progress["completed_items"] = sorted(completed_items)
        subject_progress["completed_items"] = sorted(subject_completed)
        subject_progress["failed_items"] = sorted(subject_failed)

        total_items = len(self.output_levels) * len(CONTENT_TYPES)
        completed_subjects = set(self.progress["completed"])
        if (
            len(subject_progress["completed_items"]) == total_items
            and not subject_failed
        ):
            completed_subjects.add(subject.name)
        else:
            completed_subjects.discard(subject.name)
        self.progress["completed"] = sorted(completed_subjects)
        return item_record

    def _create_skip_metadata(
        self,
        subject: SubjectRequest,
        level: str,
        ctype: str,
        candidates: list[SourceCandidate],
        output_path: Path,
        links_path: Path,
        metadata_path: Path,
    ) -> dict[str, Any]:
        text = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        links = (
            links_path.read_text(encoding="utf-8")
            if links_path.exists()
            else render_reference_links(candidates)
        )
        used_stub = "Status: stub" in text
        metadata = {
            "subject": subject.name,
            "level": level,
            "content_type": ctype,
            "status": "skipped",
            "used_stub": used_stub,
            "source_candidates": [candidate.__dict__ for candidate in candidates],
            "source_url": links.splitlines()[0] if links else None,
            "source_name": None,
            "tags": list(subject.tags),
            "subject_metadata": dict(subject.metadata),
            "updated_at": utc_now(),
        }
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        if not links_path.exists():
            links_path.write_text(links, encoding="utf-8")
        return metadata

    def should_skip(
        self,
        subject: SubjectRequest,
        level: str,
        ctype: str,
        candidates: list[SourceCandidate],
    ) -> bool:
        if self.force:
            return False

        output_path = self._content_path(subject, level, ctype)
        links_path = self._links_path(subject, level, ctype)
        metadata_path = self._metadata_path(subject, level, ctype)

        if not output_path.exists() or not links_path.exists():
            return False

        if not metadata_path.exists():
            self._create_skip_metadata(
                subject,
                level,
                ctype,
                candidates,
                output_path,
                links_path,
                metadata_path,
            )
        return True

    def fetch_source_content(
        self, subject: SubjectRequest, candidates: list[SourceCandidate]
    ) -> Optional[FetchResult]:
        if not self.use_web:
            return None

        fetch_errors: list[str] = []
        for candidate in candidates:
            try:
                response = self.session.get(candidate.url, timeout=20)
                response.raise_for_status()
                extracted = extract_page_text(candidate.url, response.text)
                if len(extracted) < 300:
                    raise ValueError("Extracted content was too short")
                return FetchResult(
                    source_name=candidate.source_name,
                    source_url=candidate.url,
                    extracted_text=extracted,
                    fetch_errors=fetch_errors,
                )
            except Exception as exc:
                error = f"{candidate.source_name}: {candidate.url} ({exc})"
                logging.warning("Fetch failed for %s", error)
                fetch_errors.append(error)
        if candidates:
            return FetchResult(
                source_name=candidates[0].source_name,
                source_url=candidates[0].url,
                extracted_text="",
                fetch_errors=fetch_errors,
            )
        return None

    def _render_header(
        self,
        subject: SubjectRequest,
        level: str,
        ctype: str,
        *,
        status: str,
        source_name: Optional[str],
        source_url: Optional[str],
        used_stub: bool,
    ) -> list[str]:
        lines = [
            f"# {subject.name} - {level.capitalize()} {ctype.capitalize()}",
            "",
            f"Status: {status}",
            f"Generated: {utc_now()}",
        ]
        if source_name:
            lines.append(f"Source: {source_name}")
        if source_url:
            lines.append(f"URL: {source_url}")
        if subject.tags:
            lines.append(f"Tags: {', '.join(subject.tags)}")
        if subject.metadata:
            metadata_text = ", ".join(
                f"{key}={value}" for key, value in subject.metadata.items()
            )
            lines.append(f"Subject metadata: {metadata_text}")
        lines.extend(
            [
                f"Stub content: {'yes' if used_stub else 'no'}",
                "",
                "## Level focus",
                LEVEL_GUIDANCE[ctype][level],
                "",
            ]
        )
        return lines

    def render_fetched_content(
        self, subject: SubjectRequest, level: str, ctype: str, fetch_result: FetchResult
    ) -> str:
        excerpt = fetch_result.extracted_text[: LEVEL_CHAR_LIMITS[level]].strip()
        body = self._render_header(
            subject,
            level,
            ctype,
            status="fetched",
            source_name=fetch_result.source_name,
            source_url=fetch_result.source_url,
            used_stub=False,
        )
        body.extend(
            [
                "## Extracted notes",
                excerpt,
            ]
        )
        if fetch_result.fetch_errors:
            body.extend(
                [
                    "",
                    "## Other source attempts",
                    "\n".join(f"- {error}" for error in fetch_result.fetch_errors),
                ]
            )
        return "\n".join(body).strip() + "\n"

    def render_stub_content(
        self,
        subject: SubjectRequest,
        level: str,
        ctype: str,
        candidates: list[SourceCandidate],
        fetch_errors: list[str],
    ) -> str:
        references = [candidate.url for candidate in candidates]
        body = self._render_header(
            subject,
            level,
            ctype,
            status="stub",
            source_name=candidates[0].source_name if candidates else None,
            source_url=references[0] if references else None,
            used_stub=True,
        )
        body.extend(
            [
                "## Suggested study outline",
                f"- Define what {subject.name} is and why it matters.",
                f"- Capture the most useful beginner-to-advanced patterns for {subject.name}.",
                "- Record pitfalls, troubleshooting notes, and terminology to revisit later.",
                "",
            ]
        )
        if references:
            body.extend(
                [
                    "## Reference URLs",
                    "\n".join(f"- {url}" for url in references),
                    "",
                ]
            )
        if fetch_errors:
            body.extend(
                [
                    "## Fetch notes",
                    "\n".join(f"- {error}" for error in fetch_errors),
                ]
            )
        return "\n".join(body).strip() + "\n"

    def create_content(
        self, subject: SubjectRequest, level: str, ctype: str
    ) -> tuple[str, dict[str, Any]]:
        candidates = build_source_candidates(subject)
        fetch_result = self.fetch_source_content(subject, candidates)

        if fetch_result and fetch_result.extracted_text:
            content = self.render_fetched_content(subject, level, ctype, fetch_result)
            metadata = {
                "status": "generated",
                "used_stub": False,
                "source_name": fetch_result.source_name,
                "source_url": fetch_result.source_url,
                "fetch_errors": fetch_result.fetch_errors,
                "source_candidates": [candidate.__dict__ for candidate in candidates],
            }
            return content, metadata

        fetch_errors = fetch_result.fetch_errors if fetch_result else []
        content = self.render_stub_content(
            subject, level, ctype, candidates, fetch_errors
        )
        metadata = {
            "status": "generated",
            "used_stub": True,
            "source_name": fetch_result.source_name if fetch_result else None,
            "source_url": fetch_result.source_url if fetch_result else None,
            "fetch_errors": fetch_errors,
            "source_candidates": [candidate.__dict__ for candidate in candidates],
        }
        return content, metadata

    def update_index_html(self, subject: SubjectRequest) -> None:
        subject_dir = self._subject_dir(subject)
        rows = [
            "<html><head><meta charset='utf-8'><title>ReadMine</title></head><body>",
            f"<h1>{subject.name}</h1>",
            "<ul>",
        ]
        for level in self.output_levels:
            rows.append(f"<li><strong>{level.title()}</strong><ul>")
            for ctype in CONTENT_TYPES:
                content_path = self._content_path(subject, level, ctype)
                if content_path.exists():
                    rows.append(
                        "<li>"
                        f"<a href='{level}/{ctype}.txt'>{ctype}.txt</a> | "
                        f"<a href='{level}/{ctype}_links.txt'>links</a> | "
                        f"<a href='{level}/{ctype}.meta.json'>metadata</a>"
                        "</li>"
                    )
            rows.append("</ul></li>")
        rows.extend(["</ul>", "</body></html>"])
        (subject_dir / "index.html").write_text("\n".join(rows), encoding="utf-8")

    def process(self) -> dict[str, Any]:
        subjects = load_subject_requests(self.subjects_file)
        summary: dict[str, Any] = {
            "subjects_total": len(subjects),
            "generated": 0,
            "skipped": 0,
            "failed": 0,
            "stub_generated": 0,
            "fetched_generated": 0,
            "output_dir": str(self.base_dir),
            "subjects": {},
        }

        for subject in subjects:
            self._prune_unused_output_levels(subject)
            self._prune_unused_progress_items(subject)
            summary["subjects"][subject.name] = {
                "generated": 0,
                "skipped": 0,
                "failed": 0,
                "stub_generated": 0,
                "fetched_generated": 0,
            }
            for level in self.output_levels:
                for ctype in CONTENT_TYPES:
                    candidates = build_source_candidates(subject)
                    output_path = self._content_path(subject, level, ctype)
                    links_path = self._links_path(subject, level, ctype)
                    metadata_path = self._metadata_path(subject, level, ctype)
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    if self.should_skip(subject, level, ctype, candidates):
                        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                        self._record_item(
                            subject,
                            level,
                            ctype,
                            status="skipped",
                            output_path=output_path,
                            links_path=links_path,
                            metadata_path=metadata_path,
                            source_name=metadata.get("source_name"),
                            source_url=metadata.get("source_url"),
                            used_stub=metadata.get("used_stub", False),
                        )
                        summary["skipped"] += 1
                        summary["subjects"][subject.name]["skipped"] += 1
                        continue

                    try:
                        content, metadata = self.create_content(subject, level, ctype)
                        output_path.write_text(content, encoding="utf-8")
                        links_path.write_text(
                            render_reference_links(candidates), encoding="utf-8"
                        )
                        metadata_payload = {
                            "subject": subject.name,
                            "level": level,
                            "content_type": ctype,
                            "tags": list(subject.tags),
                            "subject_metadata": dict(subject.metadata),
                            "updated_at": utc_now(),
                            **metadata,
                        }
                        metadata_path.write_text(
                            json.dumps(metadata_payload, indent=2), encoding="utf-8"
                        )
                        self._record_item(
                            subject,
                            level,
                            ctype,
                            status="generated",
                            output_path=output_path,
                            links_path=links_path,
                            metadata_path=metadata_path,
                            source_name=metadata_payload.get("source_name"),
                            source_url=metadata_payload.get("source_url"),
                            used_stub=metadata_payload.get("used_stub", False),
                            fetch_errors=metadata_payload.get("fetch_errors", []),
                        )
                        summary["generated"] += 1
                        summary["subjects"][subject.name]["generated"] += 1
                        if metadata_payload.get("used_stub"):
                            summary["stub_generated"] += 1
                            summary["subjects"][subject.name]["stub_generated"] += 1
                        else:
                            summary["fetched_generated"] += 1
                            summary["subjects"][subject.name]["fetched_generated"] += 1
                    except Exception as exc:
                        logging.error(
                            "Failed to generate %s / %s / %s: %s",
                            subject.name,
                            level,
                            ctype,
                            exc,
                        )
                        self._record_item(
                            subject,
                            level,
                            ctype,
                            status="failed",
                            output_path=output_path,
                            links_path=links_path,
                            metadata_path=metadata_path,
                            error=str(exc),
                        )
                        summary["failed"] += 1
                        summary["subjects"][subject.name]["failed"] += 1

            self.update_index_html(subject)

        self.progress["last_run"] = utc_now()
        self.save_progress()
        return summary


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ReadMine documentation generator")
    parser.add_argument("--no-web", action="store_true", help="Disable web fetching")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=DEFAULT_BASE_DIR,
        help="Output directory for generated documentation",
    )
    parser.add_argument(
        "--progress-file",
        type=Path,
        default=DEFAULT_PROGRESS_FILE,
        help="Progress JSON file path",
    )
    parser.add_argument(
        "--subjects-file",
        type=Path,
        default=DEFAULT_SUBJECTS_FILE,
        help="Input subjects file path",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate files even when outputs already exist",
    )
    parser.add_argument(
        "--json-summary",
        action="store_true",
        help="Print a JSON summary instead of a text summary",
    )
    return parser


def main() -> int:
    args = build_argument_parser().parse_args()
    fetcher = DocumentationFetcher(
        use_web=not args.no_web,
        base_dir=args.base_dir,
        progress_file=args.progress_file,
        subjects_file=args.subjects_file,
        force=args.force,
    )
    summary = fetcher.process()
    if args.json_summary:
        print(json.dumps(summary))
    else:
        print(format_readmine_summary(summary))
    return 0 if summary.get("failed", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
