from functools import wraps

from django.http import JsonResponse


def api_login_required(view_func):
    """
    Require an authenticated Django session for API endpoints.
    Return JSON 401 instead of redirecting to the login page.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:

            return JsonResponse(
                {
                    "success": False,
                    "error": "Authentication required."
                },
                status=401
            )

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper