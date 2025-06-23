from django.db import models
from django import forms

# Transaction Model
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('payment', 'Payment'),
        ('deposit', 'Deposit'),
    ]
    type = models.CharField(max_length=50, blank=True, null=True)  # e.g., 'salary', 'purchase'
    date = models.DateField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    reference = models.CharField(max_length=100)
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    from_person = models.CharField(max_length=100, blank=True, null=True)
    to_person = models.CharField(max_length=100, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.transaction_type} - {self.amount}"

# BankStatement Model
class BankStatement(models.Model):
    file = models.FileField(upload_to='statements/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

# Payment Model
class Payment(models.Model):
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    to_person = models.CharField(max_length=100)
    reference = models.CharField(max_length=100, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return f"{self.date} - {self.to_person} - {self.amount}"

# Deposit Model
class Deposit(models.Model):
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    from_person = models.CharField(max_length=100)
    reference = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.date} - {self.from_person} - {self.amount}"

class BankStatementUploadForm(forms.Form):
    bank_statement_file = forms.FileField(
        label='Select a bank statement file',
        help_text='Upload your bank statement file here.'
    )
