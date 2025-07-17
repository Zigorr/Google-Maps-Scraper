# Google Maps Lead Scraper

**⚠️ CURRENT STATUS: DEBUGGING REQUIRED - Application hangs during business data extraction**

**Automated Lead Generation Tool for Small Business Outreach**

A Python desktop application that automates the process of finding and qualifying business leads through Google Maps scraping, specifically targeting businesses without established web presence for outreach opportunities.

## 🚨 Critical Issue - Not Currently Working

**Problem**: The application hangs at "Extracting business data... (1/20)" and does not progress beyond the first business extraction.

**Status**: Under active debugging - multiple fixes attempted but issue persists.

**Last Working Version**: Previous versions worked correctly, but current implementation has extraction hanging issues.

## 🎯 Project Overview

This tool addresses the manual, time-intensive process of lead generation for business outreach by automating Google Maps searches and applying intelligent filtering to identify high-potential prospects.

### Problem Solved
- **Manual Process**: Hours spent manually searching Google Maps and qualifying leads
- **Inconsistent Results**: Human error in data collection and qualification criteria
- **Scalability Issues**: Limited ability to process large volumes of potential leads

### Solution Delivered (When Working)
- **Automated Search**: Systematically searches Google Maps based on keyword + location
- **Intelligent Filtering**: Automatically identifies businesses without established websites
- **Data Export**: Clean, structured CSV output ready for CRM import or outreach campaigns

## 🔧 Technical Implementation

### Core Technologies
- **Python 3.x** - Main development language
- **Selenium WebDriver** - Browser automation for web scraping
- **Tkinter** - Cross-platform GUI framework (no external dependencies)
- **Pandas** - Data manipulation and CSV export
- **Chrome Automation** - Reliable, human-like browsing behavior

### Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GUI Layer     │    │  Scraping Engine │    │ Data Processing │
│   (Tkinter)     │───▶│   (Selenium)     │───▶│   (Pandas)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Components
- **`main.py`** - GUI application with user-friendly interface
- **`scraper.py`** - Core Google Maps scraping logic ⚠️ (DEBUGGING REQUIRED)
- **`data_filter.py`** - Business filtering and qualification algorithms
- **`lead_scraper.py`** - Integrated pipeline combining scraping and filtering
- **`build_exe.py`** - Standalone executable creation

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.8+** (tested on 3.9-3.11)
- **Chrome Browser** (automatically managed by webdriver-manager)
- **Windows 10+** (primary target, cross-platform compatible)

### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd google-maps-scraper

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Dependencies
```
selenium>=4.15.0
webdriver-manager>=4.0.1
pandas>=2.0.0
```

## 🎮 Usage Guide

### Basic Operation (When Working)
1. **Launch Application**: Run `python main.py` or use `GoogleMapsLeadScraper.exe`
2. **Enter Search Criteria**:
   - Business Type: "nail salons", "barbershops", "massage therapy"
   - City: "Nashville", "Miami", "Los Angeles"
   - Max Businesses: 25-50 (recommended starting point)
3. **Start Search**: Click "Find Leads" and wait for results
4. **Export Results**: Click "Save to CSV" to export qualified leads

### Lead Qualification Criteria
**✅ QUALIFIED LEADS (Businesses we KEEP):**
- No website presence (phone/address only)
- Instagram-only business presence
- Uses booking platforms (Squarespace, Booksy) instead of real websites
- Social media links instead of business websites

**❌ DISQUALIFIED (Businesses we FILTER OUT):**
- Established custom websites (e.g., business-name.com)
- Large chains with corporate websites
- Businesses with professional web presence

### CSV Export Format
```csv
Business Name,Phone,Address,IG found?,Squarespace link found?,Booksy link found?,Qualification Reason,Notes
Salon Example,(555) 123-4567,123 Main St,Yes,No,No,Instagram-only presence,@salonexample
```

## 🚨 Current Debugging Status

### Issue Description
- **Symptom**: Application hangs at "Extracting business data... (1/20)"
- **Behavior**: No progress beyond first business extraction attempt
- **Impact**: Core functionality completely broken

### Attempted Fixes
1. ✅ **Removed Aggressive Chrome Optimizations** - Simplified browser configuration
2. ✅ **Implemented Cross-Platform Timeout** - 30-second timeout per business using threading
3. ✅ **Enhanced Browser Connectivity Checks** - Multi-layer connection verification
4. ✅ **Increased All Timeout Values** - 45s page load, 20s explicit wait
5. ✅ **Added Session Recovery** - Automatic browser restart on failures
6. ✅ **Progressive Delay System** - Escalating delays based on consecutive failures
7. ✅ **Timeout-Aware Element Detection** - Quick fallbacks for element finding

