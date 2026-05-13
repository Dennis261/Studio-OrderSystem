from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from orders import views as order_views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", order_views.dashboard, name="dashboard"),
    path("", include("accounts.urls")),
    path("orders/", include("orders.urls")),
    path("todos/", include("todos.urls")),
    path("manage/statuses/", order_views.manage_statuses, name="manage_statuses"),
    path("manage/templates/", order_views.manage_templates, name="manage_templates"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
