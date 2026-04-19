import functools
from django.urls.resolvers import ResolverMatch


def test_issue_reproduction():
    # Create a simple view function
    def my_view(request, arg1, arg2):
        return None
    
    # Create a partial function from the view
    partial_view = functools.partial(my_view, arg2='fixed_value')
    
    # Create a ResolverMatch with the partial view
    match = ResolverMatch(
        func=partial_view,
        args=(),
        kwargs={'arg1': 'test'},
        url_name='test_url'
    )
    
    # The repr should show the underlying function, not 'functools.partial'
    repr_str = repr(match)
    
    # This assertion will fail because the current implementation shows
    # 'functools.partial' instead of the underlying function path
    assert 'functools.partial' not in repr_str
    assert 'my_view' in repr_str