from django.core.management.base import BaseCommand
from datetime import datetime, timezone, timedelta

from django.contrib.auth.models import User
import pytz
from assign4_stepanovicApp.models import Auction
from assign4_stepanovicApp.models import Bid

class Command(BaseCommand):
    help = "Command for populating the database"
    def handle(self, *args, **options):
        for i in range(50):
            username = 'user' + str(i + 1)
            email = username + '@example.com'
            password = 'p' + str(i + 51) + 'a' + str(i + 551) + 's' + str(i + 1051)
            user = User.objects.create_user(username, email, password)
            user.save()
            title = 'Auction' + str(i + 1)
            seller = user
            description = 'Description' + str(i + 1)
            minimum_price = 1
            deadline = pytz.utc.localize(datetime.now()) + timedelta(3, 7200 * i)
            auction = Auction.objects.create(seller=seller, title=title, description=description,
                                             minimum_price=minimum_price, deadline=deadline)
            auction.save()
            if i > 1:
                bidder_username1 = 'user' + str(i)
                bidder_username2 = 'user' + str(i - 1)
                u1 = User.objects.get(username__exact=bidder_username1)
                u2 = User.objects.get(username__exact=bidder_username2)
                bidobj1 = Bid(bid=i)
                bidobj1.save()
                auction.bid_set.add(bidobj1)
                u1.bid_set.add(bidobj1)
                bidobj2 = Bid(bid=2 * i)
                bidobj2.save()
                auction.bid_set.add(bidobj2)
                u2.bid_set.add(bidobj2)