# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models

class Printable:
    def __repr__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4)

    def __str__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4)


class Companyaliases(models.Model, Printable):
    companyname = models.CharField(db_column='CompanyName', blank=True, null=False, max_length=70)  # Field name made lowercase.
    alias = models.CharField(db_column='Alias', primary_key=True, blank=True, null=False, max_length=70)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'CompanyAliases'

    def __str__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4)

        
class Jobpostings(models.Model, Printable):
    identifier = models.TextField(primary_key=True, db_column='Id', unique=True)  # Field name made lowercase.
    company = models.TextField(db_column='Company', blank=True, null=True, max_length=70)  # Field name made lowercase.
    title = models.TextField(db_column='Title')  # Field name made lowercase.
    locale = models.TextField(db_column='Locale', blank=True, null=True)  # Field name made lowercase.
    url = models.TextField(db_column='URL')  # Field name made lowercase.
    posteddate = models.DateField(db_column='postedDate', blank=True, null=True)  # Field name made lowercase.
    inserteddate = models.DateTimeField(db_column='insertedDate', blank=True, null=True)  # Field name made lowercase.
    city = models.TextField(db_column='City', blank=True, null=True)  # Field name made lowercase.
    province = models.TextField(db_column='Province', blank=True, null=True)  # Field name made lowercase.
    searchterms = models.TextField(db_column='SearchTerms', blank=True, null=True)  # Field name made lowercase.
    elementhtml = models.TextField(db_column='ElementHtml', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'JobPostings'

    def __str__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4)
    
    
class Recruitingcompanies(models.Model, Printable):
    name = models.TextField(db_column='Name', primary_key=True, blank=True, null=False, max_length=70)  # Field name made lowercase.
    datecontacted = models.DateTimeField(db_column='DateContacted', blank=True, null=True)  # Field name made lowercase.
    comment = models.TextField(db_column='Comment', blank=True, null=True)  # Field name made lowercase.
    resumesubmitted = models.NullBooleanField(db_column='ResumeSubmitted')  # Field name made lowercase.
    notinterested = models.NullBooleanField(db_column='NotInterested')  # Field name made lowercase.
    url = models.TextField(db_column='URL', blank=True, null=True)  # Field name made lowercase.
    cannotsubmitresume = models.NullBooleanField(db_column='CannotSubmitResume')  # Field name made lowercase.
    dateinserted = models.DateTimeField(db_column='DateInserted', blank=True, null=True)  # Field name made lowercase.
    telephone = models.TextField(db_column='Telephone', blank=True, null=True)  # Field name made lowercase.
    contactperson = models.TextField(db_column='ContactPerson', blank=True, null=True)  # Field name made lowercase.
    nearestoffice = models.TextField(db_column='NearestOffice', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'RecruitingCompanies'

    def __str__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4)

        
class AuthGroup(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    name = models.CharField(unique=True, max_length=80)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    username = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    action_time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'
