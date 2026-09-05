from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def get_accessible_parties(user):
    """
    Returns a Party queryset the given user is allowed to see.
    Admin/Sales Head see everyone; an Executive sees only their own parties.
    """
    from core.models import Party

    profile = getattr(user, 'profile', None)
    if profile is None:
        return Party.objects.none()

    if profile.sees_all_data:
        return Party.objects.all()

    if profile.role == 'executive' and profile.executive:
        return Party.objects.filter(executive=profile.executive)

    return Party.objects.none()


def role_required(*allowed_roles):
    """
    View decorator - only allows access if the logged-in user's profile role
    is in allowed_roles. Use like: @role_required('admin', 'sales_head')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            profile = getattr(request.user, 'profile', None)
            if profile is None or profile.role not in allowed_roles:
                return redirect('login')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator