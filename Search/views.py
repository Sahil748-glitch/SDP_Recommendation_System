from sklearn.metrics.pairwise import cosine_similarity
import json
import pandas as pd
from django.shortcuts import render,redirect
import requests
from . import models
from sklearn.feature_extraction.text import TfidfVectorizer
from difflib import get_close_matches
from django.http import HttpResponse,JsonResponse
import pymongo
from bson import ObjectId
# Create your views here.
client = pymongo.MongoClient(port=27017)
db=client.SDP
restaurants = []

def LoadCity(request):
    if request.method == "POST": 
        username = request.POST['name']
        cities = pd.read_csv("..\RealTaste\static\Data\cities_r2.csv") 
        data = get_close_matches(username,cities['name_of_city'],50,0.5)

        city = {'data':data}
        return JsonResponse(city)
def LoadCityName(request):
    headers = {'user-key': '9bbd972eb4cedb32df268dd69cf1c9d5',
           'Accept': 'application / json'}
    if request.method == "POST":
         city  = request.POST['name'] 
    url='https://developers.zomato.com/api/v2.1/cities?q='+city
    response = requests.get(url, headers=headers)
    data = json.loads(response.text)
    print(data)
    if not data['location_suggestions']:
        return JsonResponse({'result':"This city has no zomato base so pls search other city..."})
    d = data['location_suggestions']
    city = d[0]['id']
    name = d[0]['name']
    if 'user' in request.session:
        user = request.session['user']
        query = { "name": user }
        newvalues = { "$set": { "city": name ,"cityid":city} }
        db.User.update_one(query, newvalues)
    j = {'cityid':city,'cityname':name}
    return JsonResponse(j)

def LoadRes(request):
    headers = {'user-key': '9bbd972eb4cedb32df268dd69cf1c9d5',
            'Accept': 'application / json'}
    global restaurants
    restaurants.clear()
    cityid=""
    cityname=""
    if 'login' in request.GET:
        d = db.User.find({'name':request.session['user']})
        for doc in d:
            cityid = str(doc['cityid'])
            cityname = doc['city']
    else:
        cityid = request.GET['cityid']
        cityname=request.GET['cityname']
    if db.Restaurants.find_one({'city': cityname}) is None:
        url1 = 'https://developers.zomato.com/api/v2.1/search?entity_id='+ cityid+'&entity_type=city'
        response1 = requests.get(url1, headers=headers)
        res = json.loads(response1.text)
        for item1 in res['restaurants']:
            a = models.Restaurant()
            a.name =  item1['restaurant']['name']
            a.price = item1['restaurant']['average_cost_for_two']
            a.cuisine = item1['restaurant']['cuisines']
            a.rating = item1['restaurant']['user_rating']['aggregate_rating']
            a.city = cityname
            a.number = item1['restaurant']['phone_numbers']
            a.hasDel = item1['restaurant']['has_online_delivery']
            a.hasBoo = item1['restaurant']['has_table_booking']
            db.Restaurants.insert_one({'name':a.name,'price':a.price,'cuisine':a.cuisine,'rating':a.rating,'city':a.city,'number':a.number,'del':a.hasDel,'book':a.hasBoo})
            restaurants.append({'name':a.name,'price':a.price,'cuisine':a.cuisine,'rating':a.rating,'city':a.city,'number':a.number,'del':a.hasDel,'book':a.hasBoo})
    else:
        res = db.Restaurants.find({'city':cityname})
        for doc in res:
            restaurants.append(doc)
    return redirect('/Search/Search/?city='+cityname+'&cityid='+cityid)
   

