from django.conf.urls import url

from rest_framework import routers

from apps.company import views as company_views


router = routers.SimpleRouter()
router.register('create-company', company_views.CreateCompanyUserView)
router.register('employees', company_views.EmployeesView)
router.register('update-company', company_views.UpdateCompanyView)
router.register('company', company_views.InviteEmployeeView)
router.register('company', company_views.CreateCompanyView)
router.register('employee', company_views.EmployeeCompanyView)
router.register('employee-detail', company_views.RetreiveEmployee)

urlpatterns = router.urls

urlpatterns += [
    url(r'^employee/invitation/(?P<token>\w+-\w+--\d+--\d+)/$',
        company_views.InvitationView.as_view(), name='employee_invitation'),
]
