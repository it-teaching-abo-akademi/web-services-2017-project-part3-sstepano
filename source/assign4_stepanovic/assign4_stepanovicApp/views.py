# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import auth
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from datetime import datetime, timezone, timedelta
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib.auth.models import User
import pytz
from django.utils import translation
from django.utils.translation import ugettext as _

import importlib
import itertools
import json
import os
import warnings

from django import http
from django.apps import apps
from django.conf import settings
from django.template import Context, Engine
from django.urls import translate_url
from django.utils import six
from django.utils._os import upath
from django.utils.deprecation import RemovedInDjango20Warning
from django.utils.encoding import force_text
from django.utils.formats import get_format
from django.utils.http import is_safe_url, urlunquote
from django.utils.translation import (
    LANGUAGE_SESSION_KEY, check_for_language, get_language, to_locale,
)
from django.utils.translation.trans_real import DjangoTranslation
from django.views.generic import View


from assign4_stepanovicApp.models import Auction
from assign4_stepanovicApp.forms import createAuction, confirmAuction, currencyExchangeRate, fetchRates, MyUserForm
from assign4_stepanovicApp.pyoxr import OXRClient
from assign4_stepanovicApp.models import Bid

def set_lang(request, user_languagecode="en"):
    request.session[translation.LANGUAGE_SESSION_KEY] = user_languagecode
    translation.activate(user_languagecode)
    if "current_view" in request.session:
        current_view = request.session["current_view"]
    else:
        current_view = "/auction/"
    return HttpResponseRedirect(current_view)


def set_lang_view(request, current_view='/auction/'):
    if translation.LANGUAGE_SESSION_KEY in request.session:
        user_languagecode = request.session[translation.LANGUAGE_SESSION_KEY]
        translation.activate(user_languagecode)
    else:
        user_languagecode = "en"
        request.session[translation.LANGUAGE_SESSION_KEY] = user_languagecode
        #translation.activate(user_languagecode)
    request.session["current_view"] = current_view

##START #######################################################################

def auction(request):
    #set_lang_view(request=request, current_view='/auction/')
    if translation.LANGUAGE_SESSION_KEY not in request.session:
        request.session[translation.LANGUAGE_SESSION_KEY] = 'en'
        translation.activate('en')
    if request.user.is_staff:
        auctions = Auction.objects.order_by('-title')
    else:
        auctions = Auction.objects.filter(state='Active').order_by('-title')
    form = currencyExchangeRate()
    return render(request, "auctions.html",{'auctions':auctions, 'form':form})

@method_decorator(login_required, name="dispatch")
class CreateAuctionView(View):
    def get(self, request):
        #set_lang_view(request=request, current_view='/createauction/')
        form = createAuction()
        return render(request,'createauction.html', {'form' : form})

    def post(self, request):
        def dateValid(deadline):
            #deadline = datetime.strptime(date_string, "%d-%m-%Y")
            d = pytz.utc.localize(datetime.now())
            diff = deadline - d
            if diff.days < 3:
                return False
            return True
        nid = request.user.id
        form = createAuction(request.POST)
        if "user_id" not in request.session:
            request.session["user_id"] = request.user.id
            request.session.save()
        if form.is_valid():
            #seller_id = user.id
            #print("Sell", seller_id)
            cd = form.cleaned_data
            deadline = cd['deadline']
            minimum_price = cd['minimum_price']
            if not dateValid(deadline):
                messages.add_message(request, messages.ERROR, _("Not valid deadline. The minimum duration of an auction is 72 hours from the moment it is created. "))
                return render(request, 'createauction.html', {'form': form, })
            if minimum_price <= 0:
                messages.add_message(request, messages.ERROR, _("Not valid minimum price. The minimum price must be positive. "))
                return render(request, 'createauction.html', {'form': form, })
            if dateValid(deadline):
                title = cd['title']
                description = cd['description']
                form = confirmAuction()
                print(deadline)
                print(deadline.strftime('%d-%m-%Y %H:%M:%S'))
                deadline = deadline.strftime("%d-%m-%Y-%H:%M:%S")
                print("MIN", minimum_price)
                return render(request,'confirmauction.html', {'form' : form, 'title': title, 'description': description, 'minimum_price': minimum_price, 'deadline': deadline})
        else:
            messages.add_message(request, messages.ERROR, _("Not valid data"))
            return render(request,'createauction.html', {'form' : form, })

