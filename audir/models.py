from django.db import models
from django.contrib.auth.models import AbstractUser

#use default user model, allauth for user authentication
class User(AbstractUser) :
    pass

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    project = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.project
    
class Image(models.Model) :
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    file = models.ImageField(upload_to="upload/") #input image
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.file.name

class Result(models.Model) :
    image = models.OneToOneField(Image, on_delete=models.CASCADE)
    length_index = models.FloatField(null=True, blank=True)  
    length_ring = models.FloatField(null=True, blank=True)   
    ratio = models.FloatField(null=True, blank=True) #digit ratio
    result_image = models.ImageField(upload_to='result/', null=True, blank=True) #output image
    progression = models.CharField(max_length=10, default='uploaded') #the default status is 'uploaded'
    handedness = models.CharField(max_length=10, default='N/A', null=True, blank=True) #the default status is 'N/A'

    def __str__(self):
        return self.image.file.name #filename of input image
