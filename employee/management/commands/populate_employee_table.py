from django.core.management.base import BaseCommand
from employee.models import Employee
from faker import Faker





class Command(BaseCommand):
    help = 'Populate the Employee table with fake data'

    def handle(self, *args, **kwargs):
        fake = Faker()
        for _ in range(100):  # Adjust the range for the number of employees you want to create
            Employee.objects.create(
                first_name=fake.first_name()[:15],
                last_name=fake.last_name()[:15],
                email=fake.email()[:15],
                phone=fake.phone_number()[:15],
                country=fake.country()[:15],
                team=fake.random_element(elements=[
                    'dev team', 
                    'design team', 
                    'biz dev team', 
                    'test team', 
                    'mkt team', 
                    'tech team'
                ])[:15],
                role=fake.job()[:15],
                date_of_birth=fake.date_of_birth()
            )
        self.stdout.write(self.style.SUCCESS('Successfully populated the Employee table'))
        
        # To run this command, you need to use the Django management command system.
        # Open your terminal and navigate to the directory containing your Django project (where manage.py is located).
        # Then run the following command:

        # python manage.py populate_employee_table