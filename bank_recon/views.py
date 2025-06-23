from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.db.models import Sum
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.utils.dateparse import parse_date

from datetime import datetime
import pandas as pd
import fitz  # PyMuPDF
import os
import re

from .models import Transaction, Payment, Deposit, BankStatement
from .forms import BankStatementUploadForm


def dashboard_report(request):
    payments_summary = Payment.objects.values('to_person').annotate(total_amount=Sum('amount')).order_by('to_person')
    deposits_summary = Deposit.objects.values('from_person').annotate(total_amount=Sum('amount')).order_by('from_person')

    total_payments = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_deposits = Deposit.objects.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'payments_summary': payments_summary,
        'deposits_summary': deposits_summary,
        'total_payments': total_payments,
        'total_deposits': total_deposits,
    }
    return render(request, 'bank_recon/dashboard_report.html', context)

# === Upload Bank Statement (Excel) ===
def upload_bank_statement(request):
    if request.method == 'POST' and request.FILES.get('bank_statement_file'):
        file = request.FILES['bank_statement_file']
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ['.xls', '.xlsx']:
            messages.error(request, "Please upload a valid Excel file (.xls or .xlsx)")
            return redirect('dashboard')

        try:
            df = pd.read_excel(file)
            required_columns = {'Date', 'Type', 'Amount'}
            if not required_columns.issubset(df.columns):
                messages.error(request, "Excel file missing required columns: Date, Type, Amount")
                return redirect('dashboard')

            new_count = 0
            for _, row in df.iterrows():
                try:
                    date_obj = pd.to_datetime(row['Date']).date()
                    amount = float(row['Amount'])
                    trans_type = row['Type'].lower()
                    description = row.get('Description', '')
                except:
                    continue

                if not Transaction.objects.filter(date=date_obj, amount=amount, description=description).exists():
                    Transaction.objects.create(
                        date=date_obj,
                        transaction_type=trans_type,
                        amount=amount,
                        description=description,
                        from_person=row.get('From', ''),
                        to_person=row.get('To', ''),
                        reference=row.get('Reference', ''),
                    )
                    if trans_type == 'payment':
                        Payment.objects.create(date=date_obj, amount=amount, to_person=row.get('To', ''))
                    elif trans_type == 'deposit':
                        Deposit.objects.create(date=date_obj, amount=amount, from_person=row.get('From', ''))
                    new_count += 1

            messages.success(request, f"{new_count} transactions uploaded successfully.")
            return redirect('dashboard')

        except Exception as e:
            messages.error(request, f"Failed to process Excel file: {e}")
            return redirect('dashboard')

    return render(request, 'bank_recon/upload_bank_statement.html', {})

def all_transactions_report(request):
    queryset = Transaction.objects.all().order_by('-date')

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_payments = queryset.filter(transaction_type='payment').aggregate(Sum('amount'))['amount__sum'] or 0
    total_deposits = queryset.filter(transaction_type='deposit').aggregate(Sum('amount'))['amount__sum'] or 0

    page_payments_total = sum(t.amount for t in page_obj if t.transaction_type == 'payment')
    page_deposits_total = sum(t.amount for t in page_obj if t.transaction_type == 'deposit')

    return render(request, 'bank_recon/transactions.html', {
        'page_obj': page_obj,
        'total_payments': total_payments,
        'total_deposits': total_deposits,
        'page_payments_total': page_payments_total,
        'page_deposits_total': page_deposits_total,
        'title': 'All Transactions Report',
    })


# === Dashboard View with Filters ===
def dashboard(request):
    transactions = Transaction.objects.all().order_by('-date')

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    transaction_type = request.GET.get('transaction_type')

    if start_date_str:
        start_date = parse_date(start_date_str)
        transactions = transactions.filter(date__gte=start_date)

    if end_date_str:
        end_date = parse_date(end_date_str)
        transactions = transactions.filter(date__lte=end_date)

    if transaction_type and transaction_type != 'all':
        transactions = transactions.filter(transaction_type=transaction_type)

    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_deposit = transactions.filter(transaction_type='deposit').aggregate(Sum('amount'))['amount__sum'] or 0
    total_payment = transactions.filter(transaction_type='payment').aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'page_obj': page_obj,
        'total_deposit': total_deposit,
        'total_payment': total_payment,
    }
    return render(request, 'bank_recon/dashboard.html', context)

# === Export Excel ===
def export_excel(request):
    df = pd.DataFrame(Transaction.objects.all().values())
    df['date'] = pd.to_datetime(df['date']).dt.date
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="transactions.xlsx"'
    df.to_excel(response, index=False)
    return response

