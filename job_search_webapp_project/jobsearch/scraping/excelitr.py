# coding: utf-8
import logging
import re

import requests
from bs4 import BeautifulSoup
import geopy.geocoders
import geopy.distance
import geopy.exc

import jobsearch
import jobsearch.scraping
import jobsearch.models as models
from jobsearch import scrapeJobPostings

NUMBER_POSTINGS_PER_REQUEST = 25

MAX_POSTINGS_RETRIEVED = 1000

logger = logging.getLogger(__name__)

job_site_details = {
    'www.excelitr.com': {
        'url': 'https://www.excelitr.com/api/OpportunitySearch',
        'url_parameters': [
            {
                'Keywords': 'java',
                'Regions': '0',
                'Cities': 'Work Remotely',
                'DivisionGroups': 2,
                'PositionTypes': 2,
                'SearchTypeNo': 0,
                'MaxItemsToReturn': 0
            },
            {
                'Keywords': 'java',
                'Regions': '0',
                'Cities': 'Work+Remotely',
                'DivisionGroups': 2,
                'PositionTypes': 2,
                'SearchTypeNo': 0,
                'MaxItemsToReturn': 0
            },
            {
                'Keywords': 'java',
                'Regions': '1',
                'Cities': 'All Cities',
                'DivisionGroups': 2,
                'PositionTypes': 2,
                'SearchTypeNo': 0,
                'MaxItemsToReturn': 0
            }],
        'headers': {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "en-US,en;q=0.9",
            "referrer": "https://www.excelitr.com/Search",
            "referrerPolicy": "no-referrer-when-downgrade",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "x-requested-with": "XMLHttpRequest"
        },
        'request_parameters': {
            "body": None,
            "method": "GET",
            "mode": "cors"
        },
        'parseInfo': {
            'numberJobsFound': {
                'element': 'div',
                'criteria': {'id': 'searchCount'},
                'regex': '^Jobs (?:[0-9,]+) to (?:[0-9,]+) of ([0-9,]+)$',
            },
            'parentElement': 'div',
            'parentCriteria': {'class': 'row',
                               'itemtype': 'http://schema.org/JobPosting'},
            'fields': {
                'title': {
                    'element': 'a',
                    'criteria': {'itemprop': 'title'},
                    'property': 'title',
                },
                'id': {
                    'element': 'parent',
                    'criteria': {},
                    'property': 'data-jk',
                },
                'locale': {
                    'element': 'span',
                    'criteria': {'itemprop': 'addressLocality'},
                },
                'company': {
                    'element': 'span',
                    'criteria': {'itemprop': 'hiringOrganization'},
                },
                'url': {
                    'element': 'a',
                    'criteria': {'itemprop': 'title'},
                    'property': 'href',
                },
                'postedDate': {
                    'element': 'span',
                    'criteria': {'class': 'date'},
                },
            },
        }
    },
}


def parse_html_page(page_html, job_site_details, aliases, geo_locator, home_location, geo_locations,
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
    num_saved = 0
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
                posting_info['postedDate'] = scrapeJobPostings.convert_ago_to_date(
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
            if jobsearch.scraping.save_posting_to_db(posting_info, 'linkedin', search_terms, aliases,
                                                     geo_locator, home_location, geo_locations):

                postings_list[posting_info['id']] = posting_info
                num_saved = num_saved + 1
            if verbose:
                logger.info(('Adding item details for id "{}" to list with posted'
                             ' Date {}').format(posting_info['id'],
                                                posting_info.get('postedDate')))
        else:
            logger.info('Unknown item not being added to list')
    return postings_list, len(items), total_number_jobs_found, num_saved


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


def get_job_postings_from_site(job_site_details_info, search_term, aliases,
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
    response = session.get('https://www.excelitr.com/Search')
    logger.debug('response getting https://www.excelitr.com/Search: {}'.format(response))
    total_num_saved = 0
    session.headers.clear()
    headers = job_site_details_info.get('headers')
    session.headers.update(headers)
    url = job_site_details_info['url']
    url_arguments_list = job_site_details_info['url_parameters']
    for url_query_arguments in url_arguments_list:
        url_query_arguments['Keywords'] = search_term
        logger.debug('session get parameters: \nurl: {}\nheaders: {}\nurl query params: {}'.format(
            url, session.headers, url_query_arguments))
        page = session.get(url, params=url_query_arguments, verify=False)
        if page.status_code != 200:
            logger.warning('Bad request for call to {} with query parameters {}!'.format(page.url, url_query_arguments))
            continue
        postings_list, num_postings_on_page, init_total_num_postings, num_saved = parse_html_page(
            page.text, job_site_details_info, aliases, geo_locator,
            home_location, geo_locations, search_term, verbose)
        total_num_saved = total_num_saved + num_saved
        logger.info('Saved {} of Found {} new of {} postings of {} from url {}'.format(
            num_saved, len(postings_list), num_postings_on_page,
            init_total_num_postings, page.url))
        # while check_for_more_postings(num_postings_on_page, expected_postings_per_page,
        #                               len(postings_list), init_total_num_postings,
        #                               start_index, max_pages, min_pages, verbose):
        #     start_index += expected_postings_per_page
        #     if job_site_details_info['pageIndexType'] == 'pageCount':
        #         url_query_arguments[job_site_details_info['pageIndexKey']] += 1
        #     else:
        #         url_query_arguments[job_site_details_info['pageIndexKey']] = start_index
        #     page = session.get(url, params=url_query_arguments, verify=False)
        #     postings_list, num_postings_on_page, total_number_jobs_found, num_saved = parse_html_page(
        #         page.text, job_site_details_info, aliases, geo_locator,
        #         home_location, geo_locations, search_term, verbose)
        #     total_num_saved = total_num_saved + num_saved
        #     logger.info('Found {} new of {} postings of {} from url {}'.format(len(postings_list),
        #                                                                        num_postings_on_page,
        #                                                                        total_number_jobs_found,
        #                                                                        page.url))
    return total_num_saved


def scrape_new_job_postings(config=None, geo_locator=None, geo_locations=None, home_location=None):
    if not config:
        config = jobsearch.scraping.get_configuration()

    if not geo_locator:
        geo_locator = geopy.geocoders.Nominatim(user_agent="JobSearch")

    if not geo_locations:
        geo_locations = {}

    if not home_location:
        # Get coordinates for home
        home_location_str = config.get('home_location')
        home_location = scrapeJobPostings.get_geo_location(geo_locator, home_location_str)

    search_terms_list = ['java', 'devops', 'python', ]
    job_site_details_info = job_site_details.get('www.excelitr.com')
    aliases = models.CompanyAliases.objects.all()

    session = requests.Session()
    num_saved = 0
    expected_postings_per_page = 10
    max_pages = 100
    min_pages = 4
    verbose = False
    for searchTerm in search_terms_list:
        num_saved = num_saved + get_job_postings_from_site(
            job_site_details_info, searchTerm, aliases,
            geo_locator, home_location, geo_locations,
            expected_postings_per_page=expected_postings_per_page,
            max_pages=max_pages, min_pages=min_pages, session=session,
            verbose=verbose)
    logger.info('{} postings saved from Excel'.format(num_saved))
    return num_saved
