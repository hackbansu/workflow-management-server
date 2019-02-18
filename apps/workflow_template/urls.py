from django.conf.urls import url

from rest_framework import routers

from apps.workflow_template.views import TemplateListRetrieveView

router = routers.SimpleRouter()
router.register('workflow-template', TemplateListRetrieveView)

urlpatterns = router.urls
