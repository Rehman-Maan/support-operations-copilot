from django.urls import path

from . import views

app_name = "knowledge_base"

urlpatterns = [
    path("", views.knowledge_list, name="list"),
    path("documents/upload/", views.upload_document, name="upload_document"),
    path("documents/<int:document_id>/retry/", views.retry_document, name="retry_document"),
    path("macros/create/", views.create_macro, name="create_macro"),
]
