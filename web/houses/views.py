from django.shortcuts import render


def dashboard(request):
    return render(request, "houses/dashboard.html", {"overview": {}})
