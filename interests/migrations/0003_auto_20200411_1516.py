# Generated by Django 2.2.3 on 2020-04-11 15:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('interests', '0002_shortterminterest_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='longterminterest',
            name='user',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='long_term_interests', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='shortterminterest',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='short_term_interests', to=settings.AUTH_USER_MODEL),
        ),
    ]