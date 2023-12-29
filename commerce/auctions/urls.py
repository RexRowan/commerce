from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create/", views.create_listing, name="create_listing"),
    path("listing/<int:listing_id>/", views.listing_detail, name="listing_detail"),
    path("watchlist/", views.view_watchlist, name="view_watchlist"),
    path("categories/", views.view_categories, name="view_categories"),
    path("category/<int:category_id>/", views.view_category_listings, name="view_category_listings"),
    path('closed/', views.closed_listings, name='closed_listings'),
]
