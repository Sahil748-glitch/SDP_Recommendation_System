from django.shortcuts import redirect, render


# Create your views here.
def LoadHome(request):
    if('user' in request.session):
        return redirect('http://127.0.0.1:8000/Search/?login=1')
    return render(request,'Home.html')