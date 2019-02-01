from django.conf.urls import url
from rest_framework import routers

from apps.auth.views import UserView

router = routers.SimpleRouter()
router.register('user', UserView)

urlpatterns = router.urls
