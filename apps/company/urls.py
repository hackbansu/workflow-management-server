from django.conf.urls import url
from rest_framework import routers

from apps.company import views as company_views


router = routers.SimpleRouter()
router.register('company', company_views.CreateCompanyUserView)
router.register('company', company_views.EmployeesView)
router.register('employee', company_views.EmployeeCompanyView)
router.register('company', company_views.InviteEmployeeView)
router.register('company', company_views.CreateCompanyView)


urlpatterns = router.urls
