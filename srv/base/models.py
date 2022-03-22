from django.contrib.auth.models import User
from django.db import models

class Task(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True
    )
    title = models.CharField(max_length=35)
    description = models.TextField(null=True, blank=True)
    complete = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering=['complete']

class Profile(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    bio = models.TextField(null=True, blank=True)
    profile_pic = models.ImageField(null=True, blank=True, upload_to="images/profile/")
    
    def __str__(self):
        return str(self.user)

class UserFiles(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='namefile',
        null=True,
        blank=True
    )
    namefile = models.TextField(null=True, blank=True, unique=True)
    canedit = models.BooleanField(default=True)
    filetype = models.TextField(null=True)
    fillformdoc = models.BooleanField(default=False)
    def __str__(self):
        return self.title