def Load(request):
    user = "Login"
    check=""
    rec='You have not Logged in...'
    if 'user' in request.session:
        user = request.session['user']
        for d in db.Choice.find({'name':request.session['user']}):
            for i in d['choice']:
                if(i['city'] == request.GET['city']):
                    rec= i['new']
        if(rec == 'You have not Logged in...'):
            rec = "You have not added any restaurants as favourite,so there is no detail of user as a result no recomendation..."
        else:
            check="true"
    d = findPOF(request)
    if (check != "true"):
        return render(request,'Search.html',{'REC' :[],'RECLine':rec ,'POF':d['POF'],'TOP':d['TOP'],'ALL':d['ALL'],'city':request.GET['city'],'name':user,'cityid':request.GET['cityid'],'LoginValue':'Login'})
    else : 
        return render(request,'Search.html',{'REC' :findRec(request,rec) ,'POF':d['POF'],'TOP':d['TOP'],'ALL':d['ALL'],'city':request.GET['city'],'name':user,'cityid':request.GET['cityid'],'LoginValue':'Login'})

def findRec(request,name):
    dataset = []
    dataset1 = []
    global restaurants
    print(restaurants)
    for item1 in restaurants:
        #db.Restaurants.insert_one({'name': item['restaurant']['name'],'city':city})
        dataset.append({'name': item1['name'],
                        'cusine': item1['cuisine']})
        dataset1.append({'name': item1['name'],
                        'price': item1['price']})
        #dataset.append({'name' : item1['restaurant']['name'],'cusine' : item1['restaurant']['cuisines']})
    df = pd.DataFrame(dataset)
    df1 = pd.DataFrame(dataset1)

    tfv = TfidfVectorizer(min_df=2, max_features=None,
                        strip_accents='unicode', analyzer='word',
                        ngram_range=(1, 2),
                        stop_words='english')
    #df1['price'] = df1['price'].fillna('')
    #df['cusine'] = df['cusine'].fillna('')

    tvf_matrix = tfv.fit_transform(df['cusine'])


    tvf_matrix1 = tfv.fit_transform(df1['price'].astype(str))


    sig = cosine_similarity(tvf_matrix, Y=None, dense_output=True)
    sig1 = cosine_similarity(tvf_matrix1, Y=None, dense_output=True)

    indices = pd.Series(df.index, index=df['name']).drop_duplicates()
    ind = indices[name]

    sig_scores = list(enumerate(sig[ind]))

    sig_scores1 = list(enumerate(sig1[ind]))
    sig_scores.sort(reverse=True, key=lambda x: x[1])
    sig_scores1.sort(reverse=True, key=lambda x: x[1])
    sig_scores = sig_scores[1:10]
    sig_scores1 = sig_scores1[1:10]
    index = [i[0] for i in sig_scores]
    index1 = [i[0] for i in sig_scores1]
    final = []
    first = []
    last = []
    first_two = []
    second = []
    second_two = []
    print(df['name'].iloc[index1])
    print(df['name'].iloc[index])

    for i in range(5):
            if index[i] in index1:
                if(index1.index(index[i]) < len(index1)/2):
                    first.append(index[i])
                else:
                    first_two.append(index[i])
            else:
                last.append(index[i])
    for i in range(5, 9):
            if index[i] in index1:
                if(index1.index(index[i]) < len(index1)/2):
                    second.append(index[i])
                else:
                    second_two.append(index[i])
            else:
                last.append(index[i])
    final = first + first_two + second + second_two + last
    data =[]
    for name in df['name'].iloc[final]:
        
        for item1 in restaurants:
            
            if(item1['name'] == name):
                a = models.Restaurant()
                a.name =  item1['name']
                a.price = item1['price']
                a.cuisine = item1['cuisine']
                a.rating = item1['rating']
                data.append(a)
    return(data)

def findPOF(request):
    data=[]
    data2=[]
    data3=[]
    global restaurants
    for item1 in restaurants:
        a = models.Restaurant()
        a.name =  item1['name']
        a.price = item1['price']
        a.cuisine = item1['cuisine']
        a.rating = item1['rating']
        if(item1['price'] <= 250):
            data.append(a)
        data2.append(a)
        if(float(item1['rating']) > 4):
            data3.append(a) 
    data.sort(key=lambda x:x.price)
    data3.sort(key=lambda x:x.rating,reverse=True)
    re = {'POF':data,'TOP':data3,'ALL':data2}
    print(re)
    return(re)    


