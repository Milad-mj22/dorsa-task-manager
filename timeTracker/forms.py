from .models import Sprint, Story, Task, Team, TimeEntry
from django.contrib.auth.models import User
import datetime

from django import forms

class TeamForm(forms.ModelForm):
    admins = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    class Meta:
        model = Team
        fields = ['name', 'members', 'admins']

class SprintForm(forms.ModelForm):
    class Meta:
        model = Sprint
        fields = ['name','is_active', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set today's date as default
        if not self.initial.get('start_date'):
            self.initial['start_date'] = datetime.date.today()

        # Add floating label classes
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'floating-input',
                'placeholder': ' ',
            })

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date <= start_date:
            self.add_error('end_date', 'End date must be after start date.')

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title','priority', 'description', 'story','goal_time', 'assigned_to', 'status']






class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ['title','priority', 'description', 'team', 'sprint']




class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ['hours_spent']  # add other fields if you have, but NOT datetime

    def clean_hours_spent(self):
        hours = self.cleaned_data.get('hours_spent')

        return hours
    


from django import forms
from .models import Story

class AssignStoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ['project']  # Only include the project field to assign a project to the story
