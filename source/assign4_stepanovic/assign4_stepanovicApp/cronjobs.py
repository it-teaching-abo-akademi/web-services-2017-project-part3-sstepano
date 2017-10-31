from django_cron import CronJobBase, Schedule
from django.shortcuts import get_object_or_404
from assign4_stepanovicApp.models import Auction
from datetime import datetime
from django.contrib.auth.models import User
from assign4_stepanovicApp.models import Bid
from django.core.mail import send_mail
from datetime import datetime, timezone
import pytz

class MyCronJob(CronJobBase):
    RUN_EVERY_MINS = 1
    RETRY_AFTER_FAILURE_MINS = 1

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS,retry_after_failure_mins=RETRY_AFTER_FAILURE_MINS)
    code = 'assign4_stepanovicApp.my_cron_job'    # a unique code

    def do(self):
        #d = pytz.utc.localize(datetime.now())
        auctions = Auction.objects.filter(state = 'Active')
        for auction in auctions:
            if (pytz.utc.localize(datetime.now()) > auction.deadline):
                bids = list(Bid.objects.filter(auctions=auction).all())
                if bids != []:
                    bidders = list(User.objects.filter(bid__in=bids).all())
                    bidders = list(set(bidders))
                    bidders_emails = [x.email for x in bidders ]
                    bidders_emails.append(auction.seller.email)
                    bidssorted = sorted(bids, key=lambda x: x.bid, reverse=True)
                    bidmax = bidssorted[0]
                    biddermax = get_object_or_404(User, bid=bidmax)
                    auction.state = 'Adjudicated'
                    auction.save()
                    message = """Hi,\
                            \nThe auction %s has been resolved.\
                            \nThe winner is %s.\
                            \nThe winning bid is %.2f EUR."""% (auction.title, biddermax.username, bidmax.bid)
                    send_mail(
                        #'Your auction',
                        'The auction has been resolved',
                        message,
                        'stepanovic2002@yahoo.com',
                        bidders_emails,
                        fail_silently=False,
                    )
                else:
                    auction.state = 'Due'
                    auction.save()
                print("Deadline!")
            print("I am running!")