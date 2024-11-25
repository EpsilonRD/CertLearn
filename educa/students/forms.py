from django import forms
from courses.models import Course

class CourseEnrollForm(forms.Form):
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        widget=forms.HiddenInput
    )
    def __init__(self, *args, **kwargs):
        """
        Inicializa el formulario y actualiza el queryset del campo 'course'
        para incluir todos los cursos disponibles.
        """
        super().__init__(*args, **kwargs)  # Llama al método de la clase base
        self.fields['course'].queryset = Course.objects.all() 