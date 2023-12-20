from django.shortcuts import render
from django.views.generic import TemplateView,ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Message


class Index(TemplateView):
	template_name='social/index.html'

class Profile(LoginRequiredMixin,ListView):
	model=Message
	template_name='social/profile.html'
