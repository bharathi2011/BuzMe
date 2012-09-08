# Create your views here.
from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.http import HttpResponse
from django.core.mail import send_mail
from models import Customer, WaitList, Restaurant, RestaurantAdmin, RecentActivity, ArchiveTag, Analytics
from django.contrib import auth
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User
from django import forms
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from twilio.rest import TwilioRestClient
from twilio import TwilioRestException
import csv
from random import randint
from datetime import tzinfo, timedelta, datetime
import qrcode
import os, binascii
from django_mobile import get_flavour
from validators import valid_customer_creation_parameters
from django import forms
from django.contrib.localflavor.us.forms import USPhoneNumberField
from subprocess import Popen, PIPE


viewlog = open("views.log","wb")
def log(msg):
    viewlog.write("%s: %s\n" % (datetime.now(), msg))
    viewlog.flush()

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

class AddPatronForm(forms.Form):
    name        = forms.CharField(label="icon-user", max_length=30,
                                  widget=forms.TextInput(attrs={'placeholder': 'Patron Name'}))
    party_size  = forms.IntegerField(label="icon-group", min_value=1, max_value=100,
                                   widget=forms.TextInput(attrs={'placeholder': 'Party Size'}))
    phone       = USPhoneNumberField(label="icon-iphone",
                                   widget=forms.TextInput(attrs={'placeholder': 'Phone Number'}),
                                   required=False)
    email       = forms.EmailField(label="icon-envelope",
                                   widget=forms.TextInput(attrs={'placeholder': 'Email'}),
                                   required=False)
    def clean(self):
        cleaned_data = super(AddPatronForm, self).clean()
        phone = cleaned_data.get("phone")
        email = cleaned_data.get("email")
        if (not phone) and (not email):
           raise forms.ValidationError("Either a phone number or an e-mail address is required.")
        return cleaned_data


class UpdateProfileForm(forms.Form):
    username    = forms.CharField(label="icon-user", max_length=30,
                                  widget=forms.TextInput(attrs={'placeholder': 'LoginID'}))
    email       = forms.EmailField(label="icon-envelope",
                                   widget=forms.TextInput(attrs={'placeholder': 'Contact Email'}))
    nickname    = forms.CharField(label="icon-star", max_length=30,
                                  widget=forms.TextInput(attrs={'placeholder': 'User Name'}))
    restname    = forms.CharField(label="icon-glass",
                                  widget=forms.TextInput(attrs={'placeholder': 'Restaurant Name'}))
    restcontact = forms.CharField(label="icon-home",
                                  widget=forms.TextInput(attrs={'placeholder': 'Restaurant Address'}))
    email_from    = forms.EmailField(label="",
                                   widget=forms.TextInput(attrs={'placeholder': 'Restaurant\'s Email'}))
    email_subject = forms.CharField(label="",
                                  widget=forms.TextInput(attrs={'placeholder': 'Email Subject'}))
    email_message = forms.CharField(label="",
                                  widget=forms.Textarea(attrs={'placeholder': 'Email Message'}))


class SignupProfileForm(UpdateProfileForm):
    password    = forms.CharField(label="icon-asterisk", max_length=30,
                                  widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    password1   = forms.CharField(label="icon-asterisk", max_length=30,
                                  widget=forms.PasswordInput(attrs={'placeholder': 'Retype Password'}))
    def clean_password1(self):
        password = self.cleaned_data.get('password')
        password1 = self.cleaned_data.get('password1')
        if password and password1:
            if password != password1:
                raise forms.ValidationError(("The two password fields didn't match."))
        return password1
    def clean_username(self):
       username = self.cleaned_data['username']
       try:
          user = User.objects.get(username=username)
       except User.DoesNotExist:
          return username
       raise forms.ValidationError(u'%s already exists' % username )



def debug_customers_all(request):
    return render_to_response('buzme/debug_customers.html',
                              {'customers_qs': Customer.objects.all()})

@login_required(login_url='/')
def checkin_customer(request, customer_id):
    return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.CHECKEDIN)
   
