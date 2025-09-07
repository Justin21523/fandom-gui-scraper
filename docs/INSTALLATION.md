# 📦 Installation Guide

This guide provides detailed instructions for setting up the Fandom Scraper GUI application on different operating systems.

## 📋 Table of Contents

- [System Requirements](#-system-requirements)
- [Prerequisites Installation](#-prerequisites-installation)
- [Application Installation](#-application-installation)
- [Environment Configuration](#-environment-configuration)
- [Verification](#-verification)
- [Troubleshooting](#-troubleshooting)

## 🖥️ System Requirements

### **Minimum Requirements**
- **CPU**: Dual-core processor, 2.0 GHz or higher
- **RAM**: 4 GB minimum (8 GB recommended)
- **Storage**: 2 GB free disk space
- **Network**: Stable internet connection for web scraping
- **Display**: 1024x768 resolution minimum

### **Supported Operating Systems**
- **Windows**: Windows 10 (version 1903+) or Windows 11
- **Linux**: Ubuntu 18.04+, CentOS 7+, Debian 10+
- **macOS**: macOS 10.14 (Mojave) or later
- **WSL**: Windows Subsystem for Linux (WSL2 recommended)

## 🛠️ Prerequisites Installation

### **Step 1: Install Python 3.10+**

#### Windows
1. Download Python from [python.org](https://www.python.org/downloads/windows/)
2. Run the installer and check "Add Python to PATH"
3. Verify installation:
   ```cmd
   python --version
   ```

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt update

# Install Python 3.10
sudo apt install python3.10 python3.10-venv python3.10-dev

# Verify installation
python3.10 --version
```

#### macOS
```bash
# Using Homebrew
brew install python@3.10

# Verify installation
python3.10 --version
```

### **Step 2: Install Conda**

#### Option A: Miniconda (Recommended)
1. Download Miniconda from [docs.conda.io](https://docs.conda.io/en/latest/miniconda.html)
2. Install following the platform-specific instructions
3. Restart your terminal
4. Verify installation:
   ```bash
   conda --version
   ```

#### Option B: Anaconda
1. Download Anaconda from [anaconda.com](https://www.anaconda.com/products/distribution)
2. Follow the installation wizard
3. Verify installation:
   ```bash
   conda --version
   ```

### **Step 3: Install MongoDB**

#### Windows
1. Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Run the installer and follow the setup wizard
3. Start MongoDB service:
   ```cmd
   net start MongoDB
   ```

#### Linux (Ubuntu/Debian)
```bash
# Import MongoDB public GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Update package list and install
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### macOS
```bash
# Using Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
brew services start mongodb/brew/mongodb-community
```

#### Option: MongoDB Atlas (Cloud)
1. Create account at [mongodb.com/atlas](https://www.mongodb.com/atlas)
2. Create a free cluster
3. Get connection string for application configuration

### **Step 4: Install Git**

#### Windows
1. Download Git from [git-scm.com](https://git-scm.com/download/win)
2. Run installer with default settings
3. Verify installation:
   ```cmd
   git --version
   ```

#### Linux
```bash
# Ubuntu/Debian
sudo apt install git

# CentOS/RHEL
sudo yum install git
```

#### macOS
```bash
# Using Homebrew
brew install git

# Or use Xcode Command Line Tools
xcode-select --install
```

## 🚀 Application Installation

### **Method 1: Quick Installation (Recommended)**

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/fandom-scraper-gui.git
cd fandom-scraper-gui

# 2. Create conda environment
conda env create -f environment.yml

# 3. Activate environment
conda activate env-web

# 4. Initialize project structure
python setup_project_structure.py

# 5. Configure application
cp .env.example .env
# Edit .env file with your settings

# 6. Launch application
python main.py
```

### **Method 2: Automated Setup (Linux/WSL)**

```bash
# 1. Clone repository
git clone https://github.com/yourusername/fandom-scraper-gui.git
cd fandom-scraper-gui

# 2. Make setup script executable
chmod +x setup_conda_environment.sh

# 3. Run automated setup
./setup_conda_environment.sh

# 4. Activate environment
source activate_env.sh

# 5. Launch application
python main.py
```

### **Method 3: Manual Installation**

```bash
# 1. Clone repository
git clone https://github.com/yourusername/fandom-scraper-gui.git
cd fandom-scraper-gui

# 2. Create conda environment manually
conda create -n env-web python=3.10 -y
conda activate env-web

# 3. Install conda packages
conda install -c conda-forge numpy pandas pillow pyyaml lxml requests beautifulsoup4 pyqt=5 -y

# 4. Install pip packages
pip install -r requirements.txt

# 5. Initialize project structure
python setup_project_structure.py

# 6. Configure application
cp .env.example .env

# 7. Launch application
python main.py
```

## ⚙️ Environment Configuration

### **Database Configuration**

Edit the `.env` file to configure your database connection:

```bash
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=fandom_scraper

# For MongoDB Atlas
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

### **Application Settings**

Configure application behavior in `.env`:

```bash
# Scraping Configuration
USER_AGENT=FandomScraper/1.0 (+https://github.com/yourusername/fandom-scraper)
REQUEST_DELAY=1.0
CONCURRENT_REQUESTS=8

# Storage Configuration
STORAGE_PATH=./storage/
IMAGES_PATH=./storage/images/
EXPORTS_PATH=./storage/exports/

# GUI Configuration
WINDOW_THEME=dark
AUTO_SAVE_INTERVAL=300
```

### **Advanced Configuration**

For advanced users, additional settings can be configured in:
- `config/default_config.py`: Application defaults
- `config/selector_configs/`: Website-specific selectors
- `scraper/settings.py`: Scrapy framework settings

## ✅ Verification

### **Step 1: Environment Verification**

```bash
# Activate environment
conda activate env-web

# Check Python version
python --version
# Expected: Python 3.10.x

# Check key packages
python -c "
import scrapy
import PyQt5
import pymongo
import pydantic
print('✅ All core packages imported successfully!')
print(f'Scrapy: {scrapy.__version__}')
print(f'PyQt5: {PyQt5.QtCore.PYQT_VERSION_STR}')
print(f'PyMongo: {pymongo.__version__}')
print(f'Pydantic: {pydantic.__version__}')
"
```

### **Step 2: Database Verification**

```bash
# Test MongoDB connection
python -c "
from pymongo import MongoClient
try:
    client = MongoClient('mongodb://localhost:27017/')
    client.admin.command('ping')
    print('✅ MongoDB connection successful!')
    print('Available databases:', client.list_database_names())
except Exception as e:
    print('❌ MongoDB connection failed:', e)
"
```

### **Step 3: Application Verification**

```bash
# Test base spider
python scraper/base_spider.py

# Launch GUI application
python main.py
```

### **Expected Output**

If everything is installed correctly, you should see:
- ✅ Python 3.10.x version
- ✅ All packages imported successfully
- ✅ MongoDB connection successful
- ✅ Application GUI launches without errors

## 🔧 Troubleshooting

### **Common Issues**

#### Issue: Python Version Mismatch
```bash
# Problem: Wrong Python version
# Solution: Ensure Python 3.10+ is installed and activated
conda activate env-web
python --version
```

#### Issue: PyQt5 Installation Failed
```bash
# Problem: PyQt5 compilation errors
# Solution: Install via conda instead of pip
conda install -c conda-forge pyqt=5
```

#### Issue: MongoDB Connection Failed
```bash
# Problem: MongoDB not running
# Solution: Start MongoDB service

# Windows
net start MongoDB

# Linux
sudo systemctl start mongod

# macOS
brew services start mongodb/brew/mongodb-community
```

#### Issue: Package Import Errors
```bash
# Problem: Packages not found
# Solution: Verify environment activation
conda activate env-web
pip list | grep -E "(scrapy|PyQt|pymongo)"
```

### **Platform-Specific Issues**

#### Windows Issues

**Issue: Conda not recognized**
- Add Conda to system PATH
- Restart Command Prompt/PowerShell
- Use Anaconda Prompt instead

**Issue: Permission errors**
- Run Command Prompt as Administrator
- Check antivirus software blocking installation

#### Linux Issues

**Issue: Python development headers missing**
```bash
# Ubuntu/Debian
sudo apt install python3.10-dev

# CentOS/RHEL
sudo yum install python3-devel
```

**Issue: System package conflicts**
```bash
# Use conda packages instead of system packages
conda install package_name
```

#### macOS Issues

**Issue: Xcode Command Line Tools missing**
```bash
xcode-select --install
```

**Issue: Homebrew permissions**
```bash
# Fix Homebrew permissions
brew doctor
```

### **Getting Help**

If you encounter issues not covered here:

1. **Check Documentation**: Review other guides in `docs/`
2. **Search Issues**: Look for similar problems in [GitHub Issues](https://github.com/yourusername/fandom-scraper-gui/issues)
3. **Create Issue**: Report new bugs with detailed information
4. **Join Discussions**: Ask questions in [GitHub Discussions](https://github.com/yourusername/fandom-scraper-gui/discussions)

### **Diagnostic Information**

When reporting issues, please include:

```bash
# System information
uname -a                    # System details
python --version           # Python version
conda --version            # Conda version
conda env list             # Available environments
pip list                   # Installed packages

# Application logs
cat logs/app.log           # Application logs
```

## 🎯 Next Steps

After successful installation:

1. **Read User Guide**: Check [USER_GUIDE.md](USER_GUIDE.md) for usage instructions
2. **Configure Settings**: Customize application behavior in `.env`
3. **Test Scraping**: Try scraping a small anime wiki
4. **Explore Features**: Test different application features
5. **Join Community**: Participate in project discussions

---

**Need help?** Join our community discussions or create an issue on GitHub!
