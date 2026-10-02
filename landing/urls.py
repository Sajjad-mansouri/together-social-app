from django.urls import path

from . import views

app_name = "landing"

urlpatterns = [
    path("", views.landing_page, name="home"),
    path("message/", views.ContactMessage.as_view(), name="contact_message"),
    path("get-site-feature/", views.SiteTypingFeature.as_view(), name="typing_feature"),
]
