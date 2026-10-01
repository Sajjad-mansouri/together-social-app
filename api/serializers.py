from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from django.utils.timesince import timesince
from rest_framework import serializers

from account.models import Block, Contact, Profile
from social.models import (
    Comment,
    GeneralProblem,
    Like,
    LikeComment,
    Message,
    Report,
    ReportProblem,
    SavePost,
)

UserModel = get_user_model()


class PostSerializer(serializers.ModelSerializer):
    def get_author(self, obj):
        try:
            image_url = obj.user.profile.profile_image.url
        except (Profile.DoesNotExist, ValueError):
            image_url = ""

        return {
            "username": obj.user.username,
            "profile_image": image_url,
        }

    owner = serializers.SerializerMethodField("get_author")

    def liked(self, obj):
        user = self._context["request"].user

        try:
            like_obj = user.like_set.get(post=obj)
        except Like.DoesNotExist:
            like_obj = None

        like_count = obj.likes.count()

        try:
            user_likes = user.like_set.values_list("post", flat=True)
        except AttributeError:
            user_likes = []

        if obj.id in user_likes:
            return (True, like_obj.id, like_count)
        else:
            return (False, None, like_count)

    is_liked = serializers.SerializerMethodField("liked")

    def saved(self, obj):
        user = self._context["request"].user

        try:
            saved_obj = user.savepost_set.get(post=obj)
        except SavePost.DoesNotExist:
            saved_obj = None

        try:
            user_saves = user.savepost_set.values_list("post", flat=True)
        except AttributeError:
            user_saves = []

        if obj.id in user_saves:
            return (True, saved_obj.id)
        else:
            return (False, None)

    is_saved = serializers.SerializerMethodField("saved")

    def to_internal_value(self, data):
        user = self._context["request"].user.id
        data["user"] = user
        return super().to_internal_value(data)

    def is_valid(self, raise_exception=False):
        valid = super().is_valid()

        return valid

    class Meta:
        model = Message
        fields = [
            "id",
            "text",
            "image",
            "created",
            "owner",
            "user",
            "is_liked",
            "is_saved",
        ]
        read_only_fields = ["owner", "is_liked"]


class SearchSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(source="profile.profile_image")

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "username", "profile_image"]


class RelationSerializer(serializers.ModelSerializer):
    def get_relation(self, obj):
        username = self.context["owner"]
        if self.context["relation"] == "following":
            return obj.rel_to.get(from_user__username=username).id
        elif self.context["relation"] == "follower":
            return obj.rel_from.get(to_user__username=username).id

    profile_image = serializers.ImageField(source="profile.profile_image")
    relation = serializers.SerializerMethodField("get_relation")

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "username", "profile_image", "relation"]


class UserSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(
        source="profile.profile_image",
        read_only=True,
    )

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email", "username", "profile_image"]


class ContactSerializer(serializers.ModelSerializer):
    def reverse(self, obj):
        return Contact.objects.filter(
            from_user=obj.to_user, to_user=obj.from_user
        ).exists()

    reverse_following = serializers.SerializerMethodField("reverse")

    class Meta:
        model = Contact
        fields = ["id", "from_user", "to_user", "access", "reverse_following"]

    def to_internal_value(self, data):
        if not getattr(self.root, "partial", False):
            from_user = self._context["request"].user.id
            data["from_user"] = from_user

        return super().to_internal_value(data)

    def create(self, validated_data):
        to_user = validated_data.get("to_user")
        access = False if to_user.profile.private else True
        validated_data["access"] = access

        return Contact.objects.create(**validated_data)


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["id", "user", "post"]

    def to_internal_value(self, data):
        user = self._context["request"].user.id
        data["user"] = user

        return super().to_internal_value(data)


class SavedPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavePost
        fields = ["id", "user", "post"]

    def to_internal_value(self, data):
        user = self._context["request"].user.id
        data["user"] = user

        return super().to_internal_value(data)


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Profile
        fields = [
            "id",
            "user",
            "profile_image",
            "birth_day",
            "bio",
            "private",
        ]

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        user = get_user_model().objects.create_user(**user_data)

        return Profile.objects.create(
            user=user,
            **validated_data,
        )

    def update(self, instance, validated_data):
        instance_user = instance.user
        user = validated_data.get("user")

        instance.private = validated_data.get(
            "private",
            instance.private,
        )
        instance.profile_image = validated_data.get(
            "profile_image",
            instance.profile_image,
        )
        instance.birth_day = validated_data.get(
            "birth_day",
            instance.birth_day,
        )
        instance.bio = validated_data.get(
            "bio",
            instance.bio,
        )

        if user:
            instance_user.first_name = user.get(
                "first_name",
                instance_user.first_name,
            )
            instance_user.last_name = user.get(
                "last_name",
                instance_user.last_name,
            )
            instance_user.email = user.get(
                "email",
                instance_user.email,
            )
            instance_user.username = user.get(
                "username",
                instance_user.username,
            )
            instance_user.save()

        instance.save()
        return instance


