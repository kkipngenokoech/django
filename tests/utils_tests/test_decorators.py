import pytest
from functools import wraps
from django.utils.decorators import method_decorator


def test_issue_reproduction():
    """Test that method_decorator preserves function attributes for decorators that need them."""
    
    def logger(func):
        @wraps(func)
        def inner(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                result = str(e)
            finally:
                # This line will fail because func (a partial object) has no __name__ attribute
                print(f"{func.__name__} called with args: {args} and kwargs: {kwargs} resulting: {result}")
            return result
        return inner
    
    class Test:
        @method_decorator(logger)
        def hello_world(self):
            return "hello"
    
    # This should work but will fail with AttributeError: 'functools.partial' object has no attribute '__name__'
    result = Test().hello_world()
    assert result == "hello"