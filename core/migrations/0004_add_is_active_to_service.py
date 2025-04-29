from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_document_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ] 