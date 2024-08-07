from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView,UpdateView,DeleteView,TemplateView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.views import LoginView


from .forms import ProfileForm,UserForm,CustomCreationForm
from .emailconf import EmailConfirmation
from .models import SiteManager
User_Model=get_user_model()

class UpdateProfile(LoginRequiredMixin,SuccessMessageMixin,UpdateView):
	model=User_Model
	template_name='social/update-profile.html'
	form_class=UserForm
	success_message = "Profile successfully Updated"
	def get_success_url(self):
		return reverse('profile',args=(self.request.user.pk,))

	def get_object(self,queryset=None):
		return self.request.user
	def get_context_data(self,**kwargs):
		context=super().get_context_data(**kwargs)
		context['user_form']=ProfileForm(instance=self.get_object().profile)
		return context



	def post(self,request,*args,**kwargs):
		profile=self.get_object().profile
		profile_form=ProfileForm(
			instance=profile,
			data= self.request.POST,
			files= self.request.FILES,
			)
		if profile_form.is_valid():

			self.inf=profile_form.save(commit=False)
			self.inf.user=self.request.user
			self.inf.save()
			return super().post(request,*args,**kwargs)
		else:
			return self.form_invalid(profile_form)


class Register(CreateView):
	model=get_user_model()
	form_class=CustomCreationForm
	template_name='registration/register.html'
	success_url=reverse_lazy('home')


	def form_valid(self,form):
		self.object=form.save(commit=False)
		self.object.is_active=False
		self.object.save()
		email_conf=EmailConfirmation(email=self.object.email,request=self.request)
		email_conf.save()
		messages.success(self.request, "signed up successfully! please confirm your email")
		return HttpResponseRedirect(self.get_success_url())


class Deactivate(LoginRequiredMixin,DeleteView):
	template_name='registration/delete_account.html'
	model=User_Model
	success_url=reverse_lazy('home')



class SearchView(LoginRequiredMixin,TemplateView):
	template_name='together/search.html'

class NotificationView(LoginRequiredMixin,TemplateView):
	template_name='together/notification.html'


class ContactMe(TemplateView):
	template_name='together/contact-me.html'

	def get_context_data(self,**kwargs):
		context=super().get_context_data(**kwargs)
		context['manager']=SiteManager.objects.first()
		return context


class CustomLoginView(LoginView):
	def get_context_data(self,**kwargs):
		context=super().get_context_data(**kwargs)
		admin=User_Model.objects.filter(is_superuser=True)[0]
		context['admin']=admin
		return context
