# Create your views here.
from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.http import HttpResponse
from models import Customer, WaitList, Restaurant, RestaurantAdmin, RecentActivity
from django.contrib import auth
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User
from django import forms
from django.template import Template, RequestContext
from django.contrib.auth.decorators import login_required


class SignupForm(forms.Form):
    username    = forms.CharField(label="icon-user", max_length=30, 
                     widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password    = forms.CharField(label="icon-asterisk", max_length=30, 
                     widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password1   = forms.CharField(label="icon-asterisk", max_length=30, 
                     widget=forms.PasswordInput(attrs={'placeholder': 'Retype Password'}))
    email       = forms.EmailField(label="icon-envelope", 
                     widget=forms.TextInput(attrs={'placeholder': 'email'}))
    nickname    = forms.CharField(label="icon-star", max_length=30, 
                     widget=forms.TextInput(attrs={'placeholder': 'Nickname'}))
    restname    = forms.CharField(label="icon-glass", 
                     widget=forms.TextInput(attrs={'placeholder': 'Restaurant Name'}))
    restcontact = forms.CharField(label="icon-home", 
                     widget=forms.TextInput(attrs={'placeholder': 'Restaurant Contact'}))

def debug_customers_all(request):
    return render_to_response('buzme/debug_customers.html',
                              {'customers_qs': Customer.objects.all()})

@login_required(login_url='/')
def checkin_customer(request, customer_id):
    return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.CHECKEDIN)
   
@login_required(login_url='/')
def summon_customer(request, customer_id):
    return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.SUMMONED)

@login_required(login_url='/')
def remove_customer(request, customer_id):
    return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.REMOVED)
    ract.save()

@login_required(login_url='/')
def add_customer_to_waitlist(request, waitlist_id):
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
    ract = RecentActivity(activity="%s party of %s Added"%(name, party_size), restaurant=wl.restaurant)
    ract.save()
    return redirect('/restaurant/%d/' % wl.restaurant.id)

# Helper for summon_customer and remove_customer
def set_customer_status(request, customer_id, status):
    c = get_object_or_404(Customer, pk=customer_id)
    c.status = status
    c.save()
    ract = RecentActivity(activity="%s party of %d %s"%(c.name, c.party_size, c.get_status_display()), 
                          restaurant=c.waitlist.restaurant)
    ract.save()
    return redirect('/restaurant/%d/' % c.waitlist.restaurant.id)

@csrf_protect
def signin_new(request):
  form = SignupForm()
  stat = None
  password = None
  username = None

  if 'status' in request.REQUEST:
     stat = request.REQUEST['status']
  if 'password' in request.REQUEST:
     password = request.REQUEST['password']
  if 'username' in request.REQUEST: 
     username = request.REQUEST['username']

  if stat == "signup_exist":
    failmsg = 'Cannot Signup: User Exists'
  elif stat == "signup_ok":
    failmsg = 'Signed Up Succesfully'
  elif stat == "form_error":
    failmsg = 'Error in Signup Form input'
  elif stat == "signout":
    failmsg = 'Signed out successfully'
  elif not password and not username:
     failmsg = None
  elif not password or not username:
     failmsg = 'Please provide both username and password'

  if username and password:
     user = auth.authenticate(username=username, password=password)
     if (user is None):
        failmsg = 'Authentication failed'
     elif user.is_active:
        auth.login(request, user)
        return redirect('/restaurant/%d/' % user.restaurantAdminUser.restaurant.id)
     else:
        failmsg = 'Account %s disabled' % username
  return render_to_response('buzme/login_page.html', {'failure_message': failmsg, 'signupFormObj':form},context_instance=RequestContext(request))
 
def signup(request):
  form = SignupForm(request.POST)
  if form.is_valid():
     uname  = form.cleaned_data['username']
     pwd    = form.cleaned_data['password']
     uemail = form.cleaned_data['email']
     nname  = form.cleaned_data['nickname']
     rname  = form.cleaned_data['restname']
     rcinfo = form.cleaned_data['restcontact']
#  else:
#    return redirect('/?status=form_error')

  try:
    User.objects.get(username=uname)
  except User.DoesNotExist:
    #its ok we are good to go
    u = User.objects.create_user(uname,uemail,pwd)
    u.save()
  else:
    return redirect('/?status=signup_exist')

  r = Restaurant(name = rname, contactinfo = rcinfo)
  r.save()
  ra = RestaurantAdmin(nick = nname, adminuser=u, restaurant=r)
  ra.save()
  wl = WaitList(restaurant=r)
  wl.save()
  ract = RecentActivity(activity="Created Restaurant", restaurant=r)
  ract.save()
  return redirect('/?status=signup_ok');

@login_required(login_url='/')
def show_waitlist(request, restaurant_id):
    rstrnt = get_object_or_404(Restaurant, pk=restaurant_id)
    return render(request, 'buzme/restaurant_queue.html', {'waitlist':rstrnt.waitlists.all()[0], 'restaurant':rstrnt, 'admin':rstrnt.restaurantAdministrator.all()[0]})


def signout(request):
    auth.logout(request)
    return redirect('/?status=signout')
    

def debug_misc(request):
    '''Use this however you want, it's accessible from /debug/misc. Leave it as you found it, though.'''
    return HttpResponse(str(request.user))
