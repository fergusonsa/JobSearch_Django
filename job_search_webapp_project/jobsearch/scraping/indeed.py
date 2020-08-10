# coding: utf-8
import logging
import pathlib

import django
import indeed
from django.utils import timezone
import geopy.geocoders
import geopy.distance
import geopy.exc

import jobsearch
import jobsearch.scraping
import jobsearch.models as models
from python_miscelaneous import configuration

NUMBER_POSTINGS_PER_REQUEST = 25

MAX_POSTINGS_RETRIEVED = 1000

logger = logging.getLogger(__name__)


def scrape_new_job_postings(config=None, geo_locator=None, geo_locations=None, home_location=None):
    if not config:
        config = jobsearch.scraping.get_configuration()
    if not geo_locator:
        geo_locator = geopy.geocoders.Nominatim(user_agent="JobSearch")
    if not home_location:
        # Get coordinates for home
        home_location_str = config.get('home_location')
        home_location = jobsearch.scraping.get_geo_location(geo_locator, home_location_str)
    if not geo_locations:
        geo_locations = {}  # Cache of geo locations, so do not have to get the same location multiple times

    client = indeed.IndeedClient(config.get('indeed_publisher'))

    search_terms_list = ['java', 'devops', 'python', ]
    inserted_timestamp = django.utils.timezone.now()

    for search_term in search_terms_list:
        start_index = 0
        get_more_postings = True
        while get_more_postings:
            get_more_postings = False
            params = {
                'q': search_term,
                'jt': 'contract',
                'l': "ottawa,ontario,canada",
                'userip': "1.2.3.4",
                'useragent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2)",
                'start': start_index,
                'limit': NUMBER_POSTINGS_PER_REQUEST,
                'co': 'ca',
                'sort': 'date'
            }
            logger.debug("Getting postings for {} starting index {}".format(search_term, start_index))
            search_response = client.search(**params)
            logger.debug(search_response)
            results_postings = search_response.get('results')
            if results_postings:
                aliases = models.CompanyAliases.objects.all()

                for posting in results_postings:
                    if jobsearch.scraping.save_posting_to_db(posting, 'indeed', search_term, aliases,
                                                             geo_locator, home_location, geo_locations):
                        get_more_postings = True
                start_index += len(results_postings)
            if not results_postings:
                logger.debug('No postings returned from indeed api call, so not trying to get any more!')
                break
            if start_index > MAX_POSTINGS_RETRIEVED:
                logger.debug('Already retrieved max number, {}, of postings, so not trying to get any more!'.format(
                    MAX_POSTINGS_RETRIEVED))
                break

    num_new_postings = models.JobPostings.objects.filter(inserted_date__gte=inserted_timestamp).count()
    num_saved_aliases = models.CompanyAliases.objects.filter(inserted_date__gte=inserted_timestamp).count()
    num_saved_recruiters = models.RecruitingCompanies.objects.filter(date_inserted__gte=inserted_timestamp).count()
    logger.debug('# new postings from Indeed saved: {}  # aliases: {}  # recruiters: {} '.format(num_new_postings,
                                                                                                 num_saved_aliases,
                                                                                                 num_saved_recruiters))
    return num_new_postings
