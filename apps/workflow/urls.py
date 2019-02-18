from django.conf.urls import url

from rest_framework import routers

from apps.workflow import views as workflow_views

router = routers.SimpleRouter()

urlpatterns = router.urls
