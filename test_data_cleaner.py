"""
Simple tests for the data cleaner module (no Ollama required).
"""

import asyncio
import tempfile
import pandas as pd
from pathlib import Path

def test_experience_level_classification():
    """Test experience level classification from years."""
    from genai_job_finder.data_cleaner.models import ExperienceLevel
    
    test_cases = [
        (0, ExperienceLevel.INTERN, "Intern"),
        (1, ExperienceLevel.ENTRY_JUNIOR, "Entry / Junior"),
        (2, ExperienceLevel.EARLY_CAREER_ASSOCIATE, "Early-career / Associate"),
        (4, ExperienceLevel.MID, "Mid"),
        (6, ExperienceLevel.SENIOR, "Senior"),
        (10, ExperienceLevel.STAFF_PRINCIPAL, "Staff / Principal"),
        (15, ExperienceLevel.DIRECTOR_EXECUTIVE, "Director / Executive"),
    ]
    
    for years, expected_level, expected_label in test_cases:
        level = ExperienceLevel.from_years(years)
        assert level == expected_level, f"Years {years}: expected {expected_level}, got {level}"
        assert level.get_label() == expected_label, f"Years {years}: expected '{expected_label}', got '{level.get_label()}'"
    
    print("✅ Experience level classification tests passed")


def test_salary_range_model():
    """Test salary range model calculations."""
    from genai_job_finder.data_cleaner.models import SalaryRange
    
    # Test mid salary calculation
    salary_range = SalaryRange(min_salary=80000, max_salary=120000)
    assert salary_range.mid_salary == 100000, f"Expected mid salary 100000, got {salary_range.mid_salary}"
    
    # Test with no values
    empty_range = SalaryRange()
    assert empty_range.mid_salary is None, "Expected None for empty salary range"
    
    print("✅ Salary range model tests passed")


def test_keyword_extraction():
    """Test keyword-based experience extraction."""
    from genai_job_finder.data_cleaner.chains.experience_extraction import ExperienceExtractionChain
    from genai_job_finder.data_cleaner.config import CleanerConfig
    
    config = CleanerConfig()
    chain = ExperienceExtractionChain(config)
    
    test_cases = [
        ("Looking for 5+ years of experience", 5),
        ("Minimum 3 years experience required", 3),
        ("At least 7 years in the field", 7),
        ("2-4 years experience preferred", 2),
        ("Entry level position", 0),
        ("Senior developer role", 6),
        ("Principal engineer position", 10),
        ("No specific experience mentioned", -1),
    ]
    
    for content, expected_years in test_cases:
        years = chain._extract_years_with_keywords(content)
        if expected_years >= 0:
            assert years == expected_years, f"Content '{content}': expected {expected_years}, got {years}"
        else:
            assert years == -1, f"Content '{content}': expected -1 (not found), got {years}"
    
    print("✅ Keyword extraction tests passed")


def test_salary_regex_extraction():
    """Test regex-based salary extraction."""
    from genai_job_finder.data_cleaner.chains.salary_extraction import SalaryExtractionChain
    from genai_job_finder.data_cleaner.config import CleanerConfig
    
    config = CleanerConfig()
    chain = SalaryExtractionChain(config)
    
    test_cases = [
        ("Salary range: $80,000 - $120,000", 80000, 120000),
        ("$90K to $130K per year", 90000, 130000),
        ("Competitive salary of $95,000.00/yr - $140,000.00/yr", 95000, 140000),
        ("No salary information", None, None),
    ]
    
    for content, expected_min, expected_max in test_cases:
        salary_range = chain._extract_salary_with_regex(content)
        
        if expected_min is not None:
            assert salary_range is not None, f"Content '{content}': expected salary range, got None"
            assert salary_range.min_salary == expected_min, f"Content '{content}': expected min {expected_min}, got {salary_range.min_salary}"
            assert salary_range.max_salary == expected_max, f"Content '{content}': expected max {expected_max}, got {salary_range.max_salary}"
        else:
            assert salary_range is None, f"Content '{content}': expected None, got {salary_range}"
    
    print("✅ Salary regex extraction tests passed")


def test_data_structure():
    """Test data structure models (without actual cleaning)."""
    from genai_job_finder.data_cleaner.models import ExperienceLevel, WorkLocationType, EmploymentType, SalaryRange
    import pandas as pd
    
    # Test creating a basic job data structure
    test_data = {
        'id': 'test-1',
        'company': 'TestCorp',
        'title': 'Software Engineer',
        'location': 'San Francisco, CA',
        'content': 'Test job description',
        'min_years_experience': 3,
        'experience_level': ExperienceLevel.MID.value,
        'experience_level_label': ExperienceLevel.MID.get_label(),
        'work_location_type': WorkLocationType.HYBRID.value,
        'employment_type': EmploymentType.FULL_TIME.value,
        'min_salary': 90000,
        'max_salary': 130000,
        'mid_salary': 110000,
    }
    
    # Test conversion to DataFrame
    df = pd.DataFrame([test_data])
    
    # Verify DataFrame structure
    expected_columns = [
        'id', 'company', 'title', 'location', 'content',
        'min_years_experience', 'experience_level', 'experience_level_label',
        'work_location_type', 'employment_type',
        'min_salary', 'max_salary', 'mid_salary'
    ]
    
    for col in expected_columns:
        assert col in df.columns, f"Expected column '{col}' not found in DataFrame"
    
    # Verify data
    assert len(df) == 1, f"Expected 1 row, got {len(df)}"
    assert df.iloc[0]['experience_level_label'] == "Mid", f"Expected 'Mid', got {df.iloc[0]['experience_level_label']}"
    assert df.iloc[0]['mid_salary'] == 110000, f"Expected 110000, got {df.iloc[0]['mid_salary']}"
    
    print("✅ Data structure tests passed")


async def run_tests():
    """Run all tests."""
    print("Running Data Cleaner Module Tests")
    print("=" * 40)
    
    test_experience_level_classification()
    test_salary_range_model()
    test_keyword_extraction()
    test_salary_regex_extraction()
    test_data_structure()
    
    print("\n✅ All tests passed!")
    print("The data cleaner module is ready to use.")
    print("\nTo test with Ollama:")
    print("1. Start Ollama: ollama serve")
    print("2. Pull model: ollama pull llama3.2")
    print("3. Run: python examples/data_cleaner_demo.py")


if __name__ == "__main__":
    asyncio.run(run_tests())
