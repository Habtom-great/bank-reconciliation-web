import pandas as pd

data = {
    'Date': ['2025-05-20', '2025-05-21', '2025-05-22'],
    'Type': ['Debit', 'Credit', 'Debit'],
    'Amount': [120.50, 500.00, 45.00],
    'Description': ['Electricity Bill', 'Client Payment', 'Office Supplies'],
    'From': ['Utility', 'Client A', ''],
    'To': ['', '', 'Supplier'],
    'Reference': ['EB123', 'CP456', 'OS789']
}

df = pd.DataFrame(data)
df.to_excel('sample_bank_statement_clean.xlsx', index=False)
print("Excel file created: sample_bank_statement_clean.xlsx")
