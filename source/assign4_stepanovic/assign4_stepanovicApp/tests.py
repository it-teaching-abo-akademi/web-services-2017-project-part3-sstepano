from django.test import TestCase, RequestFactory, Client
from django.core import mail
from django.contrib.auth.models import AnonymousUser, User
from datetime import datetime, timezone, timedelta
from assign4_stepanovicApp.models import Auction
from .views import *
import pytz
from django.http import HttpResponseRedirect, HttpResponse
from assign4_stepanovicApp.models import Bid

# Create your tests here.
class TR2_1(TestCase):
    fixtures = ['test_data.json',]

    def setUp(self):
        self.user = User.objects.create_user(
            username='abc', email='abc@abo.fi', password='abc')
        #self.d = pytz.utc.localize(datetime.now()) + timedelta(3, 7200)
        date_str = '31-12-2017-13:00:05'
        self.dt = datetime.strptime(date_str, '%d-%m-%Y-%H:%M:%S')

#1
    def test_auctions(self):
        countbefore = Auction.objects.count()
        Auction.objects.create(seller=self.user, title='my title', description='my content',
                                         minimum_price=1, deadline=self.dt)
        countafter = Auction.objects.count()
        self.failUnlessEqual(countafter,countbefore+1)
#2
    def test_createauction_get(self):
        self.client.login(username="jovana", password="dubrovnik")
        response = self.client.get('/createauction/')
        self.failUnlessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "createauction.html")
#3
    def test_createauction_and_saveauction_post(self):
        # Try to add a new auction without authenticating user
        resp = self.client.post('/createauction/', {'title':'my title', 'description':'my description', 'minimum_price':1, 'deadline':'31-12-2017-13:00:05'})
        self.assertRedirects(resp, '/login/?next=/createauction/')

        # Try to add a new auction after authenticating user
        self.client.login(username='jovana', password='dubrovnik')
        response = self.client.post('/createauction/',
                                {'title': 'my title', 'description': 'my description',
                                 'minimum_price': 1, 'deadline': '31-12-2017-13:00:05',})
        self.failUnlessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "confirmauction.html")
        response = self.client.post('/saveauction/',
                                {'option':'No', 'title': 'my title', 'description': 'my description',
                                 'minimum_price': 1, 'deadline': '31-12-2017-13:00:05',})
        self.assertRedirects(response, '/auction/')
        self.assertEqual(len(mail.outbox),0)
        response = self.client.post('/saveauction/',
                                {'option':'Yes', 'title': 'my title', 'description': 'my description',
                                 'minimum_price': 1, 'deadline': '31-12-2017-13:00:05',})
        self.assertRedirects(response, '/auction/')
        self.assertEqual(len(mail.outbox),1)
        self.assertEqual(mail.outbox[0].subject, 'Your auction has been created.')


#4
    def test_createauction_post_min_price(self):
        # Try to add a new auction after authenticating user
        self.client.login(username='jovana', password='dubrovnik')
        response = self.client.post('/createauction/',
                                {'title': 'my title', 'description': 'my description',
                                 'minimum_price': 0, 'deadline': '31-12-2017-13:00:05',})
        self.failUnlessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "createauction.html")
        self.assertContains(response, "Not valid minimum price")
#5
    def test_createauction_post_deadline(self):
        # Try to add a new auction after authenticating user
        self.client.login(username='jovana', password='dubrovnik')
        response = self.client.post('/createauction/',
                                {'title': 'my title', 'description': 'my description',
                                 'minimum_price': 1, 'deadline': '01-11-2017-13:00:05',})
        self.failUnlessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "createauction.html")
        self.assertContains(response, "Not valid deadline")
#6
    def test_saveauction_session_expired(self):
        self.client.login(username="jovana", password="dubrovnik")
        response = self.client.post('/saveauction/',
                                    {'option': 'Yes', 'title': 'my title', 'description': 'my description',
                                     'minimum_price': 1, 'deadline': '31-12-2017-13:00:05', })
        self.assertRedirects(response, '/createauction/')

