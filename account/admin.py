from django.contrib import admin
from .models import Profile,Contact

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display=['user','profile_image','birth_day']

@admin.register(Contact)
class Contact(admin.ModelAdmin):
	list_display=['from_user','to_user']