#!/bin/bash

# Conda Environment Setup for Fandom Scraper
# Compatible with Windows (miniconda3) and WSL (miniconda3)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Environment configuration
ENV_NAME="env-web"
PYTHON_VERSION="3.10"

# Function to check conda installation
check_conda_installation() {
    print_status "Checking conda installation..."

    if command -v conda >/dev/null 2>&1; then
        CONDA_VERSION=$(conda --version 2>/dev/null)
        print_success "Found conda: $CONDA_VERSION"

        # Check conda info
        conda info --base >/dev/null 2>&1
        if [ $? -eq 0 ]; then
            CONDA_BASE=$(conda info --base)
            print_status "Conda base directory: $CONDA_BASE"
        fi

        return 0
    else
        print_error "Conda not found. Please install miniconda3."
        print_status "Download from: https://docs.conda.io/en/latest/miniconda.html"
        return 1
    fi
}

# Function to clean up old environments
cleanup_old_environments() {
    print_status "Checking for existing environments..."

    # Check if environment already exists
    if conda env list | grep -q "^${ENV_NAME} "; then
        print_warning "Environment '${ENV_NAME}' already exists."
        read -p "Do you want to remove it and create a new one? (y/N): " choice
        case "$choice" in
            y|Y )
                print_status "Removing existing environment..."
                conda env remove -n ${ENV_NAME} -y
                print_success "Old environment removed"
                ;;
            * )
                print_status "Keeping existing environment. Will update packages instead."
                return 1
                ;;
        esac
    fi

    # Clean up old venv if exists
    if [ -d "venv" ]; then
        print_warning "Found old venv directory."
        read -p "Do you want to remove it? (y/N): " choice
        case "$choice" in
            y|Y )
                rm -rf venv
                print_success "Old venv directory removed"
                ;;
            * )
                print_status "Keeping venv directory"
                ;;
        esac
    fi

    return 0
}

# Function to create conda environment
create_conda_environment() {
    print_status "Creating conda environment: ${ENV_NAME}"

    # Create environment with specified Python version
    conda create -n ${ENV_NAME} python=${PYTHON_VERSION} -y

    if [ $? -eq 0 ]; then
        print_success "Environment '${ENV_NAME}' created successfully"
    else
        print_error "Failed to create environment"
        exit 1
    fi
}

# Function to install packages
install_packages() {
    print_status "Installing packages in environment: ${ENV_NAME}"

    # Activate environment
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate ${ENV_NAME}

    # Update conda and pip
    conda update conda -y
    conda install pip -y
    pip install --upgrade pip

    # Install conda packages first (better dependency resolution)
    print_status "Installing conda packages..."
    conda install -c conda-forge -y \
        numpy \
        pandas \
        pillow \
        pyyaml \
        lxml \
        requests \
        beautifulsoup4

    # Install PyQt5 via conda (better compatibility)
    print_status "Installing PyQt5..."
    conda install -c conda-forge pyqt=5 -y

    # Install remaining packages via pip
    print_status "Installing pip packages..."

    # Create temporary requirements file for pip packages
    cat > temp_requirements.txt << EOF
# Web Scraping
Scrapy>=2.8.0
motor>=3.1.0

# Database
pymongo>=4.3.0

# Data Validation
pydantic>=1.10.0

# Configuration
python-dotenv>=1.0.0

# Logging
loguru>=0.6.0

# Testing
pytest>=7.2.0
pytest-qt>=4.2.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0

# Code Quality
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.0.0

# Documentation
sphinx>=6.1.0
sphinx-rtd-theme>=1.2.0

# Development Tools
pre-commit>=3.0.0
ipython>=8.10.0

# Data Export
openpyxl>=3.1.0
reportlab>=3.6.0

# Networking
user-agent>=0.1.10
fake-useragent>=1.4.0

# Async Support
aiohttp>=3.8.0
EOF

    pip install -r temp_requirements.txt

    # Clean up
    rm temp_requirements.txt

    if [ $? -eq 0 ]; then
        print_success "All packages installed successfully"
    else
        print_error "Some packages failed to install"
        exit 1
    fi
}

