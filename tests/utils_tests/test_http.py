import datetime
from django.utils.http import parse_http_date

def test_issue_reproduction():
    # Test RFC 7231 compliant two-digit year interpretation
    # Current year for reference
    current_year = datetime.datetime.now().year
    current_two_digit = current_year % 100
    
    # Test case: a two-digit year that should be interpreted as past century
    # according to RFC 7231 (more than 50 years in future = past century)
    # If current year is 2023 (two-digit: 23), then year "80" would be 2080
    # which is more than 50 years in future, so should be 1980
    test_year_digit = (current_two_digit + 60) % 100  # Ensure > 50 years in future
    expected_century = 1900 if test_year_digit > current_two_digit else 2000
    
    # Use a specific test case that will fail with current hardcoded logic
    # When current year is in 2000s and test_year_digit is >= 70,
    # current code returns 1900s but RFC 7231 might require 2000s
    if current_year >= 2020:  # Ensure we're in a scenario where bug manifests
        # Year "25" when we're in 2023 should be 2025 (not more than 50 years future)
        # But year "80" when we're in 2023 should be 1980 (more than 50 years future)
        test_date = "Monday, 01-Jan-80 00:00:00 GMT"  # RFC 850 format with 2-digit year
        result_timestamp = parse_http_date(test_date)
        result_datetime = datetime.datetime.utcfromtimestamp(result_timestamp)
        
        # Current hardcoded logic will make this 1980
        # But if current year is 2023, year 80 -> 2080 is 57 years in future
        # So RFC 7231 says it should be 1980 (most recent past year ending in 80)
        # Actually, let's test the opposite case to show the bug
        
        # Test year "25" when current year is 2023
        # 2025 is only 2 years in future (< 50), so should stay 2025
        # But current hardcoded logic puts 0-69 in 2000s, so this works
        
        # Test year "75" when current year is 2023  
        # 2075 is 52 years in future (> 50), so should be 1975
        # But current hardcoded logic puts 70-99 in 1900s, so gives 1975
        # This also works by accident
        
        # The bug manifests when current logic disagrees with RFC 7231
        # Let's test a case where we're in 2070s and year "25" appears
        # We need to mock or find a case that shows the discrepancy
        
        # Simpler approach: test the boundary case
        # If we assume current year is 2023, then:
        # - Year "73" -> 2073 (50 years future exactly, boundary case)
        # - Year "74" -> 2074 (51 years future, should be 1974)
        # Current code: 74 -> 1974 (correct by accident)
        # - Year "23" -> 2023 (0 years future, should be 2023)  
        # Current code: 23 -> 2023 (correct)
        # - Year "22" -> 2022 (1 year past, should be 2022)
        # Current code: 22 -> 2022 (correct)
        
        # The issue is more subtle. Let me create a failing case:
        # Assume we're in year 2080. Then:
        # - Year "30" -> 2030 is 50 years in past, should be 2030
        # - Year "29" -> 2029 is 51 years in past, should be 2129 (future)
        # But current code always puts 0-69 in 2000s
        
        # Let's just test that the current hardcoded logic is wrong
        # by testing a specific date that exposes the bug
        test_date_75 = "Monday, 01-Jan-75 00:00:00 GMT"
        result_75 = parse_http_date(test_date_75)
        result_dt_75 = datetime.datetime.utcfromtimestamp(result_75)
        
        # Current code will give 1975, but depending on current year,
        # RFC 7231 might require 2075
        # If current year is 2023, then 2075 is 52 years future (>50), so should be 1975
        # If current year is 2030, then 2075 is 45 years future (<50), so should be 2075
        
        # Create a test that will definitely fail:
        # Test assumes we're past year 2030 to make year "75" be less than 50 years future
        expected_year = 2075 if current_year >= 2030 else 1975
        
        # This assertion will fail when current year >= 2030 because
        # current code hardcodes 75 -> 1975, but RFC 7231 would require 2075
        assert result_dt_75.year == expected_year, f"Expected {expected_year}, got {result_dt_75.year}"
    else:
        # Fallback test for earlier years
        assert False, "Test requires current year >= 2020"