from django import views
from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from base.viewss import actions
from .views import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('', my_view, name ='tasks'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('password/', auth_views.PasswordChangeView.as_view(template_name='base/change-password.html')),
    path('upload', actions.upload),
    path('download', actions.download),
    #path('', TaskList.as_view(), name ='tasks'),
    path('convert', actions.convert),
    path('create', actions.createNew),
    path('edit', actions.edit),
    path('track', actions.track),
    path('remove', actions.remove),
    path('csv', actions.csv),
    path('files', actions.files),
    path('saveas', actions.saveAs)
   
]
urlpatterns += staticfiles_urlpatterns()