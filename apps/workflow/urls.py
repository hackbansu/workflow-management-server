from django.conf.urls import url

from rest_framework import routers

from apps.workflow import views as workflow_views

router = routers.SimpleRouter()
router.register('workflow', workflow_views.WorkflowCRLView)

urlpatterns = router.urls
