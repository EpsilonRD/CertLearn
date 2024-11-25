from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
#from django.db.models.query import QuerySet
from django.db.models import Count
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from .models import Course, Content, Module, Subject 
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import (LoginRequiredMixin, PermissionRequiredMixin)
from django.views.generic.base import TemplateResponseMixin, View
from .forms import ModuleFormSet
from django.apps import apps 
from django.forms.models import modelform_factory
from django.core.cache import cache
from students.forms import CourseEnrollForm
from braces.views import CsrfExemptMixin, JsonRequestResponseMixin

# Create your views here.



class OwnerMixin:
    """
       A mixin that filters the QuerySet to return only objects owned by the current user.
       Methods:
        get_queryset: Filters objects based on the owner attribute.
        """
    def get_queryset(self):
        """
        Overrides the get_queryset method to return only the courses 
        created by the user making the request.

        Returns:
            QuerySet: Courses filtered by the current owner (self.request.user).
        """
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)
    
class OwnerEditMixin(OwnerMixin):
    """
      Extends OwnerMixin to include additional logic for handling forms.
      Automatically assigns the owner (owner) of the object before saving it.

    Methods:
        form_valid: Overrides the method to set the current user as the owner.
    """
    def form_valid(self, form):
        """
        Assigns the current user to the owner attribute of the object 
        before saving it.

        Parameters:
            form (Form): The form being processed.

        Returns:
            HttpResponse: The HTTP response after validating the form.
        """
        form.instance.owner = self.request.user 
        return super().form_valid(form)
    
class OwnerCourseMixin(OwnerMixin, LoginRequiredMixin, PermissionRequiredMixin):
    """
    Extends OwnerMixin and defines additional configurations specific to the Course model.

    Attributes:
        model: The associated model (Course).
        fields: Fields included in the view's form.
        success_url: The URL to redirect to after a successful operation.
    """
    model = Course 
    fields = ['subject', 'title', 'slug', 'overview']
    success_url = reverse_lazy('manage_course_list')

# Mixin for editing Course objects with specific configurations

class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    template_name = 'courses/manage/course/form.html'

class CourseCreateView(OwnerCourseEditMixin,CreateView):
    permission_required = 'courses.add_course'

class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    permission_required = 'courses.change_course'


class CourseDeleteView(OwnerCourseMixin, DeleteView):
    template_name = 'courses/manage/course/delete.html'
    permission_required = 'courses.delete_course'

class ManageCourseListView(ListView):
    """
    A class-based generic view that displays a list of courses created 
    by the current user.

    Attributes:
        model: The model associated with the view (Course).
        template_name: The HTML template used to render the view.
    """
    model = Course
    template_name = 'courses/manage/course/list.html'
    permission_required ='courses.view_course'
    def get_queryset(self):
        """
        Overrides the get_queryset method to return only the courses 
        created by the user making the request.

        Returns:
            QuerySet: Courses filtered by the current owner (self.request.user).
        """
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)
    

#Views for the module forms 
class CourseModuleUpdateView(TemplateResponseMixin, View):
    template_name ='courses/manage/module/formset.html'
    course = None 
    def get_formset(self, data=None):
        return ModuleFormSet(instance=self.course, data=data)
    def dispatch(self, request, pk):
        self.course = get_object_or_404(
            Course, id=pk, owner=request.user
        )
        return super().dispatch(request,pk)
    
    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return self.render_to_response(
            {'course': self.course, 'formset': formset}
        )

    
    def post(self, request, *args, **kwargs):
        formset =self.get_formset(data=request.POST) 
        if formset.is_valid():
            formset.save()
            return redirect('manage_course_list')
        return self.render_to_response(
            {'course': self.course, 'formset':formset}
        )
    

#Views for Add content to the modules 
class ContentCreateUpdateView(TemplateResponseMixin, View):
    module = None 
    model = None 
    obj = None 
    template_name = 'courses/manage/content/form.html'
    def get_model(self, model_name): 
        if model_name in ['text', 'video', 'image', 'file']:
            return apps.get_model(
                app_label='courses', model_name=model_name
            )
        return None 
    
    def get_form(self, model, *args, **kwargs):
        Form = modelform_factory(
            model, exclude=['owner', 'order', 'created', 'updated']
        )
        return Form(*args, **kwargs)
    def dispatch(self, request, module_id, model_name, id=None):
        self.module = get_object_or_404(
            Module, id=module_id, course__owner=request.user
        )
        self.model = self.get_model(model_name)
        if id: 
            self.obj = get_object_or_404(
                self.model, id=id, owner = request.user
            )
        return super().dispatch(request, module_id, model_name, id)
    def get(self, request, module_id, model_name, id=None):
        form = self.get_form(
        self.model, 
        instance=self.obj
    )
        return self.render_to_response(
        {'form': form, 'object': self.obj}
        )
    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(
        self.model, 
        instance=self.obj,
        data=request.POST,
        files=request.FILES
    )
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
            # Añadir nuevo contenido
                Content.objects.create(module=self.module, item=obj)
                return redirect('module_content_list', self.module.id)
        return self.render_to_response(
            {'form': form, 'object': self.obj}
            )
    
class ContentDeleteView(View):
    def post(self, request, id):
        content = get_object_or_404(
            Content, id=id, module__course__owner=request.user
        )
        module = content.module
        content.item.delete()
        content.delete()
        return redirect('module_content_list', module.id)


#Managing the Modules content

class ModuleContentListView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/content_list.html'
    def get(self, request, module_id): 
        module = get_object_or_404(
            Module, id=module_id, course__owner=request.user
        )
        return self.render_to_response({'module':module})
    

#Using Mixins of Django-braces
class ModuleOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Module.objects.filter(
                id=id, course__owner=request.user
            ).update(order=order)
        return self.render_json_response({'saved': 'OK'})
    
class ContentOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Content.objects.filter(
                id=id, module__course__owner=request.user
            ).update(order=order)
        return self.render_json_response({'saved': 'OK'})
    

#View for cisualization of the course catalog 
class CourseListView(TemplateResponseMixin, View):
    model = Course
    template_name = 'courses/course/list.html'
    def get(self, request, subject=None):
        subjects = cache.get('all_subjects')
        if not subjects:
            subjects = Subject.objects.annotate(
            total_courses=Count('courses')
            )
            cache.set('all_subjects', subjects)
        
        courses = Course.objects.annotate(
            total_modules=Count('modules')
        )

        if subject: 
            subject = get_object_or_404(Subject, slug=subject)
            courses = courses.filter(subject=subject)

        return self.render_to_response(
            {
                'subjects':subjects,
                'subject': subject,
                'courses':courses
            }
        )
    
#generic detail view 

class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course/detail.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enroll_form'] = CourseEnrollForm(
            initial={'course':self.object}
        )
        return context