# coding: utf-8
import logging
import datetime
import re

import requests
from bs4 import BeautifulSoup
import geopy.geocoders
import geopy.distance
import geopy.exc

import jobsearch.scraping
import jobsearch.models as models

NUMBER_POSTINGS_PER_REQUEST = 25

MAX_POSTINGS_RETRIEVED = 1000

logger = logging.getLogger(__name__)


def get_max_len_of_dict_vals_for_keys(this_dict, keys):
    lengths = [len(this_dict.get(key)) if this_dict.get(key) else 0
               for key in keys]
    if len(lengths) == 0:
        lengths.append(0)
    return max(lengths)


def get_max_len_of_dict_vals_for_key_in_list_of_dicts(dict_list, keys):
    lengths = [get_max_len_of_dict_vals_for_keys(thisDict, keys)
               for thisDict in dict_list]
    if len(lengths) == 0:
        lengths.append(0)
    return max(lengths)


def convert_ago_to_date(ago_str):
    try:
        if ago_str.lower() in ('just posted', 'today'):
            return datetime.datetime.now().strftime('%Y-%m-%d')
        else:
            value = re.sub('([0-9]+[+]?) (?:minute[s]?|hour[s]?|day[s]?) ago',
                           r"\1",
                           ago_str)

            if 'minute' in ago_str:
                dt = (datetime.datetime.now() - datetime.timedelta(
                    minutes=int(value))).strftime('%Y-%m-%d %H:%M')
            elif 'hour' in ago_str:
                dt = (datetime.datetime.now() - datetime.timedelta(
                    hours=int(value))).strftime('%Y-%m-%d %H:%M')
            elif 'today' in ago_str.lower():
                dt = datetime.datetime.now().strftime('%Y-%m-%d')
            elif 'day' in ago_str:
                if value == '30+':
                    dt = 'over 30 days old'
                else:
                    dt = (datetime.datetime.now() - datetime.timedelta(
                        days=int(value))).strftime('%Y-%m-%d')
            else:
                dt = ago_str
    except Exception as exc:
        logger.error('Could not convert "{}" to a date'.format(ago_str), exc)
        dt = ago_str
    return dt


def parse_html_page(page_html, source, job_site_details, aliases, geo_locator, home_location, geo_locations,
                    search_terms='',
                    verbose=False):
    """
            'numberJobsFound': {
                'element':'div',
                'criteria':{'id':'searchCount'},
                'regex': '^Jobs (?:[0-9,]+) to (?:[0-9,]+) of ([0-9,]+)$',
            },
    """
    logger.debug(('parse_html_page(page_html, job_site_details={}, # aliases={}, geo_locator, home_location, '
                  'geo_locations, search_terms={}, verbose={})').format(job_site_details, len(aliases),
                                                                        search_terms, verbose))
    soup = BeautifulSoup(page_html, 'html.parser')
    total_number_jobs_found = -1
    num_jobs_details = job_site_details['parseInfo'].get('numberJobsFound')
    if num_jobs_details:
        number_postings_elem = soup.find(num_jobs_details['element'],
                                         num_jobs_details['criteria'])
        if number_postings_elem:
            prop = num_jobs_details.get('property')
            if prop:
                value = number_postings_elem[prop]
            elif hasattr(number_postings_elem, 'text'):
                value = number_postings_elem.text
            else:
                value = number_postings_elem.string

            if num_jobs_details.get('regex'):
                value = re.sub(num_jobs_details['regex'], r"\1", value)
            stripped_val = value.replace(',', '')
            if stripped_val.isdigit():
                total_number_jobs_found = int(stripped_val)
            else:
                logger.info(
                    'For %s site, the numberJobsFound parsing information, "%s", appears to return a non-numeric '
                    'string "%s" '
                    % (job_site_details['netLoc'], num_jobs_details['regex'], value))
                total_number_jobs_found = 1  # Just to ensure that it is known that at least 1 job found

    items = soup.findAll(job_site_details['parseInfo']['parentElement'],
                         job_site_details['parseInfo']['parentCriteria'])
    postings_list = {}

    for it in items:
        posting_info = {'elem': it, 'searchTerms': search_terms}
        for field in job_site_details['parseInfo']['fields'].keys():
            field_info = job_site_details['parseInfo']['fields'][field]
            #             logger.info('looking for field {}'.format(field))
            try:
                value = None
                elem_type = field_info['element']
                if elem_type == 'parent':
                    elem = it
                else:
                    elem = it.find(elem_type, field_info.get('criteria'))
                prop = field_info.get('property')
                if prop and elem.has_attr(prop):
                    value = elem[prop]
                elif hasattr(elem, 'text'):
                    value = elem.text
                elif elem:
                    value = elem.string

                if field_info.get('regex'):
                    value = re.sub(field_info['regex'], r"\1", value)

                if value:
                    posting_info[field] = re.sub(r"^\s+|\s+$|\s+(?=\s)", "", value)
            except Exception as exc:
                logger.error(('Unable to parse posting {} information for item: '
                              '\n\n{} \n\nError type: {}, val: {}').format(field, it,
                                                                           type(exc), exc))

        if posting_info.get('id'):
            if posting_info.get('postedDate'):
                posting_info['postedDate'] = convert_ago_to_date(
                    posting_info['postedDate'])

            if posting_info.get('url'):
                posting_info['url'] = 'http://{}{}'.format(
                    job_site_details['netLoc'], posting_info['url'])
            if posting_info.get('elem'):
                link_elements = posting_info['elem'].findAll('a')
                for linkElem in link_elements:
                    if not linkElem['href'].startswith('http'):
                        if linkElem['href'].startswith('/'):
                            linkElem['href'] = 'http://{}{}'.format(
                                job_site_details['netLoc'], linkElem['href'])
                        else:
                            linkElem['href'] = 'http://{}/{}'.format(
                                job_site_details['netLoc'], linkElem['href'])
            if posting_info.get('locale'):
                posting_info['locale'] = posting_info['locale'].replace(' , ', ', ')
            if jobsearch.scraping.save_posting_to_db(posting_info, source, search_terms, aliases,
                                                     geo_locator, home_location, geo_locations):
                postings_list[posting_info['id']] = posting_info
            if verbose:
                logger.info(('Adding item details for id "{}" to list with posted'
                             ' Date {}').format(posting_info['id'],
                                                posting_info.get('postedDate')))
        else:
            logger.info('Unknown item not being added to list')
    return postings_list, len(items), total_number_jobs_found