# === Export PDF ===
def export_pdf(request):
    from weasyprint import HTML
    html_string = render_to_string('bank_recon/transactions_pdf.html', {
        'transactions': Transaction.objects.all()
    })
    html = HTML(string=html_string)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="transactions.pdf"'
    html.write_pdf(response)
    return response

# === Delete Transaction ===
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    transaction.delete()
    return redirect('dashboard')

# === Report Views ===
def payment_report(request):
    payments = Transaction.objects.filter(transaction_type='payment').order_by('-date')
    return render_transaction_report(request, payments, title="Payment Report")

def deposit_report(request):
    deposits = Transaction.objects.filter(transaction_type='deposit').order_by('-date')
    return render_transaction_report(request, deposits, title="Deposit Report")

def render_transaction_report(request, queryset, title):
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    total = queryset.aggregate(Sum('amount'))['amount__sum'] or 0
    page_total = sum(t.amount for t in page_obj)

    context = {
        'page_obj': page_obj,
        'total_payments': total if title.startswith("Payment") else 0,
        'total_deposits': total if title.startswith("Deposit") else 0,
        'page_payments_total': page_total if title.startswith("Payment") else 0,
        'page_deposits_total': page_total if title.startswith("Deposit") else 0,
        'title': title,
    }
    return render(request, 'bank_recon/transactions.html', context)

# === Statement List ===
def statement_list(request):
    statements = BankStatement.objects.all().order_by('-uploaded_at')
    
    return render(request, 'statement_list.html', {'statements': statements})

def process_excel(file, form, request):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip().str.title()  # normalize column names

    required_columns = {'Date', 'Type', 'Amount'}
    if not required_columns.issubset(df.columns):
        form.add_error('bank_statement_file', 'Excel file missing required columns: Date, Type, Amount')
        return render(request, 'bank_recon/upload_bank_statement.html', {'form': form})

    for _, row in df.iterrows():
        try:
            date_obj = pd.to_datetime(row['Date']).date()
            amount = float(row['Amount'])
            trans_type = row['Type'].lower()
        except:
            continue

        if not Transaction.objects.filter(date=date_obj, amount=amount, description=row.get('Description', '')).exists():
            Transaction.objects.create(
                date=date_obj,
                transaction_type=trans_type,
                amount=amount,
                description=row.get('Description', ''),
                from_person=row.get('From', ''),
                to_person=row.get('To', ''),
                reference=row.get('Reference', ''),
            )
            if trans_type == 'payment':
                Payment.objects.create(date=date_obj, amount=amount, to_person=row.get('To', ''))
            elif trans_type == 'deposit':
                Deposit.objects.create(date=date_obj, amount=amount, from_person=row.get('From', ''))


# === Process PDF ===
def process_pdf(file):
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        text = ''.join(page.get_text() for page in doc)

    pattern = re.compile(r'(\d{4}-\d{2}-\d{2})\s+(Debit|Credit)\s+([\d,\.]+)\s+(.*)')
    for line in text.split('\n'):
        match = pattern.match(line)
        if match:
            date_str, trans_type, amount_str, description = match.groups()
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                amount = float(amount_str.replace(',', ''))
            except:
                continue

            if not Transaction.objects.filter(date=date_obj, amount=amount, description=description).exists():
                if trans_type == 'Debit':
                    Payment.objects.create(date=date_obj, amount=amount, to_person=description)
                    Transaction.objects.create(date=date_obj, amount=amount, description=description, transaction_type='payment')
                elif trans_type == 'Credit':
                    Deposit.objects.create(date=date_obj, amount=amount, from_person=description)
                    Transaction.objects.create(date=date_obj, amount=amount, description=description, transaction_type='deposit')


import pdfplumber
import pandas as pd
from django.http import HttpResponse

def convert_pdf_to_excel(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        uploaded_file = request.FILES['pdf_file']

        if not uploaded_file.name.endswith('.pdf'):
            return HttpResponse("Please upload a valid .pdf file.")

        try:
            with pdfplumber.open(uploaded_file.file) as pdf:
                all_data = []
                for page in pdf.pages:
                    table = page.extract_table()
                    if table:
                        all_data.extend(table)

            if not all_data:
                return HttpResponse("No table data found in PDF.")

            df = pd.DataFrame(all_data[1:], columns=all_data[0])
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="converted.xlsx"'
            df.to_excel(response, index=False)
            return response

        except Exception as e:
            return HttpResponse(f"Failed to convert PDF: {e}")

    return render(request, 'bank_recon/convert_pdf_to_excel.html')
