from django.db.models import Q
from django.shortcuts import render, get_object_or_404
import jobsearch.models as models
import jobsearch.forms as forms
from django.template import loader
from django.http import HttpResponse
import jobsearch.scrapeJobPostings

def index(request):
    print('Into index()')
        # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = forms.JobSearchForm(request.POST)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = forms.JobSearchForm()

    latest_jobposted_list = models.Jobpostings.objects.order_by('-posteddate')[:5]

    for posting in latest_jobposted_list:
        print(posting)

    template = loader.get_template('jobsearch/index.html')
    context = {
        'search_form': form,
        'latest_jobposted_list': latest_jobposted_list,
    }
    return HttpResponse(template.render(context, request))

    
def listing(request):
    print('Into listing()')
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = forms.JobSearchForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            
            company = form.cleaned_data['company']
            start_date = form.cleaned_data['postedDateStart']
            end_date = form.cleaned_data['postedDateEnd']
            location = form.cleaned_data['location']

            queries = []
            if company:
                queries.append(Q(company__contains=company))
            if start_date:
                queries.append(Q(posteddate__gte=start_date))
            if end_date:
                queries.append(Q(posteddate__lte=end_date))
            if location:
                queries.append(Q(location__contains=location))
            if len(queries) > 0:
                latest_jobposted_list = models.Jobpostings.objects.filter(queries)
            else: 
                latest_jobposted_list = models.Jobpostings.objects.order_by('-posteddate')[:5]

    # if a GET (or any other method) we'll create a blank form
    else:
        form = forms.JobSearchForm()
        latest_jobposted_list = models.Jobpostings.objects.order_by('-posteddate')[:5]

    for posting in latest_jobposted_list:
        print(posting)
        
    template = loader.get_template('jobsearch/index.html')
    context = {
        'search_form': form,
        'latest_jobposted_list': latest_jobposted_list,
    }
    return HttpResponse(template.render(context, request))


def import_postings(request):
    print('Into listing()')
    jobsearch.scrapeJobPostings.scrape_new_job_postings()
    
def detail(request, identifier):
    print('Into detail("%s")' % identifier)
    
    job_posting = get_object_or_404(models.Jobpostings, pk=identifier)
    print('job_posting.elementhtml: \n%s\n%r' % (job_posting.elementhtml, job_posting.elementhtml))
    return render(request, 'jobsearch/detail.html', {'jobposting': job_posting})

    
def recruiter(request, company_name):
    print('Into recruiter("%s")' % company_name)
    
    alias = models.Companyaliases.objects.get(alias=company_name)
    recruiter_company = get_object_or_404(models.Recruitingcompanies, pk=alias.companyname)
    aliases = models.Companyaliases.objects.filter(companyname=recruiter_company.name)
    return render(request, 'jobsearch/recruiter.html', {'recruiter_company': recruiter_company, 'aliases': aliases})


    