def sort_by_sub_dict(dictionary, sub_dict_key):
    return sorted(dictionary.items(), key=lambda k_v: k_v[1][sub_dict_key])


def login_to_web_site(session, job_site_detail_info):
    logger.debug('login_to_web_site(session, job_site_detail_info={})'.format(job_site_detail_info))
    if job_site_detail_info.get('username') and job_site_detail_info.get('password'):
        login_data = {
            'action': 'Login',
            '__email': job_site_detail_info['username'],
            '__password': job_site_detail_info['password'],
            'remember': '1',
            'hl': 'en',
            # 'continue': '/account/view?hl=en',
        }
        if job_site_detail_info['nextUrl']:
            login_data['next'] = job_site_detail_info['nextUrl']

        # res = session.get(job_site_detail_info['loginUrl'], verify=False)
        res = session.post(job_site_detail_info['loginUrl'], data=login_data,
                           headers={"Referer": "HOMEPAGE"})
        # if logger.getLogger().getEffectiveLevel() == logger.DEBUG:
        logger.debug('session.post("{}", data={}) returns {}'.format(job_site_detail_info['loginUrl'],
                                                                     login_data, res))
    else:
        logger.debug('Username "{}" or password "{}" is not set. Not logging in to website {}. Details: {}'.format(
            job_site_detail_info.get('username'),
            job_site_detail_info.get('password'),
            job_site_detail_info.get('loginUrl'),
            job_site_detail_info))


def get_postings_from_site_for_multiple_search_terms(source,
                                                     job_site_details_info,
                                                     search_terms_list,
                                                     aliases,
                                                     geo_locator,
                                                     home_location,
                                                     geo_locations,
                                                     expected_postings_per_page=10,
                                                     max_pages=100, min_pages=4,
                                                     verbose=False):
    logger.debug(('get_postings_from_site_for_multiple_search_terms(job_site_details_info: {}, search_terms_list: {}, '
                  '# aliases: {}, expected_postings_per_page={}, geo_locator, home_location: {}, geo_locations,'
                  'max_pages={}, min_pages={}, verbose={})').format(job_site_details_info,
                                                                    search_terms_list,
                                                                    len(aliases),
                                                                    home_location,
                                                                    expected_postings_per_page,
                                                                    max_pages,
                                                                    min_pages, verbose))
    session = requests.Session()

    if job_site_details_info['urlSchema'] == 'https':
        login_to_web_site(session, job_site_details_info)

    for searchTerm in search_terms_list:
        get_job_postings_from_site(
            source, job_site_details_info, searchTerm, aliases,
            geo_locator, home_location, geo_locations,
            expected_postings_per_page=expected_postings_per_page,
            max_pages=max_pages, min_pages=min_pages, session=session,
            verbose=verbose)


