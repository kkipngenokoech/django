from django.http import HttpResponse
from django.test import TestCase


class MemoryViewResponseTest(TestCase):
    """
    Test that HttpResponse properly handles memoryview objects.
    """

    def test_memoryview_content(self):
        """Test that memoryview objects are properly converted to bytes."""
        original_bytes = b'My Content'
        mv = memoryview(original_bytes)
        response = HttpResponse(mv)
        
        # The content should be the original bytes, not a string representation
        self.assertEqual(response.content, original_bytes)
        self.assertIsInstance(response.content, bytes)

    def test_memoryview_with_unicode(self):
        """Test memoryview with unicode content."""
        original_text = 'Hello, 世界'
        original_bytes = original_text.encode('utf-8')
        mv = memoryview(original_bytes)
        response = HttpResponse(mv)
        
        self.assertEqual(response.content, original_bytes)
        self.assertIsInstance(response.content, bytes)

    def test_memoryview_empty(self):
        """Test empty memoryview."""
        mv = memoryview(b'')
        response = HttpResponse(mv)
        
        self.assertEqual(response.content, b'')
        self.assertIsInstance(response.content, bytes)

    def test_memoryview_iteration_not_triggered(self):
        """Test that memoryview is not treated as an iterable for content processing."""
        original_bytes = b'Test Content'
        mv = memoryview(original_bytes)
        response = HttpResponse(mv)
        
        # Should not iterate over the memoryview bytes
        self.assertEqual(response.content, original_bytes)
        self.assertNotEqual(response.content, b''.join(original_bytes))
