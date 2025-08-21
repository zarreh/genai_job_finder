# GenAI Job Finder Frontend

A Streamlit-based web application for searching and analyzing job listings from LinkedIn.

## Features

- **Job Search Interface**: Easy-to-use form for searching jobs with various criteria
- **Real-time Results**: Live job parsing from LinkedIn with progress indicators
- **Paginated Results**: View up to 15 jobs per page with navigation controls
- **Data Export**: Download search results as CSV files
- **Responsive Design**: Works on desktop and mobile devices

## Usage

### Starting the Application

From the project root directory:

```bash
# Option 1: Using the launcher script
python genai_job_finder/frontend/run.py

# Option 2: Direct Streamlit command
streamlit run genai_job_finder/frontend/app.py
```

The application will be available at `http://localhost:8501`

### Search Features

1. **Job Title/Keywords**: Enter job titles, skills, or keywords (required)
2. **Location**: Specify location or leave empty for all locations
3. **Time Posted**: Filter by posting date (past 24 hours, week, month, or any time)
4. **Max Pages**: Control how many pages to search (each page ≈ 25 jobs)

### Search Tips

- Use specific job titles for better results (e.g., "Software Engineer" vs "Engineer")
- Combine skills with roles (e.g., "Python Developer", "React Frontend Developer")
- Location can be city, state, country, or "Remote"
- More pages = more results but longer search time

## Components

- `app.py`: Main Streamlit application
- `config.py`: Configuration settings
- `run.py`: Launcher script
- `__init__.py`: Module initialization

## Dependencies

The frontend uses the following main dependencies:
- Streamlit for the web interface
- Pandas for data manipulation
- The existing LinkedIn parser and database modules

## Future Enhancements

- Search history tracking
- Job favorites and bookmarking
- Advanced filtering options
- Job analytics and insights
- Email notifications for new matches
- Resume matching and scoring
