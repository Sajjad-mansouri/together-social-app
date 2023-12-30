from rest_framework import generics
from rest_framework.parsers import FormParser,MultiPartParser
from django.contrib.auth import get_user_model

from .serializers import PostSerializer,UserSerializer,ContactSerializer,LikeSerializer
from social.models import Message,Like
from account.models import Contact
UserModel=get_user_model()

class PostListApiView(generics.ListCreateAPIView):

	serializer_class=PostSerializer
	parser_classes=[FormParser,MultiPartParser]
	queryset=Message.objects.all()


class UserListAPiView(generics.ListAPIView):
	serializer_class=UserSerializer
	
	def get_queryset(self):

		search=self.request.query_params.get('search')
		return UserModel.objects.filter(username__istartswith=search).exclude(username=self.request.user)

class ContactApiView(generics.ListCreateAPIView):
	serializer_class=ContactSerializer
	queryset=Contact.objects.all()


class ContactDetailApiView(generics.RetrieveDestroyAPIView):
	serializer_class=ContactSerializer
	queryset=Contact.objects.all()

class LikeApiView(generics.ListCreateAPIView):
	serializer_class=LikeSerializer
	queryset=Like.objects.all()


class LikeDetailApiView(generics.RetrieveDestroyAPIView):
	serializer_class=LikeSerializer
	queryset=Like.objects.all()