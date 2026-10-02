from rest_framework import serializers

from landing.models import EmailInbox, TypingFeature


class EmailInboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailInbox
        fields = ["name", "email", "message", "subject"]


class SiteTypingFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypingFeature
        fields = ["text"]
