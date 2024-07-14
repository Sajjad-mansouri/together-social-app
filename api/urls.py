from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

urlpatterns=[
	
	path('',views.PostListApiView.as_view(),name='post-list'),
	path('posts/saved/',views.PostListApiView.as_view(),name='post-saved-list'),
	path('post/<int:pk>/',views.PostRetrieveDestroyAPIView.as_view(),name='post-detail'),
	path('users/',views.UserListAPiView.as_view(),name='user-list'),
	path('contact/',views.ContactApiView.as_view(),name='contact'),
	path('contact/<int:pk>/',views.ContactDetailApiView.as_view(),name='contact-detail'),
	path('conection/<str:to_user>/',views.ContactDetailApiView.as_view(),name='conection'),

	path('like/',views.LikeApiView.as_view(),name='like'),
	path('like/<int:pk>/',views.LikeDetailApiView.as_view(),name='like-detail'),

	path('profiles/',views.ProfileApiView.as_view(),name='profile'),
	path('profiles/<int:pk>',views.ProfileDetailApiView.as_view(),name='profile-detail'),


	path('token/', TokenObtainPairView.as_view(), name='token-obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    path('post/<int:message_id>/comments',views.CommentApiView.as_view(),name='comments'),
    path('comment/<int:pk>',views.CommentDetailApiView.as_view(),name='comment'),

    path('comments/likes/',views.LikeCommentApiView.as_view(),name='comments-likes'),
    path('comment/likes/<int:pk>',views.LikeCommentDetailApiView.as_view(),name='comment-likes'),

    path('saved/',views.AddSavedApiView.as_view(),name='saved'),
	path('saved/<int:pk>/',views.SavedPostDetailApiView.as_view(),name='saved-detail'),

	path('change-password/',views.ChangePasswordView.as_view(),name='change-password'),

	path('reports/',views.ReportsView.as_view(),name='reports'),

	path('report/',views.ReportApiView.as_view(),name='report'),

	path('restriction/<str:to_user>/',views.RestrictionApiView.as_view(),name='restriction'),

	path('report-problem/',views.ReportProblemApiView.as_view(),name='report-problem'),

	path('message/',views.MessageApiView.as_view(),name='message')




	
]