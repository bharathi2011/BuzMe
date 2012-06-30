# Create your views here.
from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.http import HttpResponse
from models import Customer, WaitList, Restaurant, RestaurantAdmin, RecentActivity, ArchiveTag, Analytics
from django.contrib import auth
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User
from django import forms
from django.template import Template, RequestContext
from django.contrib.auth.decorators import login_required
from twilio.rest import TwilioRestClient
from twilio import TwilioRestException
import datetime
import csv
import array
from random import randint
from datetime import tzinfo, timedelta, datetime
import qrcode
import os,binascii
from django_mobile import get_flavour



ZERO = timedelta(0)

# A UTC class.
class UTC(tzinfo):
    """UTC"""
    def utcoffset(self, dt):
        return ZERO
    def tzname(self, dt):
        return "UTC"
    def dst(self, dt):
        return ZERO


class UpdateProfileForm(forms.Form):
    username    = forms.CharField(label="icon-user", max_length=30, 
                     widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    email       = forms.EmailField(label="icon-envelope", 
                     widget=forms.TextInput(attrs={'placeholder': 'email'}))
    nickname    = forms.CharField(label="icon-star", max_length=30, 
                     widget=forms.TextInput(attrs={'placeholder': 'Nickname'}))
    restname    = forms.CharField(label="icon-glass", 
                     widget=forms.TextInput(attrs={'placeholder': 'Restaurant Name'}))
    restcontact = forms.CharField(label="icon-home", 
                     widget=forms.TextInput(attrs={'placeholder': 'Restaurant Contact'}))

class SignupProfileForm(UpdateProfileForm):
    password    = forms.CharField(label="icon-asterisk", max_length=30, 
                     widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password1   = forms.CharField(label="icon-asterisk", max_length=30, 
                     widget=forms.PasswordInput(attrs={'placeholder': 'Retype Password'}))

def debug_customers_all(request):
    return render_to_response('buzme/debug_customers.html',
                              {'customers_qs': Customer.objects.all()})

@login_required(login_url='/')
def checkin_customer(request, customer_id):
    return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.CHECKEDIN)
   
@login_required(login_url='/')
def summon_customer(request, customer_id):
   c = get_object_or_404(Customer, pk=customer_id)
   client = TwilioRestClient()
   try:
      message = client.sms.messages.create(to=c.phone, from_="+14086001289",
                     body="Hello %s. Your table at %s is ready. Please come by."%(c.name, c.waitlist.restaurant.name))
   except TwilioRestException:
      return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.SUMMON_FAILED)
      
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
    c = Customer(name = name, party_size = party_size, phone = phone, waitlist = wl, dateTag="current")
    c.save()
    ract = RecentActivity(activity=Customer.CUSTOMER_STATUS.WAITING, customer=c, restaurant=wl.restaurant, dateTag="current")
    ract.save()
    return redirect('/waitlist/current/')

# Helper for summon_customer and remove_customer
def set_customer_status(request, customer_id, status):
    c = get_object_or_404(Customer, pk=customer_id)
    c.status = status
    c.save()
    ract = RecentActivity(activity=c.status, customer=c,
                          restaurant=c.waitlist.restaurant, dateTag="current")
    ract.save()
    return redirect('/waitlist/current/')

@csrf_protect
def signin_new(request):
  form = SignupProfileForm()
  stat = None
  password = None
  username = None
  gmtoffset = None

  if 'status' in request.REQUEST:
     stat = request.REQUEST['status']
  if 'password' in request.REQUEST:
     password = request.REQUEST['password']
  if 'username' in request.REQUEST: 
     username = request.REQUEST['username']
  if 'gmtoffset' in request.REQUEST: 
     gmtoffset = request.REQUEST['gmtoffset']

  if stat == "signup_exist":
    failmsg = 'Cannot Signup: User Exists'
  elif stat == "signup_ok":
    failmsg = 'Signed Up Succesfully'
  elif stat == "form_error":
    failmsg = 'Error in Signup Form input'
  elif stat == "signout":
    failmsg = 'Signed out successfully'
  elif stat == "delete":
    failmsg = 'Restaurant deleted successfully'
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
        if gmtoffset:
           user.restaurantAdminUser.restaurant.client_gmt_offset = gmtoffset
           user.restaurantAdminUser.restaurant.save()
        return redirect('/waitlist/current/')
     else:
        failmsg = 'Account %s disabled' % username
  return render_to_response('buzme/login_page.html', {'failure_message': failmsg, 'signupFormObj':form},context_instance=RequestContext(request))
 
