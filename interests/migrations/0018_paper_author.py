# Generated by Django 2.2.3 on 2020-06-21 05:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interests', '0017_auto_20200507_2128'),
    ]

    operations = [
        migrations.AddField(
            model_name='paper',
            name='author',
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
    ]
