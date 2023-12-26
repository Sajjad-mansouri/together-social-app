from django.shortcuts import render
from django.views.generic import TemplateView,ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model

from .models import Message

UserModel=get_user_model()
class Index(TemplateView):
	template_name='social/index.html'

class Profile(LoginRequiredMixin,ListView):
	template_name='social/profile.html'

	def get_queryset(self):
		return Message.objects.filter(user=self.request.user)

class Search(LoginRequiredMixin,ListView):
	template_name='social/search.html'

	def get_queryset(self):
		return UserModel.objects.all()