@login_required(login_url='/')
def summon_customer(request, customer_id):
    c = get_object_or_404(Customer, pk=customer_id)
    has_phone = c.phone and (not c.phone == "")
    has_email = c.email and (not c.email == "")
    phone_failed = False
    email_failed = False
    if (not has_phone) and (not has_email):
        request.session['err_msg'] = "PLEASE SUMMON %s, PARTY OF %d YOURSELF. They did not leave a phone number or e-mail address." % (c.name, c.party_size)
        return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.SUMMON_FAILED)

    if (has_phone):
        if c.is_test():
            request.session['test_sms_msg'] = "Hello %s. Your table at %s is ready. Please come by." % (c.name, c.waitlist.restaurant.name)
        else:
            client = TwilioRestClient()
            try:
                client.sms.messages.create(to=c.phone, from_="+14086001289",
                                           body="Hello %s. Your table at %s is ready. Please come by." % (c.name, c.waitlist.restaurant.name))
            except TwilioRestException:
                phone_failed = True
                return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.SUMMON_FAILED)

    if (has_email):
        try:
            r = request.user.restaurantAdminUser.restaurant
            if c.is_test():
                request.session['test_email_msg'] = r.email_message.replace("[CUSTOMER]", c.name) 
            else:
                send_mail(
                    r.email_subject, 
                    r.email_message.replace("[CUSTOMER]", c.name), 
                    r.email_from,
                    [c.email],
                    fail_silently=False
                )    
                log ("sent mail to %s from %s" % (c.email, r.email_from))
        except Exception as e:
            if c.is_test():
                print e
            else:
                log(e)
            email_failed = True

    total_failure = ((not has_phone) or (has_phone and phone_failed)) and ((not has_email) or (has_email and email_failed))
    err_msg = "" 
    if total_failure:
        err_msg = "PLEASE SUMMON %s, PARTY OF %d YOURSELF." % (c.name, c.party_size) 
    if phone_failed:
        err_msg += " The phone number they left was invalid."
    if email_failed:
        err_msg += " The e-mail failed to send."
    if err_msg != "":
        request.session['err_msg'] = err_msg # show error messages for failed modes of communication even on success

    if total_failure:
        return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.SUMMON_FAILED)
    return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.SUMMONED)


@login_required(login_url='/')
def remove_customer(request, customer_id):
    return set_customer_status(request, customer_id, Customer.CUSTOMER_STATUS.REMOVED)

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
        failmsg = 'Error in input'
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
        if (user == None):
            failmsg = 'Authentication failed'
        elif user.is_active:
            auth.login(request, user)
            if gmtoffset:
                user.restaurantAdminUser.restaurant.client_gmt_offset = gmtoffset
                user.restaurantAdminUser.restaurant.save()
            return redirect('/waitlist/current/')
        else:
            failmsg = 'Account %s disabled' % username
    return render_to_response('buzme/login_page.html', {'failure_message': failmsg, 'signupFormObj':form}, context_instance=RequestContext(request))
 
def signup(request):
    if request.method == 'POST':
        form = SignupProfileForm(request.POST)
    else:
        form = SignupProfileForm()

    if form.is_valid():
        uname = form.cleaned_data['username']
        pwd = form.cleaned_data['password']
        uemail = form.cleaned_data['email']
        nname = form.cleaned_data['nickname']
        rname = form.cleaned_data['restname']
        rcinfo = form.cleaned_data['restcontact']
        email_from = form.cleaned_data['email_from']
        email_subject = form.cleaned_data['email_subject']
        email_message = form.cleaned_data['email_message']
    else:
        return render_to_response('buzme/login_page.html', 
                                  {'signupFormObj':form, 'signup_view':'yes'}, 
                                  context_instance=RequestContext(request))
    
    try:
        User.objects.get(username=uname)
    except User.DoesNotExist:
        #its ok we are good to go
        u = User.objects.create_user(uname, uemail, pwd)
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
        if not os.path.exists("buzme/static/qrcodes/%s" % (fname)):
            break
    
    img.save("buzme/static/qrcodes/%s" % (fname))
    r = Restaurant(name=rname, contactinfo=rcinfo, client_gmt_offset=0, qrfile=fname,
                   email_from=email_from, email_subject=email_subject, email_message=email_message)
    r.save()
    ra = RestaurantAdmin(nick=nname, adminuser=u, restaurant=r)
    ra.save()
    wl = WaitList(restaurant=r)
    wl.save()
    return redirect('/?status=signup_ok');


