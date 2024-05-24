from django.urls import path
from . import views

urlpatterns=[
	path('',views.Home.as_view(),name='home'),
	path('',views.Index.as_view(),name='index'),
	path('profile/',views.Profile.as_view(),name='profile'),
	path('profile/<str:username>',views.Profile.as_view(),name='profile'),
	path('search/',views.Search.as_view(),name='search'),
	path('settings/',views.Setting.as_view(),name='setting'),
	path('liked-post/',views.LikedPost.as_view(),name='liked_post')
	
]