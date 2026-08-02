from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("auth_app", "0002_alter_user_odoo_id")]

    operations = [
        migrations.AlterField(
            model_name="visitor",
            name="page",
            field=models.URLField(default="https://codestra.co"),
        ),
    ]
