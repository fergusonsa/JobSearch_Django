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
    # ex: /jobsearch/recruiters/
    url(r'^recruiters/$', jobsearch.views.recruiters, name='recruiters'),
    # ex: /jobsearch/recruiter/<row_id>/
    url(r'^recruiter/(?P<row_id>[0-9]+)/$', jobsearch.views.recruiter, name='recruiter'),
    # ex: /jobsearch/gov_b_s/check
    url(r'^gov_b_s/check/$', jobsearch.views.check_government_buy_sell, name='check_government_buy_sell'),
    # ex: /jobsearch/gov_b_s/list
    url(r'^gov_b_s/list/$', jobsearch.views.list_government_buy_sell, name='list_government_buy_sell'),
    # ex: /jobsearch/5/
    url(r'^(?P<identifier>[a-zA-Z0-9._-]+)/$', jobsearch.views.detail, name='detail'),
    # ex: /jobsearch/5/int
    url(r'^(?P<identifier>[a-zA-Z0-9._-]+)/(?P<interest>[a-z]+)$', jobsearch.views.record_interest,
        name='record_interest'),
]
