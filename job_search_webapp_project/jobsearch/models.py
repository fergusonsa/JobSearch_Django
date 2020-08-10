from __future__ import unicode_literals

from django.db import models
import django.utils.timezone
from django.utils.translation import gettext_lazy as _


class InterestedChoices(models.TextChoices):
    NOT_REVIEWED = '', _('Not reviewed')
    REVIEWED = 'rev', _('Reviewed')
    SUBMITTED = 'sub', _('Submitted')
    CONTACTED = 'con', _('Contacted')
    NOT_INTERESTED = 'not', _('Not Interested')
    INTERESTED = 'int', _('Interested')


class Printable:
    def __repr__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4)

    def __str__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4)


class CompanyAliases(models.Model, Printable):
    company_name = models.CharField(db_column='CompanyName', blank=True, null=False, max_length=70)
    alias = models.CharField(db_column='Alias', primary_key=True, blank=True, null=False, max_length=70)
    inserted_date = models.DateTimeField(db_column='inserted_date', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'CompanyAliases'

    def __str__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4)

        
class JobPostings(models.Model, Printable):
    identifier = models.TextField(primary_key=True, db_column='Id', unique=True)
    company = models.TextField(db_column='Company', blank=True, null=True, max_length=70)  
    title = models.TextField(db_column='Title')  
    locale = models.TextField(db_column='Locale', blank=True, null=True)  
    url = models.TextField(db_column='URL')  
    source = models.TextField(db_column='source', blank=True, null=True)
    posted_date = models.DateTimeField(db_column='postedDate', blank=True, null=True)
    inserted_date = models.DateTimeField(db_column='insertedDate', blank=True, default=django.utils.timezone.now)
    city = models.TextField(db_column='City', blank=True, null=True)
    province = models.TextField(db_column='Province', blank=True, null=True)
    search_terms = models.TextField(db_column='SearchTerms', blank=True, null=True)
    element_html = models.TextField(db_column='ElementHtml', blank=True, null=True)
    distance_from_home = models.FloatField(db_column='DistanceFromHome')
    reviewed_date = models.DateTimeField(db_column='reviewed_date', blank=True, null=True)
    interested = models.CharField(db_column='interested', max_length=15,
                                  choices=InterestedChoices.choices, default=InterestedChoices.NOT_REVIEWED)

    class Meta:
        managed = False
        db_table = 'JobPostings'

    def __str__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4)
    
    
class RecruitingCompanies(models.Model, Printable):
    row_id = models.IntegerField(db_column='rowid')
    name = models.TextField(db_column='Name', primary_key=True, blank=True, null=False, max_length=70)  
    date_contacted = models.DateTimeField(db_column='DateContacted', blank=True, null=True)  
    comment = models.TextField(db_column='Comment', blank=True, null=True)  
    resume_submitted = models.BooleanField(db_column='ResumeSubmitted', null=True)
    not_interested = models.BooleanField(db_column='NotInterested', null=True)
    url = models.TextField(db_column='URL', blank=True, null=True)  
    cannot_submit_resume = models.BooleanField(db_column='CannotSubmitResume', null=True)
    date_inserted = models.DateTimeField(db_column='DateInserted', blank=True, null=True)  
    telephone = models.TextField(db_column='Telephone', blank=True, null=True)  
    contact_person = models.TextField(db_column='ContactPerson', blank=True, null=True)  
    nearest_office = models.TextField(db_column='NearestOffice', blank=True, null=True)  

    class Meta:
        managed = False
        db_table = 'RecruitingCompanies'

    def __str__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4)


class TemporaryId(models.Model):
    id = models.TextField(db_column='ID', primary_key=True)


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


class ContactData(models.Model, Printable):
    identifier = models.TextField(primary_key=True, db_column='Id', unique=True)
    company_name = models.TextField(db_column='company_name', blank=True, null=True, max_length=70)
    contact_name = models.TextField(db_column='contact_name', blank=True, null=True, max_length=70)
    contact_type = models.TextField(db_column='contact_type')
    date = models.DateTimeField(db_column='contact_date', blank=True, null=True)
    comments = models.TextField(db_column='comments', blank=True, null=True)
    inserted_date = models.DateTimeField(db_column='inserted_date', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'contacts'

    def __str__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4)
