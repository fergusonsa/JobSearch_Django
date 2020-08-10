# Generated by Django 3.0.7 on 2020-06-23 18:23

from django.db import migrations, models
import django.utils.timezone
import jobsearch.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AuthGroup',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=80, unique=True)),
            ],
            options={
                'db_table': 'auth_group',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthGroupPermissions',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'auth_group_permissions',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthPermission',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('codename', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'auth_permission',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthUser',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('password', models.CharField(max_length=128)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('is_superuser', models.BooleanField()),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=30)),
                ('email', models.CharField(max_length=254)),
                ('is_staff', models.BooleanField()),
                ('is_active', models.BooleanField()),
                ('date_joined', models.DateTimeField()),
                ('username', models.CharField(max_length=150, unique=True)),
            ],
            options={
                'db_table': 'auth_user',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthUserGroups',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'auth_user_groups',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthUserUserPermissions',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'auth_user_user_permissions',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='CompanyAliases',
            fields=[
                ('company_name', models.CharField(blank=True, db_column='CompanyName', max_length=70)),
                ('alias', models.CharField(blank=True, db_column='Alias', max_length=70, primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'CompanyAliases',
                'managed': False,
            },
            bases=(models.Model, jobsearch.models.Printable),
        ),
        migrations.CreateModel(
            name='DjangoAdminLog',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('object_id', models.TextField(blank=True, null=True)),
                ('object_repr', models.CharField(max_length=200)),
                ('action_flag', models.PositiveSmallIntegerField()),
                ('change_message', models.TextField()),
                ('action_time', models.DateTimeField()),
            ],
            options={
                'db_table': 'django_admin_log',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoContentType',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('app_label', models.CharField(max_length=100)),
                ('model', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'django_content_type',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoMigrations',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('app', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('applied', models.DateTimeField()),
            ],
            options={
                'db_table': 'django_migrations',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoSession',
            fields=[
                ('session_key', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('session_data', models.TextField()),
                ('expire_date', models.DateTimeField()),
            ],
            options={
                'db_table': 'django_session',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='JobPostings',
            fields=[
                ('identifier', models.TextField(db_column='Id', primary_key=True, serialize=False, unique=True)),
                ('company', models.TextField(blank=True, db_column='Company', max_length=70, null=True)),
                ('title', models.TextField(db_column='Title')),
                ('locale', models.TextField(blank=True, db_column='Locale', null=True)),
                ('url', models.TextField(db_column='URL')),
                ('posted_date', models.DateTimeField(blank=True, db_column='postedDate', null=True)),
                ('inserted_date', models.DateTimeField(blank=True, db_column='insertedDate', default=django.utils.timezone.now)),
                ('city', models.TextField(blank=True, db_column='City', null=True)),
                ('province', models.TextField(blank=True, db_column='Province', null=True)),
                ('search_terms', models.TextField(blank=True, db_column='SearchTerms', null=True)),
                ('element_html', models.TextField(blank=True, db_column='ElementHtml', null=True)),
                ('distance_from_home', models.FloatField(db_column='DistanceFromHome')),
            ],
            options={
                'db_table': 'JobPostings',
                'managed': False,
            },
            bases=(models.Model, jobsearch.models.Printable),
        ),
        migrations.CreateModel(
            name='RecruitingCompanies',
            fields=[
                ('name', models.TextField(blank=True, db_column='Name', max_length=70, primary_key=True, serialize=False)),
                ('date_contacted', models.DateTimeField(blank=True, db_column='DateContacted', null=True)),
                ('comment', models.TextField(blank=True, db_column='Comment', null=True)),
                ('resume_submitted', models.NullBooleanField(db_column='ResumeSubmitted')),
                ('not_interested', models.NullBooleanField(db_column='NotInterested')),
                ('url', models.TextField(blank=True, db_column='URL', null=True)),
                ('cannot_submit_resume', models.NullBooleanField(db_column='CannotSubmitResume')),
                ('date_inserted', models.DateTimeField(blank=True, db_column='DateInserted', null=True)),
                ('telephone', models.TextField(blank=True, db_column='Telephone', null=True)),
                ('contact_person', models.TextField(blank=True, db_column='ContactPerson', null=True)),
                ('nearest_office', models.TextField(blank=True, db_column='NearestOffice', null=True)),
            ],
            options={
                'db_table': 'RecruitingCompanies',
                'managed': False,
            },
            bases=(models.Model, jobsearch.models.Printable),
        ),
    ]