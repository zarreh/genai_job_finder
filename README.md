# GenAI Job Finder

A comprehensive job finder application that uses AI and web scraping technologies to collect, analyze, and find relevant job opportunities from LinkedIn.

## 🚀 Features

- **LinkedIn Job Scraping**: Automated job collection from LinkedIn using requests and BeautifulSoup
- **Web Frontend**: Streamlit-based user interface for easy job searching
- **Database Storage**: SQLite database for storing job listings and tracking parsing runs
- **Job Analysis**: Jupyter notebooks for analyzing collected job data
- **AI Integration**: Ready for AI-powered job matching and analysis (using LangChain, OpenAI, Ollama)
- **Vector Store Support**: Chroma vector database for semantic job search
- **Modular Architecture**: Clean, organized codebase with separate modules

## 📋 Requirements

- Python 3.12+
- Poetry (for dependency management)

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone https://github.com/zarreh/genai_job_finder.git
cd genai_job_finder
```

2. **Install dependencies using Poetry:**
```bash
poetry install
```

3. **Activate the virtual environment:**
```bash
poetry shell
```

## 🏗️ Project Structure

```
genai_job_finder/
├── genai_job_finder/           # Main package
│   ├── __init__.py            # Package exports
│   ├── frontend/              # Streamlit web frontend
│   │   ├── __init__.py
│   │   ├── app.py            # Main Streamlit application
│   │   ├── config.py         # Frontend configuration
│   │   ├── run.py            # Application launcher
│   │   └── README.md         # Frontend documentation
│   ├── linkedin_parser/       # LinkedIn job scraping module
│   │   ├── __init__.py
│   │   ├── models.py         # Job and JobRun data models
│   │   ├── parser.py         # Main LinkedIn parser
│   │   ├── database.py       # Database operations
│   │   └── config.py         # Parser configuration
│   └── legacy/               # Legacy scraping code
├── notebooks/                # Jupyter notebooks for analysis
│   └── job_analysis.ipynb   # Job data analysis notebook
├── data/                     # Database and data files
│   └── jobs.db              # SQLite database
├── example_usage.py          # Example script to run the parser
├── pyproject.toml           # Poetry configuration
└── README.md
```

## 🎯 Usage

### Web Frontend (Recommended)

Launch the Streamlit web application for an easy-to-use interface:

```bash
# Option 1: Using the launch script
./run_frontend.sh

# Option 2: Using Poetry directly
poetry run streamlit run genai_job_finder/frontend/app.py
```

The application will be available at `http://localhost:8501`

**Features:**
- Search jobs by title, keywords, and location
- Filter by posting date (24h, week, month)
- View results in paginated tables (15 jobs per page)
- Download results as CSV files
- Real-time search progress indicators

### Command Line Usage

Use the example script to collect job data:

```bash
poetry run python example_usage.py
```

**Options:**
1. **Parse from config** - Uses predefined search parameters
2. **Custom search** - Enter your own keywords and location
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

## 🛡️ Rate Limiting & Best Practices

- Built-in delays between requests (2-4 seconds)
- Respectful scraping practices
- User-agent rotation
- Error handling and retry logic

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is for educational and personal use. Please respect LinkedIn's Terms of Service when using this tool.

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're in the Poetry environment (`poetry shell`)
2. **Database Locked**: Close any open database connections
3. **No Jobs Found**: Check your search parameters and network connection

### Getting Help

- Check the example usage script for proper usage patterns
- Review the Jupyter notebook for data analysis examples
- Ensure all dependencies are installed with `poetry install`

## 📊 Metrics

- **Total Jobs Collected**: 212+ and growing
- **Success Rate**: High reliability with error handling
- **Performance**: ~7 jobs per page, 3-4 seconds between requests

---

**Note**: This tool is designed for personal job search assistance. Please use responsibly and in accordance with LinkedIn's Terms of Service.
