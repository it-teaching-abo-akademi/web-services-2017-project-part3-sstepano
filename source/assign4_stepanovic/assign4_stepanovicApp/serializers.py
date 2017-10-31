from rest_framework import serializers
from assign4_stepanovicApp.models import Auction
from assign4_stepanovicApp.models import Bid
from django.db import models

class AuctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auction
        fields = ('title', 'id', 'description', 'deadline', 'minimum_price', 'seller', 'state',)

class BidSerializer(serializers.ModelSerializer):
    auction_url = serializers.CharField(source='get_absolute_url',  required=False)
    class Meta:
        model = Bid
        fields = ('id', 'bid', 'auction_url')