#Details
def LoadData(request):
    user ="Login"
    fav ="yes"
    rate="no"
    if 'user' in request.session:
        user = request.session['user']
    if('name' in request.GET):
        name = request.GET['name']
        doc = db.Restaurants.find({'name':name})
        for res in doc:
            a = models.Restaurant()
            a.name = name
            a.price = res['price']
            a.cuisine = res['cuisine']
            a.rating = res['rating']
            a.number = res['number']
            a.hasBoo = res['book']
            a.hasDel = res['del']
           
            d = findRec(request,name)
            if (float(a.rating) >= 4):
                rate = "yes"
            if(a.hasBoo != 0):
                a.hasBoo = "yes"
            if(a.hasDel != 0):
                a.hasDel = "yes"
           
            if db.Fav.find({'$and':[{'name':user},{'fav':{'city':request.GET['cityname'],'res':name}}]}).count() > 0:    
                data = {'fav':fav,'value':'yes','rate':rate,'data':a,'REC':d,'city':request.GET['cityname'],'name':user,'cityid':request.GET['cityid'],'LoginValue':'Login'}
            else:
                data = {'value':'yes','data':a,'REC':d,'rate':rate,'city':request.GET['cityname'],'name':user,'cityid':request.GET['cityid'],'LoginValue':'Login'}
        return render(request,'Detail.html',data)


#User

def Register(request):
    city = request.GET['usercity']
    cityid = request.GET['cityid']
    count = 0
    doc = db.User.find({'$or':[{'email':request.POST['email']},{'number':request.POST['number']}]})
    for d in doc:
        print(d)
        count =count +1 
    if(count > 0 ):
        j={'result':"Number or Email has been Registered Before.Please login using that!"}
        return JsonResponse(j)  
    db.User.insert_one({'name':request.POST['name'],'email':request.POST['email'],'number':request.POST['number'],'password':request.POST['password-R'],'city':city,'cityid':cityid})
    request.session['user'] = request.POST['name']
    j = {'cityid':cityid,'cityname':city}
    return JsonResponse(j)


def Login(request):
    doc = db.User.find({'email':request.POST['email']})
    for d in doc:
        if(d['password']  == request.POST['password-L']):
            j = {'cityid':d['cityid'],'cityname':d['city']}
            request.session['user'] = d['name']
            return JsonResponse(j)
        else:
            j = {'result':"your password does not match,please check it."}
            return JsonResponse(j)
    j = {'result':'Such an email does not exist, please register again.'}
    return JsonResponse(j)


def Logout(request):
    if 'user' in request.session:
        del request.session['user']
        j={'s':'s','result':'s'}
        return JsonResponse(j)
    else:
        j={'result':'You are not loged in '}
        return JsonResponse(j)

def makeFav(request):
    if 'user' in request.session:
        if db.Fav.find({'name': request.session['user']}).count() > 0:
            db.Fav.update({'name':request.session['user']},{'$push':{'fav':{'city': request.POST['cityname'],'res':request.POST['name']}}})
        else:
            db.Fav.insert_one({'name':request.session['user'],'fav':[{'city':request.POST['cityname'],'res':request.POST['name']}]})
        j = {}

        if db.Choice.find({'name':request.session['user'],'choice.city':request.POST['cityname']}).count() > 0:
            doc = db.Choice.find({'name':request.session['user']})
            last=''
            for d in doc:
                for i in d['choice']:
                    if(i['city'] == request.POST['cityname']):
                        last = i['new']
               
          
            db.Choice.update({'name':request.session['user'],'choice.city':request.POST['cityname']},{'$set':{'choice.$.new':request.POST['name'],'choice.$.last':last}})
        else:
            if(db.Choice.find({'name':request.session['user']}).count() > 0):
               
               
                db.Choice.update({'name':request.session['user']},{'$push':{'choice':{'new':request.POST['name'],'last':request.POST['name'],'city': request.POST['cityname']}}})
            else:  
                
                db.Choice.insert_one({'name':request.session['user'],'choice':[{'new':request.POST['name'],'last':request.POST['name'],'city':request.POST['cityname']}]})
        return JsonResponse(j)
    else:
        j = {'result':'please Login or register to favourite it..'}
        return JsonResponse(j)