def check_for_more_postings(num_postings_on_page, expected_postings_per_page,
                            num_unique_postings_found_on_page, num_postings_site_found,
                            start_index, max_pages, min_pages, verbose=False):
    """
    Checks criteria for whether to check for more postings on the next page.

    Args:
        :param num_postings_on_page: the total number of postings found on the page
        :param expected_postings_per_page: the number of postings expected to be on the page
        :param num_unique_postings_found_on_page: the number of new/unique postings found on the page
        :param num_postings_site_found: the total number of postings found on the site
        :param start_index: the starting index for the page, should be a multiple of expectedPostingsPerPage
        :param max_pages: the maximum number of pages to scrape
        :param min_pages: the minimum number of pages to scrape
        :param verbose:
    """
    logger.debug(('check_for_more_postings(num_postings_on_page={}, expected_postings_per_page={}, '
                  'num_all_unique_postings_found_on_page={}, num_postings_site_found={}, '
                  'start_index={}, max_pages={}, min_pages={}, verbose={})').format(num_postings_on_page,
                                                                                    expected_postings_per_page,
                                                                                    num_unique_postings_found_on_page,
                                                                                    num_postings_site_found,
                                                                                    start_index, max_pages,
                                                                                    min_pages, verbose))
    if start_index + expected_postings_per_page <= num_postings_site_found:
        if num_postings_on_page == expected_postings_per_page:
            if (num_unique_postings_found_on_page > 0 and
                    start_index < expected_postings_per_page * (max_pages - 1)):
                return True
            elif start_index < expected_postings_per_page * (min_pages - 1):
                return True
        if verbose:
            logger.info(
                'numPostingsOnPage ({0}) != expectedPostingsPerPage ({1}) OR numAllUniquePostingsFoundOnPage ({2}) == '
                '0 OR startIndex ({3}) < expectedPostingsPerPage ({4}) * (maxPages ({5}) -1) OR startIndex ({3}) < '
                'expectedPostingsPerPage ({4}) * (minPages ({6}) -1) '.format(
                    num_postings_on_page, expected_postings_per_page, num_unique_postings_found_on_page,
                    start_index, expected_postings_per_page, max_pages, min_pages))
        return False
    else:
        if verbose:
            logger.debug('startIndex ({}) + expectedPostingsPerPage ({}) <= numPostingsSiteFound ({}) is False'.format(
                          start_index, expected_postings_per_page, num_postings_site_found))
        return False


def get_job_postings_from_site(source, job_site_details_info, search_term, aliases,
                               geo_locator, home_location, geo_locations,
                               expected_postings_per_page=10, max_pages=100,
                               min_pages=4, session=None, verbose=False):
    logger.debug(('get_job_postings_from_site(job_site_details_info={}, search_term={}, # aliases={},'
                  'geo_locator, home_location, geo_locations, '
                  'expected_postings_per_page={}, max_pages={}, '
                  'min_pages={}, session={}, verbose={}').format(job_site_details_info, search_term, len(aliases),
                                                                 geo_locator, home_location, geo_locations,
                                                                 expected_postings_per_page, max_pages,
                                                                 min_pages, session, verbose))
    if not session:
        session = requests.Session()

        if job_site_details_info['urlSchema'] == 'https':
            login_to_web_site(session, job_site_details_info)

    start_index = 0
    url_arguments = {'q': search_term,
                     'l': job_site_details_info['location'],
                     job_site_details_info['jobTypeKey']: 'contract',
                     'sort': 'date',
                     job_site_details_info['pageIndexKey']: 0,
                     }

    url = '{}://{}/{}'.format(job_site_details_info['urlSchema'],
                              job_site_details_info['netLoc'],
                              job_site_details_info['urlPath'])
    page = session.get(url, params=url_arguments, verify=False)
    # logger.info('\n\n page header content-type info: {}\n'.format(
    #     page.headers['content-type']))
    logger.info('\n\nHere is initial URL to be "scraped": {}\n'.format(page.url))

    postings_list, num_postings_on_page, init_total_num_postings = parse_html_page(
        page.text, source, job_site_details_info, aliases, geo_locator,
        home_location, geo_locations, search_term, verbose)
    logger.info('Found {} new of {} postings of {} from url {}'.format(
        len(postings_list), num_postings_on_page,
        init_total_num_postings, page.url))
    while check_for_more_postings(num_postings_on_page, expected_postings_per_page,
                                  len(postings_list), init_total_num_postings,
                                  start_index, max_pages, min_pages, verbose):
        start_index += expected_postings_per_page
        if job_site_details_info['pageIndexType'] == 'pageCount':
            url_arguments[job_site_details_info['pageIndexKey']] += 1
        else:
            url_arguments[job_site_details_info['pageIndexKey']] = start_index
        page = session.get(url, params=url_arguments, verify=False)
        postings_list, num_postings_on_page, total_number_jobs_found = parse_html_page(
            page.text, job_site_details_info, aliases, geo_locator,
            home_location, geo_locations, search_term, verbose)
        logger.info('Found {} new of {} postings of {} from url {}'.format(len(postings_list),
                                                                           num_postings_on_page,
                                                                           total_number_jobs_found,
                                                                           page.url))


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

    search_terms_list = ['java', 'devops', 'python', ]

    client = None

    if not client:
        logger.warning('Dice posting retrieval not implemented yet!')
        return 0

    inserted_timestamp = datetime.datetime.now()
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
                    if jobsearch.scraping.save_posting_to_db(posting, 'dice', search_term, aliases,
                                                             geo_locator, home_location, geo_locations):
                        # If we saved at least 1 posting, then we can try getting more postings from the source!
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
    logger.debug('# new postings from Dice saved: {}   # aliases: {}   # recruiters: {} '.format(num_new_postings,
                                                                                                 num_saved_aliases,
                                                                                                 num_saved_recruiters))
    return num_new_postings
