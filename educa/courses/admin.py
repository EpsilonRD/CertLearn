from django.contrib import admin
from .models import Subject, Course, Module #Adding the models to the admin site 

# Register your models here.
@admin.register(Subject) #This Decorator add the Subject model to the admin site 
class SubjectAdmin(admin.ModelAdmin):
    """This class define how the Subject model have to be shown in the admin panel of Django """
    list_display =['title', 'slug'] #This define the column that will be show in the object list Subject in the admin panel
    prepopulated_fields = {'slug':('title',)} #This make auto-fill the slug field with the title name 

class ModuleInline(admin.StackedInline):
    """This Class Allow the Module model be shown as a form embedded into the Course model with StakedInline"""
    model = Module #This point the model that will be show inline in this case Module model  

@admin.register(Course)#This Decorator add the Course model to the admin site
class CourseAdmin(admin.ModelAdmin):
    """This class define how the Subject model have to be shown in the admin panel of Django """
    list_display = ['title', 'subject', 'created'] #This define the column title, subject and created that will be displayed in the list course
    list_filter = ['created', 'subject'] #This Add filter in the admin sidebar to allow filter by created and subject
    search_fields = ['title', 'overview'] #Enable the seacrh bar 
    prepopulated_fields = {'slug':('title',)} #Auto fill the slug field automatically 
    inlines =[ModuleInline] # insert the form inline of module  into the form of Course and allow edit module of the course 