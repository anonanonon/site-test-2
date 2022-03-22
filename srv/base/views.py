
from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Task, UserFiles

from django.contrib.auth.models import User


from base.utils import users
from base.utils import docManager
import config
import json


class CustomLoginView(LoginView):
    template_name = 'base/login.html'
    fields = '__all__'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('tasks')

@login_required
def my_view(request):
    
    context = {
        'users': users.USERS,
       # 'users': User.objects.filter(user=request.user),
        'languages': docManager.LANGUAGES,
        'preloadurl': config.DOC_SERV_SITE_URL + config.DOC_SERV_PRELOADER_URL,
        'editExt': json.dumps(config.DOC_SERV_EDITED),  # file extensions that can be edited
        'convExt': json.dumps(config.DOC_SERV_CONVERT),  # file extensions that can be converted
        'files': docManager.getStoredFiles(request),  # information about stored files
        'fillExt': json.dumps(config.DOC_SERV_FILLFORMS),
        'tasks': Task.objects.all(),
        'filenames': UserFiles.objects.filter(user=request.user)
      
    }
    
    
   
    return render(request, 'task_list.html', context)


class PasswordChangeView(PasswordChangeView):
    form_class = PasswordChangeForm
    success_url = reverse_lazy('login')


   

    

       
