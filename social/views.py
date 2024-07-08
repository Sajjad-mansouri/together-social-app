from django.shortcuts import render
from django.views.generic import TemplateView,ListView,UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404,redirect,render
from django.db.models import Q



from .models import Message
from account.models import Notification

UserModel=get_user_model()
class Index(TemplateView):
	template_name='together/login.html'


class Profile(ListView):
	template_name='together/profile.html'
	

	def get_queryset(self):
		
		username=self.kwargs.get('username',self.request.user.username)
		user=self.request.user
		if username:
			owner_user=get_object_or_404(UserModel,username=username)
		self.owner=owner_user
		return Message.objects.filter(user=owner_user)

	def get_context_data(self,**kwargs):
		context=super().get_context_data(**kwargs)
		context['owner']=self.owner
		try:
			access=self.owner.rel_to.filter(from_user=self.request.user,to_user=self.owner,access=True).exists()

			requested=self.owner.rel_to.filter(from_user=self.request.user,to_user=self.owner,access=False).exists()
		except:
			access=False
			requested=False

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
		return context


class Search(LoginRequiredMixin,ListView):
	template_name='transfer/search.html'

	def get_queryset(self):
		return UserModel.objects.all()

class Home(ListView):
	template_name='together/home.html'

	def get(self,request,*args,**kwargs):
		if request.user.is_authenticated:
			return super().get(request,*args,**kwargs)
		else:
			return render(request,'registration/login.html')
	def get_queryset(self):
		following=self.request.user.rel_from.filter(access=True).values_list('to_user',flat=True)
		print(Message.objects.filter(Q(user_id__in=following)|Q(user=self.request.user)))
		print('++++++')
		return Message.objects.filter(Q(user_id__in=following)|Q(user=self.request.user))

	def get_context_data(self,**kwargs):
		context=super().get_context_data(**kwargs)
		context['owner']=self.request.user
		return context


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