def signup(request):
  form = SignupProfileForm(request.POST)
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

  qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
  )
  qr.add_data(rname)
  qr.make(fit=True)
  img = qr.make_image()
  
  while 1:
    fname = binascii.b2a_hex(os.urandom(15))
    if not os.path.exists("buzme/static/qrcodes/%s"%(fname)):
       break
  
  img.save("buzme/static/qrcodes/%s"%(fname))
  r = Restaurant(name = rname, contactinfo = rcinfo, client_gmt_offset = 0, qrfile=fname)
  r.save()
  ra = RestaurantAdmin(nick = nname, adminuser=u, restaurant=r)
  ra.save()
  wl = WaitList(restaurant=r)
  wl.save()
  return redirect('/?status=signup_ok');


def update_profile(request):
  form = UpdateProfileForm(request.POST)
  u  = request.user
  ra = u.restaurantAdminUser
  r  = ra.restaurant
  if form.is_valid():
     uname  = form.cleaned_data['username']
     uemail = form.cleaned_data['email']
     nname  = form.cleaned_data['nickname']
     rcinfo = form.cleaned_data['restcontact']
     rname  = form.cleaned_data['restname']

  ra.nick = nname;
  r.contactinfo = rcinfo;
  r.name = rname;
  u.email = uemail;
  r.save();
  ra.save();
  u.save();

  return redirect('/waitlist/current/');

