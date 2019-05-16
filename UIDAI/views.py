from django.shortcuts import render
def nearest_centre(request):
    return render(request,'nearestcentres.html')

def uidai_home(request):
    return render(request,'homepage.html')