def remFav(request):
    if 'user' in request.session:
        db.Fav.update({'name':request.session['user']},{'$pull':{'fav':{'city': request.POST['cityname'],'res':request.POST['name']}}})
        j = {}
        if db.Choice.find({'name':request.session['user'],'choice.city':request.POST['cityname']}).count() > 0:
            doc = db.Choice.find({'name':request.session['user']})
            for d in doc:
                for i in d['choice']:
                    if(i['city'] == request.POST['cityname']):
                        if (i['new'] == request.POST['name']):
                            db.Choice.update({'name':request.session['user'],'choice.city':request.POST['cityname']},{'$set':{'choice.$.new':i['last']}})
                        if(i['last'] == request.POST['name']):
                            db.Choice.update({'name':request.session['user'],'choice.city':request.POST['cityname']},{'$set':{'choice.$.last':i['new']}})
        return JsonResponse(j)
    else:
        j = {'result':'please Login or register to favourite it..'}
        return JsonResponse(j)

def Fav(request):
    r = []
    if 'user' in request.session:
        for d in db.Fav.find({'name':request.session['user']}):
                for item in d['fav']:
                    if (item['city'] == request.GET['cityname']):
                        doc = db.Restaurants.find({'name':item['res']})
                        for res in doc:
                            a = models.Restaurant()
                            a.name = item['res']
                            a.price = res['price']
                            a.cuisine = res['cuisine']
                            a.rating = res['rating']
                        r.append(a)
        data = {'data':r,'city':request.GET['cityname'],'name':request.session['user'],'cityid':request.GET['cityid']}
        return render(request,'Fav.html',data)
    else:
        return render(request,'Fav.html',{'result':'Please Login or register to proceed at ' })


def getData(request):
    if 'user' not in request.session:
        j={'result':'You are trying to access the page Illegaly.Pls Go TO Home page first... '}
        return JsonResponse(j)
    user = request.session['user']
    j={}
    for d in db.User.find({'name':user}):
        j={'name':d['name'],'email':d['email'],'number':d['number']}
    return JsonResponse(j)

def Update(request):
    if 'user' not in request.session:
        j={'result':'You are trying to access the page Illegaly.Pls Go TO Home page first... '}
        return JsonResponse(j)
    user = request.session['user']
    name=" "
    email=" "
    number= " "
    count = 0
    check="fasle"
    doc = db.User.find({'$or':[{'email':request.POST['email']},{'number':request.POST['number']}]})
    for d in doc:
        count =count +1 
    if(count > 0 ):
        j={'error':"Number or Email has been already used.Please use another email or number to update!"}
        return JsonResponse(j)  
    for d in db.User.find({'name':user}):
        if(request.POST['name'] != "" ):
            name = request.POST['name']
            check = "true"
        else:
            name = d['name']
        if(request.POST['email'] != "" ):
            email = request.POST['email']
        else:
            email = d['email']
        if(request.POST['number'] != "" ):
            number = request.POST['number']
        else:
            number = d['number']
        db.User.update({'name':user},{'name':name,'email':email,'number':number,'password':d['password'],'city':d['city'],'cityid':d['cityid']})
        
    if(check == "true"):
        db.Choice.update({'name':user},{'$set':{'name':name}})
        db.Fav.update({'name':user},{'$set':{'name':name}})
    request.session['user'] = name
    j={'result':"Updated successfully"}
    return JsonResponse(j)

def Updatepass(request):
    if 'user' not in request.session:
        j={'result':'You are trying to access the page Illegaly.Pls Go TO Home page first... '}
        return JsonResponse(j)   
    user = request.session['user']
    for d in db.User.find({'name':user}):
        if(d['password'] == request.POST['OldPassword']):
            db.User.update({'name':user},{'name':d['name'],'email':d['email'],'number':d['number'],'password':request.POST['NewPassword'],'city':d['city'],'cityid':d['cityid']})
            j={'result':'Updated successfully'}
            return JsonResponse(j)
        else:
            j={"error":"old password is not correct"}
            return JsonResponse(j)



def AddSub(request):
    db.Subscibers.insert_one({'name':request.POST['name']})
    return JsonResponse({})