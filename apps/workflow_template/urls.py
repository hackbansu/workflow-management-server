from django.conf.urls import url

from rest_framework import routers

from apps.workflow_template.views import TemplateListRetrieveView as TemplateListRetrieveView

router = routers.SimpleRouter()
router.register('workflow-templates', TemplateListRetrieveView)

urlpatterns = router.urls
