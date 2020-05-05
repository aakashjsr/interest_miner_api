# Generated by Django 2.2.3 on 2020-04-28 20:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interests', '0012_auto_20200427_1109'),
    ]

    operations = [
        migrations.AddField(
            model_name='shortterminterest',
            name='model_month',
            field=models.IntegerField(default=4),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='shortterminterest',
            name='model_year',
            field=models.IntegerField(default=2020),
            preserve_default=False,
        ),
        migrations.RemoveField(model_name='longterminterest', name='paper',),
        migrations.AddField(
            model_name='longterminterest',
            name='paper',
            field=models.ManyToManyField(
                related_name='paper_long_term_models', to='interests.Paper'
            ),
        ),
        migrations.RemoveField(model_name='longterminterest', name='tweet',),
        migrations.AddField(
            model_name='longterminterest',
            name='tweet',
            field=models.ManyToManyField(
                related_name='tweet_long_term_models', to='interests.Tweet'
            ),
        ),
        migrations.RemoveField(model_name='shortterminterest', name='paper',),
        migrations.AddField(
            model_name='shortterminterest',
            name='paper',
            field=models.ManyToManyField(
                related_name='paper_short_term_models', to='interests.Paper'
            ),
        ),
        migrations.RemoveField(model_name='shortterminterest', name='tweet',),
        migrations.AddField(
            model_name='shortterminterest',
            name='tweet',
            field=models.ManyToManyField(
                related_name='tweet_short_term_models', to='interests.Tweet'
            ),
        ),
        migrations.DeleteModel(name='InterestTrend',),
    ]
