import pytest
from django.template import Context
from django.contrib.admin.templatetags.admin_modify import submit_row


def test_issue_reproduction():
    """Test that show_save_as_new requires has_add_permission."""
    # Create a context where all conditions are met except has_add_permission is False
    context = {
        'add': False,
        'change': True,
        'is_popup': False,
        'save_as': True,
        'show_save': True,
        'show_save_and_add_another': True,
        'show_save_and_continue': True,
        'has_add_permission': False,  # User lacks add permission
        'has_change_permission': True,  # But has change permission
        'has_view_permission': True,
        'has_delete_permission': True,
        'has_editable_inline_admin_formsets': False,
        'show_delete': True,
    }
    
    result = submit_row(context)
    
    # This should be False because user lacks add permission,
    # but the current buggy code will return True
    assert result['show_save_as_new'] is False, "show_save_as_new should be False when user lacks add permission"