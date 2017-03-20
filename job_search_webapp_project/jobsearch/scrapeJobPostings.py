# coding: utf-8
import jobsearch.models as models
import datetime
import sys
import requests
import re
from bs4 import BeautifulSoup
from django.utils import timezone
import geopy.geocoders
import geopy.distance
import geopy.exc

job_site_details = {
    'ca.indeed.com': {
        'urlSchema': 'http',
        'netLoc': 'ca.indeed.com',
        'location': 'Canada',
        'urlPath': 'jobs',
        'jobTypeKey': 'jt',
        'pageIndexKey': 'start',
        'pageIndexType': 'postingCount',
        'loginUrl': 'http://ca.indeed.com/account/login',
        'nextUrl': '/',
        'username': None,
        'password': None,
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
#     'www.simplyhired.ca':   {
#         'urlSchema': 'http',
#         'netLoc': 'www.simplyhired.ca',
#         'location': 'Ontario',
#         'urlPath': 'search',
#         'jobTypeKey': 'fjt',
#         'pageIndexKey': 'pn',
#         'pageIndexType': 'pageCount',
#         'loginUrl': 'http://www.simplyhired.ca/account/signin',
#         'nextUrl': '',
#         'username': None,
#         'password': None,
#         'parseInfo': {
#             'numberJobsFound': {
#                 'element': 'h1',
#                 'criteria': {},
#                 'regex':
#                 'Showing (?:[0-9,]+)-(?:[0-9,]+) of ([0-9,]+) (?:[a-zA-Z ])*',
#             },
#             'parentElement': 'div',
#             'parentCriteria': {'class': 'js-job'},
#             'fields': {
#                 'title': {
#                     'element': 'h2',
#                     'criteria': {'itemprop': 'title'},
#                 },
#                 'id': {
#                     'element': 'parent',
#                     'criteria': {},
#                     'property': 'id',
#                     'regex': '(?mx)^r:(.*):[0-9]+$',
#                 },
#                 'locale': {
#                     'element': 'span',
#                     'criteria': {'itemprop': 'address'},
#                 },
#                 'company': {
#                     'element': 'span',
#                     'criteria': {'class': 'serp-company', 'itemprop': 'name'},
#                 },
#                 'url': {
#                     'element': 'a',
#                     'criteria': {'class': 'js-job-link'},
#                     'property': 'href',
#                 },
#                 'postedDate': {
#                     'element': 'span',
#                     'criteria': {'class': 'serp-timestamp'},
#                 },
#             },
#         }
#     },
}


def get_max_len_of_dict_vals_for_keys(thisDict, keys):
    lengths = [len(thisDict.get(key)) if thisDict.get(key) else 0
               for key in keys]
    if len(lengths) == 0:
        lengths.append(0)
    return max(lengths)


def get_max_len_of_dict_vals_for_key_in_list_of_dicts(dictList, keys):
    lengths = [get_max_len_of_dict_vals_for_keys(thisDict, keys)
               for thisDict in dictList]
    if len(lengths) == 0:
        lengths.append(0)
    return max(lengths)


def convert_ago_to_date(agoStr):
    try:
        if agoStr.lower() in ('just posted', 'today'):
            return datetime.datetime.now().strftime('%Y-%m-%d')
        else:
            value = re.sub('([0-9]+[+]?) (?:minute[s]?|hour[s]?|day[s]?) ago',
                           r"\1",
                           agoStr)

            if 'minute' in agoStr:
                dt = (datetime.datetime.now() - datetime.timedelta(
                                minutes=int(value))).strftime('%Y-%m-%d %H:%M')
            elif 'hour' in agoStr:
                dt = (datetime.datetime.now() - datetime.timedelta(
                                hours=int(value))).strftime('%Y-%m-%d %H:%M')
            elif 'today' in agoStr.lower():
                dt = datetime.datetime.now().strftime('%Y-%m-%d')
            elif 'day' in agoStr:
                if value == '30+':
                    dt = 'over 30 days old'
                else:
                    dt = (datetime.datetime.now() - datetime.timedelta(
                                days=int(value))).strftime('%Y-%m-%d')
            else:
                dt = agoStr
    except:
        print('Could not convert "{}" to a date'.format(agoStr))
        dt = agoStr
    return dt


def parse_html_page(pageHtml, jobsiteDetails, aliases, geolocator, home_location, geo_locations,
                    searchTerms='',
                    verbose=False):
    '''
            'numberJobsFound': {
                'element':'div',
                'criteria':{'id':'searchCount'},
                'regex': '^Jobs (?:[0-9,]+) to (?:[0-9,]+) of ([0-9,]+)$',
            },
    '''
    soup = BeautifulSoup(pageHtml, 'html.parser')
    totalNumberJobsFound = -1
    numJobsDetails = jobsiteDetails['parseInfo'].get('numberJobsFound')
    if numJobsDetails:
        numberPostingsElem = soup.find(numJobsDetails['element'],
                                       numJobsDetails['criteria'])
        if numberPostingsElem:
            value = None
            prop = numJobsDetails.get('property')
            if prop:
                value = numberPostingsElem[prop]
            elif hasattr(numberPostingsElem, 'text'):
                value = numberPostingsElem.text
            else:
                value = numberPostingsElem.string

            if numJobsDetails.get('regex'):
                value = re.sub(numJobsDetails['regex'], r"\1", value)
            stripped_val = value.replace(',', '')
            if stripped_val.isdigit():
                totalNumberJobsFound = int(stripped_val)
            else:
                print('For %s site, the numberJobsFound parsing information, "%s", appears to return a non-numeric string "%s"'
                      % (jobsiteDetails['netLoc'], numJobsDetails['regex'], value))
                totalNumberJobsFound = 1 # Just to ensure that it is known that at least 1 job found
            
    items = soup.findAll(jobsiteDetails['parseInfo']['parentElement'],
                         jobsiteDetails['parseInfo']['parentCriteria'])
    postingsList = {}

    for it in items:
        postingInfo = {'elem': it, 'searchTerms': searchTerms}
        for field in jobsiteDetails['parseInfo']['fields'].keys():
            fieldInfo = jobsiteDetails['parseInfo']['fields'][field]
#             print('looking for field {}'.format(field))
            try:
                value = None
                elem = None
                prop = None
                elemType = fieldInfo['element']
                if elemType == 'parent':
                    elem = it
                else:
                    elem = it.find(elemType, fieldInfo.get('criteria'))
                prop = fieldInfo.get('property')
                if prop and elem.has_attr(prop):
                    value = elem[prop]
                elif hasattr(elem, 'text'):
                    value = elem.text
                elif elem:
                    value = elem.string

                if fieldInfo.get('regex'):
                    value = re.sub(fieldInfo['regex'], r"\1", value)

                if value:
                    postingInfo[field] = re.sub(r"^\s+|\s+$|\s+(?=\s)", "",
                                                value)
            except Exception:
                typ, val, _ = sys.exc_info()
                print(('Unable to parse posting {} information for item: '
                       '\n\n{} \n\nError type: {}, val: {}').format(field, it,
                                                                    typ, val))

        if postingInfo.get('id'):
            if postingInfo.get('postedDate'):
                postingInfo['postedDate'] = convert_ago_to_date(
                                                postingInfo['postedDate'])

            if postingInfo.get('url'):
                postingInfo['url'] = 'http://{}{}'.format(
                        jobsiteDetails['netLoc'], postingInfo['url'])
            if postingInfo.get('elem'):
                linkElems = postingInfo['elem'].findAll('a')
                for linkElem in linkElems:
                    if not linkElem['href'].startswith('http'):
                        if linkElem['href'].startswith('/'):
                            linkElem['href'] = 'http://{}{}'.format(
                                    jobsiteDetails['netLoc'], linkElem['href'])
                        else:
                            linkElem['href'] = 'http://{}/{}'.format(
                                    jobsiteDetails['netLoc'], linkElem['href'])
            if postingInfo.get('locale'):
                postingInfo['locale'] = postingInfo['locale'].replace(' , ', ', ')
            if savePostingToDB(postingInfo, aliases, geolocator, home_location, geo_locations):
                postingsList[postingInfo['id']] = postingInfo
            if verbose:
                print(('Adding item details for id "{}" to list with posted'
                       ' Date {}').format(postingInfo['id'],
                                          postingInfo.get('postedDate')))
        else:
            print('Unknown item not being added to list')
    return postingsList, len(items), totalNumberJobsFound


def sort_by_subdict(dictionary, subdict_key):
    return sorted(dictionary.items(), key=lambda k_v: k_v[1][subdict_key])


def login_to_web_site(session, jobSiteDetailInfo):
    if jobSiteDetailInfo['username'] and jobSiteDetailInfo['password']:
        login_data = dict(username=jobSiteDetailInfo['username'],
                          password=jobSiteDetailInfo['password'])
        if jobSiteDetailInfo['nextUrl']:
            login_data['next'] = jobSiteDetailInfo['nextUrl']

        session.get(jobSiteDetailInfo['loginUrl'], verify=False)
        session.post(jobSiteDetailInfo['loginUrl'], data=login_data,
                     headers={"Referer": "HOMEPAGE"})


def get_postings_from_site_for_multiple_search_terms(jobSiteDetailsInfo,
                                                     searchTermsList,
                                                     aliases, 
                                                     geolocator, 
                                                     home_location, 
                                                     geo_locations,
                                                     expectedPostingsPerPage=10,
                                                     maxPages=100, minPages=4,
                                                     verbose=False):
    session = requests.Session()
    if jobSiteDetailsInfo['urlSchema'] == 'https':
        login_to_web_site(session, jobSiteDetailsInfo)

    for searchTerm in searchTermsList:
        get_job_postings_from_site(
            jobSiteDetailsInfo, searchTerm, aliases, 
            geolocator, home_location, geo_locations, 
            expectedPostingsPerPage=expectedPostingsPerPage,
            maxPages=maxPages, minPages=minPages, session=session,
            verbose=verbose)
    session = None
    

def check_for_more_postings(numPostingsOnPage, expectedPostingsPerPage,
                         numAllUniquePostingsFoundOnPage, numPostingsSiteFound,
                         startIndex, maxPages, minPages, verbose=False):
    '''
    Checks criteria for whether to check for more postings on the next page.

    Args:
        numPostingsOnPage (int): the total number of postings found on the page
        expectedPostingsPerPage (int): the number of postings expected to be on the page
        numAllUniquePostingsFoundOnPage (int): the number of new/unique postings found on the page
        numPostingsSiteFound (int): the total number of postings found on the site
        startIndex (int): the starting index for the page, should be a multiple of expectedPostingsPerPage
        maxPages (int): the maximum number of pages to scrape
        minPages (int): the minimum number of pages to scrape
    '''
    if startIndex + expectedPostingsPerPage <= numPostingsSiteFound:
        if numPostingsOnPage == expectedPostingsPerPage:
            if (numAllUniquePostingsFoundOnPage > 0 and
                    startIndex < expectedPostingsPerPage * (maxPages-1)):
                return True
            elif startIndex < expectedPostingsPerPage * (minPages-1):
                return True
        if verbose:
            print('numPostingsOnPage ({0}) != expectedPostingsPerPage ({1}) OR numAllUniquePostingsFoundOnPage ({2}) == 0 OR startIndex ({3}) < expectedPostingsPerPage ({4}) * (maxPages ({5}) -1) OR startIndex ({3}) < expectedPostingsPerPage ({4}) * (minPages ({6}) -1) '.format(numPostingsOnPage, expectedPostingsPerPage, numAllUniquePostingsFoundOnPage, startIndex, expectedPostingsPerPage, maxPages, minPages))
        return False
    else:
        if verbose:
            print('startIndex ({}) + expectedPostingsPerPage ({}) <= numPostingsSiteFound ({}) is False'.format(startIndex, expectedPostingsPerPage, numPostingsSiteFound))
        return False


def get_job_postings_from_site(jobSiteDetailsInfo, searchTerm, aliases, 
                               geolocator, home_location, geo_locations,
                               expectedPostingsPerPage=10, maxPages=100,
                               minPages=4, session=None, verbose=False):
    if not session:
        session = requests.Session()

        if jobSiteDetailsInfo['urlSchema'] == 'https':
            login_to_web_site(session, jobSiteDetailsInfo)

    startIndex = 0
    urlArguments = {'q': searchTerm,
                    'l': jobSiteDetailsInfo['location'],
                    jobSiteDetailsInfo['jobTypeKey']: 'contract',
                    'sort': 'date',
                    jobSiteDetailsInfo['pageIndexKey']: 0,
                    }

    url = '{}://{}/{}'.format(jobSiteDetailsInfo['urlSchema'],
                              jobSiteDetailsInfo['netLoc'],
                              jobSiteDetailsInfo['urlPath'])
    page = session.get(url, params=urlArguments, verify=False)
    # print('\n\npage header content-type info: {}\n'.format(
    #     page.headers['content-type']))
    print('\n\nHere is initial URL to be "scraped": {}\n'.format(page.url))

    postingsList, numPostingsOnPage, initTotalNumPostings = parse_html_page(
            page.text, jobSiteDetailsInfo, aliases, geolocator, 
            home_location, geo_locations, searchTerm, verbose)
    print('Found {} new of {} postings of {} from url {}'.format(
            len(postingsList), numPostingsOnPage,
            initTotalNumPostings, page.url))
    while check_for_more_postings(numPostingsOnPage, expectedPostingsPerPage,
                               len(postingsList), initTotalNumPostings,
                               startIndex, maxPages, minPages, verbose):
        startIndex += expectedPostingsPerPage
        if jobSiteDetailsInfo['pageIndexType'] == 'pageCount':
            urlArguments[jobSiteDetailsInfo['pageIndexKey']] += 1
        else:
            urlArguments[jobSiteDetailsInfo['pageIndexKey']] = startIndex
        page = session.get(url, params=urlArguments, verify=False)
        postingsList, numPostingsOnPage, totalNumberJobsFound = parse_html_page(
            page.text, jobSiteDetailsInfo, aliases, geolocator, 
            home_location, geo_locations, searchTerm, verbose)
        print('Found {} new of {} postings of {} from url {}'.format(len(postingsList),
                                                                     numPostingsOnPage,
                                                                     totalNumberJobsFound,
                                                                     page.url))


def get_geolocation(geolocator, location_str, recursive_level=0):
    try:
        location = geolocator.geocode(location_str)
    except geopy.exc.GeocoderTimedOut:
        if recursive_level < 4:
            return get_geolocation(geolocator, location_str, recursive_level + 1)
        else:
            print('GeoCoder Timed out 5 times for {}, so skipping'.format(location_str))
            return None
    return location


def savePostingToDB(posting, aliases, geolocator, home_location, geo_locations):
    company_name = posting.get('company')
    if company_name and not aliases.filter(alias=company_name).exists():
        if company_name and not models.Recruitingcompanies.objects.filter(name=company_name).exists():
            new_date = timezone.now().strftime('%Y-%m-%d')
            new_company = models.Recruitingcompanies.objects.create(name=company_name, dateinserted=new_date)
            new_company.save()
        new_company_alias = models.Companyaliases.objects.create(companyname=company_name, alias=company_name)
        new_company_alias.save()
    locale = posting.get('locale')
    city = None
    prov = None
    if '.' in locale:
        parts = locale.split(',')
        city = parts[0].strip()
        prov = parts[1].strip()
    if locale not in geo_locations:
        geo_locations[locale] = get_geolocation(geolocator, locale)
    if geo_locations.get(locale):
        dist = round(geopy.distance.distance(home_location.point, geo_locations[locale].point).km, 0)
    else:
        dist = 0.0
    try:
        db_posting = models.Jobpostings.objects.create(
            identifier=posting['id'], 
            company=posting.get('company'), 
            title=posting['title'], 
            locale=locale, 
            url=posting['url'], 
            posteddate=posting.get('postedDate'), 
            city=city, 
            province=prov, 
            searchterms=posting['searchTerms'], 
            elementhtml=posting['elem'].prettify(formatter="html"), 
            distance_from_home=dist)
        db_posting.save()
        return True
    except Exception as e:
        print('Exception %s occurred while trying to insert posting %s %s %s.' % (e, posting['id'], posting['title'], posting.get('company')))
        return False


def scrape_new_job_postings():
    searchTermsList = ['java', 'devops', 'python', ]
    siteList = job_site_details
    aliases = models.Companyaliases.objects.all()
    
    geolocator = geopy.geocoders.Nominatim()
    # Get coordinates for home
    home_location_str = '1695 Playfair Drive, Ottawa, ON, Canada'
    home_location = get_geolocation(geolocator, home_location_str)
    geo_locations = {}

    for jobSiteDetailsInfo in siteList.values():        
        get_postings_from_site_for_multiple_search_terms(
            jobSiteDetailsInfo,
            searchTermsList,
            aliases, 
            geolocator, 
            home_location, 
            geo_locations)