def saveauction(request):
    newid=request.user.id
    print("Save",newid)
    option = request.POST.get('option', '')
    if "user_id" in request.session:
        user_id = request.session["user_id"]
    else:
        return HttpResponseRedirect('/createauction/')
    if option == 'Yes':
        #seller_id = request.POST.get('seller_id', '')
        #print("Sell", seller_id)
        user = User.objects.get(id=user_id)
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        minimum_price = request.POST.get('minimum_price', '')
        print("MIN1", minimum_price)
        date_str = request.POST.get('deadline', '')
        auction = Auction(seller_id=user.id, title = title, description = description, minimum_price = minimum_price, deadline = datetime.strptime(date_str, '%d-%m-%Y-%H:%M:%S'))
        auction.save()
        messages.add_message(request, messages.INFO, _("New auction has been created"))
        current_site = get_current_site(request)
        message = render_to_string('confirmemail.html', {
            'user': user,
            'auction': auction,
            'domain': current_site.domain,
        })

        send_mail(
            #'Your auction',
            _('Your auction has been created.'),
            message,
            'stepanovic2002@yahoo.com',
            [user.email],
            fail_silently=False,
        )
        return HttpResponseRedirect('/auction/')
    else:
        return HttpResponseRedirect('/auction/')

def showauction(request, id):
    #set_lang_view(request=request, current_view='/showauction/%d/' % int(id))
    if request.user.is_staff:
        auction = get_object_or_404(Auction, id=id)
    else:
        auction = get_object_or_404(Auction, id=id, state='Active')
#    if request.method == 'POST':
    form = currencyExchangeRate()
    rates = fetchRates()
    option = request.GET.get('option', '')
    if option in rates.keys():
        exchangeRate = rates[option]/rates["EUR"]
        form.fields["option"].initial = option
    else:
        exchangeRate = 1
        form.fields["option"].initial = "EUR"
    auction.minimum_price = auction.minimum_price * exchangeRate
    return render(request,"auctions.html",
        {'auctions' : [auction], 'form': form, 'id':id})


def searchauction(request, option):
    #set_lang_view(request=request, current_view='/searchauction/%s/' % option)
    form = currencyExchangeRate()
    #if request.method=="POST":
    title = request.GET.get('title', '')
    if request.user.is_staff:
        auctions = Auction.objects.filter(title = title)
    else:
        auctions = Auction.objects.filter(title = title, state='Active')
    rates = fetchRates()
    #option = request.GET.get('option', '')
    if option in rates.keys():
        exchangeRate = rates[option]/rates["EUR"]
        form.fields["option"].initial = option
    else:
        exchangeRate = 1
        form.fields["option"].initial = "EUR"
    for auction in auctions:
        auction.minimum_price = auction.minimum_price * exchangeRate
    #else:
        #auctions = Auction.objects.all()
        #title=''
    return render(request, "auctions.html",
                  {'auctions': auctions, 'title': title, 'form': form, 'option': option})

def changecurrency(request, title):
    id = request.GET.get('id', '')
    if id != '':
        auctions = Auction.objects.filter(id=id)
    elif title != '':
        auctions = Auction.objects.filter(title = title)
    else:
        auctions = Auction.objects.order_by('-title')
    form = currencyExchangeRate()
    rates = fetchRates()
    option = request.GET.get('option', '')
    if option in rates.keys():
        exchangeRate = rates[option]/rates["EUR"]
        form.fields["option"].initial = option
    else:
        exchangeRate = 1
        form.fields["option"].initial = "EUR"
    for auction in auctions:
        auction.minimum_price = auction.minimum_price * exchangeRate
    return render(request, "auctions.html",{'auctions':auctions, 'form':form, 'option':option, 'title':title, 'id':id})

def editauction(request, id):
    #set_lang_view(request=request, current_view='/edit/%d/' %int(id))
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/?next=%s' % request.path)
    auction = get_object_or_404(Auction, id=id)
    if request.user == auction.seller and auction.state == "Active":
        auction.lockedby = request.session._get_or_create_session_key()
        auction.save()
        return render(request,"editauction.html", {'auction' : auction})
    elif auction.state != "Active":
        messages.add_message(request, messages.INFO, _("Auction is not active"))
        return HttpResponseRedirect(reverse("home"))
    else:
        messages.add_message(request, messages.INFO, _("Only the seller can change the description of an auction"))
        return HttpResponseRedirect(reverse("home"))

def updateauction(request, id):
    auctions = Auction.objects.filter(id= id)
    if len(auctions) > 0:
        auction = auctions[0]
    else:
        messages.add_message(request, messages.INFO, _("Invalid auction id"))
        return HttpResponseRedirect(reverse("home"))

    if request.method=="POST":
        description = request.POST["description"].strip()
        auction.lockedby=""
        auction.description = description
        auction.save()
        messages.add_message(request, messages.INFO, _("Auction description updated"))

    return HttpResponseRedirect(reverse("home"))

