# Generated by Django 5.2.3 on 2025-07-01 04:41

import django_ckeditor_5.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blog',
            name='blog_body',
            field=django_ckeditor_5.fields.CKEditor5Field(verbose_name='Content'),
        ),
        migrations.AlterField(
            model_name='blog',
            name='short_description',
            field=django_ckeditor_5.fields.CKEditor5Field(verbose_name='Description'),
        ),
    ]
