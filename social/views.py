from django.shortcuts import render
from django.views.generic import TemplateView,ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import Message

UserModel=get_user_model()
class Index(TemplateView):
	template_name='social/index.html'

class Profile(LoginRequiredMixin,ListView):
	template_name='social/profile.html'

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
		if access:
			context['contact_id']=self.owner.rel_to.get(from_user=self.request.user,to_user=self.owner).id
		else:
			context['contact_id']=''
		context['access']=access
		return context


class Search(LoginRequiredMixin,ListView):
	template_name='social/search.html'

	def get_queryset(self):
		return UserModel.objects.all()
