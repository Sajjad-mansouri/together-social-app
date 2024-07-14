from django.shortcuts import render
from django.views.generic import TemplateView,ListView,UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404,redirect,render
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
import json


from .models import Message,Report
from account.models import Notification,AboutSite

UserModel=get_user_model()
class Index(TemplateView):
	template_name='together/login.html'


class Profile(ListView):
	template_name='together/profile.html'
	

	def get_queryset(self):
		ct=ContentType.objects.get_for_model(Message)
		object_ids=Report.objects.filter(content_type__pk=ct.pk).values_list('object_id')

		username=self.kwargs.get('username',self.request.user.username)
		user=self.request.user
		if username:
			owner_user=get_object_or_404(UserModel,username=username)
		self.owner=owner_user
		return Message.objects.filter(user=owner_user).exclude(reports__content_type__pk=ct.pk,reports__object_id__in=object_ids)

	def get_context_data(self,**kwargs):
		context=super().get_context_data(**kwargs)
		context['owner']=self.owner

		access=self.owner.rel_to.filter(from_user=self.request.user,to_user=self.owner,access=True).exists()
		requested=self.owner.rel_to.filter(from_user=self.request.user,to_user=self.owner,access=False).exists()
		is_block=self.request.user.block_from.filter(to_user=self.owner).exists()


		if self.owner==self.request.user:
			access=True
			print('======')
			print(access)


		following_count=self.owner.rel_from.filter(access=True).count()
		follower_count=self.owner.rel_to.filter(access=True).count()
		total_post=self.owner.messages.count()
		context['following_count']=following_count
		context['follower_count']=follower_count
		context['total_post']=total_post
		if access and self.owner !=self.request.user:
			context['contact_id']=self.owner.rel_to.get(from_user=self.request.user,to_user=self.owner).id
		elif requested:
			context['requested_id']=self.owner.rel_to.get(from_user=self.request.user,to_user=self.owner).id
		else:
			context['contact_id']=''
			context['requested_id']=''

		
		context['access']=access
		context['requested']=requested
		context['owner']=self.owner
		context['is_block']=is_block
		return context




class Home(ListView):
	template_name='together/home.html'

	def get(self,request,*args,**kwargs):
		if request.user.is_authenticated:
			return super().get(request,*args,**kwargs)
		else:
			descriptions=json.dumps([item.text for item in AboutSite.objects.all()])
			print(descriptions)
			return render(request,'registration/login.html',{'descriptions':descriptions})
	def get_queryset(self):
		ct=ContentType.objects.get_for_model(Message)
		object_ids=Report.objects.filter(content_type__pk=ct.pk).values_list('object_id')
		following=self.request.user.rel_from.filter(access=True).values_list('to_user',flat=True)

		return Message.objects.filter(Q(user_id__in=following)|Q(user=self.request.user)).exclude(reports__content_type__pk=ct.pk,reports__object_id__in=object_ids).exclude(user__block_from__to_user=self.request.user)





class Setting(LoginRequiredMixin,TemplateView):
	template_name='together/settings.html'

	def get_context_data(self,**kwargs):
		context=super().get_context_data(**kwargs)
		context['owner']=self.request.user
		return context


class LikedPost(LoginRequiredMixin,ListView):
	template_name='social/home.html'
	def get_queryset(self):
		return Message.objects.filter(likes__user=self.request.user)



# class ReportProblem(LoginRequiredMixin,FormView):
# 	template_name