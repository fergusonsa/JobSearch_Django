
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
import django.utils.timezone

import jobsearch
from jobsearch import models
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
    '''

    :param posting: Should be a dict containing the following keys: company, jobkey, jobtitle, date, city, state, url,
    and any other descriptive keys desired
    :param source:
    :param search_term:
    :param aliases:
    :param geo_locator:
    :param home_location:
    :param geo_locations:
    :return:
    '''
    if posting.get('expired', False):
        logging.debug('Not saving expired Posting {}'.format(posting))
        return False
    if 'date_parsed' in posting:
        posted_date = posting.get('date_parsed')
    else:
        posted_date = datetime.datetime.strptime(posting.get('date'), '%a, %d %b %Y %H:%M:%S %Z')
    company_name = posting.get('company')
    if company_name and not aliases.filter(alias=company_name).exists():
        if company_name and not models.RecruitingCompanies.objects.filter(name=company_name).exists():
            new_date = django.utils.timezone.now()
            new_company = models.RecruitingCompanies.objects.create(name=company_name, date_inserted=new_date)

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

        new_company_alias = models.CompanyAliases.objects.create(company_name=company_name, alias=company_name)
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
        db_posting = models.JobPostings.objects.create(
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
        # db_posting.delete()

        logger.warning('IntegrityError %s occurred while trying to insert posting %s %s %s.' % (
            e, posting['jobkey'], posting['jobtitle'], posting.get('company')))
        return False
    except Exception as e:
        logger.error('Exception %s occurred while trying to insert posting %s %s %s.' % (
            e, posting['jobkey'], posting['jobtitle'], posting.get('company')), e)
        return False