@login_required(login_url='/')
def waitlist(request, datetag):
    rstrnt = request.user.restaurantAdminUser.restaurant
    wl = rstrnt.waitlists.all()[0]
    form = UpdateProfileForm({
            'username': request.user.username,
            'email': request.user.email,
            'nickname': request.user.restaurantAdminUser.nick,
            'restname': rstrnt.name,
            'restcontact': rstrnt.contactinfo,
       })
    form.fields['username'].widget.attrs['readonly'] = True

    #if pulling up archive pages, generate analytics
    if ((datetag != "current") and (datetag != "unprocessed") and (not Analytics.objects.filter(restaurant__exact=rstrnt).filter(dateTag__exact=datetag).exists())):
       chkinc = [0]*24
       avgwt  = [0]*24
       avgwtc = [0]*24
       for c in Customer.objects.filter(waitlist__exact=wl).filter(dateTag__exact=datetag):
          cact  =  None
          wact =  None
          for act in c.activities.all():
             if act.activity == Customer.CUSTOMER_STATUS.CHECKEDIN:
                cact = act
             if act.activity == Customer.CUSTOMER_STATUS.WAITING:
                wact = act
          if cact:
             chkinc[cact.hour()] = chkinc[cact.hour()]+1
             if wact:
                difftime = cact.activityTime - wact.activityTime
                avgwt[wact.hour()] += difftime.seconds/60
                avgwtc[wact.hour()] = avgwtc[wact.hour()]+1
       for n in range(24):
          if avgwtc[n]:
             avgwt[n] = avgwt[n]/avgwtc[n]
          else:
             avgwt[n] = 0
       anlyt = Analytics(restaurant=rstrnt, dateTag=datetag, averagewaittime=avgwt, checkincount=chkinc)
       anlyt.save()
       print anlyt

    cic = None
    awt = None
    if Analytics.objects.filter(restaurant__exact=rstrnt).filter(dateTag__exact=datetag).exists():
       cic = Analytics.objects.filter(restaurant__exact=rstrnt).filter(dateTag__exact=datetag).all()[0].print_checkincount()
       awt = Analytics.objects.filter(restaurant__exact=rstrnt).filter(dateTag__exact=datetag).all()[0].print_averagewaittime()

   
    tfile  = 'buzme/restaurant_queue.html'
    if (get_flavour() == "mobile"):
       tfile  = 'buzme/m_restaurant_queue.html'
       
    return render(request, tfile, {
         'waitlist':rstrnt.waitlists.all()[0], 
         'restaurant':rstrnt, 'admin':rstrnt.restaurantAdministrator.all()[0], 
         'signupFormObj':form, 
         'datetag':datetag, 
         'activities':RecentActivity.objects.filter(restaurant__exact=rstrnt).filter(dateTag__exact=datetag),
         'customers':Customer.objects.filter(waitlist__exact=rstrnt.waitlists.all()[0]).filter(dateTag__exact=datetag),
         'archivedtags':ArchiveTag.objects.filter(restaurant__exact=rstrnt),
         'count_waiting':Customer.objects.filter(waitlist__exact=rstrnt.waitlists.all()[0]).filter(dateTag__exact=datetag).filter(status__exact=Customer.CUSTOMER_STATUS.WAITING).count,
         'count_summoned':Customer.objects.filter(waitlist__exact=rstrnt.waitlists.all()[0]).filter(dateTag__exact=datetag).filter(status__exact=Customer.CUSTOMER_STATUS.SUMMONED).count,
         'count_checkedin':Customer.objects.filter(waitlist__exact=rstrnt.waitlists.all()[0]).filter(dateTag__exact=datetag).filter(status__exact=Customer.CUSTOMER_STATUS.CHECKEDIN).count,
         'count_summonfailed':Customer.objects.filter(waitlist__exact=rstrnt.waitlists.all()[0]).filter(dateTag__exact=datetag).filter(status__exact=Customer.CUSTOMER_STATUS.SUMMON_FAILED).count,
         'count_removed':Customer.objects.filter(waitlist__exact=rstrnt.waitlists.all()[0]).filter(dateTag__exact=datetag).filter(status__exact=Customer.CUSTOMER_STATUS.REMOVED).count,
         'checkincount': cic,
         'averagewaittime': awt,
          })




@login_required(login_url='/')
def archive_current(request):
    rstrnt = request.user.restaurantAdminUser.restaurant
    for ract in RecentActivity.objects.filter(restaurant__exact=rstrnt).filter(dateTag__exact="current"):
       ract.dateTag = ArchiveTag.addTag(rstrnt, ract.activityTime)
       ract.save()
    fc1 = Customer.objects.filter(waitlist__exact=rstrnt.waitlists.all()[0])
    for c in fc1.filter(status__exact=Customer.CUSTOMER_STATUS.REMOVED):
       c.dateTag = ArchiveTag.addTag(rstrnt, c.activityTime)
       c.save()
    for c in fc1.filter(status__exact=Customer.CUSTOMER_STATUS.CHECKEDIN):
       c.dateTag = ArchiveTag.addTag(rstrnt, c.activityTime)
       c.save()
    return redirect('/waitlist/current/');


def signout(request):
    auth.logout(request)
    return redirect('/?status=signout')
    

def debug_misc(request):
    '''Use this however you want, it's accessible from /debug/misc. Leave it as you found it, though.'''
    return HttpResponse(str(request.user))


