# Create your views here.
from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.http import HttpResponse
from models import Customer, WaitList, Restaurant
from django.contrib import auth
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect

def debug_customers_all(request):
    return render_to_response('buzme/debug_customers.html',
                              {'customers_qs': Customer.objects.all()})
    
def summon_customer(request, customer_id):
    return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.SUMMONED)

def remove_customer(request, customer_id):
    return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.REMOVED)

def create_in_waitlist(request, waitlist_id):
    name = None
    if 'name' in request.POST:
        name = request.POST['name']
    party_size = None
    if 'party_size' in request.POST:
        party_size = request.POST['party_size']
    phone = None
    if 'phone' in request.POST:
        phone = request.POST['phone']
    wl = get_object_or_404(WaitList, pk=waitlist_id)
    c = Customer(name = name, party_size = party_size, phone = phone, waitlist = wl)
    c.save()
    return redirect('/waitlist/%s/' % waitlist_id)

# Helper for summon_customer and remove_customer
def set_customer_status(request, customer_id, status):
    c = get_object_or_404(Customer, pk=customer_id)
    c.status = status
    c.save()
    return redirect('/waitlist/%d/' % c.waitlist.id)
   
@csrf_protect
def show_waitlist(request, waitlist_id):
    wl = get_object_or_404(WaitList, pk=waitlist_id)
    return render(request, 'buzme/restaurant_queue.html',
                              {'waitlist': wl})

def signin(request, restaurant_id):
    username = None
    password = None
    
    restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    
    if 'password' in request.REQUEST:
        password = request.REQUEST['password']
    if 'username' in request.REQUEST: 
        username = request.REQUEST['username']
    
    if not password and not username:
        return render_to_response('buzme/signin.html')
    elif not password or not username:
        return render_to_response('buzme/signin.html',
                                  {'failure_message': 'Please provide both username and password',
                                   'username': username})
    
    user = auth.authenticate(username=username, password=password)
    if (user is None) or (user.id != restaurant.user.id and not user.is_superuser):
        return render_to_response('buzme/signin.html',
                                  {'failure_message': 'Authentication failed',
                                   'username': username})
    if user.is_active:
        auth.login(request, user)
        return redirect('/waitlist/%d/' % Restaurant.objects.all()[0].waitlists.all()[0].id)
    else:
        return render_to_response('buzme/signin.html',
                                  {'failure_message': 'Account %s disabled' % username,
                                   'username': username})
        
    
def signout(request):
    username = None
    if request.user.is_authenticated:
        username = request.user.username;
        auth.logout(request.user)
    render_to_response('buzme/signin.html',
                       {'username': username})
    

def debug_misc(request):
    '''Use this however you want, it's accessible from /debug/misc. Leave it as you found it, though.'''
    return HttpResponse(str(request.user))
    
        
    
