import jobsearch.scraping
import apscheduler.jobstores.sqlalchemy
import apscheduler.schedulers.background


def start():
    config = jobsearch.scraping.get_configuration()
    value = config.get("scheduler").get("posting_frequency_check_value")
    job_store = apscheduler.jobstores.sqlalchemy.SQLAlchemyJobStore(url='sqlite:///jobstore.sqlite')
    scheduler = apscheduler.schedulers.background.BackgroundScheduler(job_store=job_store)

    # scheduler.add_job(jobsearch.scraping.daily_get_all_new_postings, 'cron', hour="*")
    scheduler.add_job(jobsearch.scraping.daily_get_all_new_postings, 'cron', minute=value)
    scheduler.start()
    scheduler.print_jobs()

    # jobs = scheduler.get_jobs()
    # for job in jobs:
    #     logging.info("Scheduled job: {} {} {}".format(job.id, ))
