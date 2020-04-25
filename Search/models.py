from django.db import models

# Create your models here.

class Restaurant:
    name:str
    Price:str
    Cuisine:str
    rating:str
    city:str
    number:str
    hasDel:str
    hasBoo:str

class User:
    name:str
    number:str
    email:str
    password:str
    city:str