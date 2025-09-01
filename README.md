# GenAI Job Finder

A comprehensive job finder application that scrapes LinkedIn job postings with AI-ready features for job analysis and matching. The system features a **separate company enrichment pipeline** with intelligent company data management and advanced frontend display capabilities.

## 🚀 Key Features

- **� Separate Company Enrichment Pipeline**: Dedicated company information service with lookup-first approach to eliminate redundant parsing  
- **� Optimized LinkedIn Parser**: Smart company handling with 3-5x performance improvement for existing companies
- **🛡️ Built-in Rate Limiting**: No more LinkedIn blocks - intelligent delays prevent rate limiting
- **📊 Enhanced Frontend Display**: Separate "Company Info" column with rich metadata formatting (🏭 Industry • � Size • �‍� Followers)
- **🌍 Location Intelligence**: Automatic location extraction and work type classification (Remote/Hybrid/On-site)
- **🤖 AI-Powered Data Cleaning**: Advanced job data enhancement with experience analysis, salary extraction, and field validation
- **💰 Smart Salary Processing**: AI-powered salary range extraction and normalization
- **🎓 Experience Classification**: Automatic experience level categorization (Entry level → Junior → Associate/Early career → Mid-level → Senior → Staff/Principal/Lead → Director/VP/Executive)
- **🖥️ Enhanced Web Frontend**: Multi-tab Streamlit interface with dedicated Company Info display
- **💾 Database Storage**: SQLite database with separate companies table and foreign key relationships
- **📤 Automatic CSV Export**: Enhanced data export with comprehensive company information
- **📈 Progress Tracking**: Visual progress bars and detailed statistics

## 📋 Requirements

