import logging

import geopy

import jobsearch.scraping

logger = logging.getLogger(__name__)


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
        home_location = jobsearch.scraping.get_geo_location(geo_locator, home_location_str)

    logger.warning('SI Systems job scraping has nt been implemented yet!')
    return 0
