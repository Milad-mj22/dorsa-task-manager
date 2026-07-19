from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class City(models.Model):
    name =  models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Project(models.Model):
    name = models.CharField(max_length=200)
    city = models.ForeignKey(City,on_delete=models.SET_NULL, null=True,related_name='project_city')
    persons = models.ManyToManyField(User, related_name="projects_person")  # people involved in mission
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="projects/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name
