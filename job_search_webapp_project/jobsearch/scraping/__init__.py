
__all__ = ['indeed', 'excelitr', 'linkedin', 'dice', 'sisystems', 'myticas']

import datetime
import logging
import pathlib
import pprint

import geopy
import geopy.geocoders
import geopy.distance
import geopy.exc
from django.db import transaction, IntegrityError
import django.db.models
import django.utils.timezone

import jobsearch
import jobsearch.models
import jobsearch.scraping.myticas
import jobsearch.scraping.linkedin
import jobsearch.scraping.indeed
import jobsearch.scraping.sisystems
import jobsearch.scraping.excelitr

from python_miscelaneous import configuration

logger = logging.getLogger(__name__)


def get_configuration():
    return configuration.get_configuration('jobSearch_config', location_path=pathlib.Path('~/jobSearch'),
                                           config_type=configuration.CONFIGURATION_TYPE_JSON)


def get_geo_location(geo_locator, location_str, recursive_level=0):
    try:
        location = geo_locator.geocode(location_str)
    except geopy.exc.GeocoderUnavailable as exp:
        logging.warning('GeoCoder unavailable, so skipping, returning None.', exp)
        return None
    except geopy.exc.GeocoderTimedOut:
        if recursive_level < 4:
            return get_geo_location(geo_locator, location_str, recursive_level + 1)
        else:
            logger.info('GeoCoder Timed out 5 times for {}, so skipping'.format(location_str))
            return None
    logger.info('Location info for {} is {}'.format(location_str, location))
    return location


def save_posting_to_db(posting, source, search_term, aliases, geo_locator, home_location, geo_locations):
    """

    :param posting: Should be a dict containing the following keys: company, jobkey, jobtitle, date, city, state, url,
    and any other descriptive keys desired
    :param source:
    :param search_term:
    :param aliases:
    :param geo_locator:
    :param home_location:
    :param geo_locations:
    :return:
    """
    if posting.get('expired', False):
        logging.debug('Not saving expired Posting {}'.format(posting))
        return False
    if 'date_parsed' in posting:
        posted_date = posting.get('date_parsed')
    else:
        posted_date = datetime.datetime.strptime(posting.get('date'), '%a, %d %b %Y %H:%M:%S %Z')
    company_name = posting.get('company')
    if company_name and not aliases.filter(alias=company_name).exists():
        if company_name and not jobsearch.models.RecruitingCompanies.objects.filter(name=company_name).exists():
            new_date = django.utils.timezone.now()
            new_company = jobsearch.models.RecruitingCompanies.objects.create(name=company_name, date_inserted=new_date)

            with transaction.atomic():
                try:
                    new_company.save()
                except IntegrityError as e:
                    logger.warning('IntegrityError %s occurred while trying to insert new company %s.' % (
                        e, company_name), e)
                    logger.warning('Unable to save posting id {}, title "{}", posted {} ({}), from {} to db'.format(
                        posting['jobkey'],
                        posting['jobtitle'],
                        posted_date,
                        posting.get('date'),
                        posting.get('company')))
                    return False
                except Exception as e:
                    logger.error('Exception %s occurred while trying to insert new company %s.' % (
                        e, company_name), e)
                    logger.warning('Unable to save posting id {}, title "{}", posted {} ({}), from {} to db'.format(
                        posting['jobkey'],
                        posting['jobtitle'],
                        posted_date,
                        posting.get('date'),
                        posting.get('company')))
                    return False

        new_company_alias = jobsearch.models.CompanyAliases.objects.create(company_name=company_name, alias=company_name)
        with transaction.atomic():
            try:
                new_company_alias.save()
            except IntegrityError as e:
                logger.warning('IntegrityError %s occurred while trying to insert new company alias %s.' % (
                    e, company_name))
                logger.warning('Unable to save posting id {}, title "{}", posted {} ({}), from {} to db'.format(
                    posting['jobkey'],
                    posting['jobtitle'],
                    posted_date,
                    posting.get('date'),
                    posting.get('company')))
                return False

            except Exception as e:
                logger.error('Exception %s occurred while trying to insert new company alias %s.' % (
                    e, company_name), e)
                logger.warning('Unable to save posting id {}, title "{}", posted {} ({}), from {} to db'.format(
                    posting['jobkey'],
                    posting['jobtitle'],
                    posted_date,
                    posting.get('date'),
                    posting.get('company')))
                return False
    locale = posting.get('locale')
    if locale:
        locale_parts = locale.split(',')
        city = locale_parts[0]
        prov = locale_parts[1].strip()
    else:
        city = posting['city']
        prov = posting['state']
        if city.lower() == 'kanata' and prov.lower() == 'on':
            locale = 'Kanata, Ottawa, On'
        else:
            locale = '{}, {}'.format(city, prov)
    if locale not in geo_locations:
        geo_locations[locale] = get_geo_location(geo_locator, locale)
    if geo_locations.get(locale):
        dist = round(geopy.distance.distance(home_location.point, geo_locations[locale].point).km, 0)
    else:
        dist = 0.0
    try:
        db_posting = jobsearch.models.JobPostings.objects.create(
            identifier=posting['jobkey'],
            company=posting.get('company'),
            title=posting['jobtitle'],
            locale=locale,
            url=posting['url'],
            posted_date=django.utils.timezone.make_aware(posted_date),
            inserted_date=django.utils.timezone.make_aware(datetime.datetime.now()),
            city=city,
            province=prov,
            search_terms=search_term,
            element_html=pprint.pformat(posting, indent=2),
            distance_from_home=dist,
            interested=jobsearch.models.InterestedChoices.NOT_REVIEWED,
            source=source)
        with transaction.atomic():
            db_posting.save()
        logger.debug('Saved posting id {}, title "{}", posted {} ({}), from {} to db'.format(posting['jobkey'],
                                                                                             posting['jobtitle'],
                                                                                             posted_date,
                                                                                             posting.get('date'),
                                                                                             posting.get('company')))
        return True
    except IntegrityError as e:
        logger.warning('IntegrityError %s occurred while trying to insert posting %s %s %s.' % (
            e, posting['jobkey'], posting['jobtitle'], posting.get('company')))
        return False
    except Exception as e:
        logger.error('Exception %s occurred while trying to insert posting %s %s %s.' % (
            e, posting['jobkey'], posting['jobtitle'], posting.get('company')), e)
        return False


