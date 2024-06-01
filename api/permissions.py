from rest_framework import permissions


class AuthorDeletePermission(permissions.BasePermission):

	def has_object_permission(self,request,view,obj):
		if request.method in permissions.SAFE_METHODS :
			return True
		if obj.__class__.__name__=='Comment':
			return obj.author==request.user
		else:

			return obj.user==request.user


class RelationDeletePermission(permissions.BasePermission):
	def has_object_permission(self,request,view,obj):
		print(obj.from_user)
		print(obj.to_user)
		print(request.user)
		return obj.from_user==request.user or obj.to_user==request.user