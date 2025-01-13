from django.db import models

from accounts.models import CustomUser


# Create your models here.
class Dreams(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    video = models.FileField(upload_to="videos/")
    interpret = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}, {self.created_at}"