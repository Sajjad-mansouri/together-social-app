from django.shortcuts import render
from django.views.generic import TemplateView,ListView,UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Message

UserModel=get_user_model()
class Index(TemplateView):
	template_name='social/index.html'

class Profile(LoginRequiredMixin,ListView):
	template_name='transfer/profile.html'
	

	def get_queryset(self):
		username=self.kwargs.get('username')
		user=self.request.user
		if username:
			user=get_object_or_404(UserModel,username=username)
		self.owner=user
		return Message.objects.filter(user=user)

	def get_context_data(self,**kwargs):
		context=super().get_context_data(**kwargs)
		context['owner']=self.owner
		access=self.owner.rel_to.filter(from_user=self.request.user,to_user=self.owner).exists()
		following_count=self.owner.rel_from.count()
		follower_count=self.owner.rel_to.count()
		total_post=self.owner.messages.count()
		context['following_count']=following_count
		context['follower_count']=follower_count
		context['total_post']=total_post
		if access:
			context['contact_id']=self.owner.rel_to.get(from_user=self.request.user,to_user=self.owner).id
		else:
			context['contact_id']=''
		context['access']=access
		return context


class Search(LoginRequiredMixin,ListView):
	template_name='transfer/search.html'

	def get_queryset(self):
		return UserModel.objects.all()

class Home(LoginRequiredMixin,ListView):
	template_name='transfer/home.html'
	def get_queryset(self):
		following=self.request.user.rel_from.values_list('to_user',flat=True)
		return Message.objects.filter(Q(user_id__in=following)|Q(user=self.request.user))

class Setting(LoginRequiredMixin,TemplateView):
	template_name='transfer/settings.html'


class LikedPost(LoginRequiredMixin,ListView):
	template_name='social/home.html'
	def get_queryset(self):
		return Message.objects.filter(likes__user=self.request.user)