def daily_get_all_new_postings():
    latest_scraped_posting = jobsearch.models.JobPostings.objects.aggregate(django.db.models.Max('inserted_date'))
    config = jobsearch.scraping.get_configuration()
    collection_frequency_hours = config.get("scheduler").get("posting_collection_frequency_hours")
    now = django.utils.timezone.now()
    time_since_last_collection = now - latest_scraped_posting.get('inserted_date__max')
    if time_since_last_collection > datetime.timedelta(hours=collection_frequency_hours):
        logger.debug("Starting scheduled collection of postings")
        get_all_new_postings()
    else:
        logger.debug('Not collecting new postings because less than {} hours since job collected, which was {}'.format(
            collection_frequency_hours, time_since_last_collection))


def get_all_new_postings():
    geo_locations = {}
    config = jobsearch.scraping.get_configuration()
    geo_locator = geopy.geocoders.Nominatim(user_agent="JobSearch")
    home_location_str = config.get('home_location')
    home_location = jobsearch.scraping.get_geo_location(geo_locator, home_location_str)

    num_imported_from_indeed = jobsearch.scraping.indeed.scrape_new_job_postings(config=config,
                                                                                 geo_locator=geo_locator,
                                                                                 geo_locations=geo_locations,
                                                                                 home_location=home_location)
    logger.debug('Number of postings from Indeed: {}'.format(num_imported_from_indeed))
    # num_imported_from_dice = jobsearch.scrapeJobPostings.scrape_new_job_postings(config=config,
    #                                                                        geo_locator=geo_locator,
    #                                                                        geo_locations=geo_locations,
    #                                                                        home_location=home_location)
    # logger.debug('Number of postings from Dice: {}'.format(num_imported_from_dice))
    # num_imported_from_linkedin = jobsearch.scraping.linkedin.scrape_new_job_postings(config=config,
    #                                                                                  geo_locator=geo_locator,
    #                                                                                  geo_locations=geo_locations,
    #                                                                                  home_location=home_location)
    # logger.debug('Number of postings from Linkedin: {}'.format(num_imported_from_linkedin))
    # num_imported_from_excelitr = jobsearch.scraping.excelitr.scrape_new_job_postings(config=config,
    #                                                                                  geo_locator=geo_locator,
    #                                                                                  geo_locations=geo_locations,
    #                                                                                  home_location=home_location)
    # logger.debug('Number of postings from Excel: {}'.format(num_imported_from_excelitr))
    # num_imported_from_sisystems = jobsearch.scraping.sisystems.scrape_new_job_postings(config=config,
    #                                                                                  geo_locator=geo_locator,
    #                                                                                  geo_locations=geo_locations,
    #                                                                                  home_location=home_location)
    # logger.debug('Number of postings from SI Systems: {}'.format(num_imported_from_sisystems))
    num_imported_from_myticas = jobsearch.scraping.myticas.scrape_new_job_postings(config=config,
                                                                                   geo_locator=geo_locator,
                                                                                   geo_locations=geo_locations,
                                                                                   home_location=home_location)
    logger.debug('Number of postings from Myticas: {}'.format(num_imported_from_myticas))


def get_list_of_ids_not_in_db(posting_ids, source):
    if len(posting_ids):
        try:
            jobsearch.models.TemporaryId.objects.all().delete()
            id_objs = [jobsearch.models.TemporaryId(id=posting_id) for posting_id in posting_ids]
            jobsearch.models.TemporaryId.objects.bulk_create(id_objs)
            response = jobsearch.models.TemporaryId.objects.raw(
                ("SELECT jobsearch_TemporaryId.* FROM jobsearch_TemporaryId LEFT JOIN jobsearch_JobPostings ON "
                 "jobsearch_TemporaryId.Id = jobsearch_JobPostings.Id and jobsearch_JobPostings.source = %s WHERE "
                 "jobsearch_JobPostings.Id IS NULL;"), [source])
            new_uids = [row.id for row in response]
            jobsearch.models.TemporaryId.objects.all().delete()
            return new_uids
        except Exception as exc:
            logger.warning('Exception {} occurred while trying to get list of ids not in db from {} for source {}. '
                           'Not filtering any.'.format(exc, posting_ids, source))
            return posting_ids
    else:
        return []