- **Python 3.12+**
- **Poetry** (for dependency management)
- **Internet connection** (for LinkedIn scraping)
- **Ollama** (optional, for AI data cleaning features)
  - Install from [ollama.ai](https://ollama.ai)
  - Pull model: `ollama pull llama3.2`

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone https://github.com/zarreh/genai_job_finder.git
cd genai_job_finder
```

2. **Install dependencies:**
```bash
make install
# or: poetry install
```

3. **Verify installation:**
```bash
make help
```

## 🎯 Quick Start

### Single Comprehensive Command (Recommended)

```bash
make run-parser
```

**This optimized command provides:**
- 🔍 **Complete job scraping** from LinkedIn
- 🏢 **Smart company handling** (lookup-first approach) 
- 📍 **Location intelligence** with work type classification
- 🛡️ **Built-in rate limiting** (5-10s delays) to avoid LinkedIn blocks
- 📤 **Automatic CSV export** with 21-column enhanced data
- 📊 **Progress tracking** and detailed statistics
- ⚡ **3-5x faster** for companies that already exist in database

### Company Enrichment Pipeline

```bash
# Show company enrichment statistics
make run-company-enrichment STATS=true

# Enrich companies that need additional data
make run-company-enrichment ENRICH=true

# Enrich specific company
make run-company-enrichment COMPANY='Microsoft'
```

**The company enrichment pipeline:**
- 📊 **Shows statistics** about company data coverage
- 🔧 **Enriches missing data** for companies that need it
- ⚡ **Efficient processing** with built-in rate limiting
- 🎯 **Independent operation** - can be run separately from job parsing

### Full Processing Pipeline

```bash
make run-pipeline
```

**Complete workflow:**
1. 🎯 **Optimized job parsing** with smart company handling
2. 🏢 **Company enrichment** for any missing company data  
3. 🤖 **AI data cleaning** and enhancement
4. 📊 **Comprehensive statistics** and analytics

### Advanced Customization

```bash
# Custom search parameters
make run-parser QUERY='software engineer' LOCATION='Austin' JOBS=100

# Include remote and part-time jobs
make run-parser REMOTE=true PARTTIME=true

# Direct Python execution with options
poetry run python run_parser.py --search-query "data scientist" --total-jobs 50
```

**All methods will:**
- 💾 Store results in SQLite database (`data/jobs.db`)
- 📤 Export to CSV (`data/jobs_export.csv`) with all 21 columns
- 📊 Display progress with visual indicators
- 🎯 Apply location and company intelligence automatically

## 🏢 Company Intelligence & Optimization

The system features a **comprehensive separate company enrichment pipeline** that dramatically improves efficiency and data quality:

### ✅ **Separate Company Enrichment Service**:
- **�️ Dedicated Pipeline**: Independent company enrichment service (`CompanyEnrichmentService`)
- **🔍 Lookup-First Approach**: Checks existing company data before attempting to parse
- **⚡ Performance Optimization**: 3-5x faster processing for existing companies  
- **🔄 Smart Enrichment**: Only fetches company data when needed or missing
- **📊 Independent Operation**: Can be run separately from job parsing

### ✅ **Enhanced Frontend Display**:
- **📋 Separate Company Info Column**: Dedicated column for rich company metadata
- **🎨 Rich Formatting**: Company info displayed as "🏭 Industry • 👥 Size • 👨‍💼 Followers"
- **🔧 Clean Organization**: Company name and metadata separated for better readability
- **📱 Responsive Design**: Works across all frontend tabs (Live Search, Stored Jobs, AI Enhanced, Search History)

### ✅ **Typical Coverage Rates (After Enrichment)**:
- **👥 Company Size**: 60-80% of companies (e.g., "10,001+ employees", "51-200 employees")
- **📊 Company Followers**: 60-80% of companies with smart formatting (e.g., "467.3K followers", "29.5M followers") 
- **🏭 Company Industry**: 15-25% of companies (e.g., "Software Development", "IT Services")
- **🔗 Company LinkedIn URL**: 70-90% of companies (e.g., "https://www.linkedin.com/company/microsoft")
- **🏠 Work Location Type**: 100% classification (Remote/Hybrid/On-site)

### 🎯 **Performance Improvements**:
- **Before**: Parsed company info for every job (~10 seconds per job)
- **After**: Only parses new companies (~2-3 seconds per job for existing companies)
- **Success Rate**: Maintains ~60-70% company data enrichment
- **Efficiency**: ~3-5x faster for repeat companies
- **Smart Caching**: Database-first lookup with intelligent fallback to parsing

### 🏢 **Advanced Company Management**:
- **🗃️ Separate Database Table**: Companies stored in dedicated `companies` table
- **🔗 Foreign Key Relationships**: Jobs reference companies via `company_id` 
- **🔄 Independent Pipeline**: Company enrichment runs separately from job parsing
- **📊 Bulk Operations**: Bulk company enrichment with progress tracking
- **📈 Statistics & Analytics**: Comprehensive company data coverage reporting

### Web Frontend

Launch the interactive Streamlit web application:

```bash
make run-frontend
# or: poetry run python genai_job_finder/frontend/run.py
```

**Available at:** `http://localhost:8501`

**Frontend Features:**
- **🔍 Live Job Search Tab**: Interactive search with LinkedIn scraping and AI enhancement
  - Real-time job searching with custom parameters  
  - **⏰ Enhanced time filtering**: Past hour, 24 hours, week, month options
  - Location filtering and remote job options
  - **🤖 Automatic AI enhancement**: Jobs are processed through data cleaner pipeline
  - **🏢 Company Info Column**: Dedicated column showing "🏭 Industry • 👥 Size • 👨‍💼 Followers"
  - Results pagination and filtering
- **📊 Stored Jobs Tab**: View jobs from database with enhanced company display
  - Display all jobs from previous parser runs
  - **🏢 Separate Company Info**: Company name and metadata in dedicated columns
  - Shows enhanced company information with emoji formatting
  - **🖱️ Click-to-view details**: Click any row to see full job details with formatted content and LinkedIn link
  - Advanced filtering by title, company, location, and work type
  - CSV export functionality with company information
- **🤖 AI-Enhanced Jobs Tab**: Manage AI-processed job data with company enrichment
  - View jobs enhanced with experience level classification
  - **🏢 Company Intelligence**: Enhanced company data display across all enhanced jobs
  - Salary extraction and normalization
  - Location and employment type validation
  - Comprehensive filtering and analytics
- **📈 Search History Tab**: Parser run analytics
  - View recent parser execution history
  - Job count and timing statistics
  - Run status and error tracking

## 🏗️ Project Structure

```
genai_job_finder/
├── 📁 genai_job_finder/           # Main package
│   ├── 📁 data_cleaner/          # 🤖 AI-powered job data enhancement
│   │   ├── graph.py              # LangGraph workflow for data cleaning
│   │   ├── models.py             # Data models and validation
│   │   ├── llm.py                # LLM integration (Ollama)
│   │   ├── config.py             # Cleaner configuration
│   │   └── chains/               # Individual AI processing chains
│   ├── 📁 frontend/              # 🖥️ Modular Streamlit web interface with company display
│   │   ├── app.py                # Main application entry point
│   │   ├── config.py             # Frontend configuration
│   │   ├── components/           # Reusable UI components
│   │   │   └── job_display.py    # Job display with separate Company Info column
│   │   ├── tabs/                 # Individual tab implementations
│   │   │   ├── live_search.py    # Live job search with AI enhancement
│   │   │   ├── stored_jobs.py    # Stored jobs with company info display
│   │   │   ├── ai_enhanced.py    # AI-enhanced jobs with company data
│   │   │   └── search_history.py # Search history and runs
│   │   └── utils/                # Common utilities
│   │       ├── common.py         # Shared functions and database path resolution
│   │       └── data_operations.py # Database operations with company enrichment
│   ├── 📁 linkedin_parser/       # ⭐ Enhanced LinkedIn scraping with company pipeline
│   │   ├── models.py             # Job and Company data models
│   │   ├── parser.py             # LinkedIn parser with company integration
│   │   ├── company_enrichment.py # 🆕 Separate company enrichment service
│   │   ├── company_parser.py     # Company-specific parsing logic
│   │   ├── database.py           # Database operations with companies table
│   │   ├── config.py             # Parser configuration
│   │   └── run_parser.py         # Parser runner module
│   └── 📁 legacy/                # Original scraping code (reference)
├── 📁 notebooks/                 # Jupyter notebooks for analysis
│   └── job_analysis.ipynb        # 🆕 Enhanced analysis with location intelligence
├── 📁 data/                      # 💾 Database and output files
│   ├── jobs.db                   # SQLite database
│   └── jobs_export.csv           # Latest CSV export
├── 📄 Makefile                   # 🛠️ Build automation with multiple commands
├── 📄 run_parser.py              # 🎯 Simple parser runner (calls module)
└── 📄 pyproject.toml             # Poetry configuration
```

### 🎨 Frontend Architecture

The frontend has been **refactored into a modular structure** for better maintainability:

- **🎯 Modular Design**: Each tab is a separate module (~80-150 lines vs 1200+ monolithic)
- **🔧 Reusable Components**: Common UI elements extracted to `components/`
- **🛠️ Shared Utilities**: Database operations and common functions in `utils/`
- **📊 Tab-Based Organization**: Live search, stored jobs, AI-enhanced, and history tabs
- **🚀 Developer Friendly**: Easy to add new features or modify existing ones

## 📊 Enhanced Data Structure

The parser produces **21 columns** of comprehensive job data, including automatic company information extraction:

### 🔧 Core Job Information (Legacy Compatible)
| Column | Description | Example |
|--------|-------------|---------|
| `id` | Unique job identifier (UUID) | `abc123-def4-5678-90ab-cdef12345678` |
| `company` | Company name | `Microsoft` |
| `title` | Job title | `Senior Data Scientist` |
| `level` | Experience level | `Mid-Senior level` |
| `salary_range` | Salary information | `$120,000 - $180,000/year` |
| `content` | Full job description | `We are looking for...` |
| `employment_type` | Employment type | `Full-time` |
| `job_function` | Job category | `Engineering and Information Technology` |
| `industries` | Related industries | `Computer Software` |
| `posted_time` | When posted | `2 days ago` |
| `applicants` | Number of applicants | `47 applicants` |
| `job_id` | LinkedIn's job ID | `3567890123` |
| `date` | Parsing date | `2025-08-21` |
| `parsing_link` | Search URL used | `https://linkedin.com/...` |
| `job_posting_link` | Direct job link | `https://linkedin.com/jobs/...` |

### 🆕 Location Intelligence Features
| Column | Description | Example |
|--------|-------------|---------|
| `location` | Extracted location | `San Francisco, CA` |
| `work_location_type` | AI-classified work type | `Remote`, `Hybrid`, `On-site` |

### � Company Information (Auto-Extracted & Enhanced Display)
| Column | Description | Example | Frontend Display |
|--------|-------------|---------|------------------|
| `company_size` | Number of employees | `1,000-5,000 employees` | **Company Info column**: 👥 1,000-5,000 employees |
| `company_followers` | LinkedIn followers | `150,000 followers` | **Company Info column**: 👨‍💼 150.0K followers |
| `company_industry` | Company industry | `Computer Software` | **Company Info column**: 🏭 Computer Software |
| `company_info_link` | LinkedIn company page URL | `https://www.linkedin.com/company/microsoft` | Backend reference |

**✨ Enhanced Frontend Display Example:**
- **Company Column**: "Microsoft"
- **Company Info Column**: "🏭 Technology • 👥 10,001+ employees • 👨‍💼 29.5M followers"

## 🏢 Company Enrichment Service

The system includes a comprehensive company enrichment service that can be used independently:

### Company Enrichment CLI

```bash
# Show company enrichment statistics
poetry run python -m genai_job_finder.linkedin_parser.company_enrichment --show-missing

# Enrich all companies needing data
poetry run python -m genai_job_finder.linkedin_parser.company_enrichment

# Enrich specific company
poetry run python -m genai_job_finder.linkedin_parser.company_enrichment --company "Microsoft"

# Force re-enrichment of company
poetry run python -m genai_job_finder.linkedin_parser.company_enrichment --company "Microsoft" --force

# Create missing company records
poetry run python -m genai_job_finder.linkedin_parser.company_enrichment --create-missing
```

### Makefile Company Commands

```bash
# Show company statistics
make run-company-enrichment STATS=true

# Enrich companies that need data
make run-company-enrichment ENRICH=true

# Enrich specific company
make run-company-enrichment COMPANY='Microsoft'
```

### Company Service Features

- **📊 Statistics Display**: Shows coverage rates and companies needing enrichment
- **🔍 Smart Detection**: Identifies companies with missing data automatically  
- **⚡ Efficient Processing**: Only enriches companies that need additional information
- **🛡️ Rate Limiting**: Built-in delays to respect LinkedIn's rate limits
- **📈 Progress Tracking**: Visual progress bars for bulk operations
- **🔄 Fallback Handling**: Graceful handling of enrichment failures

## 🤖 Programmatic Usage

### Basic Usage with Company Enrichment
```python
from genai_job_finder.linkedin_parser import LinkedInJobParser, DatabaseManager
from genai_job_finder.linkedin_parser.company_enrichment import CompanyEnrichmentService

# Initialize components with company enrichment
db = DatabaseManager("data/jobs.db")
company_service = CompanyEnrichmentService(database=db)
parser = LinkedInJobParser(database=db, company_service=company_service)

# Parse jobs with integrated company intelligence
jobs = parser.parse_jobs(
    search_query="senior data scientist",
    location="San Francisco",
    total_jobs=100  # Specify number of jobs to collect
)

print(f"Found {len(jobs)} jobs with company enrichment")

# Export to CSV with all enhanced columns including company info
csv_file = db.export_jobs_to_csv("data/my_jobs.csv")
print(f"Exported to: {csv_file}")

# Get company statistics
company_service.show_statistics()

# Get as pandas DataFrame for analysis
df = db.get_jobs_as_dataframe()
print(f"DataFrame shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
```

### Quick Start Function
```python
# Alternative: Use the built-in runner function
from genai_job_finder.linkedin_parser import run_parser
run_parser()  # Uses default settings: "data scientist" in "San Antonio"
```

## 🤖 AI-Powered Data Cleaning & Enhancement

The system includes a comprehensive AI data cleaner that enhances raw job data with intelligent analysis and structured information extraction.

### 🎯 AI Enhancement Features

- **🎓 Experience Analysis**: Extracts minimum years of experience and classifies into 7 levels
- **💰 Salary Intelligence**: Parses salary ranges with currency and period normalization  
- **🏠 Location Validation**: Validates and corrects work location types (Remote/Hybrid/On-site)
- **💼 Employment Type Standardization**: Validates Full-time/Part-time/Contract/Internship classifications

### 📊 Experience Level Classification

Jobs are automatically classified into 7 experience levels:

| Level | Years | Label |
|-------|-------|-------|
| 0 | 0 years | Entry level |
| 1 | 1 year | Junior |
| 2 | 2-3 years | Associate/Early career |
| 3 | 4-5 years | Mid-level |
| 4 | 6-8 years | Senior |
| 5 | 9-12 years | Staff/Principal/Lead |
| 6 | 13+ years | Director/VP/Executive |

### 🚀 AI Cleaner Usage

#### Enhanced Frontend Pipeline
Use the enhanced frontend for complete parse & clean workflow:

```bash
make run-enhanced-frontend
```

Features a **Parse & Clean** tab that:
- Parses jobs from LinkedIn
- Automatically applies AI enhancement
- Shows real-time progress
- Displays enhanced results immediately

#### Command Line Interface
```bash
# Basic AI cleaning
python -m genai_job_finder.data_cleaner.run_graph

# With custom options
python -m genai_job_finder.data_cleaner.run_graph \
    --db-path data/jobs.db \
    --model llama3.2 \
    --verbose
```

#### Programmatic Usage
```python
from genai_job_finder.data_cleaner import JobDataCleaner

# Initialize AI cleaner
cleaner = JobDataCleaner()

# Clean individual job
enhanced_job = await cleaner.clean_job_data(job_data)

# Process database jobs
cleaner.process_database("data/jobs.db")
```

### 🧪 Individual Component Testing

Test each AI component independently:

```bash
# Test experience extraction
python -m genai_job_finder.data_cleaner.chains.experience_extraction

# Test salary extraction  
python -m genai_job_finder.data_cleaner.chains.salary_extraction

# Test location validation
python -m genai_job_finder.data_cleaner.chains.location_validation

# Test employment validation
python -m genai_job_finder.data_cleaner.chains.employment_validation
```

### 📈 Enhanced Output Fields

The AI cleaner adds these fields to your job data:

#### Experience Enhancement
- `min_years_experience`: Required years (0-15+)
- `experience_level`: Classified level (0-6)
- `experience_level_label`: Human-readable label

#### Salary Enhancement  
- `min_salary`, `max_salary`, `mid_salary`: Salary range breakdown
- `salary_currency`: Currency (USD, EUR, etc.)
- `salary_period`: Period (yearly, monthly, hourly)

#### Validation Enhancement
- `work_location_type_corrected`: Location validation flag
- `employment_type_corrected`: Employment type validation flag

## 🎛️ Available Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `make run-parser` | 🎯 Run LinkedIn parser with company intelligence | **Recommended** |
| `make run-parser-mod` | 🔧 Run LinkedIn parser as module | Advanced usage |
| `make run-company-enrichment` | 🏢 Run company enrichment pipeline separately | **Company data management** |
| `make run-pipeline` | 🚀 Run parser + company enrichment + AI cleaner | **Full processing** |
| `make run-cleaner` | 🤖 Run AI data cleaner only | Process existing data |
| `make run-frontend` | 🖥️ Launch enhanced Streamlit web app | **Interactive UI with Company Info** |
| `make install` | 📦 Install dependencies | First-time setup |
| `make test` | 🧪 Run tests | Development |
| `make clean` | 🧹 Clean temporary files | Maintenance |
| `make help` | ❓ Show all available commands | Get help |

## 🔧 Advanced Configuration

### Location Intelligence Features

The parser automatically provides:

- **🎯 Smart Location Extraction**: Parses job locations from various formats
- **🤖 AI-Powered Classification**: Intelligently categorizes work arrangements:
  - **🏠 Remote**: Jobs with remote work keywords (`remote`, `work from home`, `distributed`)
  - **🔄 Hybrid**: Jobs mentioning flexible arrangements (`hybrid`, `flexible`, `remote optional`)
  - **🏢 On-site**: Traditional office-based positions

### Customizing Search Parameters

```python
# Advanced search customization
jobs = parser.parse_jobs(
    search_query="machine learning engineer",  # Job keywords
    location="New York",                       # Location filter
    total_jobs=200,                           # Number of jobs to collect
    time_filter="r604800",                    # Last 7 days (default: r86400 = 24h)
    remote=False,                             # Include remote jobs
    parttime=False                            # Include part-time jobs
)
```

### Time Filters

The enhanced time filtering system supports:
- **⏰ Past hour** (`r3600`): Most recent job postings
- **📅 Past 24 hours** (`r86400`): Default filter 
- **📆 Past week** (`r604800`): Weekly job updates
- **� Past month** (`r2592000`): Monthly comprehensive search

*Note: The time filter bug has been fixed - selections now properly filter LinkedIn API calls instead of defaulting to 24 hours.*

## 📈 Recent Major Updates

### � Company Enrichment & Frontend Enhancement (v4.0)
- ✅ **Separate Company Info Column** - Dedicated "Company Info" column with rich metadata display
- ✅ **Company Enrichment Service** - Independent pipeline with lookup-first optimization
- ✅ **Performance Optimization** - 3-5x faster processing for existing companies
- ✅ **Enhanced Frontend Display** - Company info formatted as "🏭 Industry • 👥 Size • 👨‍💼 Followers"
- ✅ **Database Architecture** - Separate companies table with foreign key relationships
- ✅ **Smart Followers Formatting** - Automatic conversion to K/M format (e.g., "467.3K followers")

### �🎯 Frontend Refactoring & Time Filter Fix (v3.0)
- ✅ **Modular frontend architecture** - Split 1200+ line monolith into organized modules
- ✅ **Enhanced time filtering** - Added "Past hour" option and fixed hardcoded filter bug
- ✅ **Improved developer experience** - Each tab in separate file for better maintainability
- ✅ **Streamlined Makefile** - Single `run-frontend` command with all features integrated
- ✅ **Clean project structure** - Removed unnecessary shell scripts, organized utilities

### 🤖 AI Data Cleaning Integration (v2.5)
- ✅ **Complete AI pipeline** - Automatic job enhancement with experience, salary, and location analysis
- ✅ **Real-time processing** - Live search results enhanced with AI in frontend
- ✅ **Comprehensive enhancement** - 7-level experience classification, salary extraction, location validation
- ✅ **Visual progress tracking** - Real-time AI processing status and statistics

### 🎯 LinkedIn Parser Enhancement (v2.0)
- ✅ **Complete architecture rewrite** with modular structure
- ✅ **17-column data structure** matching legacy format exactly
- ✅ **Location intelligence engine** with automatic extraction and classification
- ✅ **Multiple execution methods** (script, module, programmatic)
- ✅ **Enhanced database schema** with automatic migration support
- ✅ **Improved error handling** and rate limiting
- ✅ **Comprehensive documentation** and examples

### 🆕 Key Features Added
- **� Separate Company Enrichment**: Independent company intelligence pipeline with lookup-first optimization
- **📋 Company Info Column**: Dedicated frontend column for enhanced company metadata display  
- **�🌍 Location Intelligence**: Automatic location extraction and work type classification
- **🔧 Modular Architecture**: Proper Python package structure with company service separation
- **📊 Enhanced Analytics**: Updated analytics with company intelligence insights
- **⚡ Multiple Entry Points**: Run as script, module, or import programmatically
- **💾 Smart Data Export**: All outputs include comprehensive company information
- **🎛️ Comprehensive CLI**: Multiple Makefile commands including company enrichment

### 🔄 Migration & Compatibility
- **✅ Full backward compatibility** with existing data and workflows
- **✅ Automatic database migration** when running updated parser with companies table
- **✅ Legacy format preserved** - no breaking changes to output structure
- **✅ Enhanced with new fields** - company enrichment and display improvements

## 🔍 Example Outputs

### Command Line
```bash
$ make run-parser
Starting LinkedIn job parsing...
Getting job IDs: 100%|████████████████| 2/2 [00:05<00:00,  2.60s/it]
Getting job details: 100%|██████████████| 20/20 [00:45<00:00,  2.28s/it]
✅ Successfully parsed 20 jobs
📊 Jobs exported to: data/jobs_export.csv
```

### CSV Output Sample
```csv
id,company,title,location,work_location_type,level,salary_range,company_size,company_followers,company_industry...
abc123...,Microsoft,Senior Data Scientist,Seattle WA,Hybrid,Mid-Senior level,$150k-200k,10001+ employees,29500000 followers,Technology...
def456...,Google,ML Engineer,San Francisco CA,Remote,Senior level,$180k-250k,10001+ employees,30000000 followers,Technology...
```

### Frontend Company Info Display
```
Company          | Company Info                                      | Title                | Location
Microsoft        | 🏭 Technology • 👥 10,001+ employees • 👨‍💼 29.5M   | Senior Data Scientist | Seattle, WA
Google           | 🏭 Technology • 👥 10,001+ employees • 👨‍💼 30.0M   | ML Engineer          | San Francisco, CA
The Swift Group | 🏭 IT Services • 👥 51-200 employees • 👨‍💼 13.6K   | DevOps Engineer      | San Antonio, TX
```

### Location Intelligence Results
- **🏢 On-site**: 42% of jobs (traditional office-based)
- **🏠 Remote**: 24% of jobs (work from anywhere)  
- **🔄 Hybrid**: 24% of jobs (flexible arrangements)
- **📊 High accuracy**: 90%+ location data coverage

## 🛡️ Best Practices

- **Rate limiting**: Built-in delays between requests (2-3 seconds)
- **Respectful scraping**: User-agent rotation and proper headers
- **Error handling**: Comprehensive retry logic and graceful failures
- **Data integrity**: Automatic duplicate prevention and validation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with tests
4. Submit a pull request

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Poetry environment is activated
   ```bash
   poetry shell
   ```

2. **No Jobs Found**: Check internet connection and search parameters

3. **Database Issues**: Database auto-migrates, but you can reset:
   ```bash
   rm data/jobs.db  # Reset database if needed
   ```

### Getting Help

- Use `make help` to see all available commands
- Check `notebooks/` for data analysis examples
- Review `run_parser.py` for usage patterns

## 📝 License

This project is for educational and personal use. Please respect LinkedIn's Terms of Service.

---

**🎯 Ready to start? Just run `make run-parser` and begin collecting job data with enhanced location intelligence!**
3. **View parsing history** - See recent parsing runs

### Example Custom Search

```python
from genai_job_finder import LinkedInJobParser, DatabaseManager

# Initialize database and parser
db = DatabaseManager("data/jobs.db")
parser = LinkedInJobParser(database=db)

# Parse jobs
jobs = parser.parse_jobs(
    search_query="senior data scientist",
    location="San Francisco",
    max_pages=3
)

print(f"Found {len(jobs)} jobs")
```

### Analyzing Job Data

Open the Jupyter notebook for detailed job analysis:

```bash
jupyter notebook notebooks/job_analysis.ipynb
```

The notebook provides:
- Total job counts and statistics
- Top 10 most recent jobs with details
- Company and location distribution
- Salary information analysis
- Remote work statistics

## 📊 Data Models

### Job Model
```python
@dataclass
class Job:
    job_id: str
    title: str
    company: str
    location: str
    description: str
    posted_date: Optional[datetime]
    salary_range: Optional[str]
    job_type: Optional[JobType]
    experience_level: Optional[ExperienceLevel]
    remote_option: bool
    easy_apply: bool
    linkedin_url: Optional[str]
    # ... additional fields
```

### JobRun Model
```python
@dataclass
class JobRun:
    id: Optional[int]
    run_date: datetime
    search_query: str
    location_filter: str
    job_count: int
    status: str
    # ... additional tracking fields
```

## 🔧 Configuration

### Search Parameters

Configure search parameters in `genai_job_finder/legacy/config.py`:

```python
LINKEDIN_JOB_SEARCH_PARAMS = [
    {
        "keywords": "senior data scientist",
        "location": "San Antonio",
        "f_TPR": "r86400",  # last 24 hours
        "remote": False,
    },
    # Add more search configurations...
]
```

### Time Filters
- `r86400`: Last 24 hours
- `r604800`: Last 7 days  
- `r2592000`: Last 30 days

## 🤖 AI Integration

The project includes AI frameworks for future enhancements:

- **LangChain**: For building AI applications
- **LangGraph**: For complex AI workflows
- **OpenAI Integration**: GPT models support
- **Ollama Support**: Local LLM integration
- **Chroma Vector Store**: Semantic job search

## 📈 Database Schema

### Tables

1. **jobs** - Stores individual job listings
2. **job_runs** - Tracks parsing sessions

### Key Features
- Automatic duplicate prevention
- Run tracking and status monitoring
- Comprehensive job metadata storage
- SQLite for lightweight, portable database

## 🚦 Getting Started

1. **First Run:**
```bash
poetry run python example_usage.py
```
Choose option 1 to parse jobs using default configuration.

2. **View Results:**
Open `notebooks/job_analysis.ipynb` and run all cells to see your collected job data.

3. **Customize:**
- Modify search parameters in the config file
- Add new search terms and locations
- Adjust the number of pages to parse

## 🔍 Example Output

```
Total jobs in database: 212
Recent parsing runs:
- Run 7: senior data scientist (21 jobs) - completed
- Run 6: senior data scientist (12 jobs) - completed

Top Companies:
• EY: 3 jobs
• Lensa: 2 jobs
• USAA: 2 jobs

Remote Jobs: 45% of listings
Easy Apply: 67% of listings
```

## 🛡️ Best Practices & Rate Limiting

- **⏱️ Built-in delays**: 2-3 seconds between requests
- **🤖 Respectful scraping**: Proper user-agent headers and request patterns
- **🔄 Error handling**: Comprehensive retry logic and graceful failure handling
- **📊 Progress tracking**: Visual progress bars for long-running operations
- **💾 Data integrity**: Automatic duplicate prevention and data validation

## 🧪 Data Analysis

The enhanced Jupyter notebook (`notebooks/job_analysis.ipynb`) provides:

- **📊 Location intelligence analytics** with work type distribution
- **🏢 Company and location insights** with visual statistics
- **💰 Salary analysis** by work type and location
- **📈 Trending job functions** and industries
- **🎯 Data quality metrics** and validation reports

**To use:**
```bash
jupyter notebook notebooks/job_analysis.ipynb
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature-name`
3. **Make** your changes with proper tests
4. **Ensure** all commands work: `make test`
5. **Submit** a pull request with detailed description

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **Import Errors** | Ensure Poetry environment: `poetry shell` |
| **No Jobs Found** | Check search parameters and internet connection |
| **Database Locked** | Close any open database connections |
| **Permission Errors** | Ensure write access to `data/` folder |

### Getting Help

- 📖 **Documentation**: This README covers all features
- 💻 **Examples**: Check `run_parser.py` and notebook examples
- 🔧 **Commands**: Run `make help` for all available commands
- 🧪 **Testing**: Use `make test` to validate installation

## 📊 Performance Metrics

- **🎯 Success Rate**: 95%+ job collection reliability
- **⚡ Performance**: ~10-20 jobs per page, 2-3 seconds per request
- **🎖️ Data Quality**: 90%+ location intelligence coverage
- **💾 Storage**: Efficient SQLite database with migration support
- **📈 Scalability**: Handles hundreds of jobs with progress tracking

---

## 🎉 Why Choose GenAI Job Finder?

### ✅ **Single Command Solution**
- **Before**: Multiple commands for parsing, company data, manual enhancement, etc.
- **After**: One `make run-parser` command with integrated company intelligence!

### ✅ **Dedicated Company Info Display** 
- **Separate Company Info Column**: Rich metadata display with emojis and formatting
- **Clean Organization**: Company name and details properly separated
- **Consistent Display**: Works across all frontend tabs and exports
- **Smart Formatting**: Automatic number formatting (29.5M followers, 13.6K followers)

### ✅ **Built-in Company Intelligence** 
- **60-70% coverage** for company size and followers with smart enrichment service
- **3-5x performance improvement** through lookup-first optimization
- **Smart rate limiting** prevents LinkedIn blocks
- **Independent pipeline** for company data management

### ✅ **Production Ready**
- **Enhanced output** with comprehensive job + company data
- **Separate companies table** with foreign key relationships
- **Built-in error handling** and recovery with company service fallbacks
- **Progress tracking** with detailed company enrichment statistics
- **Automatic CSV export** with full company information

### ✅ **Developer Friendly**
- **Modular architecture** for easy customization
- **Comprehensive documentation** with examples
- **Streamlit web interface** for interactive use
- **AI integration** for data enhancement

---

## 📝 License & Usage

This project is designed for **educational and personal use**. Please use responsibly and in accordance with LinkedIn's Terms of Service.

**🚀 Ready to start? Run `make run-parser` and collect comprehensive job data with company intelligence in one command!**
