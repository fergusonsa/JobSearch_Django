from django.conf.urls import url

import jobsearch.views

urlpatterns = [
    # ex: /jobsearch/
    url(r'^$', jobsearch.views.index, name='index'),
    # ex: /jobsearch/import
    url(r'^import/$', jobsearch.views.import_postings, name='import'),
    # ex: /jobsearch/get_postings
    url(r'^get_postings/$', jobsearch.views.postings_as_json, name='get_postings'),
    # ex: /jobsearch/listing
    #     url(r'^listing/$', jobsearch.views.listing, name='listing'),
    # ex: /jobsearch/special
    url(r'^special/$', jobsearch.views.special, name='special'),
    # ex: /jobsearch/5/
    url(r'^(?P<identifier>[a-zA-Z0-9._-]+)/$', jobsearch.views.detail, name='detail'),
    # ex: /jobsearch/recruiter/<company_name>/
    url(r'^recruiter/(?P<company_name>[a-zA-Z0-9._\- ]+)/$', jobsearch.views.recruiter, name='recruiter'),
    # ex: /jobsearch/gov_b_s/check
    url(r'^gov_b_s/check/$', jobsearch.views.recruiter, name='check_govenment_buy_sell'),
    # ex: /jobsearch/gov_b_s/list
    url(r'^gov_b_s/list/$', jobsearch.views.recruiter, name='check_govenment_buy_sell'),
]
