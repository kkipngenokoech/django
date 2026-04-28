import datetime
from django.utils.http import parse_http_date

def test_issue_reproduction():
    # Test the RFC 7231 requirement for two-digit year interpretation
    # The rule: if a two-digit year appears to be more than 50 years in the future,
    # it should be interpreted as the most recent year in the past with the same last two digits
    
    # Get current year for relative calculations
    current_year = datetime.datetime.now().year
    current_two_digit = current_year % 100
    
    # Test case 1: A year that should be interpreted as future (within 50 years)
    # If current year is 2023 (two-digit: 23), then year 25 should be 2025
    future_year_2digit = (current_two_digit + 2) % 100
    if future_year_2digit < 10:
        future_year_str = f"0{future_year_2digit}"
    else:
        future_year_str = str(future_year_2digit)
    
    expected_future_year = current_year + 2
    if expected_future_year % 100 != future_year_2digit:
        # Handle century rollover
        expected_future_year = (current_year // 100) * 100 + future_year_2digit
        if expected_future_year - current_year > 50:
            expected_future_year -= 100
    
    # Test case 2: A year that should be interpreted as past (more than 50 years in future)
    # If current year is 2023 (two-digit: 23), then year 80 should be 1980, not 2080
    past_year_2digit = (current_two_digit + 60) % 100  # 60 years ahead -> should be past
    if past_year_2digit < 10:
        past_year_str = f"0{past_year_2digit}"
    else:
        past_year_str = str(past_year_2digit)
    
    # Calculate expected year for past case
    naive_future_year = (current_year // 100) * 100 + past_year_2digit
    if naive_future_year <= current_year:
        naive_future_year += 100
    
    if naive_future_year - current_year > 50:
        expected_past_year = naive_future_year - 100
    else:
        expected_past_year = naive_future_year
    
    # Create RFC850 date strings for testing
    future_date_str = f"Sunday, 01-Jan-{future_year_str} 12:00:00 GMT"
    past_date_str = f"Sunday, 01-Jan-{past_year_str} 12:00:00 GMT"
    
    # Parse the dates
    future_timestamp = parse_http_date(future_date_str)
    past_timestamp = parse_http_date(past_date_str)
    
    # Convert back to datetime to check the year
    future_dt = datetime.datetime.utcfromtimestamp(future_timestamp)
    past_dt = datetime.datetime.utcfromtimestamp(past_timestamp)
    
    # The current buggy implementation uses hardcoded ranges:
    # 0-69 -> 2000-2069, 70-99 -> 1970-1999
    # This test should fail because it doesn't follow RFC 7231's relative rule
    
    # Assert the correct RFC 7231 behavior
    assert future_dt.year == expected_future_year, f"Future year {future_year_2digit} should be {expected_future_year}, got {future_dt.year}"
    assert past_dt.year == expected_past_year, f"Past year {past_year_2digit} should be {expected_past_year}, got {past_dt.year}"
    
    # Specific test case that will definitely fail with current implementation
    # If we're in 2023, year "80" should be 1980 (not 2080 as current code would make it)
    # But current code hardcodes 70-99 -> 1970-1999, so "80" becomes 1980
    # Let's test a case where current code definitely fails
    
    # Test year "25" when current year is 2023 - should be 2025, but current code makes it 2025 (happens to work)
    # Test year "75" when current year is 2023 - should be 1975 (75 is 52 years in future from 23, so goes to past)
    # But current code makes it 1975 (happens to work due to hardcoded range)
    
    # Better test: if current year is 2023, test year "30"
    # RFC 7231: 30 is 7 years in future from 23, so should be 2030
    # Current code: 30 is in range 0-69, so becomes 2030 (happens to work)
    
    # Better test: if current year is 2023, test year "69" 
    # RFC 7231: 69 is 46 years in future from 23, so should be 2069
    # Current code: 69 is in range 0-69, so becomes 2069 (happens to work)
    
    # The real test: if current year is 2023, test year "70"
    # RFC 7231: 70 is 47 years in future from 23, so should be 2070
    # Current code: 70 is in range 70-99, so becomes 1970 (FAILS!)
    
    test_date_70 = "Sunday, 01-Jan-70 12:00:00 GMT"
    timestamp_70 = parse_http_date(test_date_70)
    dt_70 = datetime.datetime.utcfromtimestamp(timestamp_70)
    
    # This should be 2070 according to RFC 7231 (47 years from 2023 is < 50)
    # But current code makes it 1970
    assert dt_70.year == 2070, f"Year 70 should be 2070 according to RFC 7231, got {dt_70.year}"