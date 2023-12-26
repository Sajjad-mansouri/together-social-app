from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

urlpatterns=[
	
	path('',views.PostListApiView.as_view(),name='post_list'),
	path('users/',views.UserListAPiView.as_view(),name='user_list'),

	path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

	
]