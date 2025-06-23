from django.urls import path
from bank_recon import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Dashboard report (only include this if the view exists)
    # path('dashboard/report/', views.dashboard_report, name='dashboard_report'),

    # Reports
    path('payments/', views.payment_report, name='payment_report'),
    path('deposits/', views.deposit_report, name='deposit_report'),

    # File Upload
    path('upload/', views.upload_bank_statement, name='upload_statement'),

    # Transactions
    path('transactions/', views.dashboard, name='all_transactions'),  # using dashboard for all transactions view
    # path('transactions/report/', views.all_transactions_report, name='all_transactions_report'),  # remove if not defined
    path('transactions/report/', views.all_transactions_report, name='all_transactions_report'),
    # convert pdf to excel
    path('convert/pdf-to-excel/', views.convert_pdf_to_excel, name='convert_pdf_to_excel'),

    # Export
    path('export/excel/', views.export_excel, name='export_excel'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),

    # Delete
    path('delete/<int:pk>/', views.delete_transaction, name='delete_transaction'),
]

# Media files (if you're serving uploaded files in development)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
