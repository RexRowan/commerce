from django import forms
from .models import AuctionListing, Bid, Comment

class CreateListingForm(forms.ModelForm):
    class Meta:
        model = AuctionListing
        fields = ['title', 'description', 'starting_bid', 'image_url', 'category']


class BidForm(forms.Form):
    bid_amount = forms.DecimalField(max_digits=10, decimal_places=2)

class CommentForm(forms.Form):
    comment_text = forms.CharField(widget=forms.Textarea)