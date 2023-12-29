from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import User, AuctionListing, Bid, Comment, Category
from .forms import CreateListingForm, BidForm, CommentForm



def index(request):
    active_listings = AuctionListing.objects.filter(active=True)
    return render(request, "auctions/index.html", {"active_listings": active_listings})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    if request.method == "POST":
        form = CreateListingForm(request.POST)
        if form.is_valid():
            new_listing = form.save(commit=False)
            new_listing.creator = request.user
            new_listing.save()
            return redirect('index')  # Redirect to the active listings page
    else:
        form = CreateListingForm()
    return render(request, "auctions/create_listing.html", {"form": form})

@login_required
def view_watchlist(request):
    user = request.user
    watchlist_items = user.watchlist.all()
    return render(request, "auctions/watchlist.html", {"watchlist_items": watchlist_items})

def listing_detail(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    user = request.user

    # Handle adding/removing from watchlist
    if 'toggle_watchlist' in request.POST:
        if user.is_authenticated:
            if listing in user.watchlist.all():
                user.watchlist.remove(listing)
            else:
                user.watchlist.add(listing)
            return HttpResponseRedirect(reverse('listing_detail', args=[listing_id]))

    # Handle placing a bid
    if 'place_bid' in request.POST and user.is_authenticated:
        bid_form = BidForm(request.POST)
        if bid_form.is_valid():
            bid_amount = bid_form.cleaned_data['bid_amount']
            current_highest_bid = listing.current_bid if listing.current_bid else listing.starting_bid
            if bid_amount > current_highest_bid:
                # The bid is valid, create and save the bid
                bid = Bid(user=user, listing=listing, bid_amount=bid_amount)
                bid.save()
                listing.current_bid = bid_amount
                listing.save()
                # Redirect to avoid resubmitting the form
                return HttpResponseRedirect(reverse('listing_detail', args=[listing_id]))
            else:
                # The bid is not high enough, add an error to the form
                bid_form.add_error('bid_amount', 'Bid must be higher than current bid and at least as high as the starting bid.')
        
        # If the form is not valid or the bid is not high enough, re-render the page with the form errors
        comment_form = CommentForm()  # Initialize an empty comment form
        return render(request, "auctions/listing_detail.html", {
            "listing": listing,
            "bid_form": bid_form,
            "comment_form": comment_form,
            # Include other context variables as needed
        })

    # Handle closing the auction
    if 'close_auction' in request.POST and user.is_authenticated and listing.creator == user:
        listing.active = False
        listing.save()
        # Redirect to avoid resubmitting the form
        return HttpResponseRedirect(reverse('listing_detail', args=[listing_id]))

    # Handle adding a comment
    if 'post_comment' in request.POST and user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment_text = comment_form.cleaned_data['comment_text']
            comment = Comment(user=user, listing=listing, comment_text=comment_text)
            comment.save()
            # Redirect to avoid resubmitting the form
            return HttpResponseRedirect(reverse('listing_detail', args=[listing_id]))

    # Initialize forms
    bid_form = BidForm()
    comment_form = CommentForm()

    # Check if the user has won the auction (if it's closed)
    has_won = False
    if not listing.active and listing.bids.filter(user=user).exists():
        winning_bid = listing.bids.order_by('-bid_amount').first()
        if winning_bid.user == user:
            has_won = True

    return render(request, "auctions/listing_detail.html", {
        "listing": listing,
        "bid_form": bid_form,
        "comment_form": comment_form,
        "has_won": has_won,
        "comments": listing.comments.all(),
        "is_on_watchlist": listing in user.watchlist.all() if user.is_authenticated else False,
    })

def view_categories(request):
    categories = Category.objects.all()
    return render(request, "auctions/categories.html", {"categories": categories})

def view_category_listings(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    listings = AuctionListing.objects.filter(category=category.name, active=True)
    return render(request, "auctions/category_listings.html", {
        "category": category,
        "listings": listings
    })