@login_required(login_url='/')
def test_add(request,inputd, inputp, es):
    utc = UTC()
    gmtoffset = request.user.restaurantAdminUser.restaurant.client_gmt_offset
    day = int(inputd)
    patrons = int(inputp)
    wl  = request.user.restaurantAdminUser.restaurant.waitlists.all()[0]
    maxusers = patrons*day
    d = datetime.utcnow()
    d = d + timedelta(minutes=-gmtoffset)
    d0 = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=utc)
    startd = d0 + timedelta(days=-(day-1))

    while maxusers > 0:
      testdata = csv.reader(open('website/templates/buzme/testdata.csv', 'rb'), delimiter=',')
      for row in testdata:
         p = row.pop()
         n = row.pop()
         ps = randint(1,6)
         if randint(1,10) % 4 == 0:
            d1 = startd + timedelta(minutes=((randint(0,day-1)*1440)+randint(17*60, 23*60)+gmtoffset))
            c = Customer(name = n, party_size = ps, phone = p, waitlist = wl, dateTag="current", activityTime=d1)
            c.save()
            c.activityTime = d1
            c.save()
            ract = RecentActivity(activity=Customer.CUSTOMER_STATUS.WAITING, customer=c, restaurant=wl.restaurant, dateTag="current")
            ract.save()
            ract.activityTime = d1
            ract.save()
            maxusers = maxusers - 1
            if maxusers == 0:
               break

    for c in Customer.objects.filter(waitlist__exact=wl).filter(dateTag__exact="current"):
       midstate = None
       de = randint(3,60)
       dm = randint(1,de)
       if randint(1,10) % 4 == 0:
          endstate = Customer.CUSTOMER_STATUS.REMOVED
          if randint(1,10)%4 == 0:
             midstate = Customer.CUSTOMER_STATUS.SUMMON_FAILED
          else:
             midstate = Customer.CUSTOMER_STATUS.SUMMONED
       elif es == "checkedin_removed":
          endstate = Customer.CUSTOMER_STATUS.CHECKEDIN
          if randint(1,10)%2 == 0:
             midstate = Customer.CUSTOMER_STATUS.SUMMONED
          elif randint(1,10)%4 == 0:
             midstate = Customer.CUSTOMER_STATUS.SUMMON_FAILED
       elif randint(1,10) % 2 == 0:
          endstate = Customer.CUSTOMER_STATUS.WAITING
       elif randint(1,10) % 3 == 0:
          endstate = Customer.CUSTOMER_STATUS.SUMMONED
       elif randint(1,10) % 4 == 0:
          endstate = Customer.CUSTOMER_STATUS.SUMMON_FAILED
       else:
          endstate = Customer.CUSTOMER_STATUS.CHECKEDIN

       
       if midstate:
          d1 = c.activityTime + timedelta(minutes=dm)
          c.status = midstate
          c.save()
          ract = RecentActivity(activity=c.status, customer=c, restaurant=wl.restaurant, dateTag="current")
          ract.save()
          ract.activityTime = d1
          ract.save()

       if endstate != Customer.CUSTOMER_STATUS.WAITING:
          d1 = c.activityTime + timedelta(minutes=de)
          c.status = endstate
          c.save()
          ract = RecentActivity(activity=c.status, customer=c, restaurant=wl.restaurant, dateTag="current")
          ract.save()
          ract.activityTime = d1
          ract.save()
    if day == 1:
       return redirect('/waitlist/current');
    return redirect('/archive_current/');


def purgeCustomers(request):
    r   = request.user.restaurantAdminUser.restaurant
    wl  = r.waitlists.all()[0]

    for ract in RecentActivity.objects.filter(restaurant__exact=r):
       ract.delete()
    for at in ArchiveTag.objects.filter(restaurant__exact=r):
       at.delete()
    for c in Customer.objects.filter(waitlist__exact=wl):
       c.delete()
    for a in Analytics.objects.filter(restaurant__exact=r):
       a.delete()

@login_required(login_url='/')
def test_purgeall(request):
    purgeCustomers(request)
    return redirect('/waitlist/current/')

@login_required(login_url='/')
def delete_profile(request):
    purgeCustomers(request)
    r = request.user.restaurantAdminUser.restaurant
    u = request.user
    for wl in WaitList.objects.filter(restaurant__exact=r):
       wl.delete()
    for ra in RestaurantAdmin.objects.filter(restaurant__exact=r):
       ra.delete()
    os.remove("buzme/static/qrcodes/%s"%(r.qrfile))
    r.delete()
    auth.logout(request)
    u.delete()
    return redirect('/?status=delete')
