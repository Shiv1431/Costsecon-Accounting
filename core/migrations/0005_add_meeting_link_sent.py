from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_add_is_active_to_service'),
    ]

    operations = [
        migrations.AddField(
            model_name='consultation',
            name='meeting_link_sent',
            field=models.BooleanField(default=False),
        ),
    ] 