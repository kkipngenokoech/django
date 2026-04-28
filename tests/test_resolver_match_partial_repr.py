import functools
from django.urls.resolvers import ResolverMatch


def test_issue_reproduction():
    # Create a simple function to wrap with partial
    def my_view(request, arg1, arg2):
        return None
    
    # Create a partial function
    partial_view = functools.partial(my_view, arg2='fixed_value')
    
    # Create a ResolverMatch with the partial function
    match = ResolverMatch(
        func=partial_view,
        args=(),
        kwargs={},
        url_name='test_url',
        app_names=[],
        namespaces=[],
        route='test/'
    )
    
    # The repr should show information about the underlying function,
    # but currently it shows 'functools.partial' which is not helpful
    repr_str = repr(match)
    
    # This assertion will fail because the current implementation
    # shows 'functools.partial' instead of the underlying function
    assert 'my_view' in repr_str, f"Expected 'my_view' in repr, got: {repr_str}"
    assert 'functools.partial' not in repr_str, f"Should not show 'functools.partial' in repr: {repr_str}"