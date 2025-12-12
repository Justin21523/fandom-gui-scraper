# 🎯 Fandom Scraper GUI Application

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()
[![Development Status](https://img.shields.io/badge/status-Feature%20Complete-brightgreen.svg)]()

A comprehensive desktop application for scraping, managing, and exploring anime character data from Fandom wikis through an intuitive PyQt GUI interface powered by advanced web scraping technology.

![Application Demo](docs/images/screenshots/main_window_preview.png)

## 🌟 Key Features

### 🕷️ **Intelligent Web Scraping**
- **Multi-source Data Collection**: Automated extraction from multiple Fandom wiki sources
- **Anti-ban Protection**: Respectful rate limiting and user agent rotation
- **Robust Error Handling**: Comprehensive retry mechanisms and failure recovery
- **Real-time Progress Tracking**: Live updates on scraping progress and statistics

### 🖥️ **Intuitive Desktop Interface**
- **User-friendly GUI**: PyQt-based interface designed for non-technical users
- **Real-time Monitoring**: Live progress indicators and status updates
- **Advanced Search & Filtering**: Powerful tools to find and organize data
- **Data Visualization**: Interactive charts and statistics display

### 🗄️ **Smart Data Management**
- **MongoDB Storage**: Scalable NoSQL database with intelligent indexing
- **Automatic Deduplication**: Smart algorithms to prevent duplicate entries
- **Data Quality Scoring**: Automated assessment of data completeness and accuracy
- **Multi-format Export**: Support for JSON, CSV, Excel, and PDF formats

### 🔧 **Extensible Architecture**
- **Modular Design**: Clean separation of concerns for easy maintenance
- **API Interface**: RESTful API for external integrations
- **CLI Support**: Command-line interface for batch operations
- **Plugin System**: Extensible framework for custom scrapers

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.10 or higher
- **Conda**: Miniconda3 or Anaconda
- **MongoDB**: Local installation or cloud instance
- **OS**: Windows 10+, Ubuntu 18.04+, or macOS 10.14+

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/fandom-scraper-gui.git
   cd fandom-scraper-gui
   ```

2. **Create conda environment**
   ```bash
   # Create environment from configuration
   conda env create -f environment.yml

   # Activate environment
   conda activate env-web
   ```

3. **Initialize project structure**
   ```bash
   python setup_project_structure.py
   ```

4. **Configure application**
   ```bash
   # Copy and edit environment configuration
   cp .env.example .env
   # Edit .env file with your MongoDB settings
   ```

5. **Launch application**
   ```bash
   python main.py
   ```

### Alternative Installation Methods

<details>
<summary>📋 <strong>Automated Setup (Linux/WSL)</strong></summary>

```bash
# Make setup script executable
chmod +x setup_conda_environment.sh

# Run automated setup
./setup_conda_environment.sh

# Activate environment
source activate_env.sh
```

</details>

<details>
<summary>🪟 <strong>Windows Setup</strong></summary>

```cmd
REM Create environment
conda env create -f environment.yml

REM Activate environment
activate_env.bat

REM Launch application
python main.py
```

</details>

## 📖 Documentation

### 📚 **User Guides**
- [Installation Guide](docs/INSTALLATION.md) - Detailed setup instructions
- [User Manual](docs/USER_GUIDE.md) - Complete application usage guide
- [Configuration Guide](docs/CONFIGURATION.md) - Settings and customization

### 👨‍💻 **Developer Resources**
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Architecture and development setup
- [API Documentation](docs/API_DOCUMENTATION.md) - RESTful API reference
- [Contributing Guidelines](docs/CONTRIBUTING.md) - How to contribute to the project

### 🔧 **Technical Documentation**
- [Architecture Overview](docs/ARCHITECTURE.md) - System design and components
- [Database Schema](docs/DATABASE_SCHEMA.md) - MongoDB collection structures
- [Testing Guide](docs/TESTING.md) - Testing framework and procedures

## 🎯 Project Roadmap

### ✅ **Phase 1: Foundation**
- [x] Project environment setup and configuration
- [x] MongoDB data models with Pydantic validation
- [x] Base scraper architecture with Scrapy framework
- [x] Utility modules for data processing

### ✅ **Phase 2: Core Development**
- [x] Fandom-specific spider implementations
- [x] Image download and storage pipelines
- [x] PyQt main window and progress dialogs
- [x] GUI-scraper integration with threading

### ✅ **Phase 3: Advanced Features**
- [x] Multi-source data fusion and intelligent deduplication
- [x] Advanced search, filtering, and visualization components
- [x] Tag management and user annotation systems
- [x] Performance optimization and error handling

### ✅ **Phase 4: Extensions**
- [x] RESTful API for external integrations
- [x] Command-line interface for batch operations
- [x] Data export capabilities (JSON, CSV, Excel, PDF)
- [x] Comprehensive testing and documentation (164 tests)

## 🛠️ Technology Stack

### **Backend Technologies**
- **Python 3.10+**: Core application language
- **Scrapy**: Advanced web scraping framework
- **MongoDB**: Document-based database storage
- **PyMongo**: MongoDB driver for Python
- **Pydantic**: Data validation and serialization
- **FastAPI**: RESTful API framework
- **Typer**: CLI application framework

### **Frontend Technologies**
- **PyQt6**: Cross-platform GUI framework
- **Qt Designer**: Visual interface design tool
- **Rich**: Terminal formatting and progress display

### **Data Processing**
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Pillow**: Image processing
- **Matplotlib**: Data visualization

### **Development Tools**
- **pytest**: Testing framework (164+ tests)
- **Black**: Code formatting
- **Flake8**: Code linting
- **Sphinx**: Documentation generation

## 📊 Current Status

### **Development Progress**
- 🟢 **Foundation Setup**: 100% Complete
- 🟢 **Core Development**: 100% Complete
- 🟢 **Advanced Features**: 100% Complete
- 🟢 **Extensions**: 100% Complete

### **Supported Anime Wikis**
- [x] One Piece Fandom Wiki
- [x] Naruto Fandom Wiki
- [x] Dragon Ball Fandom Wiki
- [x] Generic Fandom Wiki Support

### **Data Coverage**
- Character profiles and relationships
- Episode information and summaries
- Character images and media files
- Anime series metadata

## 🤝 Contributing

We welcome contributions from the community! Please see our [Contributing Guidelines](docs/CONTRIBUTING.md) for details.

### **Ways to Contribute**
- 🐛 **Bug Reports**: Help us identify and fix issues
- 💡 **Feature Requests**: Suggest new functionality
- 🔧 **Code Contributions**: Submit pull requests
- 📖 **Documentation**: Improve guides and documentation
- 🎨 **UI/UX**: Enhance user interface design

### **Development Workflow**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Scrapy Team**: For the powerful web scraping framework
- **PyQt Community**: For the excellent GUI toolkit
- **MongoDB**: For the flexible database solution
- **Fandom Community**: For maintaining comprehensive anime wikis

## 📞 Support & Contact

### **Getting Help**
- 📖 **Documentation**: Check our comprehensive guides in the `docs/` directory
- 🐛 **Issues**: Report bugs on [GitHub Issues](https://github.com/yourusername/fandom-scraper-gui/issues)
- 💬 **Discussions**: Join community discussions on [GitHub Discussions](https://github.com/yourusername/fandom-scraper-gui/discussions)

### **Project Maintainers**
- **Lead Developer**: [Your Name](https://github.com/yourusername)
- **Documentation**: Community Contributors
- **Testing**: Community Contributors

---

<div align="center">

**⭐ Star this repository if you find it helpful! ⭐**

Made with ❤️ by the Fandom Scraper community

</div>