class profileSerializerReadOnly(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["profile_image"]


class UserProfileSerializer(serializers.ModelSerializer):
    profile = profileSerializerReadOnly(read_only=True)

    class Meta:
        model = get_user_model()
        fields = ["username", "profile"]


class CommentSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    created = serializers.SerializerMethodField()
    is_user_comment = serializers.SerializerMethodField()
    like_info = serializers.SerializerMethodField()

    def get_created(self, obj):
        return timesince(obj.created).split(",")[0]

    def get_is_user_comment(self, obj):
        return obj.author_id == self.context["request"].user.id

    def get_like_info(self, obj):
        user_id = self.context["request"].user.id
        like_count = obj.like.count()

        liked = obj.likecomment_set.filter(user_id=user_id).first()

        data = {
            "is_liked": liked is not None,
            "like_count": like_count,
        }

        if liked is not None:
            data["id"] = liked.id

        return data

    def validate_object_id(self, value):
        if not Message.objects.filter(pk=value).exists():
            raise serializers.ValidationError("The specified message does not exist.")

        return value

    def create(self, validated_data):
        user = self.context["request"].user
        object_id = validated_data.pop("object_id")

        return Comment.objects.create(
            content_object=Message.objects.get(pk=object_id),
            author=user,
            comment=validated_data["comment"],
            parent=validated_data.get("parent"),
            main_comment=validated_data.get("main_comment"),
        )

    class Meta:
        model = Comment
        fields = [
            "id",
            "comment",
            "object_id",
            "author",
            "parent",
            "main_comment",
            "created",
            "is_user_comment",
            "like_info",
        ]
        read_only_fields = [
            "id",
            "author",
            "created",
            "is_user_comment",
            "like_info",
        ]


class LikeCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LikeComment
        fields = ["id", "user", "comment"]

    def to_internal_value(self, data):
        user = self._context["request"].user.id

        data["user"] = user

        return super().to_internal_value(data)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True, max_length=200)
    password1 = serializers.CharField(required=True, write_only=True, max_length=200)
    password2 = serializers.CharField(required=True, write_only=True, max_length=200)

    def to_internal_value(self, data):
        return super().to_internal_value(data)

    def is_valid(self, raise_exception=False):
        valid = super().is_valid(raise_exception=True)

        return valid

    def validate_old_password(self, value):
        user = self._context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("old password is not correct")
        return value

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError("doesnot match passwords")

        validate_password(data["password1"], self._context["request"].user)

        return data

    def save(self, **kwargs):
        password = self.validated_data["password1"]
        user = self._context["request"].user
        user.set_password(password)
        user.save()
        return user


class GeneralReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralProblem
        fields = ["id", "title"]


class ReportSerializer(serializers.ModelSerializer):
    content_type = serializers.CharField(write_only=True)
    post_owner = serializers.CharField(write_only=True)
    is_following = serializers.SerializerMethodField()

    def get_is_following(self, obj):
        request = self.context["request"]

        return Contact.objects.filter(
            from_user=request.user,
            to_user__username=obj.post_owner,
        ).exists()

    def validate_content_type(self, value):
        if value not in {"post", "user"}:
            raise serializers.ValidationError(
                "Content type must be either 'post' or 'user'."
            )
        return value

    def validate(self, attrs):
        content_type = attrs["content_type"]
        object_id = attrs["object_id"]

        if content_type == "post":
            if not Message.objects.filter(pk=object_id).exists():
                raise serializers.ValidationError(
                    {"object_id": "The specified post does not exist."}
                )

        elif content_type == "user":
            if not UserModel.objects.filter(pk=object_id).exists():
                raise serializers.ValidationError(
                    {"object_id": "The specified user does not exist."}
                )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]

        content_type = validated_data.pop("content_type")
        post_owner = validated_data.pop("post_owner")
        object_id = validated_data.pop("object_id")

        if content_type == "post":
            content_object = Message.objects.get(pk=object_id)
        else:
            content_object = UserModel.objects.get(pk=object_id)

        report = Report.objects.create(
            user=request.user,
            content_object=content_object,
            general_report=validated_data["general_report"],
        )

        # Keep the owner available for SerializerMethodField.
        report.post_owner = post_owner

        return report

    class Meta:
        model = Report
        fields = [
            "id",
            "object_id",
            "general_report",
            "content_type",
            "post_owner",
            "is_following",
        ]
        read_only_fields = ["id", "is_following"]


class ReportProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportProblem
        fields = ["user", "report"]
        read_only_fields = ["user"]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class RestrictionSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        data = data.copy()

        self.user = self._context["request"].user.id
        data["from_user"] = self.user

        if "to_user" in data:
            to_user = get_object_or_404(
                UserModel,
                username=data["to_user"],
            )
            data["to_user"] = to_user.pk

        return super().to_internal_value(data)

    class Meta:
        model = Block
        fields = ["id", "from_user", "to_user"]


class MessageSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    message = serializers.CharField(max_length=None)
