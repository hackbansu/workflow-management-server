from django.conf.urls import url

from rest_framework import routers

from apps.report.views import IJLEmployeeCount, UserReport

router = routers.SimpleRouter()

urlpatterns = router.urls

urlpatterns += [
    url(r'^ijl-employees', IJLEmployeeCount.as_view(), name='ijl-employees'),
    url(r'^employee-report/(?P<pk>[0-9]+)/$', UserReport.as_view(), name='employee-report'),
]
