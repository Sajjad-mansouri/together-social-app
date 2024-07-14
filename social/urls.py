from django.urls import path
from account.views import CustomLoginView
from . import views

urlpatterns=[
	path('',views.Home.as_view(),name='home'),
	path('login/',CustomLoginView.as_view(),name='login'),
	path('profile/',views.Profile.as_view(),name='profile'),
	path('profile/<str:username>',views.Profile.as_view(),name='profile'),

	path('settings/',views.Setting.as_view(),name='setting'),
	path('liked-post/',views.LikedPost.as_view(),name='liked_post'),

	# path('report-problem/',views.ReportProblem.as_view(),name='report_problem')
	
]