from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Profile

class ProfileForm(forms.ModelForm):

	class Meta:
		model=Profile
		fields=['profile_image','birth_day']



class CustomCreationForm(UserCreationForm):
	email=forms.EmailField()
	class Meta(UserCreationForm.Meta):
		model=get_user_model()
		fields=('username','email',)
		
class UserForm(forms.ModelForm):
	class Meta:
		model=get_user_model()
		fields=['first_name','last_name','username','email']