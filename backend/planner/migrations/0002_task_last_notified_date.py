# Generated manually for weekly task notification tracking.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planner', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='last_notified_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