# Function to create environment activation scripts
create_activation_scripts() {
    print_status "Creating activation scripts..."

    # Create activation script for Unix/Linux/WSL
    cat > activate_env.sh << 'EOF'
#!/bin/bash

# Fandom Scraper Environment Activation Script

# Check if conda is available
if ! command -v conda >/dev/null 2>&1; then
    echo "Error: conda not found. Please install miniconda3."
    exit 1
fi

# Initialize conda for bash
source "$(conda info --base)/etc/profile.d/conda.sh"

# Activate environment
conda activate fandom-scraper

if [ $? -eq 0 ]; then
    echo "✅ Environment 'fandom-scraper' activated successfully"
    echo "🐍 Python version: $(python --version)"
    echo "📦 Conda environment: $(conda info --envs | grep '*')"
    echo ""
    echo "🚀 Ready for development!"
    echo "💡 To deactivate: conda deactivate"
else
    echo "❌ Failed to activate environment 'fandom-scraper'"
    exit 1
fi
EOF

    chmod +x activate_env.sh

    # Create activation script for Windows
    cat > activate_env.bat << 'EOF'
@echo off
REM Fandom Scraper Environment Activation Script for Windows

REM Check if conda is available
where conda >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: conda not found. Please install miniconda3.
    exit /b 1
)

REM Activate environment
call conda activate fandom-scraper

if %ERRORLEVEL% EQU 0 (
    echo ✅ Environment 'fandom-scraper' activated successfully
    python --version
    echo.
    echo 🚀 Ready for development!
    echo 💡 To deactivate: conda deactivate
) else (
    echo ❌ Failed to activate environment 'fandom-scraper'
    exit /b 1
)
EOF

    print_success "Activation scripts created:"
    print_status "  - Linux/WSL: ./activate_env.sh"
    print_status "  - Windows: activate_env.bat"
}

# Function to update project configuration
update_project_config() {
    print_status "Updating project configuration..."

    # Create or update .env file
    cat > .env << EOF
# Fandom Scraper Environment Configuration

# Python Environment
CONDA_ENV_NAME=fandom-scraper
PYTHON_VERSION=3.10

# Database Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=fandom_scraper

# Scraping Configuration
USER_AGENT=FandomScraper/1.0 (+https://github.com/user/fandom-scraper)
REQUEST_DELAY=1.0
CONCURRENT_REQUESTS=8

# Storage Configuration
STORAGE_PATH=./storage/
IMAGES_PATH=./storage/images/
EXPORTS_PATH=./storage/exports/

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# GUI Configuration
WINDOW_THEME=dark
AUTO_SAVE_INTERVAL=300
EOF

    # Create conda environment export
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate ${ENV_NAME}
    conda env export > environment.yml

    print_success "Project configuration updated"
    print_status "  - .env file created"
    print_status "  - environment.yml exported"
}

# Function to verify installation
verify_installation() {
    print_status "Verifying installation..."

    # Activate environment
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate ${ENV_NAME}

    # Check Python version
    PYTHON_VERSION_ACTUAL=$(python --version 2>&1)
    print_success "Python version: $PYTHON_VERSION_ACTUAL"

    # Check key packages
    print_status "Checking key packages..."

    packages_to_check=("scrapy" "PyQt5" "pymongo" "pydantic" "pandas" "numpy")

    for package in "${packages_to_check[@]}"; do
        if python -c "import $package" 2>/dev/null; then
            version=$(python -c "import $package; print(getattr($package, '__version__', 'unknown'))" 2>/dev/null || echo "unknown")
            print_success "  ✅ $package ($version)"
        else
            print_error "  ❌ $package (not found)"
        fi
    done

    # Show environment info
    print_status "Environment information:"
    conda info --envs | grep ${ENV_NAME}

    print_success "Installation verification completed"
}

# Main execution
main() {
    echo "==============================================="
    echo "🚀 Fandom Scraper Conda Environment Setup"
    echo "==============================================="

    # Check prerequisites
    if ! check_conda_installation; then
        exit 1
    fi

    # Clean up old environments
    cleanup_old_environments
    update_existing=$?

    # Create or update environment
    if [ $update_existing -eq 0 ]; then
        create_conda_environment
    else
        print_status "Updating existing environment..."
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate ${ENV_NAME}
    fi

    # Install packages
    install_packages

    # Create activation scripts
    create_activation_scripts

    # Update project configuration
    update_project_config

    # Verify installation
    verify_installation

    echo ""
    echo "==============================================="
    echo "✅ Conda environment setup completed!"
    echo "==============================================="
    echo ""
    echo "📋 Next steps:"
    echo "1. Activate environment:"
    echo "   Linux/WSL: source activate_env.sh"
    echo "   Windows: activate_env.bat"
    echo ""
    echo "2. Verify installation:"
    echo "   python -c 'import scrapy, PyQt5, pymongo; print(\"All packages imported successfully!\")'"
    echo ""
    echo "3. Start development:"
    echo "   python main.py"
    echo ""
    echo "📖 Environment details:"
    echo "  - Name: ${ENV_NAME}"
    echo "  - Python: ${PYTHON_VERSION}"
    echo "  - Activation scripts created"
    echo "  - Configuration files updated"
}

# Execute main function
main "$@"