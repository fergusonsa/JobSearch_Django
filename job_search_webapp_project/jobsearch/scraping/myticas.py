import logging
import datetime
import time
import urllib.parse

import geopy
import feedparser

import jobsearch.scraping
from jobsearch import models

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

    # logger.warning('Myticas job scraping has not been implemented yet!')

    aliases = models.CompanyAliases.objects.all()
    total_num_saved = 0
    for rss_url in config["myticas"].get("rss_feed_urls"):
        logger.debug("Getting postings from RSS feed url {}".format(rss_url))
        feed = feedparser.parse(rss_url)
        url_parts = urllib.parse.urlparse(rss_url)
        query_parts = urllib.parse.parse_qs(url_parts.query)
        search_term = query_parts.get('search_keywords', ['unknown'])[0]
        num_saved = 0
        for entry in feed.entries:
            locale = entry.get("job_listing_location")
            posting = {
                "url": entry.link,
                "locale": locale,
                "date_parsed": datetime.datetime.fromtimestamp(time.mktime(entry.published_parsed)),
                "jobtitle": entry.title,
                "jobkey": entry.title,
                "company": "Myticas",
                "description": entry.content
            }
            if jobsearch.scraping.save_posting_to_db(posting, 'myticas', search_term, aliases,
                                                     geo_locator, home_location, geo_locations):
                num_saved += 1
        logging.debug("{} postings saved from {} total postings from rss url {}".format(num_saved, len(feed.entries),
                                                                                        rss_url))
        total_num_saved = total_num_saved + num_saved
    logger.debug("Saved a total of {} postings from rss feeds for Myticas".format(total_num_saved))
    return total_num_saved
