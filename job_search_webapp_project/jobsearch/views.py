import logging
import datetime

import django
import geopy
from django.core import serializers
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.template import loader
from django.http import HttpResponse

import jobsearch.models as models
import jobsearch.forms as forms
import jobsearch.scrapeJobPostings
import jobsearch.scraping.excelitr
import jobsearch.scraping.indeed
import jobsearch.scraping.linkedin
import jobsearch.scraping.myticas
import jobsearch.scraping.sisystems

MAX_POSTINGS_TO_RETURN = 25

logger = logging.getLogger(__name__)


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
        if job_search_form or form.is_valid():
            # process the data in form.cleaned_data as required
            if job_search_form:
                company = job_search_form.company
                after_inserted_date = job_search_form.insertedDateStart
                start_date = job_search_form.postedDateStart
                end_date = job_search_form.postedDateEnd
                location = job_search_form.location
                sort_by_choice = job_search_form.sort_by
                interest = job_search_form.interest
            else:
                company = form.cleaned_data['company']
                after_inserted_date = form.cleaned_data['insertedDateStart']
                start_date = form.cleaned_data['postedDateStart']
                end_date = form.cleaned_data['postedDateEnd']

                location = form.cleaned_data['location']
                sort_by_choice = form.cleaned_data.get('sort_by')
                interest = form.cleaned_data.get('interest')

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
            if interest != 'ALL':
                queries = queries & Q(interested=interest)
            if sort_by_choice:
                latest_jobs_posted_list = models.JobPostings.objects.order_by(sort_by_choice)
            else:
                latest_jobs_posted_list = models.JobPostings.objects.all()

            if queries:
                logger.debug('Postings filters: {}'.format(queries))
                latest_jobs_posted_list = latest_jobs_posted_list.filter(queries)
            else:
                latest_jobs_posted_list = latest_jobs_posted_list[:MAX_POSTINGS_TO_RETURN]
        else:
            logger.debug('Looks like the form is invalid?!')
            logger.debug(form)
            latest_jobs_posted_list = models.JobPostings.objects.order_by('-posted_date')[:MAX_POSTINGS_TO_RETURN]
    
    # if a GET (or any other method) we'll create a blank form
    else:
        form = forms.JobSearchForm()
        latest_jobs_posted_list = models.JobPostings.objects.order_by('-posted_date')[:MAX_POSTINGS_TO_RETURN]

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
    jobsearch.scraping.get_all_new_postings()
    return index(request, form)
    # return django.shortcuts.redirect('index')


def detail(request, identifier):
    logger.debug('Into detail("%s")' % identifier)

    job_posting = get_object_or_404(models.JobPostings, pk=identifier)
    if job_posting and not job_posting.interested:
        job_posting.interested = jobsearch.models.InterestedChoices.REVIEWED
        job_posting.reviewed_date = datetime.datetime.now()
        with transaction.atomic():
            job_posting.save()
    else:
        logger.warning('Could not find posting with key: {}'.format(identifier))

    return render(request, 'jobsearch/detail.html', {'job_posting': job_posting})


def record_interest(request, identifier, interest):
    logger.debug('Into record_interest("{}", "{}")'.format(identifier, interest))

    job_posting = get_object_or_404(models.JobPostings, pk=identifier)
    if job_posting and interest:
        if interest in jobsearch.models.InterestedChoices.values:
            job_posting.interested = interest
            job_posting.reviewed_date = datetime.datetime.now()
            with transaction.atomic():
                job_posting.save()
        else:
            logger.warning('Could not find posting with key: {} or no interest was provided: {}'.format(identifier,
                                                                                                        interest))
    else:
        logger.warning('Not a valid interest: {} for the identifier {}'.format(interest, identifier))
    return render(request, 'jobsearch/detail.html', {'job_posting': job_posting})


def recruiter(request, row_id):
    logger.debug('Into recruiter({})'.format(row_id))

    recruiter_company = get_object_or_404(models.RecruitingCompanies, row_id=row_id)
    aliases = models.CompanyAliases.objects.filter(company_name=recruiter_company.name)
    return render(request, 'jobsearch/recruiter.html', {'recruiter_company': recruiter_company, 'aliases': aliases})


# def recruiter_by_name(request, company_name):
#     logger.debug('Into recruiter_by_name({})'.format(company_name))
#
#     recruiter_company = get_object_or_404(models.RecruitingCompanies, row_id=row_id)
#     aliases = models.CompanyAliases.objects.filter(company_name=recruiter_company.name)
#     return render(request, 'jobsearch/recruiter.html', {'recruiter_company': recruiter_company, 'aliases': aliases})


def recruiters(request):
    logger.debug('Into recruiters')

    if request.method == 'POST':
        search_form = forms.CompanySearchForm(request.POST)
        recruiters = get_list_or_404(models.RecruitingCompanies)
    else:
        search_form = forms.CompanySearchForm()
        recruiters = get_list_or_404(models.RecruitingCompanies)
    context = {
        'search_form': search_form,
        'companies': recruiters
    }
    return render(request, 'jobsearch/recruiters.html', context)


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


def special_2(request):
    logger.debug('Into special()')
    import apscheduler.schedulers.background
    scheduler = apscheduler.schedulers.background.BackgroundScheduler()
    jobs = scheduler.get_jobs()


def special(request):
    logger.debug('Into special()')

    # ExcelITR testing
    # jobs_posted_list = models.JobPostings.objects.all()
    # for posting in jobs_posted_list:
    #     json_str = posting.element_html
    #     json_str = json_str.replace("\\\\", "")
    #     posting.element_html = json.dumps(json_str[1:-1], indent=2)
    #     logger.debug(posting.element_html)
    #     with transaction.atomic():
    #         posting.save()
    # num_postings = jobsearch.scraping.excelitr.scrape_new_job_postings()
    # logger.debug('{} postings saved from jobsearch.scraping.excelitr.scrape_new_job_postings()'.format(num_postings))

    # Linkedin testing
    # num_postings = jobsearch.scraping.linkedin.scrape_new_job_postings()
    # logger.debug('{} postings saved from jobsearch.scraping.linkedin.scrape_new_job_postings()'.format(num_postings))

    # Myticas testing
    num_postings = jobsearch.scraping.myticas.scrape_new_job_postings()
    logger.debug('{} postings saved from jobsearch.scraping.myticas.scrape_new_job_postings()'.format(num_postings))
    return django.shortcuts.redirect('index')


def show_contacts_with_recruiters(request):
    logger.debug('Into show_contacts_with_recruiters()')

    return render(request, 'jobsearch/contacts.html')


def linkedin_login():
    return None