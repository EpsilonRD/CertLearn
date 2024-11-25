from django.contrib.auth.models import User
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey #Using for created Polymorphic content
from django.contrib.contenttypes.models import ContentType #usinf for created models for Polymorphic content 
from .fields import OrderField #importing the OrderField class in the fields.py file 
from django.template.loader import render_to_string

# Create your models here.

#Model for the Subject Tables in the Database 
class Subject(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ['title'] #this class meta for the subject models mean how is have to be sort the data by title
    def __str__(self) -> str:
        return self.title
    
#Model for the Courses Table in the DataBase
class Course(models.Model):
    #This owner field is for the Instructor who created the course 
    owner = models.ForeignKey( 
        User,
        related_name='courses_created',
        on_delete=models.CASCADE
        )
    #This Subject field is for the Subject of the curse belong to.
    subject = models.ForeignKey(
        Subject,
        related_name='courses',
        on_delete=models.CASCADE
        )
    title = models.CharField(max_length=200) #Title of the course
    slug = models.SlugField(max_length=200, unique=True) #The Slug of the course who it will be used for urls
    overview = models.TextField() #This TextField column store overview of the course 
    created = models.DateTimeField(auto_now_add=True) # This save the date an time when the course was created
    students = models.ManyToManyField(
        User,
        related_name='courses_joined',
        blank=True
    )
    class Meta:
        ordering = ['-created']
    def __str__(self):
        return self.title

#model for the Module Table in the DataBase
class Module(models.Model):
    """
    Each course is divided into severl modules. Therefore, the Module models contains
    a ForeignKey field that points to the Course model.

    """
    course = models.ForeignKey(
        Course, related_name='modules', on_delete=models.CASCADE
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = OrderField(blank=True, for_fields=['course'])
    def __str__(self) -> str:
        return f'{self.order}. {self.title}'
    
    class Meta:
        ordering = ['order']

#Creating models for polymorphic content
class Content(models.Model):
    #This associates each contained model object with a specific module
    module = models.ForeignKey(
        Module,
        related_name='contents',
        on_delete=models.CASCADE
    )
    #This field is a foreign key to Django's ContentType model, which allows storing the type of model referenced by each Content
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={
            'model_in':('text','video','image', 'file')
        }
    )
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['module'])
    
    class Meta:
        ordering = ['order']




#Model for the type of the contents Imagen, text and video 

#abstract class for the content 
class ItemBase(models.Model):
    owner = models.ForeignKey(
        User,
        related_name='%(class)s_related',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta: 
        abstract = True #This indicated to Django that this will be a an abstract class 

    def __str__(self) -> str:
        return self.title
    
    def render(self):
        return render_to_string(
            f'courses/content/{self._meta.model_name}.html',
            {'item': self}
        )  
    
class Text(ItemBase):
    """Model for save Text content"""
    content = models.TextField()

class File(ItemBase):
    """Model for save file such pdf """
    content = models.FileField('files')

class Image(ItemBase):
    """Model for save image"""
    file = models.FileField(upload_to='images')

class Video(ItemBase):
    """Model for save Video"""
    url = models.URLField()