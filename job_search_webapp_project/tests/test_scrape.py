import logging
import os

from django.test import TestCase

import geopy
import requests

import jobsearch.scrapeJobPostings
import jobsearch.models as models

logger = logging.getLogger(__name__)


class ScapeJobPostingsTestCase(TestCase):
    pass
    # def setup(self):
    #     log_formatter = logging.Formatter(
    #         "%(asctime)s %(levelname)-5.5s %(module)-10.10s %(funcName)-10.10s  %(message)s")
    #     root_logger = logging.getLogger()
    #     root_logger.setLevel(logging.DEBUG)
    #
    #     console_handler = logging.StreamHandler()
    #     console_handler.setLevel(logging.DEBUG)
    #     console_handler.setFormatter(log_formatter)
    #     root_logger.addHandler(console_handler)
    #     root_logger.disable(logging.NOTSET)

    # def test_login(self):
    #     session = requests.Session()
    #     job_site_details = jobsearch.scrapeJobPostings.job_site_details
    #     indeed_site_details = job_site_details['ca.indeed.com']
    #     jobsearch.scrapeJobPostings.login_to_web_site(session, indeed_site_details)
    #     self.assertEqual(True, True)

    # def test_parse_html(self):
    #     job_site_details = jobsearch.scrapeJobPostings.job_site_details
    #     indeed_site_details = job_site_details['ca.indeed.com']
    #     search_terms_list = ['java', 'devops', 'python', ]
    #     geo_locator = geopy.geocoders.Nominatim()
    #     home_location_str = '1695 Playfair Drive, Ottawa, ON, Canada'
    #     home_location = jobsearch.scrapeJobPostings.get_geo_location(geo_locator, home_location_str)
    #     geo_locations = {}
    #     aliases = models.CompanyAliases.objects.all()
    #
    #     data_file_path = './tests/test_data/indeed_java_or_python_pg1.html'
    #     self.assertTrue(os.path.isfile(data_file_path), 'Cannot find test data file {}'.format(data_file_path))
    #     with open(data_file_path) as data_file:
    #         page_source = data_file.read()
    #
    #         postings_list, num_postings_on_page, init_total_num_postings = jobsearch.scrapeJobPostings.parse_html_page(
    #             page_source, indeed_site_details, aliases, geo_locator,
    #             home_location, geo_locations, search_terms_list, False)
    #         logger.info('# postings_list {}, num_postings_on_page {}, init_total_num_postings: {}'.format(
    #             len(postings_list), num_postings_on_page, init_total_num_postings))
    #         self.assertIsNotNone(postings_list)
    #         self.assertIsNotNone(num_postings_on_page)
    #         self.assertIsNotNone(init_total_num_postings)
    #

    # def test_indeed_api(self):
    #     # search_terms_list = ['java', 'devops', 'python', ]
    #     jobsearch.scrapeJobPostings.get_indeed_postings()
    #     self.assertTrue(True)

    # def test_config(self):
    #     import python_miscelaneous.configuration
    #     import pathlib
    #     location_path = pathlib.Path('~/JobSearch')
    #
    #     config = python_miscelaneous.configuration.get_configuration(
    #         'jobSearch_config',
    #         location_path,
    #         python_miscelaneous.configuration.CONFIGURATION_TYPE_JSON)
    #
    #     expected_config = {
    #         'indeed_publisher': 'xxxxx',
    #         'home_location': '1695 Playfair Drive, Ottawa, ON, Canada',
    #     }
    #     self.assertDictEqual(expected_config, config)

    def test_distance_calculations(self):
        geo_locator = geopy.geocoders.Nominatim(user_agent="JobSearch")

        home_location_str = '1695 Playfair Drive, Ottawa, Ontario, Canada'
        home_location = jobsearch.scrapeJobPostings.get_geo_location(geo_locator, home_location_str)
        logger.info('Location for "{}": {}'.format(home_location_str, home_location))
        for locale in ['Ottawa, Ontario', 'Orleans, Ontario', 'Kanata, Ontario', 'Kanata, Ottawa, Ontario',
                       'Toronto, Ontario', 'Gatineau, Quebec']:
            geo_location = jobsearch.scrapeJobPostings.get_geo_location(geo_locator, locale)
            logger.info('Location for "{}": {}'.format(locale, geo_location))
            dist = round(geopy.distance.distance(home_location.point, geo_location.point).km, 0)
            logger.info('distance from {} to {}: {}'.format(home_location_str, locale, dist))
            self.assertGreaterEqual(dist, 0.0)
