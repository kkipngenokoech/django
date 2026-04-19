#!/usr/bin/env python
import os
import sys
import tempfile

# Add Django to path
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_sqlite')

import django
django.setup()

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import MemoryUploadedFile, TemporaryUploadedFile

def test_current_behavior():
    print(f"Current FILE_UPLOAD_PERMISSIONS: {settings.FILE_UPLOAD_PERMISSIONS}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = FileSystemStorage(location=temp_dir)
        
        # Create a MemoryUploadedFile (small file)
        memory_file = MemoryUploadedFile(
            name='memory_test.txt',
            content_type='text/plain',
            size=10,
            charset='utf-8'
        )
        memory_file.write(b'test data')
        memory_file.seek(0)
        
        # Create a TemporaryUploadedFile (simulates large file)
        temp_file = TemporaryUploadedFile(
            name='temp_test.txt',
            content_type='text/plain',
            size=10,
            charset='utf-8'
        )
        temp_file.write(b'test data')
        temp_file.seek(0)
        
        # Save both files using the storage
        memory_path = storage.save('memory_test.txt', memory_file)
        temp_path = storage.save('temp_test.txt', temp_file)
        
        # Get the actual file paths
        memory_full_path = storage.path(memory_path)
        temp_full_path = storage.path(temp_path)
        
        # Get file permissions
        memory_perms = oct(os.stat(memory_full_path).st_mode)[-3:]
        temp_perms = oct(os.stat(temp_full_path).st_mode)[-3:]
        
        print(f"Memory file permissions: {memory_perms}")
        print(f"Temp file permissions: {temp_perms}")
        print(f"Permissions match: {memory_perms == temp_perms}")
        
        return memory_perms == temp_perms

if __name__ == '__main__':
    test_current_behavior()