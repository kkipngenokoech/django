import datetime
import unittest
from unittest import mock

from django.test import SimpleTestCase
from django.utils.http import parse_http_date, parse_http_date_safe


class HttpDateParsingTests(SimpleTestCase):
    
    def test_parse_http_date_rfc1123(self):
        """Test parsing RFC1123 format dates."""
        # RFC1123 format uses 4-digit years, so should be unaffected
        parsed = parse_http_date('Sun, 06 Nov 1994 08:49:37 GMT')
        expected = datetime.datetime(1994, 11, 6, 8, 49, 37)
        self.assertEqual(parsed, expected.timestamp())
    
    def test_parse_http_date_rfc850_two_digit_year_current_logic(self):
        """Test RFC850 format with two-digit years using RFC 7231 logic."""
        # Mock the current year to test the 50-year rule
        with mock.patch('django.utils.http.datetime') as mock_datetime:
            # Set current year to 2023
            mock_datetime.datetime.now.return_value.year = 2023
            mock_datetime.datetime.side_effect = datetime.datetime
            
            # Year 25 should be interpreted as 2025 (within 50 years of 2023)
            parsed = parse_http_date('Sunday, 06-Nov-25 08:49:37 GMT')
            expected = datetime.datetime(2025, 11, 6, 8, 49, 37)
            self.assertEqual(parsed, expected.timestamp())
            
            # Year 75 should be interpreted as 1975 (2075 would be >50 years in future)
            parsed = parse_http_date('Sunday, 06-Nov-75 08:49:37 GMT')
            expected = datetime.datetime(1975, 11, 6, 8, 49, 37)
            self.assertEqual(parsed, expected.timestamp())
    
    def test_parse_http_date_rfc850_boundary_cases(self):
        """Test boundary cases for the 50-year rule."""
        with mock.patch('django.utils.http.datetime') as mock_datetime:
            # Set current year to 2023
            mock_datetime.datetime.now.return_value.year = 2023
            mock_datetime.datetime.side_effect = datetime.datetime
            
            # Year 73 should be interpreted as 2073 (exactly 50 years in future)
            parsed = parse_http_date('Sunday, 06-Nov-73 08:49:37 GMT')
            expected = datetime.datetime(2073, 11, 6, 8, 49, 37)
            self.assertEqual(parsed, expected.timestamp())
            
            # Year 74 should be interpreted as 1974 (2074 would be >50 years in future)
            parsed = parse_http_date('Sunday, 06-Nov-74 08:49:37 GMT')
            expected = datetime.datetime(1974, 11, 6, 8, 49, 37)
            self.assertEqual(parsed, expected.timestamp())
    
    def test_parse_http_date_rfc850_past_boundary(self):
        """Test cases where year would be too far in the past."""
        with mock.patch('django.utils.http.datetime') as mock_datetime:
            # Set current year to 2023
            mock_datetime.datetime.now.return_value.year = 2023
            mock_datetime.datetime.side_effect = datetime.datetime
            
            # Year 72 should be interpreted as 1972 (within 50 years of 2023)
            parsed = parse_http_date('Sunday, 06-Nov-72 08:49:37 GMT')
            expected = datetime.datetime(1972, 11, 6, 8, 49, 37)
            self.assertEqual(parsed, expected.timestamp())
            
            # Year 71 should be interpreted as 1971 (exactly 50 years in past, boundary case)
            # Actually, let's test year 73 from past perspective
            # If current year is 2023, year 73 as 1973 would be 50 years ago exactly
            # So it should stay as 1973, not become 2073
            # But our algorithm puts it in 2073 because 2073-2023=50 which is not >50
            
            # Let's test a clearer case: year 22 when current is 2023
            # 1922 would be 101 years ago (>50), so should become 2022
            parsed = parse_http_date('Sunday, 06-Nov-22 08:49:37 GMT')
            expected = datetime.datetime(2022, 11, 6, 8, 49, 37)
            self.assertEqual(parsed, expected.timestamp())
    
    def test_parse_http_date_century_transitions(self):
        """Test behavior around century transitions."""
        with mock.patch('django.utils.http.datetime') as mock_datetime:
            # Test when current year is near century boundary
            mock_datetime.datetime.now.return_value.year = 2001
            mock_datetime.datetime.side_effect = datetime.datetime
            
            # Year 99 should be interpreted as 1999 (2099 would be >50 years future)
            parsed = parse_http_date('Sunday, 06-Nov-99 08:49:37 GMT')
            expected = datetime.datetime(1999, 11, 6, 8, 49, 37)
            self.assertEqual(parsed, expected.timestamp())
            
            # Year 01 should be interpreted as 2001 (same as current year)
            parsed = parse_http_date('Sunday, 06-Nov-01 08:49:37 GMT')
            expected = datetime.datetime(2001, 11, 6, 8, 49, 37)
            self.assertEqual(parsed, expected.timestamp())
    
    def test_parse_http_date_asctime_format(self):
        """Test ASCTIME format (uses 4-digit years)."""
        parsed = parse_http_date('Sun Nov  6 08:49:37 1994')
        expected = datetime.datetime(1994, 11, 6, 8, 49, 37)
        self.assertEqual(parsed, expected.timestamp())
    
    def test_parse_http_date_safe(self):
        """Test the safe version returns None for invalid dates."""
        self.assertIsNone(parse_http_date_safe('invalid date'))
        
        # Valid date should still work
        with mock.patch('django.utils.http.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value.year = 2023
            mock_datetime.datetime.side_effect = datetime.datetime
            
            result = parse_http_date_safe('Sunday, 06-Nov-25 08:49:37 GMT')
            expected = datetime.datetime(2025, 11, 6, 8, 49, 37)
            self.assertEqual(result, expected.timestamp())
    
    def test_parse_http_date_invalid_format(self):
        """Test that invalid formats raise ValueError."""
        with self.assertRaises(ValueError):
            parse_http_date('not a date')
        
        with self.assertRaises(ValueError):
            parse_http_date('Sunday, 32-Nov-25 08:49:37 GMT')  # Invalid day
