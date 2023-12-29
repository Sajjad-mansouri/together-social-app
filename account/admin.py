from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Profile,Contact,MyUser

class MyUserAdmin(UserAdmin):
	pass
admin.site.register(MyUser,MyUserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display=['user','profile_image','birth_day']

@admin.register(Contact)
class Contact(admin.ModelAdmin):
	list_display=['from_user','to_user']