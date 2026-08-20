from django import forms

class EmailForm(forms.Form):
    fullName = forms.CharField(max_length=100)
    companyName = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(max_length=200)
    sms = forms.CharField(widget=forms.Textarea)
    attachments = forms.FileField(required=False)