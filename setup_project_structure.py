#!/usr/bin/env python3
"""
Fandom Scraper Project Structure Setup Script
Creates the complete directory structure for the project
"""

import os
import sys
from pathlib import Path


def create_directory_structure():
    """
    Create the complete project directory structure
    """

    # Get current working directory
    project_root = Path.cwd()
    print(f"Creating project structure in: {project_root}")

    # Define the complete directory structure
    directories = [
        # Core application directories
        "gui",
        "gui/widgets",
        "gui/controllers",
        "gui/resources",
        "gui/resources/icons",
        "gui/resources/stylesheets",
        "gui/resources/translations",
        # Scraper core
        "scraper",
        "scraper/spiders",
        "scraper/items",
        "scraper/utils",
        # Data models and storage
        "models",
        "models/schemas",
        "models/repositories",
        # Utilities
        "utils",
        "utils/data_processing",
        "utils/export",
        "utils/visualization",
        # API interface
        "api",
        "api/endpoints",
        "api/schemas",
        # CLI interface
        "cli",
        # Storage directories
        "storage",
        "storage/images",
        "storage/images/characters",
        "storage/images/animes",
        "storage/images/episodes",
        "storage/documents",
        "storage/exports",
        "storage/backups",
        # Configuration
        "config",
        "config/selector_configs",
        # Testing
        "tests",
        "tests/unit",
        "tests/unit/test_models",
        "tests/unit/test_utils",
        "tests/unit/test_scraper",
        "tests/unit/test_gui",
        "tests/integration",
        "tests/fixtures",
        "tests/fixtures/sample_html",
        "tests/fixtures/sample_data",
        "tests/fixtures/mock_responses",
        # Documentation
        "docs",
        "docs/images",
        "docs/images/screenshots",
        "docs/images/diagrams",
        "docs/examples",
        # Scripts
        "scripts",
        # Logs
        "logs",
    ]

    # Create directories
    created_dirs = []
    for directory in directories:
        dir_path = project_root / directory
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            print(f"✅ Created: {directory}")
        except Exception as e:
            print(f"❌ Failed to create {directory}: {e}")

    return created_dirs


def create_init_files():
    """
    Create __init__.py files for Python packages
    """

    project_root = Path.cwd()

    # Python package directories that need __init__.py
    package_dirs = [
        "gui",
        "gui/widgets",
        "gui/controllers",
        "scraper",
        "scraper/spiders",
        "scraper/items",
        "scraper/utils",
        "models",
        "models/schemas",
        "models/repositories",
        "utils",
        "utils/data_processing",
        "utils/export",
        "utils/visualization",
        "api",
        "api/endpoints",
        "api/schemas",
        "cli",
        "config",
        "tests",
        "tests/unit",
        "tests/unit/test_models",
        "tests/unit/test_utils",
        "tests/unit/test_scraper",
        "tests/unit/test_gui",
        "tests/integration",
    ]

    created_files = []
    for package_dir in package_dirs:
        init_file = project_root / package_dir / "__init__.py"
        try:
            # Create basic __init__.py with package docstring
            package_name = package_dir.replace("/", ".").replace("\\", ".")
            content = f'"""\n{package_name} package\n"""\n'

            init_file.write_text(content, encoding="utf-8")
            created_files.append(str(init_file))
            print(f"📄 Created: {package_dir}/__init__.py")
        except Exception as e:
            print(f"❌ Failed to create {package_dir}/__init__.py: {e}")

    return created_files


def create_essential_files():
    """
    Create essential project files
    """

    project_root = Path.cwd()
    files_created = []

    # .gitignore content
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Operating System
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
logs/*.log
storage/images/*
storage/documents/*
storage/exports/*
storage/backups/*
config/local_config.py
.env
.env.local

# Database
*.db
*.sqlite3

# Temporary files
*.tmp
*.temp
temp/
tmp/

# Test coverage
htmlcov/
.coverage
.coverage.*
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py
"""

    # Create .gitignore
    gitignore_path = project_root / ".gitignore"
    gitignore_path.write_text(gitignore_content, encoding="utf-8")
    files_created.append(".gitignore")
    print("📄 Created: .gitignore")

    # README.md content
    readme_content = """# Fandom Scraper GUI Application

A comprehensive desktop application for scraping and managing anime character data from Fandom wikis.

## 🎯 Project Overview

This application provides an intuitive PyQt-based GUI for collecting, organizing, and exploring anime data through advanced web scraping technology.

## 🚀 Features

- **Automated Data Collection**: Extract structured anime data from multiple Fandom sources
- **Intuitive GUI Interface**: User-friendly desktop interface for non-technical users
- **Smart Data Management**: MongoDB storage with intelligent deduplication
- **Multi-format Export**: JSON, CSV, Excel, and PDF export capabilities
- **Extensible Architecture**: Modular design supporting API, CLI, and web extensions

## 📋 Requirements

- Python 3.8+
- MongoDB
- PyQt5/6
- See `requirements.txt` for complete dependency list

## 🛠️ Installation

1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment: `source venv/bin/activate` (Linux/macOS) or `venv\\Scripts\\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Setup MongoDB connection in config files
6. Run the application: `python main.py`

## 📖 Documentation

See `docs/` directory for comprehensive documentation including:
- Installation Guide
- User Manual
- Developer Guide
- API Documentation

## 🤝 Contributing

Please read the development guidelines in `docs/DEVELOPER_GUIDE.md` before contributing.

## 📄 License

See LICENSE file for details.
"""

    # Create README.md
    readme_path = project_root / "README.md"
    readme_path.write_text(readme_content, encoding="utf-8")
    files_created.append("README.md")
    print("📄 Created: README.md")

    return files_created


def main():
    """
    Main setup function
    """
    print("🏗️  Setting up Fandom Scraper project structure...")
    print("=" * 60)

    try:
        # Create directory structure
        print("\n📁 Creating directories...")
        created_dirs = create_directory_structure()

        # Create __init__.py files
        print(f"\n📦 Creating Python package files...")
        created_init_files = create_init_files()

        # Create essential files
        print(f"\n📄 Creating essential project files...")
        created_files = create_essential_files()

        print("\n" + "=" * 60)
        print("✅ Project structure setup completed successfully!")
        print(f"📁 Created {len(created_dirs)} directories")
        print(f"📦 Created {len(created_init_files)} package files")
        print(f"📄 Created {len(created_files)} essential files")

        print("\n🎯 Next steps:")
        print("1. Activate virtual environment")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Initialize Git repository: git init")
        print("4. Start development with Week 1 objectives")

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
