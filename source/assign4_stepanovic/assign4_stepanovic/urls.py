"""assign2_stepanovic URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from assign4_stepanovicApp.views import *
from assign4_stepanovicApp.restframework_rest_api import *
from rest_framework.authtoken import views

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^auction/$', auction, name="home"),
    url(r'^createauction/$', CreateAuctionView.as_view(), name="add_auction"),
    url(r'^saveauction/$', saveauction),
    url(r'^showauction/(?P<id>\d+)/$', showauction, name='show'),
    url(r'^searchauction/(?P<option>\w{0,3})/$', searchauction, name='search'),
    url(r'^changecurrency/(?P<title>\w*)/$', changecurrency),
    url(r'^edit/(?P<id>\d+)/$', editauction),
    url(r'^update/(?P<id>\d+)/$', updateauction),
    url(r'^createuser/$', register),
    url(r'^edituser/$', edituser),
    url(r'^updateuser/$', updateuser),
    url(r'^login/$', login_view),
    url(r'^logout/$', logout_view),
    url(r'^bid/(?P<id>\d+)/$', editbid),
    url(r'^updatebid/(?P<id>\d+)/$', updatebid),
    url(r'^ban/(?P<id>\d+)/$', ban),
    url(r'^confirmban/(?P<id>\d+)/$', confirmban),
    url(r'^api/v1/auctions/$', auction_browse_search),
    url(r'^api/v1/auctions/(?P<id>\d+)/bids/$', new_bid),
    url(r'^transcheck/$', my_translation_view),
    url(r'^set_lang/(?P<user_languagecode>\w{2})/$', set_lang),
   # url('i18n/', include('django.conf.urls.i18n'), name="set_language"),
    url('myset_language/', myset_language, name="myset_language"),
]
