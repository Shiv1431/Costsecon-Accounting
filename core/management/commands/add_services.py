from django.core.management.base import BaseCommand
from core.models import Service

class Command(BaseCommand):
    help = 'Adds default services to the database'

    def handle(self, *args, **options):
        services = [
            {
                'name': 'Personalized Tax Solutions',
                'description': 'Expert tax planning and preparation services tailored to your individual needs. We help you maximize deductions and ensure compliance with tax regulations.',
                'price': 2999.00,
                'duration': 60,
                'required_fields': ['tax_year', 'income_sources', 'previous_returns', 'deduction_documents']
            },
            {
                'name': 'Comprehensive Financial Preparation',
                'description': 'Complete financial statement preparation and analysis. We help you understand your financial position and make informed decisions.',
                'price': 3999.00,
                'duration': 90,
                'required_fields': ['financial_year', 'financial_statements', 'bank_statements', 'investment_details']
            },
            {
                'name': 'Strategic Corporate Tax Management',
                'description': 'Professional corporate tax planning and compliance services. We help businesses optimize their tax strategy and maintain regulatory compliance.',
                'price': 4999.00,
                'duration': 120,
                'required_fields': ['company_name', 'gst_number', 'pan_number', 'financial_statements']
            },
            {
                'name': 'Precise Bookkeeping Solutions',
                'description': 'Accurate and efficient bookkeeping services. We maintain your financial records and provide regular reports to help you track your business performance.',
                'price': 1999.00,
                'duration': 60,
                'required_fields': ['accounting_software', 'bank_statements', 'invoices', 'expense_receipts']
            },
            {
                'name': 'Efficient GST Return Services',
                'description': 'Timely and accurate GST return filing services. We ensure compliance with GST regulations and help you avoid penalties.',
                'price': 2499.00,
                'duration': 45,
                'required_fields': ['gst_number', 'financial_year', 'sales_invoices', 'purchase_invoices']
            },
            {
                'name': 'Strategic Business Consultation',
                'description': 'Expert business advisory services. We help you develop strategies for growth, improve operations, and achieve your business goals.',
                'price': 3499.00,
                'duration': 90,
                'required_fields': ['business_type', 'business_plan', 'financial_statements']
            },
            {
                'name': 'Effortless Payroll Management',
                'description': 'Comprehensive payroll processing and management services. We handle all aspects of payroll, from calculations to tax deductions.',
                'price': 1799.00,
                'duration': 45,
                'required_fields': ['number_of_employees', 'salary_structure', 'attendance_records', 'pf_esi_details']
            },
            {
                'name': 'Streamlined Online Filing',
                'description': 'Efficient online document filing and management services. We help you organize and maintain your digital records securely.',
                'price': 1499.00,
                'duration': 30,
                'required_fields': ['filing_type', 'financial_year', 'supporting_documents']
            },
            {
                'name': 'Personalized Consultation',
                'description': 'One-on-one consultation services tailored to your specific needs. Get expert advice on your financial and accounting concerns.',
                'price': 1999.00,
                'duration': 60,
                'required_fields': ['consultation_type', 'current_challenges', 'goals']
            }
        ]

        for service_data in services:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults={
                    'description': service_data['description'],
                    'price': service_data['price'],
                    'duration': service_data['duration']
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created service: {service.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Service already exists: {service.name}')
                ) 