import pytest
from django.contrib.sitemaps import Sitemap
from datetime import datetime


def test_issue_reproduction():
    """Test that sitemap with no items but callable lastmod raises ValueError."""
    
    class EmptySitemapWithCallableLastmod(Sitemap):
        def items(self):
            return []  # Empty list
        
        def lastmod(self, item):
            return datetime.now()  # Callable lastmod
    
    sitemap = EmptySitemapWithCallableLastmod()
    
    # This should raise ValueError: max() arg is an empty sequence
    with pytest.raises(ValueError, match="max\(\) arg is an empty sequence"):
        sitemap.get_latest_lastmod()