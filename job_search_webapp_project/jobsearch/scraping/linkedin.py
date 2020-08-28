import logging
import random
import string

import django
import geopy
import requests
from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import linkedin_compliance_fix
from django.db import transaction
from linkedin_v2 import linkedin

import jobsearch.scraping
from jobsearch import scrapeJobPostings, models

# OAuth endpoints given in the LinkedIn API documentation
AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
ACCESS_TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'

logger = logging.getLogger(__name__)


def login_using_oauth(linkedin_config):
    client_id = linkedin_config.get('APPLICATION_KEY')

    linkedin = OAuth2Session(client_id, redirect_uri=linkedin_config.get('RETURN_URL'))
    linkedin = linkedin_compliance_fix(linkedin)

    # Redirect user to LinkedIn for authorization
    authorization_url, state = linkedin.authorization_url(AUTHORIZATION_URL)
    print('Please go here and authorize,', authorization_url)


def authorization_callback(linkedin_config, redirect_response):
    client_id = linkedin_config.get('APPLICATION_KEY')
    client_secret = linkedin_config.get('APPLICATION_SECRET')
    linkedin = OAuth2Session(client_id, redirect_uri=linkedin_config.get('RETURN_URL'))
    linkedin = linkedin_compliance_fix(linkedin)

    # Fetch the access token
    linkedin.fetch_token(ACCESS_TOKEN_URL, client_secret=client_secret, authorization_response=redirect_response)

    # Fetch a protected resource, i.e. user profile
    r = linkedin.get('https://api.linkedin.com/v1/people/~')
    print(r.content)

# def test():
#     # Generate a random string to protect against cross-site request forgery
#     letters = string.ascii_lowercase
#     CSRF_TOKEN = ''.join(random.choice(letters) for i in range(24))
#
#     # Request authentication URL
#     auth_params = {'response_type': 'code',
#                    'client_id': linkedin_config.get('APPLICATION_KEY'),
#                    'redirect_uri': linkedin_config.get('RETURN_URL'),
#                    'state': CSRF_TOKEN,
#                    'scope': 'r_liteprofile,r_emailaddress,w_member_social'}
#
#     html = requests.get(AUTHORIZATION_URL,
#                         params=auth_params)
#
#     qd = {'grant_type': 'authorization_code',
#           'code': linkedin_config.get('AUTH_CODE'),
#           'redirect_uri': linkedin_config.get('RETURN_URL'),
#           'client_id': linkedin_config.get('APPLICATION_KEY'),
#           'client_secret': linkedin_config.get('APPLICATION_SECRET')}
#
#     response = requests.post(ACCESS_TOKEN_URL, data=qd, timeout=60)
#
#     response = response.json()
#
#     access_token = response['access_token']
#
#     print("Access Token:", access_token)
#     print("Expires in (seconds):", response['expires_in'])


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
    num_saved = 0
    inserted_timestamp = django.utils.timezone.now()

    authentication = linkedin.LinkedInAuthentication(
        linkedin_config.get('APPLICATION_KEY'),
        linkedin_config.get('APPLICATION_SECRET'),
        linkedin_config.get('RETURN_URL'),
        linkedin.PERMISSIONS.enums.values()
    )
    application = linkedin.LinkedInApplication(authentication)

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
