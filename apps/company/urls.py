from rest_framework import routers

from apps.company import views as company_views


router = routers.SimpleRouter()
router.register('create-company', company_views.CreateCompanyUserView)
router.register('', company_views.EmployeesView)
router.register('update-company', company_views.UpdateCompanyView)
router.register('company', company_views.InviteEmployeeView)
router.register('company', company_views.CreateCompanyView)
router.register('employee', company_views.EmployeeCompanyView)

urlpatterns = router.urls
