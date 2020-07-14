import json
import logging
import datetime

import django
from django.core import serializers
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.http import HttpResponse

import jobsearch.models as models
import jobsearch.forms as forms
import jobsearch.scrapeJobPostings

logger = logging.getLogger(__name__)


# def index(request):
#     logger.debug('Into index()')
#         # if this is a POST request we need to process the form data
#     if request.method == 'POST':
#         # create a form instance and populate it with data from the request:
#         form = forms.JobSearchForm(None, request.POST)
# 
#     # if a GET (or any other method) we'll create a blank form
#     else:
#         form = forms.JobSearchForm()
#         
#     latest_jobs_posted_list = models.Jobpostings.objects.order_by('-posteddate')[:5]
#     template = loader.get_template('jobsearch/index.html')
#     context = {
#         'search_form': form,
#         'latest_jobs_posted_list': latest_jobs_posted_list,
#     }
#     return HttpResponse(template.render(context, request))

    
def index(request, job_search_form=None, after_inserted_date=None):
    logger.debug('Into listing()')
    # if this is a POST request we need to process the form data
    if after_inserted_date:
        form = forms.JobSearchForm()
        queries = Q(inserted_date__gte=after_inserted_date)

        latest_jobs_posted_list = models.JobPostings.objects.order_by('-posted_date')
        latest_jobs_posted_list = latest_jobs_posted_list.filter(queries)

    elif job_search_form or request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = forms.JobSearchForm(request.POST)
        
        # check whether it's valid:
        if form.is_valid() or job_search_form:
            # process the data in form.cleaned_data as required
            if job_search_form:
                company = job_search_form.company
                after_inserted_date = job_search_form.insertedDateStart
                start_date = job_search_form.postedDateStart
                end_date = job_search_form.postedDateEnd
                location = job_search_form.location
                sort_by_choice = job_search_form.sort_by
            else:
                company = form.cleaned_data['company']
                after_inserted_date = form.cleaned_data['insertedDateStart']
                start_date = form.cleaned_data['postedDateStart']
                end_date = form.cleaned_data['postedDateEnd']

                location = form.cleaned_data['location']
                sort_by_choice = form.cleaned_data.get('sort_by')

            queries = Q()
            if company:
                queries = queries & Q(company__icontains=company) 
            if start_date:
                queries = queries & Q(posted_date__gte=start_date)
            if end_date:
                queries = queries & Q(posted_date__lte=end_date)
            if location:
                queries = queries & Q(location__icontains=location)
            if after_inserted_date:
                queries = queries & Q(inserted_date__gte=after_inserted_date)
            if sort_by_choice:
                latest_jobs_posted_list = models.JobPostings.objects.order_by(sort_by_choice)
            else:
                latest_jobs_posted_list = models.JobPostings.objects.all()

            if queries:
                logger.debug('Postings filters: {}'.format(queries))
                latest_jobs_posted_list = latest_jobs_posted_list.filter(queries)
            else: 
                latest_jobs_posted_list = latest_jobs_posted_list[:5]
        else:
            logger.debug('Looks like the form is invalid?!')
            logger.debug(form)
            latest_jobs_posted_list = models.JobPostings.objects.order_by('-posted_date')[:5]
    
    # if a GET (or any other method) we'll create a blank form
    else:
        form = forms.JobSearchForm()
        latest_jobs_posted_list = models.JobPostings.objects.order_by('-posted_date')[:5]

    logger.debug('number of postings being returned: {}'.format(len(latest_jobs_posted_list)))
        
    template = loader.get_template('jobsearch/index.html')
    context = {
        'search_form': form,
        'latest_jobs_posted_list': latest_jobs_posted_list,
    }
    return HttpResponse(template.render(context, request))


def import_postings(request):
    logger.debug('Into import_postings()')
    form = forms.JobSearchForm()
    form.insertedDateStart = django.utils.timezone.now()
    form.postedDateEnd = None
    form.postedDateStart = None
    form.company = None
    form.location = None
    form.sort_by = 'distance_from_home' 
    jobsearch.scrapeJobPostings.get_indeed_postings()

    return index(request, form)
    # return django.shortcuts.redirect('index')


def detail(request, identifier):
    logger.debug('Into detail("%s")' % identifier)

    job_posting = get_object_or_404(models.JobPostings, pk=identifier)
    logger.debug('job_posting.element_html: \n%s\n%r' % (job_posting.element_html, job_posting.element_html))
    return render(request, 'jobsearch/detail.html', {'job_posting': job_posting})


def recruiter(request, company_name):
    logger.debug('Into recruiter("%s")' % company_name)
    
    alias = models.CompanyAliases.objects.get(alias=company_name)
    recruiter_company = get_object_or_404(models.RecruitingCompanies, pk=alias.companyname)
    aliases = models.CompanyAliases.objects.filter(companyname=recruiter_company.name)
    return render(request, 'jobsearch/recruiter.html', {'recruiter_company': recruiter_company, 'aliases': aliases})

   
def check_government_buy_sell(request):
    pass


def list_government_buy_sell(request):
    
    template = loader.get_template('jobsearch/gov_buy_sell_listing.html')
    context = {
        'list': [],
    }
    return HttpResponse(template.render(context, request))


def postings_as_json(request):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = forms.JobSearchForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            company = form.cleaned_data['company']
            after_inserted_date = form.cleaned_data['insertedDateStart']
            start_date = form.cleaned_data['postedDateStart']
            end_date = form.cleaned_data['postedDateEnd']
            location = form.cleaned_data['location']
            sort_by_choice = form.cleaned_data.get('sort_by')

            queries = Q()
            if company:
                queries = queries & Q(company__icontains=company)
            if start_date:
                queries = queries & Q(posted_date__gte=start_date)
            if end_date:
                queries = queries & Q(posted_date__lte=end_date)
            if location:
                queries = queries & Q(location__icontains=location)
            if after_inserted_date:
                queries = queries & Q(inserted_date__gte=after_inserted_date)
            if sort_by_choice:
                latest_jobs_posted_list = models.JobPostings.objects.order_by(sort_by_choice)
            else:
                latest_jobs_posted_list = models.JobPostings.objects.all()

            if queries:
                logger.debug(queries)
                latest_jobs_posted_list = latest_jobs_posted_list.filter(queries)
            else:
                latest_jobs_posted_list = latest_jobs_posted_list[:5]
        else:
            logger.debug('Looks like the form is invalid?!')
            logger.debug(form)
            latest_jobs_posted_list = models.JobPostings.objects.order_by('-posted_date')[:5]

    # if a GET (or any other method) we'll create a blank form
    else:
        form = forms.JobSearchForm()
        latest_jobs_posted_list = models.JobPostings.objects.order_by('-posted_date')[:5]
    json = serializers.serialize('json', latest_jobs_posted_list)
    return HttpResponse(json, content_type='application/json')


def special(request):
    logger.debug('Into special()')

    jobs_posted_list = models.JobPostings.objects.all()
    for posting in jobs_posted_list:
        json_str = posting.element_html
        json_str = json_str.replace("\\\\", "")
        posting.element_html = json.dumps(json_str[1:-1], indent=2)
        logger.debug(posting.element_html)
        with transaction.atomic():
            posting.save()
    return django.shortcuts.redirect('index')
