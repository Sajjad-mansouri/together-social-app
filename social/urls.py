from django.urls import path
from . import views

urlpatterns=[
	path('',views.Index.as_view(),name='index'),
	path('profile/',views.Profile.as_view(),name='profile'),
	path('search/',views.Search.as_view(),name='search')
]