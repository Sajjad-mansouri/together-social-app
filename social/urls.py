from django.urls import path
from . import views

urlpatterns=[
	path('',views.Index.as_view(),name='index'),
	path('profile/',views.Profile.as_view(),name='profile'),
	path('profile/<str:username>',views.Profile.as_view(),name='profile'),
	path('home/',views.Home.as_view(),name='home'),
	path('search/',views.Search.as_view(),name='search')
]