class TR2_2(TestCase):
    fixtures = ['test_data.json',]

    def setUp(self):
        self.user = User.objects.create_user(
            username='abc', email='abc@abo.fi', password='abc')
        self.anotheruser = User.objects.create_user(
            username='def', email='def@abo.fi', password='def')
        date_str = '31-12-2017-13:00:05'
        self.dt = datetime.strptime(date_str, '%d-%m-%Y-%H:%M:%S')
        anotherdate_str = '01-11-2017-13:00:05'
        self.anotherdt = datetime.strptime(anotherdate_str, '%d-%m-%Y-%H:%M:%S')
        self.auction = Auction.objects.create(seller=self.user, title='my title', description='my content',
                                         minimum_price=1, deadline=self.dt)
        self.anotherauction = Auction.objects.create(seller=self.user, title='my title1', description='my content1',
                                         minimum_price=1, deadline=self.anotherdt)
        anotherbidobj = Bid(bid=10001)
        anotherbidobj.save()
        self.anotherauction.bid_set.add(anotherbidobj)
        self.anotheruser.bid_set.add(anotherbidobj)
        self.anotherauction.state = 'Due'
        self.anotherauction.save()
        #self.d = pytz.utc.localize(datetime.now()) + timedelta(3, 7200)


#7
    def test_bids(self):
        countbefore = Bid.objects.count()
        bidobj = Bid(bid=10000)
        bidobj.save()
        self.auction.bid_set.add(bidobj)
        self.anotheruser.bid_set.add(bidobj)
        countafter = Bid.objects.count()
        self.failUnlessEqual(countafter, countbefore + 1)
#8
    def test_createbid_and_savebid(self):
        self.client.login(username="jovana", password="dubrovnik")
        response = self.client.get('/bid/119/')
        self.failUnlessEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bid.html")

        response = self.client.post('/updatebid/1000/',
                                {'bid':'20',})
        self.assertRedirects(response, '/auction/')
        self.assertEqual(len(mail.outbox), 0)

        response = self.client.post('/updatebid/119/',
                                {'bid':19,})
        self.assertRedirects(response, '/auction/')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'New bid on the auction has been registered')

        response = self.client.post('/updatebid/119/',
                                {'bid':15,})
        self.assertRedirects(response, '/bid/119/')

        response = self.client.post('/updatebid/119/',
                                {'bid':'somestring',})
        self.assertRedirects(response, '/bid/119/')


#9
    def test_createbid_seller(self):
        self.client.login(username='user9', password='p59a559s1059')
        response = self.client.get('/bid/119/')
        self.assertRedirects(response, '/auction/')
#10
    def test_createbid_notactive_auction(self):
        self.client.login(username='user9', password='p59a559s1059')
        response = self.client.get('/bid/%d/' % self.anotherauction.id)
        self.assertRedirects(response, '/auction/')
#11
    def test_savebid_session_expired(self):
        self.client.login(username="jovana", password="dubrovnik")
        response = self.client.post('/updatebid/119/',
                                {'bid':'20',})
        self.assertRedirects(response, '/showauction/119/')


class TR2_3(TestCase):
    fixtures = ['test_data.json',]

    def setUp(self):
        self.client1 = Client()
        self.client2 = Client()
#12
    def test_editauction(self):
        self.client1.login(username='user9', password='p59a559s1059')
        response1 = self.client1.get('/edit/119/')
        self.failUnlessEqual(response1.status_code, 200)
        self.assertTemplateUsed(response1, "editauction.html")
        self.client2.login(username="jovana", password="dubrovnik")
        response2 = self.client2.get('/bid/119/')
        self.assertRedirects(response2, '/showauction/119/')
        response1 = self.client1.post('/update/119/', {'description':'newdescription119'})
        self.assertRedirects(response1, '/auction/')
        response2 = self.client2.get('/bid/119/')
        self.failUnlessEqual(response2.status_code, 200)
        self.assertTemplateUsed(response2, "bid.html")
        response2 = self.client2.post('/updatebid/119/',
                                {'bid':'21',})
        self.assertRedirects(response2, '/auction/')
#13
    def test_savebid(self):
        self.client1.login(username='anabela', password='krusevac')
        response1 = self.client1.get('/bid/119/')
        self.failUnlessEqual(response1.status_code, 200)
        self.assertTemplateUsed(response1, "bid.html")
        self.client2.login(username="jovana", password="dubrovnik")
        response2 = self.client2.get('/bid/119/')
        self.failUnlessEqual(response2.status_code, 200)
        self.assertTemplateUsed(response2, "bid.html")
        response1 = self.client1.post('/updatebid/119/',
                                {'bid':31,})
        response2 = self.client2.post('/updatebid/119/',
                                {'bid':30,})
        self.assertRedirects(response1, '/auction/')
        self.assertRedirects(response2, '/bid/119/')



