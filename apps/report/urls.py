from django.conf.urls import url

from rest_framework import routers

from apps.report.views import IJLEmployeeCount

router = routers.SimpleRouter()

urlpatterns = router.urls

urlpatterns += [
    url(r'^ijl-employees/', IJLEmployeeCount.as_view(), name='ijl-employees'),
]
