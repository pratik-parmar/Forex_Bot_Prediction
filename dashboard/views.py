from django.shortcuts import render


def dashboard_index(request):
    """
    Render the Forex dashboard.

    Technical indicators are loaded asynchronously
    from the technical-analysis API.
    """

    return render(
        request,
        "dashboard/index.html"
    )