# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-26 14:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assign4_stepanovicApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='auction',
            name='lockedbiddingby',
            field=models.TextField(default=''),
        ),
    ]
