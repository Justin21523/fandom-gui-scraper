# 📖 User Guide

Welcome to the Fandom Scraper GUI Application! This comprehensive guide will help you get the most out of the application's features.

## 📋 Table of Contents

- [Getting Started](#-getting-started)
- [Interface Overview](#-interface-overview)
- [Basic Operations](#-basic-operations)
- [Advanced Features](#-advanced-features)
- [Data Management](#-data-management)
- [Configuration](#-configuration)
- [Tips & Best Practices](#-tips--best-practices)
- [Troubleshooting](#-troubleshooting)

## 🚀 Getting Started

### **First Launch**

1. **Activate Environment**
   ```bash
   conda activate env-web
   ```

2. **Launch Application**
   ```bash
   python main.py
   ```

3. **Initial Setup**
   - The application will check your database connection
   - Configure basic settings through the Settings dialog
   - Verify MongoDB connection

### **Quick Start Tutorial**

Let's scrape your first anime characters:

1. **Select Anime Series**
   - Click "New Scraping Project"
   - Enter anime name (e.g., "One Piece")
   - Select target wiki source

2. **Configure Scraping**
   - Set maximum pages to scrape
   - Choose data types (characters, episodes, media)
   - Configure download settings

3. **Start Scraping**
   - Click "Start Scraping"
   - Monitor progress in real-time
   - Review results as they appear

## 🖥️ Interface Overview

### **Main Window Layout**

```
┌─────────────────────────────────────────────────────────┐
│ File  Edit  View  Tools  Help                    [- □ ×]│
├─────────────────────────────────────────────────────────┤
│ 📁 Project: One Piece    🔄 Status: Ready    ⚙️ Settings │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─ Control Panel ─┐  ┌─── Data Browser ──────────┐    │
│  │ 🎯 Target        │  │ Name         │ Type   │ ✓  │    │
│  │ ▼ One Piece      │  │ Monkey D.    │ Main   │ ✓  │    │
│  │                  │  │ Luffy        │ Char   │    │    │
│  │ 📊 Progress      │  │ Roronoa Zoro │ Main   │ ✓  │    │
│  │ [████████████]   │  │ Nami         │ Main   │ ✓  │    │
│  │ 85% (1,250/1,470)│  │ Usopp        │ Main   │ ✓  │    │
│  │                  │  │ Sanji        │ Main   │ ✓  │    │
│  │ 🎮 Controls      │  │ Tony Tony    │ Main   │ ✓  │    │
│  │ [Start] [Pause]  │  │ Chopper      │ Char   │    │    │
│  │ [Stop]  [Export] │  │ ...          │ ...    │... │    │
│  └──────────────────┘  └─────────────────────────────┘    │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ 📊 Statistics: 1,250 characters • 45 episodes • 2.1GB  │
└─────────────────────────────────────────────────────────┘
```

### **Key Interface Elements**

#### **1. Menu Bar**
- **File**: Project management, import/export
- **Edit**: Search, filters, data editing
- **View**: Layout options, visualization modes
- **Tools**: Settings, utilities, diagnostics
- **Help**: Documentation, about, support

#### **2. Control Panel**
- **Target Selection**: Choose anime and data sources
- **Progress Monitor**: Real-time scraping progress
- **Control Buttons**: Start, pause, stop, resume operations
- **Quick Statistics**: Current session summary

#### **3. Data Browser**
- **Data Grid**: Tabular view of scraped data
- **Filter Bar**: Quick search and filtering
- **Sort Options**: Multiple column sorting
- **Selection Tools**: Batch operations

#### **4. Status Bar**
- **Connection Status**: Database and network status
- **Statistics Summary**: Total data collected
- **Memory Usage**: Application resource usage

## 🎯 Basic Operations

### **Creating a New Project**

1. **File → New Project** or use shortcut `Ctrl+N`
2. **Project Configuration Dialog**:
   ```
   ┌─ New Scraping Project ──────────────────┐
   │                                         │
   │ Project Name: [One Piece Characters  ]  │
   │                                         │
   │ Target Anime: [One Piece            ]   │
   │                                         │
   │ Data Sources:                           │
   │ ☑ Characters    ☑ Episodes             │
   │ ☑ Images        ☐ Relationships        │
   │                                         │
   │ Advanced Settings:                      │
   │ Max Pages: [100    ] ▼                 │
   │ Delay: [1.0 seconds] ▼                 │
   │                                         │
   │           [Cancel]  [Create Project]    │
   └─────────────────────────────────────────┘
   ```

3. **Click "Create Project"** to initialize

### **Starting a Scraping Session**

1. **Verify Configuration**
   - Check target anime name
   - Confirm data types selected
   - Review rate limiting settings

2. **Start Scraping**
   - Click the "Start" button
   - Monitor progress in real-time
   - Watch for any error messages

3. **Monitor Progress**
   - Progress bar shows completion percentage
   - Log window displays detailed activities
   - Statistics update in real-time

### **Browsing Scraped Data**

#### **Data Grid Navigation**
- **Sorting**: Click column headers to sort
- **Filtering**: Use the filter bar for quick searches
- **Selection**: Click rows to select, Ctrl+click for multiple

#### **Search and Filter**
```
Search: [luffy              ] 🔍
Filters: [Character Type ▼] [Status ▼] [Quality ▼]
```

#### **Data Details View**
Double-click any row to open detailed view:
```
┌─ Character Details: Monkey D. Luffy ────────────┐
│                                                 │
│ ┌─ Basic Info ─┐  ┌─ Character Image ──┐       │
│ │ Name: Monkey  │  │                    │       │
│ │       D. Luffy│  │    [🖼️ Character  │       │
│ │ Age: 19       │  │     Portrait]      │       │
│ │ Status: Alive │  │                    │       │
│ │ Bounty: 3B    │  └────────────────────┘       │
│ └───────────────┘                               │
│                                                 │
│ ┌─ Description ──────────────────────────────┐  │
│ │ Monkey D. Luffy is the captain of the     │  │
│ │ Straw Hat Pirates and the main protagonist │  │
│ │ of the One Piece series...                 │  │
│ └────────────────────────────────────────────┘  │
│                                                 │
│ ┌─ Relationships ─┐  ┌─ Abilities ──────────┐  │
│ │ Crew: Straw Hat │  │ • Gomu Gomu no Mi    │  │
│ │ Brother: Ace    │  │ • Haki (All Types)   │  │
│ │ Brother: Sabo   │  │ • Enhanced Strength  │  │
│ └─────────────────┘  └──────────────────────┘  │
│                                                 │
│                      [Edit] [Export] [Close]   │
└─────────────────────────────────────────────────┘
```

## 🚀 Advanced Features

### **Multi-Source Data Fusion**

The application can intelligently combine data from multiple sources:

1. **Enable Multi-Source Mode**
   - Tools → Settings → Data Sources
   - Enable "Multi-source fusion"
   - Configure source priorities

2. **Conflict Resolution**
   - Automatic quality scoring
   - Manual conflict resolution
   - Custom merge rules

### **Advanced Search**

Access through **Edit → Advanced Search** or `Ctrl+Shift+F`:

```
┌─ Advanced Search ────────────────────────────────────┐
│                                                      │
│ Search Criteria:                                     │
│ ┌─ Text Search ────────────────────────────────────┐ │
│ │ Name: [luffy           ]  ☑ Case sensitive      │ │
│ │ Description: [         ]  ☑ Whole words only    │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ ┌─ Filters ────────────────────────────────────────┐ │
│ │ Character Type: [All ▼]  Status: [All ▼]        │ │
│ │ Age Range: [0  ] to [999]                        │ │
│ │ Quality Score: [0.0] to [1.0]                    │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ ┌─ Date Range ─────────────────────────────────────┐ │
│ │ Scraped: [2023-01-01] to [2023-12-31]           │ │
│ │ Updated: [        ] to [        ]                    │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ Results: 1,234 characters found                      │
│                                                      │
│              [Reset] [Search] [Save Query]           │
└──────────────────────────────────────────────────────┘
```

### **Data Visualization**

Access through **View → Visualizations**:

#### **Character Statistics Dashboard**
```
┌─ Statistics Dashboard ──────────────────────────────┐
│                                                     │
│ ┌─ Character Distribution ─┐ ┌─ Quality Metrics ─┐ │
│ │     Main Characters      │ │ Data Completeness  │ │
│ │ ████████████ 45%         │ │ ████████░░ 80%     │ │
│ │     Supporting           │ │ Image Availability │ │
│ │ ████████░░░░ 35%         │ │ ██████░░░░ 60%     │ │
│ │     Minor                │ │ Description Length │ │
│ │ █████░░░░░░░ 20%         │ │ ███████░░░ 70%     │ │
│ └─────────────────────────┘ └───────────────────────┘ │
│                                                     │
│ ┌─ Scraping Progress Over Time ──────────────────────┐ │
│ │                                                  │ │
│ │  1000┤                                      ••   │ │
│ │   800┤                               ••••••      │ │
│ │   600┤                      •••••••••            │ │
│ │   400┤               ••••••••                    │ │
│ │   200┤        •••••••                            │ │
│ │     0└──────────────────────────────────────────  │ │
│ │       Jan  Feb  Mar  Apr  May  Jun  Jul  Aug     │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│                              [Export Chart] [Print] │
└─────────────────────────────────────────────────────┘
```

### **Bulk Operations**

Select multiple items and use bulk operations:

1. **Select Items**:
   - `Ctrl+A`: Select all
   - `Ctrl+Click`: Multi-select
   - `Shift+Click`: Range select

2. **Available Operations**:
   - **Update Quality Scores**: Recalculate data quality
   - **Re-download Images**: Refresh image files
   - **Export Selection**: Export selected items only
   - **Delete Items**: Remove selected data
   - **Tag Management**: Apply tags to multiple items

### **Custom Scrapers**

Create custom scrapers for new anime wikis:

1. **Tools → Custom Scrapers → New Scraper**
2. **Configure Selectors**:
   ```yaml
   # Example: Custom anime wiki selectors
   selectors:
     character_list:
       url_pattern: "https://customwiki.fandom.com/wiki/Category:Characters"
       character_links: ".category-page__members a"
       next_page: ".category-page__pagination-next"
     
     character_page:
       name: "h1.page-header__title"
       infobox: ".character-infobox"
       description: ".character-description p"
       image: ".character-image img::attr(src)"
   ```

3. **Test Configuration**: Use built-in testing tools
4. **Deploy Scraper**: Add to active scrapers list

## 💾 Data Management

### **Export Options**

#### **Single Export**
Right-click any item → **Export** → Choose format:
- **JSON**: Structured data format
- **CSV**: Spreadsheet compatible
- **Excel**: Advanced spreadsheet format
- **PDF**: Formatted report

#### **Batch Export**
**File → Export → Batch Export**:
```
┌─ Batch Export Configuration ────────────────────────┐
│                                                     │
│ Export Format: [Excel (.xlsx) ▼]                   │
│                                                     │
│ Data Selection:                                     │
│ ☑ All Characters (1,234 items)                     │
│ ☐ All Episodes (567 items)                         │
│ ☑ All Images (2,345 files)                         │
│                                                     │
│ Export Options:                                     │
│ ☑ Include metadata                                  │
│ ☑ Generate summary report                           │
│ ☐ Compress large files                              │
│                                                     │
│ Output Location:                                    │
│ [C:\exports\one_piece_2023.xlsx    ] [Browse...]   │
│                                                     │
│                    [Cancel] [Export]                │
└─────────────────────────────────────────────────────┘
```

### **Import Data**

**File → Import** supports various formats:

#### **Import from Backup**
- Restore previous exports
- Merge with existing data
- Conflict resolution options

#### **Import from Other Sources**
- CSV files from other tools
- JSON exports from APIs
- Manual data entry sheets

### **Data Backup**

Automatic backups are created daily. Manual backup:

1. **File → Backup → Create Backup**
2. **Choose Backup Type**:
   - **Full Backup**: Complete database export
   - **Incremental**: Only changes since last backup
   - **Custom**: Select specific collections

3. **Backup Location**: Configure in settings

### **Data Quality Management**

#### **Quality Scores**
Each data item receives a quality score (0.0-1.0):
- **1.0**: Complete data with all fields
- **0.8**: Most fields present, minor gaps
- **0.6**: Basic information available
- **0.4**: Limited data, major gaps
- **0.2**: Minimal information
- **0.0**: Placeholder or invalid data

#### **Quality Improvement Tools**
- **Tools → Data Quality → Run Quality Check**
- **Tools → Data Quality → Fix Common Issues**
- **Tools → Data Quality → Generate Quality Report**

## ⚙️ Configuration

### **Application Settings**

Access through **Tools → Settings** or `Ctrl+,`:

#### **General Settings**
```
┌─ Application Settings ──────────────────────────────┐
│                                                     │
│ ┌─ General ─────────────────────────────────────────┐ │
│ │ Language: [English ▼]                            │ │
│ │ Theme: [Dark ▼]                                  │ │
│ │ Auto-save interval: [300] seconds                │ │
│ │ ☑ Check for updates on startup                   │ │
│ │ ☑ Send anonymous usage statistics                │ │
│ └───────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─ Database ────────────────────────────────────────┐ │
│ │ MongoDB URI: [mongodb://localhost:27017/      ]  │ │
│ │ Database Name: [fandom_scraper               ]   │ │
│ │ Connection Timeout: [30] seconds                 │ │
│ │ ☑ Enable connection pooling                      │ │
│ │                               [Test Connection]  │ │
│ └───────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─ Scraping ────────────────────────────────────────┐ │
│ │ Default delay: [1.0] seconds                     │ │
│ │ Concurrent requests: [8] threads                 │ │
│ │ Request timeout: [30] seconds                    │ │
│ │ User Agent: [FandomScraper/1.0 (...)]          │ │
│ │ ☑ Respect robots.txt                             │ │
│ │ ☑ Enable auto-throttling                         │ │
│ └───────────────────────────────────────────────────┘ │
│                                                     │
│                         [Cancel] [Apply] [OK]       │
└─────────────────────────────────────────────────────┘
```

#### **Storage Settings**
- **Image Storage**: Local directory configuration
- **Cache Settings**: Temporary file management
- **Export Defaults**: Default export formats and locations

#### **Network Settings**
- **Proxy Configuration**: HTTP/HTTPS proxy settings
- **Rate Limiting**: Advanced throttling options
- **Retry Logic**: Failed request handling

### **Custom Configurations**

#### **Selector Configurations**
Located in `config/selector_configs/`:
- `onepiece.yaml`: One Piece specific selectors
- `naruto.yaml`: Naruto specific selectors
- `generic_fandom.yaml`: General Fandom wiki selectors

#### **User Preferences**
Stored in `config/user_preferences.json`:
```json
{
  "window_geometry": "800x600+100+100",
  "column_widths": {"name": 200, "type": 100},
  "recent_projects": ["One Piece", "Naruto"],
  "favorite_filters": [
    {"name": "Main Characters", "filter": "type=main"},
    {"name": "High Quality", "filter": "quality>0.8"}
  ]
}
```

## 💡 Tips & Best Practices

### **Efficient Scraping**

#### **Rate Limiting**
- Use appropriate delays (1-2 seconds minimum)
- Enable auto-throttling for adaptive rate limiting
- Monitor for 429 (Too Many Requests) errors

#### **Data Quality**
- Enable multi-source fusion for better data coverage
- Regular quality checks and cleanup
- Manual review of low-quality items

#### **Resource Management**
- Close unused projects to free memory
- Regular database cleanup and optimization
- Monitor disk space for image storage

### **Organization Tips**

#### **Project Management**
- Use descriptive project names
- Tag data for easy categorization
- Regular backups before major operations

#### **Search Efficiency**
- Save frequently used search queries
- Use specific filters to narrow results
- Bookmark important characters for quick access

### **Performance Optimization**

#### **Database Tuning**
- Regular index maintenance
- Query optimization for large datasets
- Connection pooling for better performance

#### **Memory Management**
- Close detail views when not needed
- Limit concurrent scraping operations
- Use pagination for large result sets

## 🔧 Troubleshooting

### **Common Issues**

#### **Application Won't Start**
```bash
# Check environment activation
conda activate env-web

# Verify dependencies
python -c "import PyQt5, pymongo, scrapy"

# Check MongoDB connection
python -c "from pymongo import MongoClient; MongoClient().admin.command('ping')"
```

#### **Scraping Errors**
- **403 Forbidden**: Rate limiting triggered, increase delays
- **404 Not Found**: Check wiki URL and character pages
- **Connection Timeout**: Verify internet connection
- **SSL Errors**: Update certificates or disable SSL verification

#### **Data Issues**
- **Missing Images**: Check image URLs and download permissions
- **Incomplete Data**: Review selector configurations
- **Duplicate Entries**: Enable deduplication in settings
- **Low Quality Scores**: Manual data review and cleanup

#### **Performance Issues**
- **Slow Scraping**: Reduce concurrent requests
- **High Memory Usage**: Close unused projects and detail views
- **Database Slow**: Check indexes and query optimization

### **Log Analysis**

#### **Application Logs**
Located in `logs/app.log`:
```
2023-09-08 10:30:15 INFO Starting scraping session for One Piece
2023-09-08 10:30:16 DEBUG Loading selector config: onepiece.yaml
2023-09-08 10:30:17 INFO Found 1,234 character pages to process
2023-09-08 10:30:18 WARNING Rate limit detected, increasing delay to 2.0s
2023-09-08 10:30:20 ERROR Failed to download image: http://example.com/image.jpg
```

#### **Scrapy Logs**
Located in `logs/scrapy.log`:
```
2023-09-08 10:30:15 [scrapy.core.engine] INFO Spider opened
2023-09-08 10:30:16 [scrapy.extensions.logstats] INFO Crawled 0 pages (at 0 pages/min)
2023-09-08 10:30:17 [onepiece_spider] DEBUG Parsing character page: Luffy
```

### **Getting Help**

#### **Built-in Help**
- **Help → User Guide**: This documentation
- **Help → Keyboard Shortcuts**: Complete shortcut list
- **Help → About**: Version and system information

#### **Community Support**
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Community questions and help
- **Documentation**: Comprehensive guides in `docs/`

#### **Diagnostic Information**
When reporting issues, include:
- Application version (`Help → About`)
- Operating system and version
- Python and package versions
- Error messages and logs
- Steps to reproduce the issue

## 🎯 Advanced Workflows

### **Batch Processing Workflow**
1. Create multiple projects for different anime series
2. Configure common settings and selectors
3. Run batch scraping with staggered start times
4. Monitor progress across all projects
5. Bulk export and analysis

### **Data Analysis Workflow**
1. Export data to Excel/CSV format
2. Use external analysis tools (Python, R, Excel)
3. Generate insights and visualizations
4. Import analysis results back into application
5. Share findings with community

### **Collaborative Workflow**
1. Export project configurations
2. Share selector configs with team members
3. Merge data from multiple contributors
4. Maintain shared database instance
5. Coordinate scraping schedules

---

**Need more help?** Check our [troubleshooting guide](TROUBLESHOOTING.md) or [create an issue](https://github.com/yourusername/fandom-scraper-gui/issues) on GitHub!