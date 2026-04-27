import datetime
from django.utils.http import parse_http_date

def test_issue_reproduction():
    # Test RFC 7231 compliant two-digit year interpretation
    # Current year for reference
    current_year = datetime.datetime.now().year
    
    # Test case: year "25" should be interpreted based on current year, not hardcoded rules
    # If current year is 2023, then "25" appearing more than 50 years in future (2025 > 2023 + 50 = 2073) 
    # should be interpreted as 1925, not 2025
    
    # Use a date string with 2-digit year "25" in RFC850 format
    date_str = "Friday, 25-Dec-25 10:30:45 GMT"
    
    # Parse the date
    parsed_timestamp = parse_http_date(date_str)
    parsed_date = datetime.datetime.utcfromtimestamp(parsed_timestamp)
    
    # Current implementation incorrectly interprets "25" as 2025 (hardcoded rule: 0-69 -> 2000-2069)
    # But RFC 7231 says if 2025 is more than 50 years in future from current year,
    # it should be interpreted as 1925
    
    if current_year < 1975:  # If somehow running in past, "25" should be 2025
        expected_year = 2025
    else:  # For normal case (current year >= 1975), "25" should be 1925
        expected_year = 1925
    
    # This assertion will fail with current buggy implementation
    # because it always interprets "25" as 2025 regardless of current year
    assert parsed_date.year == expected_year, f"Expected year {expected_year}, got {parsed_date.year}"