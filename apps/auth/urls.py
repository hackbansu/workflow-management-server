from django.conf.urls import url
from rest_framework import routers

from apps.auth.views import UserAuthView, ResetPasswordView, ProfileView

router = routers.SimpleRouter()
router.register('auth', UserAuthView)
urlpatterns = router.urls

urlpatterns += [
    url(r'^user/profile/', ProfileView.as_view(), name='user_profile'),
    url(r'^auth/reset-password/(?P<token>\w+-\w+--\d+)/$',
        ResetPasswordView.as_view(), name='reset-password'),
]
