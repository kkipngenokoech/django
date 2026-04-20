import datetime
from unittest.mock import patch
from django.test import SimpleTestCase
from django.utils.http import parse_http_date


class RFC7231YearBugReproducerTest(SimpleTestCase):
    """Test that reproduces the RFC 7231 two-digit year handling bug."""

    def test_issue_reproduction(self):
        """Test RFC 7231 compliant two-digit year handling."""
        # Test case: year "80" should be interpreted as 1980, not 2080
        # when current year is 2023, because 2080 is more than 50 years in the future
        with patch('django.utils.http.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = datetime.datetime(2023, 1, 1)
            mock_datetime.datetime = datetime.datetime
            
            # Year "80" in 2023 should be interpreted as 1980
            # (2080 would be 57 years in future, > 50)
            date_str = 'Sunday, 06-Nov-80 08:49:37 GMT'
            parsed = parse_http_date(date_str)
            parsed_datetime = datetime.datetime.utcfromtimestamp(parsed)
            self.assertEqual(parsed_datetime.year, 1980)
            
            # Year "25" in 2023 should be interpreted as 2025
            # (only 2 years in future, < 50)
            date_str_25 = 'Sunday, 06-Nov-25 08:49:37 GMT'
            parsed_25 = parse_http_date(date_str_25)
            parsed_datetime_25 = datetime.datetime.utcfromtimestamp(parsed_25)
            self.assertEqual(parsed_datetime_25.year, 2025)
            
            # Boundary case: year "73" should be 2073 (exactly 50 years, <= 50)
            date_str_73 = 'Sunday, 06-Nov-73 08:49:37 GMT'
            parsed_73 = parse_http_date(date_str_73)
            parsed_datetime_73 = datetime.datetime.utcfromtimestamp(parsed_73)
            self.assertEqual(parsed_datetime_73.year, 2073)
            
            # Boundary case: year "74" should be 1974 (51 years in future, > 50)
            date_str_74 = 'Sunday, 06-Nov-74 08:49:37 GMT'
            parsed_74 = parse_http_date(date_str_74)
            parsed_datetime_74 = datetime.datetime.utcfromtimestamp(parsed_74)
            self.assertEqual(parsed_datetime_74.year, 1974)
