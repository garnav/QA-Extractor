# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-31 13:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doccon2', '0012_auto_20160731_1900'),
    ]

    operations = [
        migrations.AlterField(
            model_name='toconvert',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Document Name'),
        ),
    ]