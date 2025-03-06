import random
from django.core.management.base import BaseCommand
from employee.models import Employee, SocialMedia


class Command(BaseCommand):
    help = 'Populate SocialMedia instances for each Employee'

    def handle(self, *args, **kwargs):
        social_media_names = ['Instagram', 'Twitter', 'LinkedIn', 'Facebook']
        employees = Employee.objects.all()

        for employee in employees:
            num_profiles = random.randint(3, 4)
            for _ in range(num_profiles):
                name = random.choice(social_media_names)
                link = f"https://{name.lower()}.com/{employee.first_name.lower()}{employee.last_name.lower()}"
                SocialMedia.objects.create(employee=employee, name=name, link=link)
                self.stdout.write(self.style.SUCCESS(f'Successfully created {name} profile for {employee.first_name} {employee.last_name}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully populated social media profiles for all employees'))