from django.contrib import admin
from django.urls import path, include
from . import views
urlpatterns = [
    path('', views.LoadRes),
    path('Search/', views.Load),
    path('SearchCity', views.LoadCity),
    path('ReloadCity', views.LoadCityName),
    path('LoadRes/', views.LoadData),
    path('Register/', views.Register),
    path('Login', views.Login),
    path('makeFav', views.makeFav),
    path('Fav', views.Fav),
    path('removeFav', views.remFav),
    path('LogOut', views.Logout),
    path("GetData", views.getData),
    path("UpdateDetail", views.Update),
    path("UpdatePass", views.Updatepass),
    path("AddSub", views.AddSub)
]
