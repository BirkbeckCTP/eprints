# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-07-12 12:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Import',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField()),
                ('completed', models.BooleanField(default=False)),
                ('number_of_imports', models.PositiveIntegerField(default=0)),
            ],
        ),
    ]