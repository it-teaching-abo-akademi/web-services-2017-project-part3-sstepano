from rest_framework.views import APIView
from rest_framework.decorators import api_view, renderer_classes, authentication_classes, permission_classes
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.sites.shortcuts import get_current_site
from django.conf.urls import url


from django.http import HttpResponse
from django.http import Http404

from assign4_stepanovicApp.models import Auction
from assign4_stepanovicApp.models import Bid
from assign4_stepanovicApp.serializers import AuctionSerializer
from assign4_stepanovicApp.serializers import BidSerializer


@api_view(['GET'])
@renderer_classes([JSONRenderer,])
def auction_browse_search(request):
    title = request.GET.get('title', '')
    if request.user.is_staff:
        if title != "":
            auctions = Auction.objects.filter(title=title)
        else:
            auctions = Auction.objects.all()
    else:
        if title !="":
            auctions = Auction.objects.filter(title=title, state='Active')
        else:
            auctions = Auction.objects.filter(state='Active')

    serializer = AuctionSerializer(auctions, many=True)
    return Response(serializer.data)

@api_view(['GET', 'POST'])
@renderer_classes([JSONRenderer,])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def new_bid(request, id):
    auction = get_object_or_404(Auction, id=id)
    if request.user != auction.seller and auction.state == "Active":
        if request.method == "POST":
            data = request.data
            print(request.data)
            serializer = BidSerializer(data=data)
            if serializer.is_valid():
                bid = round(data["bid"],2)
                user_id=request.user.id
                user = get_object_or_404(User, id=user_id)
                bids = list(Bid.objects.filter(auctions=auction).all())
                previous_bids = [bid_i.bid for bid_i in bids]
                if previous_bids != []:
                    maxbid = max(previous_bids)
                else:
                    maxbid = auction.minimum_price
                if ((data["bid"] != bid) or (previous_bids != [] and bid <= maxbid) or (bid <= auction.minimum_price)):
                    if (data["bid"] != bid) and (data["bid"] > maxbid):
                        raise serializers.ValidationError({"maximum_bid":maxbid, "bid_error_message": ["The minimum bid increment is 0.01. Only two decimal places are considered when bidding."]})
                    else:
                        raise serializers.ValidationError({"maximum_bid":maxbid, "bid_error_message":["A new bid should be greater than the maximum bid %.2f EUR and the minimum price" % maxbid]})
                auction.tightDeadline()
                current_site = get_current_site(request)
                auction_url = ("http://" + current_site.domain + "/showauction/%d/") % auction.id
                serializer.save(users=[user],auctions=[auction])
                serializerBid = BidSerializer(data={'auction_url': auction_url, 'bid':bid})
                if serializerBid.is_valid():
                    return Response(serializerBid.data)
                else:
                    return Response(serializerBid.errors, status=400)
            else:
                return Response(serializer.errors, status=400)
    elif auction.state != "Active":
        raise serializers.ValidationError(
            {"auction_state_error": ["Auction is not active"]})
    else:
        raise serializers.ValidationError(
            {"authorization_error": ["The seller cannot bid on an auction"]})

