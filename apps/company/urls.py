from django.conf.urls import url
from rest_framework import routers

from apps.company.views import CompanyUserView

router = routers.SimpleRouter()
router.register('company', CompanyUserView)

urlpatterns = router.urls
