from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

urlpatterns=[
	
	path('',views.PostListApiView.as_view(),name='post_list'),
	path('post/<int:pk>/',views.PostRetrieveDestroyAPIView.as_view(),name='post_detail'),
	path('users/',views.UserListAPiView.as_view(),name='user_list'),
	path('contact/',views.ContactApiView.as_view(),name='contact'),
	path('contact/<int:pk>/',views.ContactDetailApiView.as_view(),name='contact_detail'),

	path('like/',views.LikeApiView.as_view(),name='like'),
	path('like/<int:pk>/',views.LikeDetailApiView.as_view(),name='like_detail'),

	path('profiles/',views.ProfileApiView.as_view(),name='profile'),
	path('profiles/<int:pk>',views.ProfileDetailApiView.as_view(),name='profile_detail'),


	path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('post/<int:message_id>/comments',views.CommentApiView.as_view(),name='comments'),
    path('comment/<int:pk>',views.CommentDetailApiView.as_view(),name='comment'),


	
]