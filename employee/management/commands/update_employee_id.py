import random
import string
from django.core.management.base import BaseCommand
from employee.models import Employee, generate_employee_id_with_prefix


class Command(BaseCommand):
    help = 'Update employee_id for all employees'

    def handle(self, *args, **kwargs):
        employees = Employee.objects.all()
        for employee in employees:
            new_employee_id = generate_employee_id_with_prefix(employee.team)
            employee.employee_id = new_employee_id
            employee.save()
            self.stdout.write(self.style.SUCCESS(f'Updated employee {employee.id} with new employee_id {new_employee_id}'))