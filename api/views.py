from rest_framework import generics
from rest_framework.parsers import FormParser,MultiPartParser,JSONParser
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .serializers import (
						PostSerializer,
						UserSerializer,
						SearchSerializer,
						ContactSerializer,
						LikeSerializer,
						ProfileSerializer,
						CommentSerializer,
						LikeCommentSerializer,
						SavedPostSerializer
						)

from .permissions import AuthorDeletePermission
from social.models import Message,Like,Comment,LikeComment,SavePost
from account.models import Contact,Profile
UserModel=get_user_model()

class PostListApiView(generics.ListCreateAPIView):

	serializer_class=PostSerializer
	parser_classes=[FormParser,MultiPartParser]
	def get_queryset(self):
		user=self.request.user
		print(self.request.path)
		if self.request.path=='/api/posts/saved/':

			queryset=Message.objects.filter(saved_posts__user=user)
		else:
			queryset=Message.objects.filter(user=user)
		return queryset


class PostRetrieveDestroyAPIView(generics.RetrieveDestroyAPIView):
	serializer_class=ProfileSerializer
	permission_classes=[AuthorDeletePermission]
	queryset=Message.objects.all()


class UserListAPiView(generics.ListAPIView):
	serializer_class=SearchSerializer
	
	def get_queryset(self):

		search=self.request.query_params.get('search')
		return UserModel.objects.filter(username__istartswith=search).exclude(username=self.request.user).select_related('profile')

class ContactApiView(generics.ListCreateAPIView):
	serializer_class=ContactSerializer
	queryset=Contact.objects.all()


class ContactDetailApiView(generics.RetrieveDestroyAPIView):
	permission_classes=[AuthorDeletePermission]
	serializer_class=ContactSerializer
	queryset=Contact.objects.all()

class LikeApiView(generics.ListCreateAPIView):
	serializer_class=LikeSerializer
	queryset=Like.objects.all()


class LikeDetailApiView(generics.RetrieveDestroyAPIView):
	permission_classes=[AuthorDeletePermission]
	serializer_class=LikeSerializer
	queryset=Like.objects.all()

class AddSavedApiView(generics.CreateAPIView):
	serializer_class=SavedPostSerializer
	
	def get_queryset(self):
		return SavePost.objects.filter(user=self.request.user)


class SavedPostDetailApiView(generics.RetrieveDestroyAPIView):
	permission_classes=[AuthorDeletePermission]
	serializer_class=SavedPostSerializer
	queryset=SavePost.objects.all()
class ProfileApiView(generics.ListCreateAPIView):
	serializer_class=ProfileSerializer
	queryset=Profile.objects.all()

class ProfileDetailApiView(generics.RetrieveUpdateDestroyAPIView):
	serializer_class=ProfileSerializer
	queryset=Profile.objects.all()
	parser_classes=[FormParser,MultiPartParser,JSONParser]
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
	permission_classes=[AuthorDeletePermission]
	serializer_class=CommentSerializer
	queryset=Comment.objects.all()


class LikeCommentApiView(generics.ListCreateAPIView):
	serializer_class=LikeCommentSerializer
	queryset=LikeComment.objects.all()

class LikeCommentDetailApiView(generics.RetrieveDestroyAPIView):
	Apermission_classes=[AuthorDeletePermission]
	serializer_class=LikeCommentSerializer
	queryset=LikeComment.objects.all()