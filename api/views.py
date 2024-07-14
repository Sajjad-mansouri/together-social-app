from rest_framework import generics,status
from rest_framework.parsers import FormParser,MultiPartParser,JSONParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.mixins import DestroyModelMixin,CreateModelMixin
from rest_framework.generics import GenericAPIView,CreateAPIView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from rest_framework.views import APIView

from django.db.models import Q
from .serializers import (
						PostSerializer,
						UserSerializer,
						SearchSerializer,
						ContactSerializer,
						LikeSerializer,
						ProfileSerializer,
						CommentSerializer,
						LikeCommentSerializer,
						SavedPostSerializer,
						ChangePasswordSerializer,
						RelationSerializer,
						GeneralReportSerializer,
						ReportSerializer,
						RestrictionSerializer,
						ReportProblemSerializer,
						MessageSerializer

						)
from django.core.mail import EmailMessage,mail_admins
from .permissions import AuthorDeletePermission,RelationDeletePermission
from social.models import Message,Like,Comment,LikeComment,SavePost,GeneralProblem,Report,ReportProblem
from account.models import Contact,Profile,Block
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
	serializer_class=PostSerializer
	permission_classes=[AuthorDeletePermission]
	queryset=Message.objects.all()


class UserListAPiView(generics.ListAPIView):
	
	serializer_class=SearchSerializer
	def get_serializer_class(self):
		if self.request.query_params.get('relation'):
			return RelationSerializer
		else:
			return SearchSerializer
	def get_queryset(self):

		queryset=None
		print(self.request.query_params)
		if self.request.query_params.get('search') !=None:

			search=self.request.query_params.get('search')
			print(f'search:{search}')
			print(self.request.user)
			queryset=UserModel.objects.filter(username__istartswith=search).exclude(username=self.request.user).exclude(block_from__to_user=self.request.user).select_related('profile')
			print(queryset)
		elif self.request.query_params.get('relation') == 'follower':
			print(self.request.user)
			username=self.request.query_params.get('owner')
			user=get_object_or_404(UserModel,username=username)
			queryset = UserModel.objects.filter(rel_from__to_user=user,rel_from__access=True)
			print(queryset)

			
		
		elif self.request.query_params.get('relation') == 'following':
			username=self.request.query_params.get('owner')
			user=get_object_or_404(UserModel,username=username)
			queryset = UserModel.objects.filter(rel_to__from_user=user,rel_to__access=True)
			print(queryset)



		
		return queryset
		
	def get_serializer_context(self):
		context = super().get_serializer_context()
		if self.request.query_params.get('relation'):
			context['relation']=self.request.query_params.get('relation')

			context["owner"] = self.request.query_params.get('owner')
		return context

class ContactApiView(generics.ListCreateAPIView):
	serializer_class=ContactSerializer
	queryset=Contact.objects.all()




class ContactDetailApiView(generics.RetrieveUpdateDestroyAPIView):
	permission_classes=[RelationDeletePermission]
	serializer_class=ContactSerializer
	queryset=Contact.objects.all()

	def destroy(self,request,*args,**kwargs):
		print('destrory')
		print(kwargs)
		try:
			instance = self.get_object()
		except:
			
			from_user=request.user
			to_user=kwargs.get('to_user')
			to_user=get_object_or_404(UserModel,username=to_user)
			instance=get_object_or_404(Contact,from_user=from_user,to_user=to_user)

		self.perform_destroy(instance)
		return Response(status=status.HTTP_204_NO_CONTENT)

	


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
		print('update')
		partial = kwargs.pop('partial', False)
		instance =self.get_object()
		serializer =self.get_serializer(instance, data=request.data, partial=partial)
		serializer.is_valid(raise_exception=True)
		print('update after is_valid')
		self.perform_update(serializer)

		if getattr(instance, '_prefetched_objects_cache', None):
				# If 'prefetch_related' has been applied to a queryset, we need to
				# forcibly invalidate the prefetch cache on the instance.
				instance._prefetched_objects_cache = {}
		print(serializer.data)
		return Response(serializer.data)


class CommentApiView(generics.ListCreateAPIView):
	serializer_class=CommentSerializer
	permission_classes=[AuthorDeletePermission]
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


class ChangePasswordView(generics.UpdateAPIView):
	serializer_class=ChangePasswordSerializer

	def update(self,request,*args,**kwargs):
		serializer=self.get_serializer(data=request.data)
		print('update ChangePasswordView')
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data)



class ReportsView(generics.ListAPIView):
	serializer_class=GeneralReportSerializer
	queryset=GeneralProblem.objects.all()

class ReportApiView(generics.CreateAPIView):
	serializer_class=ReportSerializer
	queryset=Report.objects.all()


class RestrictionApiView(DestroyModelMixin,CreateModelMixin,GenericAPIView):
	permission_classes=[IsAuthenticated]
	serializer_class=RestrictionSerializer
	queryset=Block.objects.all()

	def delete(self,request,*args,**kwargs):

		from_user=request.user
		to_user=kwargs.get('to_user')
		to_user=get_object_or_404(UserModel,username=to_user)
		instance=get_object_or_404(Block,from_user=from_user,to_user=to_user)

		self.perform_destroy(instance)
		return Response(status=status.HTTP_204_NO_CONTENT)

	def post(self, request, *args, **kwargs):
		to_user=request.data['to_user']
		to_user=UserModel.objects.get(username=to_user)
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		self.perform_create(serializer)
		Contact.objects.filter(Q(from_user=request.user ,to_user=to_user)|Q(from_user=to_user ,to_user=request.user)).delete()
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ReportProblemApiView(CreateAPIView):
	permission_classes=[IsAuthenticated]
	serializer_class=ReportProblemSerializer
	queryset=ReportProblem.objects.all()

	def post(self, request, *args, **kwargs):

		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		self.perform_create(serializer)
		subject='Your report be recieved!'
		body='thanks for reporting'
		
		to=request.user.email
		msg_user = EmailMessage(subject, body, None,[to])
		msg_user.send()
		admin_email_body=f'{request.user.username} report'
		admin_email_subject='a'
		mail=mail_admins(admin_email_subject,admin_email_body)
		print(mail)
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)



class MessageApiView(APIView):
	"""
	View to list all users in the system.

	* Requires token authentication.
	* Only admin users are able to access this view.
	"""
	# parser_classes=[JSONParser]
	parser_classes=[FormParser,MultiPartParser,JSONParser]
	def post(self, request, *args, **kwargs):
		subject='Your message be recieved!'
		body='Your message sent , thanks'
		
		to=request.data['email']
		msg_user = EmailMessage(subject, body, None,[to])
		msg_user.send()
		admin_email_body=render_to_string('email/message_admin.txt',{'user':request.data['name'],'message':request.data['message']})
		admin_email_subject='new message'
		mail=mail_admins(admin_email_subject,admin_email_body)
		return Response('sent')