import datetime
from django.utils.http import parse_http_date

def test_issue_reproduction():
    # Test RFC 850 two-digit year parsing according to RFC 7231
    # Current year for reference
    current_year = datetime.datetime.now().year
    current_two_digit = current_year % 100
    
    # Test case 1: A year that should be interpreted as past century
    # If current year is 2023 (two-digit: 23), then year 75 should be 1975, not 2075
    # because 2075 would be more than 50 years in the future
    test_year_past = (current_two_digit + 51) % 100
    expected_century_past = (current_year // 100 - 1) * 100 if test_year_past > current_two_digit else (current_year // 100) * 100
    expected_year_past = expected_century_past + test_year_past
    
    # Test case 2: A year that should be interpreted as current century  
    # If current year is 2023, then year 25 should be 2025, not 1925
    # because 2025 is within 50 years of current year
    test_year_future = (current_two_digit + 2) % 100
    expected_century_future = (current_year // 100) * 100 if test_year_future <= (current_two_digit + 50) % 100 else (current_year // 100 + 1) * 100
    expected_year_future = expected_century_future + test_year_future
    
    # Create RFC 850 date strings
    rfc850_date_past = f"Sunday, 01-Jan-{test_year_past:02d} 12:00:00 GMT"
    rfc850_date_future = f"Sunday, 01-Jan-{test_year_future:02d} 12:00:00 GMT"
    
    # Parse the dates
    parsed_past = parse_http_date(rfc850_date_past)
    parsed_future = parse_http_date(rfc850_date_future)
    
    # Convert back to datetime to check the year
    dt_past = datetime.datetime.utcfromtimestamp(parsed_past)
    dt_future = datetime.datetime.utcfromtimestamp(parsed_future)
    
    # The bug: current code uses hardcoded ranges instead of RFC 7231 logic
    # Test specific case that demonstrates the bug clearly
    # Using year 69 which should be 2069 if current year is 2023 (within 50 years)
    # but current code hardcodes it to 2069 regardless of current year
    rfc850_year_69 = "Sunday, 01-Jan-69 12:00:00 GMT"
    parsed_69 = parse_http_date(rfc850_year_69)
    dt_69 = datetime.datetime.utcfromtimestamp(parsed_69)
    
    # Current implementation always puts 69 in 2069, but RFC 7231 says it should be
    # relative to current year. If we're in 2023, then 69 should be 2069 (46 years future, < 50)
    # If we're in 2030, then 69 should be 1969 (would be 61 years future, > 50)
    if current_year >= 2020:  # Assuming we're in 21st century
        years_in_future_69 = 2069 - current_year
        if years_in_future_69 > 50:
            # Should be 1969, but current code gives 2069
            expected_year_69 = 1969
        else:
            # Should be 2069, current code happens to be right
            expected_year_69 = 2069
    
        # This assertion will fail when the bug exists and years_in_future_69 > 50
        assert dt_69.year == expected_year_69, f"Year 69 should be {expected_year_69} but got {dt_69.year}"
    
    # Test year 70 case - should be in past century when current year makes it >50 years future
    rfc850_year_70 = "Sunday, 01-Jan-70 12:00:00 GMT"
    parsed_70 = parse_http_date(rfc850_year_70)
    dt_70 = datetime.datetime.utcfromtimestamp(parsed_70)
    
    # Current code always puts 70 in 1970, but should be relative to current year
    years_in_future_70 = 2070 - current_year
    if years_in_future_70 > 50:
        expected_year_70 = 1970  # Current code happens to be right
    else:
        expected_year_70 = 2070  # Should be 2070, but current code gives 1970
    
    # This will fail when current year makes 2070 within 50 years but code gives 1970
    assert dt_70.year == expected_year_70, f"Year 70 should be {expected_year_70} but got {dt_70.year}"