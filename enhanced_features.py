"""
Enhanced features and utilities for the NPCs Data Processing Tool.
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are installed."""
    dependencies = {"pandas": False, "PIL": False, "ijson": False, "git": False}

    try:
        import pandas

        dependencies["pandas"] = True
    except ImportError:
        pass

    try:
        from PIL import Image

        dependencies["PIL"] = True
    except ImportError:
        pass

    try:
        import ijson

        dependencies["ijson"] = True
    except ImportError:
        pass

    try:
        result = subprocess.run(["git", "--version"], capture_output=True)
        dependencies["git"] = result.returncode == 0
    except FileNotFoundError:
        pass

    return dependencies


def install_missing_dependencies() -> bool:
    """Attempt to install missing dependencies."""
    deps = check_dependencies()
    missing = [dep for dep, installed in deps.items() if not installed and dep != "git"]

    if not missing:
        logger.info("All Python dependencies are installed")
        return True

    try:
        for dep in missing:
            if dep == "PIL":
                subprocess.run(["pip", "install", "Pillow"], check=True)
            else:
                subprocess.run(["pip", "install", dep], check=True)

        logger.info(f"Successfully installed: {', '.join(missing)}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False


def generate_requirements_file() -> None:
    """Generate requirements.txt file."""
    requirements = ["pandas>=1.3.0", "Pillow>=8.0.0", "ijson>=3.0.0"]

    with open("requirements.txt", "w") as f:
        for req in requirements:
            f.write(f"{req}\n")

    logger.info("📄 Generated requirements.txt")


def run_diagnostics() -> Dict[str, any]:
    """Run comprehensive project diagnostics."""
    diagnostics = {}

    # Check file structure
    project_dir = Path(__file__).parent
    required_dirs = ["input", "output", "data", "tests"]
    diagnostics["directories"] = {
        dir_name: (project_dir / dir_name).exists() for dir_name in required_dirs
    }

    # Check dependencies
    diagnostics["dependencies"] = check_dependencies()

    # Check Git status
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        diagnostics["git_clean"] = len(result.stdout.strip()) == 0
    except:
        diagnostics["git_clean"] = False

    return diagnostics
