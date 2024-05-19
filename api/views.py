from rest_framework import generics
from rest_framework.parsers import FormParser,MultiPartParser
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .serializers import PostSerializer,UserSerializer,ContactSerializer,LikeSerializer,ProfileSerializer,CommentSerializer
from social.models import Message,Like,Comment
from account.models import Contact,Profile
UserModel=get_user_model()

class PostListApiView(generics.ListCreateAPIView):

	serializer_class=PostSerializer
	parser_classes=[FormParser,MultiPartParser]
	queryset=Message.objects.all()

class PostRetrieveDestroyAPIView(generics.RetrieveDestroyAPIView):
	serializer_class=ProfileSerializer
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


class ProfileApiView(generics.ListCreateAPIView):
	serializer_class=ProfileSerializer
	queryset=Profile.objects.all()

class ProfileDetailApiView(generics.RetrieveUpdateDestroyAPIView):
	serializer_class=ProfileSerializer
	queryset=Profile.objects.all()

	def update(self,request,*args,**kwargs):
		partial = kwargs.pop('partial', False)
		instance =self.get_object()
		serializer =self.get_serializer(instance, data=request.data, partial=partial)
		if serializer.is_valid(raise_exception=False):


			self.perform_update(serializer)

			if getattr(instance, '_prefetched_objects_cache', None):
				# If 'prefetch_related' has been applied to a queryset, we need to
				# forcibly invalidate the prefetch cache on the instance.
				instance._prefetched_objects_cache = {}

			return Response(serializer.data)
		else:
			return Response(serializer.errors, status=400)

class CommentApiView(generics.ListCreateAPIView):
	serializer_class=CommentSerializer

	def get_queryset(self):
		message_id = self.kwargs['message_id']
		post=Message.objects.get(id=message_id)
		return post.comment.all()

class CommentDetailApiView(generics.RetrieveDestroyAPIView):
	serializer_class=CommentSerializer
	queryset=Comment.objects.all()