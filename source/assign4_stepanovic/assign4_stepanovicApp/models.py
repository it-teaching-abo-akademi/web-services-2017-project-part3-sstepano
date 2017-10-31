from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timezone, timedelta
import pytz
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import translation
from django.contrib.auth.signals import user_logged_in

class Auction(models.Model):
    seller = models.ForeignKey(User)
    title = models.CharField(max_length=150)
    description = models.TextField()
    minimum_price = models.FloatField()
    deadline = models.DateTimeField()
    state = models.CharField(max_length=15, default="Active")
    lockedby = models.TextField(default="")
    lockedbiddingby = models.TextField(default="")
    #bidders = models.ManyToManyField(Bid)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title']

    def tightDeadline(self):
        d = pytz.utc.localize(datetime.now())
        print("now",d)
        diff = self.deadline-d
        print("diff", diff)
        if diff.total_seconds() <= 300:
            self.deadline += timedelta(0,300)
#            self.save()
        return

class Bid(models.Model):
    users = models.ManyToManyField(User)
    bid = models.FloatField()
    auctions = models.ManyToManyField(Auction)
    #auct = models.ForeignKey(Auction, on_delete =models.CASCADE)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    language = models.CharField(max_length=2, blank=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(user_logged_in)
def setlang(sender, **kwargs):
    translation.activate(kwargs['user'].profile.language)
    kwargs['request'].session[translation.LANGUAGE_SESSION_KEY] = translation.get_language()
