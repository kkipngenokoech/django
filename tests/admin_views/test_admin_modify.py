import pytest
from django.template import Context
from django.contrib.admin.templatetags.admin_modify import submit_row


def test_issue_reproduction():
    """Test that show_save_as_new requires add permission."""
    # Create a context where user has change permission but NOT add permission
    context = {
        'add': False,
        'change': True,
        'is_popup': False,
        'save_as': True,
        'show_save': True,
        'show_save_and_add_another': True,
        'show_save_and_continue': True,
        'has_add_permission': False,  # User does NOT have add permission
        'has_change_permission': True,  # User has change permission
        'has_view_permission': True,
        'has_delete_permission': True,
        'has_editable_inline_admin_formsets': False,
        'show_delete': True,
    }
    
    result = submit_row(context)
    
    # The bug: show_save_as_new should be False when has_add_permission is False
    # but currently it returns True because it only checks has_change_permission
    assert result['show_save_as_new'] is False, "show_save_as_new should be False when user lacks add permission"