def register (request):
    if request.method == 'POST':
        form = MyUserForm(request.POST)
        if form.is_valid():
            new_user = form.save()

            messages.add_message(request, messages.INFO, _("New User is created. Please Login"))

            return HttpResponseRedirect(reverse("home"))
        else:
            form = MyUserForm(request.POST)
    else:
        form =MyUserForm()
    #set_lang_view(request=request, current_view='/createuser/')
    return render(request,"registration.html", {'form': form})


def login_view (request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        nextTo = request.GET.get('next', reverse("home"))
        user = auth.authenticate(username=username, password=password)

        if user is not None and user.is_active:
            auth.login(request,user)
            return HttpResponseRedirect(nextTo)
    #set_lang_view(request=request, current_view='/login/')
    return render(request,"login.html")

def logout_view(request):
    logout(request)
    messages.add_message(request, messages.INFO, "Logged out")
    return HttpResponseRedirect(reverse("home"))

def edituser(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login/?next=%s' % request.path)
    else:
        #set_lang_view(request=request, current_view='/edituser/')
        form = MyUserForm()
        form.fields["username"].initial = request.user.username
        form.fields["username"].widget.attrs['readonly']  = True
        form.fields["username"].help_text = ""
        form.fields["email"].initial = request.user.email
        form.fields["password1"].label = "New password"
        form.fields["password2"].label = "New password confirmation"
        return render(request,"editaccount.html",{'form':form})

def updateuser(request):
    if request.method == 'POST':
        form = MyUserForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            messages.add_message(request, messages.INFO, _("Your account was changed.  Please Login."))
        else:
            messages.add_message(request, messages.INFO, _("Your new account information is not valid. Please, try again."))
    else:
        messages.add_message(request, messages.INFO, _("Please, try again."))
    return HttpResponseRedirect(reverse("home"))

@login_required
def editbid(request, id):
    #set_lang_view(request=request, current_view='/bid/%d/' % int(id))
    if "user_id" not in request.session:
        request.session["user_id"] = request.user.id
        request.session.save()
    auction = get_object_or_404(Auction, id=id)
    if request.user != auction.seller and auction.state == "Active":
        if auction.lockedby == '':
            return render(request,"bid.html", {'auction' : auction})
        else:
            messages.add_message(request, messages.INFO, _("The seller has been changed the description of the auction. Please, try latter."))
            return HttpResponseRedirect("/showauction/%d/"%int(id))
    elif auction.state != "Active":
        messages.add_message(request, messages.INFO, _("Auction is not active"))
        return HttpResponseRedirect(reverse("home"))
    else:
        messages.add_message(request, messages.INFO, _("The seller cannot bid on an auction"))
        return HttpResponseRedirect(reverse("home"))

def updatebid(request, id):
    auctions = Auction.objects.filter(id= id)
    if len(auctions) > 0:
        auction = auctions[0]
    else:
        messages.add_message(request, messages.INFO, _("Invalid auction id!"))
        return HttpResponseRedirect(reverse("home"))
    if "user_id" in request.session:
        user_id = request.session["user_id"]
    else:
        messages.add_message(request, messages.INFO, _("Session expired!"))
        return HttpResponseRedirect('/showauction/%d/' % int(id))
    if request.method=="POST":
        try:
            bid = float(request.POST["bid"].strip())
        except ValueError:
            messages.add_message(request, messages.INFO, _("Invalid value!"))
            return HttpResponseRedirect('/bid/%d/' % int(id))
        users = User.objects.filter(id=user_id)
        if len(users) > 0:
            user = users[0]
        else:
            messages.add_message(request, messages.INFO, _("Invalid user id!"))
            return HttpResponseRedirect(reverse("home"))
        bids = list(Bid.objects.filter(auctions=auction).all())
        previous_bids = [bid_i.bid for bid_i in bids]
        if previous_bids != []:
            maxbid = max(previous_bids)
        else:
            maxbid = auction.minimum_price
        if ((previous_bids != [] and bid <= maxbid) or (bid <= auction.minimum_price)):
            messages.add_message(request, messages.INFO, _("A new bid should be greater than the maximum bid") + ' ' + str(maxbid) + ' ' + _("EUR and the minimum price") )
            return HttpResponseRedirect('/bid/%d/' % int(id))
        if auction.lockedbiddingby != '':
            messages.add_message(request, messages.INFO, _("The another user has been bidded on the auction. Please, try latter."))
            return HttpResponseRedirect("/showauction/%d" % int(id))
        auction.lockedbiddingby = request.session._get_or_create_session_key()
        auction.save()
        bidobj= Bid(bid=bid)
        bidobj.save()
        auction.bid_set.add(bidobj)
        user.bid_set.add(bidobj)
        auction.lockedbiddingby = ''
        auction.tightDeadline()
        auction.save()
        messages.add_message(request, messages.INFO, _("The new bid executed"))
        current_site = get_current_site(request)
        message = render_to_string('confirmemail.html', {
            'auction': auction,
            'domain': current_site.domain,
        })
        bids = list(Bid.objects.filter(auctions=auction).all())
        bidders = list(User.objects.filter(bid__in=bids).all())
        bidders = list(set(bidders))
        bidders_emails = [x.email for x in bidders ]
        bidders_emails.append(auction.seller.email)

        send_mail(
            #'Your auction',
            _('New bid on the auction has been registered'),
            message,
            'stepanovic2002@yahoo.com',
            bidders_emails,
            fail_silently=False,
        )

    return HttpResponseRedirect(reverse("home"))

def ban(request, id):
    if not request.user.is_staff:
        return HttpResponseRedirect('/login/?next=%s' % request.path)
    #set_lang_view(request=request, current_view='/ban/%d/' % int(id))
    auction = get_object_or_404(Auction, id=id)
    if  auction.state == "Active":
        return render(request,"ban.html", {'auction' : auction})
    elif auction.state != "Active":
        messages.add_message(request, messages.INFO, _("Auction is not active"))
        return HttpResponseRedirect(reverse("home"))

def confirmban(request, id):
    auctions = Auction.objects.filter(id= id)
    if len(auctions) > 0:
        auction = auctions[0]
    else:
        messages.add_message(request, messages.INFO, _("Invalid auction id!"))
        return HttpResponseRedirect(reverse("home"))
    if request.method=="POST":
        auction.state = 'Ban'
        auction.save()
        messages.add_message(request, messages.INFO, _("The auction") + ' ' + auction.title + ' ' + _("has been banned."))
        current_site = get_current_site(request)
        message = _("Hi") + """,\
                    \n""" + _("The auction") + ' ' + auction.title + ' ' + _("has been banned") + "."
        bids = list(Bid.objects.filter(auctions=auction).all())
        bidders = list(User.objects.filter(bid__in=bids).all())
        bidders = list(set(bidders))
        bidders_emails = [x.email for x in bidders ]
        bidders_emails.append(auction.seller.email)

        send_mail(
            #'Your auction',
            _('The auction has been banned'),
            message,
            'stepanovic2002@yahoo.com',
            bidders_emails,
            fail_silently=False,
        )

    return HttpResponseRedirect(reverse("home"))

def my_translation_view(request):
    user_languagecode = "fi"
    request.session[translation.LANGUAGE_SESSION_KEY] = user_languagecode
    translation.activate(user_languagecode)

    output = _("Welcome to my site.")
    return HttpResponse(output)

def myset_language(request):
    """
    Redirect to a given url while setting the chosen language in the
    session or cookie. The url and the language code need to be
    specified in the request parameters.

    Since this view changes how the user will see the rest of the site, it must
    only be accessed as a POST request. If called as a GET request, it will
    redirect to the page in the request (the 'next' parameter) without changing
    any state.
    """

    def update_profile(request, lang_code):
        user_id = request.user.id
        users = User.objects.filter(pk=user_id)
        if len(users) > 0:
            user = users[0]
        else:
            return
        user.profile.language = lang_code
        user.save()

    next = request.POST.get('next', request.GET.get('next'))
    if ((next or not request.is_ajax()) and
            not is_safe_url(url=next, allowed_hosts={request.get_host()}, require_https=request.is_secure())):
        next = request.META.get('HTTP_REFERER')
        if next:
            next = urlunquote(next)  # HTTP_REFERER may be encoded.
        if not is_safe_url(url=next, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            next = '/'
    response = http.HttpResponseRedirect(next) if next else http.HttpResponse(status=204)
    if request.method == 'POST':
        lang_code = request.POST.get('language')
        if lang_code and check_for_language(lang_code):
            if next:
                next_trans = translate_url(next, lang_code)
                if next_trans != next:
                    response = http.HttpResponseRedirect(next_trans)
            if hasattr(request, 'session'):
                request.session[LANGUAGE_SESSION_KEY] = lang_code
            else:
                response.set_cookie(
                    settings.LANGUAGE_COOKIE_NAME, lang_code,
                    max_age=settings.LANGUAGE_COOKIE_AGE,
                    path=settings.LANGUAGE_COOKIE_PATH,
                    domain=settings.LANGUAGE_COOKIE_DOMAIN,
                )
            update_profile(request=request, lang_code=lang_code)
    return response