def update_profile(request):
    form = UpdateProfileForm(request.POST)
    u = request.user
    ra = u.restaurantAdminUser
    r = ra.restaurant

    tfile = 'buzme/restaurant_queue.html'
    if (get_flavour() == "mobile"):
        tfile = 'buzme/m_restaurant_queue.html'

    if not form.is_valid():
        return render(request, tfile, {
         'waitlist':r.waitlists.all()[0],
         'modal_view':'update_profile',
         'restaurant':r, 
         'admin':ra,
         'updateFormObj':form,
         'err_msg':"error updating profile"
          })

    ra.nick = form.cleaned_data['nickname']
    r.contactinfo = form.cleaned_data['restcontact']
    r.name = form.cleaned_data['restname']
    r.email_from = form.cleaned_data['email_from']
    r.email_subject = form.cleaned_data['email_subject']
    r.email_message = form.cleaned_data['email_message']
    u.email = form.cleaned_data['email']
    r.save();
    ra.save();
    u.save();
    
    return redirect('/waitlist/current/');

@login_required(login_url='/')
def waitlist(request, datetag):
    if request.method == 'POST':
        #valid, err_msg = valid_customer_creation_parameters(request)
        patron_form = AddPatronForm(request.POST)
        if patron_form.is_valid():
            name       = patron_form.cleaned_data['name']
            party_size = patron_form.cleaned_data['party_size']
            phone      = patron_form.cleaned_data['phone']
            email      = patron_form.cleaned_data['email']
            rstrnt = request.user.restaurantAdminUser.restaurant
            wl = rstrnt.waitlists.all()[0]
            c = Customer(name=name, party_size=party_size, phone=phone, email=email, waitlist=wl, dateTag="current")
            c.save()
            ract = RecentActivity(activity=Customer.CUSTOMER_STATUS.WAITING, customer=c, restaurant=wl.restaurant, dateTag="current")
            ract.save()
            patron_form = AddPatronForm()
    else:
        patron_form = AddPatronForm()
   
    err_msg = None
    if 'err_msg' in request.session:
        err_msg = request.session['err_msg']
        del request.session['err_msg']
        if err_msg == "":
            err_msg = None
    rstrnt = request.user.restaurantAdminUser.restaurant
    wl = rstrnt.waitlists.all()[0]
    form = UpdateProfileForm({
            'username': request.user.username,
            'email': request.user.email,
            'nickname': request.user.restaurantAdminUser.nick,
            'restname': rstrnt.name,
            'restcontact': rstrnt.contactinfo,
            'email_from': rstrnt.email_from,
            'email_subject': rstrnt.email_subject,
            'email_message': rstrnt.email_message,
       })
    form.fields['username'].widget.attrs['readonly'] = True

    #if pulling up archive pages, generate analytics
    if ((datetag != "current") and (datetag != "unprocessed") and 
            (not Analytics.objects.filter(restaurant__exact=rstrnt).filter(dateTag__exact=datetag).exists())):
        chkinc = [0] * 24
        avgwt = [0] * 24
        avgwtc = [0] * 24
        for c in Customer.objects.filter(waitlist__exact=wl).filter(dateTag__exact=datetag):
            cact = None
            wact = None
            for act in c.activities.all():
                if act.activity == Customer.CUSTOMER_STATUS.CHECKEDIN:
                    cact = act
                if act.activity == Customer.CUSTOMER_STATUS.WAITING:
                    wact = act
            if cact:
                chkinc[cact.hour()] = chkinc[cact.hour()] + 1
                if wact:
                    difftime = cact.activityTime - wact.activityTime
                    avgwt[wact.hour()] += difftime.seconds / 60
                    avgwtc[wact.hour()] = avgwtc[wact.hour()] + 1
        for n in range(24):
            if avgwtc[n]:
                avgwt[n] = avgwt[n] / avgwtc[n]
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

   
    tfile = 'buzme/restaurant_queue.html'
    if (get_flavour() == "mobile"):
        tfile = 'buzme/m_restaurant_queue.html'
        patron_form.fields['name'].widget.attrs['class'] = "input-medium"
        patron_form.fields['phone'].widget.attrs['class'] = "input-small"
        patron_form.fields['party_size'].widget.attrs['class'] = "input-mini"
        patron_form.fields['email'].widget.attrs['class'] = "input-small"
    
    return render(request, tfile, {
         'waitlist':rstrnt.waitlists.all()[0],
         'restaurant':rstrnt, 
         'admin':rstrnt.restaurantAdministrator.all()[0],
         'updateFormObj':form,
         'addPatronFormObj':patron_form,
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
         'err_msg':err_msg
          })