### Current Chrome Configuration (Minimal)
```python
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--log-level=3")
# All aggressive optimizations removed for stability
```

### Next Debugging Steps
1. 🔍 **Test Non-Headless Mode** - Observe browser behavior visually
2. 🔍 **Verify Element Selectors** - Check if Google Maps structure changed
3. 🔍 **Investigate Anti-Bot Detection** - May be triggering Google's protection
4. 🔍 **Thread Timeout Verification** - Ensure threading timeout actually works
5. 🔍 **Alternative Extraction Strategies** - Consider different approaches

## 📊 Development History

### ✅ Completed Features
- **Phase 1**: Core scraping engine with Selenium automation
- **Phase 2**: Intelligent filtering for lead qualification (95%+ accuracy)
- **Phase 3**: CSV export functionality with custom columns
- **Phase 4**: Complete GUI application with progress tracking

### ⚠️ Current Issues
- **Core Extraction Hanging**: Business data extraction stops after first attempt
- **Threading Timeout**: May not be working as expected on Windows
- **Element Detection**: Possible changes in Google Maps structure

### Previous Performance (When Working)
- **25 businesses**: 1.5-2 minutes
- **50 businesses**: 3-4 minutes  
- **100 businesses**: 6-8 minutes
- **Accuracy**: 95%+ for platform detection
- **Success Rate**: 90%+ business extraction rate

## 🎯 Target Use Cases

### Primary Users
- **Web Development Agencies** - Finding businesses needing websites
- **Digital Marketing Consultants** - Identifying social media-only businesses
- **Business Development Teams** - Qualifying leads for outreach campaigns
- **Freelancers** - Discovering potential clients without web presence

### Business Types (Recommended)
- **Service Businesses**: Salons, barbershops, massage therapy
- **Local Retail**: Boutiques, specialty shops
- **Food & Beverage**: Cafes, restaurants, food trucks
- **Professional Services**: Consultants, coaches, trainers

## 🔧 Technical Architecture

### Browser Automation
- **Selenium WebDriver** with Chrome automation
- **Anti-Detection Measures** - Human-like browsing patterns
- **Error Recovery** - Automatic session restart on failures
- **Timeout Protection** - Prevents indefinite hanging (when working)

### Data Processing Pipeline
1. **Search Execution** - Automated Google Maps search
2. **Business Discovery** - Extract listing URLs with scrolling
3. **Data Extraction** - Collect business information from each page
4. **Lead Qualification** - Apply filtering criteria
5. **Export Generation** - Create structured CSV output

### GUI Features
- **Real-Time Progress** - Live updates during scraping
- **Error Handling** - User-friendly error messages
- **Input Validation** - Prevents invalid search parameters
- **Export Dialog** - Save results with automatic naming

## 🚨 Known Limitations

### Current Issues
- **Extraction Hanging**: Core functionality broken
- **Windows-Specific**: Threading timeout may not work properly
- **Google Maps Changes**: Possible structure changes affecting selectors

### General Limitations (When Working)
- **Rate Limiting**: Respectful delays to avoid detection
- **Geographic Scope**: Works best with English-language results
- **Business Types**: Service businesses have higher success rates
- **Data Accuracy**: Depends on Google Maps data quality

## 📈 Future Development (Post-Fix)

### Immediate Priorities
1. 🔍 **Fix Hanging Issue** - Restore core functionality
2. 🔍 **Verify Timeout Mechanisms** - Ensure proper timeout handling
3. 🔍 **Update Element Selectors** - Adapt to Google Maps changes
4. 🔍 **Enhance Error Recovery** - More robust failure handling

### Planned Enhancements
- **Multi-Platform Support** - MacOS and Linux compatibility
- **Advanced Filtering** - Additional qualification criteria
- **CRM Integration** - Direct export to popular CRM systems
- **Bulk Processing** - Multiple search queries in batch

## 🤝 Contributing

### Bug Reports
- **Current Focus**: Extraction hanging issue
- **Testing Needed**: Different business types and locations
- **Environment**: Windows 10+ with Chrome browser

### Development Setup
```bash
# Development environment
pip install -r requirements.txt
python -m pytest tests/  # When tests are available
```

## 📄 License

This project is proprietary software developed for specific business use cases.

## 📞 Support

For technical support or business inquiries, contact the development team.

---

**⚠️ IMPORTANT**: This application is currently not functional due to the hanging issue during business data extraction. Development is ongoing to resolve this critical problem. 