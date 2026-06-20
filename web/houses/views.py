from django.shortcuts import render


def dashboard(request):
    return render(request, "houses/base.html")