@login_required(login_url='/')
def archive_current(request):
    log("entering archive_current")
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
    log("redirecting from archive_current")
    return redirect('/waitlist/current/');


def signout(request):
    auth.logout(request)
    return redirect('/?status=signout')
    

def debug_misc(request):
    '''Use this however you want, it's accessible from /debug/misc. Leave it as you found it, though.'''
    return HttpResponse(str(request.user))


@login_required(login_url='/')
def test_add(request, inputd, inputp, es):
    log("entering test_add")
    utc = UTC()
    gmtoffset = request.user.restaurantAdminUser.restaurant.client_gmt_offset
    day = int(inputd)
    patrons = int(inputp)
    wl = request.user.restaurantAdminUser.restaurant.waitlists.all()[0]
    maxusers = patrons * day
    d = datetime.utcnow()
    d = d + timedelta(minutes= -gmtoffset)
    d0 = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=utc)
    startd = d0 + timedelta(days= -(day - 1))
    log("test_add checkpoint 1")
    testdata = csv.reader(open('website/templates/buzme/testdata.csv', 'rb'), delimiter=',')
    log("test_add checkpoint 2")
    for row in testdata:
        p = row.pop()
        n = row.pop()
        ps = randint(1, 6)
        if randint(1, 10) % 4 == 0:
            d1 = startd + timedelta(minutes=((randint(0, day - 1) * 1440) + randint(17 * 60, 23 * 60) + gmtoffset))
            c = Customer(name=n, party_size=ps, phone=p, waitlist=wl, dateTag="current", activityTime=d1)
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
    log("test_add checkpoint 3")
    for c in Customer.objects.filter(waitlist__exact=wl).filter(dateTag__exact="current"):
        midstate = None
        de = randint(3, 60)
        dm = randint(1, de)
        if randint(1, 10) % 4 == 0:
            endstate = Customer.CUSTOMER_STATUS.REMOVED
            if randint(1, 10) % 4 == 0:
                midstate = Customer.CUSTOMER_STATUS.SUMMON_FAILED
            else:
                midstate = Customer.CUSTOMER_STATUS.SUMMONED
        elif es == "checkedin_removed":
            endstate = Customer.CUSTOMER_STATUS.CHECKEDIN
            if randint(1, 10) % 2 == 0:
                midstate = Customer.CUSTOMER_STATUS.SUMMONED
            elif randint(1, 10) % 4 == 0:
                midstate = Customer.CUSTOMER_STATUS.SUMMON_FAILED
        elif randint(1, 10) % 2 == 0:
            endstate = Customer.CUSTOMER_STATUS.WAITING
        elif randint(1, 10) % 3 == 0:
            endstate = Customer.CUSTOMER_STATUS.SUMMONED
        elif randint(1, 10) % 4 == 0:
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
    log("redirecting from test_add")
    if day == 1:
        return redirect('/waitlist/current');
    return redirect('/archive_current/');


def purgeCustomers(request):
    r = request.user.restaurantAdminUser.restaurant
    wl = r.waitlists.all()[0]

    RecentActivity.objects.filter(restaurant__exact=r).delete()
    ArchiveTag.objects.filter(restaurant__exact=r).delete()
    Customer.objects.filter(waitlist__exact=wl).delete()
    Analytics.objects.filter(restaurant__exact=r).delete()

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
    os.remove("buzme/static/qrcodes/%s" % (r.qrfile))
    r.delete()
    auth.logout(request)
    u.delete()
    return redirect('/?status=delete')
