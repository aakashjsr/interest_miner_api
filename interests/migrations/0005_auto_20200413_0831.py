# Generated by Django 2.2.3 on 2020-04-13 08:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interests', '0004_auto_20200412_0702'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paper',
            name='paper_id',
            field=models.CharField(blank=True, default='manual', max_length=255, null=True),
        ),
    ]
