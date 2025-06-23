from django import forms
from .models import BankStatement
class BankStatementUploadForm(forms.Form):
    file = forms.FileField(label="Upload Excel Statement")

# bank_recon/forms.py

class BankStatementForm(forms.ModelForm):
    class Meta:
        model = BankStatement
        fields = ['file']

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Validate file type
            valid_mime_types = [
                'application/pdf',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ]
            if file.content_type not in valid_mime_types:
                raise forms.ValidationError('Unsupported file type. Upload Excel or PDF files only.')
            # You can also validate file size here if you want
        return file
