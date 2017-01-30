from django.conf.urls import url

import jobsearch.views

urlpatterns = [
    # ex: /jobsearch/
    url(r'^$', jobsearch.views.index, name='index'),
    # ex: /jobsearch/listing
    url(r'^listing/$', jobsearch.views.listing, name='listing'),
    # ex: /jobsearch/5/
    url(r'^(?P<identifier>[a-zA-Z0-9._-]+)/$', jobsearch.views.detail, name='detail'),
    # ex: /jobsearch/recruiter/<company_name>/
    url(r'^recruiter/(?P<company_name>[a-zA-Z0-9._\- ]+)/$', jobsearch.views.recruiter, name='recruiter'),
]
