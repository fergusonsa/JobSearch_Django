import logging

import django
import geopy
from django.db import transaction
from linkedin import linkedin

import jobsearch.scraping
from jobsearch import scrapeJobPostings, models

logger = logging.getLogger(__name__)


def scrape_new_job_postings(config=None, geo_locator=None, geo_locations=None, home_location=None):
    if not config:
        config = jobsearch.scraping.get_configuration()
    linkedin_config = config.get("linkedin")

    if not geo_locator:
        geo_locator = geopy.geocoders.Nominatim(user_agent="JobSearch")
    if not geo_locations:
        geo_locations = {}

    if not home_location:
        # Get coordinates for home
        home_location_str = config.get('home_location')
        home_location = jobsearch.scraping.get_geo_location(geo_locator, home_location_str)

    search_terms_list = ['java', 'devops', 'python', ]
    aliases = models.CompanyAliases.objects.all()

    authentication = linkedin.LinkedInAuthentication(
        linkedin_config.get('APPLICATION_KEY'),
        linkedin_config.get('APPLICATION_SECRET'),
        linkedin_config.get('RETURN_URL'),
        linkedin.PERMISSIONS.enums.values()
    )
    application = linkedin.LinkedInApplication(authentication)
    num_saved = 0
    inserted_timestamp = django.utils.timezone.now()

    home_postal_code = linkedin_config.get('home_postal')
    num_jobs_to_return = 10
    start_index = 0
    for search_term in search_terms_list:
        get_more_postings = True
        while get_more_postings:
            get_more_postings = False

            results = application.search_job(selectors=[{'jobs': ['id']}],
                                             params={'keywords': search_term,
                                                     'postal-code': home_postal_code,
                                                     'country_code': 'ca',
                                                     'distance': 50,
                                                     'sort': "DD",
                                                     'start': start_index,
                                                     'count': num_jobs_to_return})
            start_index += len(results)
            # see if we can check to see if the postings returned have already been saved
            results_to_save = get_list_of_ids_not_in_db(results)
            for result in results_to_save:
                posing_details = application.get_job(job_id=results[u'id'])
                posting = None
                if posting:
                    if jobsearch.scraping.save_posting_to_db(posting, 'linkedin', search_term, aliases,
                                                             geo_locator, home_location, geo_locations):
                        pass
    num_new_postings = models.JobPostings.objects.filter(inserted_date__gte=inserted_timestamp).count()
    num_saved_aliases = models.CompanyAliases.objects.filter(inserted_date__gte=inserted_timestamp).count()
    num_saved_recruiters = models.RecruitingCompanies.objects.filter(date_inserted__gte=inserted_timestamp).count()
    logger.debug('# new postings from Dice saved: {}   # aliases: {}   # recruiters: {} '.format(num_new_postings,
                                                                                                 num_saved_aliases,
                                                                                                 num_saved_recruiters))
    return num_saved


# def save_temporary_ids_to_db(ids):
#     formatted_ids = [(id,) for id in ids]
#     # logger.debug('un-formatted ids to insert: {}'.format(ids))
#     # logger.debug('formatted ids to insert: {}'.format(formatted_ids))
#     response = db_connection.executemany("insert into Temporary_IDs(ID) values (?)", formatted_ids)
#     logger.debug('insert temporary ids response rowcount: {}'.format(response.rowcount))
#     db_connection.commit()


def get_list_of_ids_not_in_db(posting_ids):
    models.TemporaryId.objects.clear()
    id_objs = [models.TemporaryId(id=posting_id) for posting_id in posting_ids]
    models.TemporaryId.objects.bulk_create(id_objs)
    response = models.TemporaryId.objects.raw('SELECT jobsearch_TemporaryId.* FROM jobsearch_TemporaryId LEFT JOIN jobsearch_JobPostings ON '
                                              'jobsearch_TemporaryId.Id = jobsearch_JobPostings.Id and jobsearch_JobPostings.source = ''linkedin'' '
                                              'WHERE jobsearch_JobPostings.Id IS NULL;')
    new_uids = [row.id for row in response]
    models.TemporaryId.objects.clear()
    return new_uids
