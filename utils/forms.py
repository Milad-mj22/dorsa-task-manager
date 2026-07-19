from django import forms

from utils.models import ProjectTicket, ProjectTicketMessage, TicketMessage,Ticket


class CSVUploadForm(forms.Form):
    file = forms.FileField(label='آپلود فایل CSV')



class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'message', 'category']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'title': 'عنوان',
            'message': 'پیام',
            'category': 'دسته‌بندی'
        }

class TicketMessageForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ['message', 'attachment']






class ProjectTicketForm(forms.ModelForm):
    class Meta:
        model = ProjectTicket
        fields = ['phone','title', 'message', 'category','image']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'phone': 'شماره تماس',
            'title': 'عنوان',
            'message': 'پیام',
            'category': 'دسته‌بندی',
            'image': 'تصویر'
        }

class ProjectTicketMessageForm(forms.ModelForm):
    class Meta:
        model = ProjectTicketMessage
        fields = ['message', 'attachment']

