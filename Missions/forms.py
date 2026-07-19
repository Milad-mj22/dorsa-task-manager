from django import forms
from .models import Mission, MissionComment
from django.contrib.auth.models import User

class MissionForm(forms.ModelForm):
    class Meta:
        model = Mission
        fields = ['project','type', 'location', 'persons', 'price','goals', 'description']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مکان ماموریت را وارد کنید'}),
            'persons': forms.CheckboxSelectMultiple(),  # shows a list of checkboxes
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'بودجه مورد نیاز' ,'id': 'price'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'توضیحات ماموریت'}),
            'goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'اهداف ماموریت'}),
        }
        labels = {
            'project': 'پروژه',
            'type': 'نوع ماموریت',
            'location': 'مکان',
            'persons': 'افراد مرتبط',
            'price': 'بودجه (ریال)',
            'description': 'توضیحات',
            'goals': 'اهداف ماموریت',
            'start_date': 'تاریخ شروع',
            'end_date': 'تاریخ پایان',
        }
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError("بودجه باید عددی مثبت باشد.")
        return price




class MissionCommentForm(forms.ModelForm):
    class Meta:
        model = MissionComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'نظر خود را وارد کنید...'})
        }