from django.apps import AppConfig


class JobsearchConfig(AppConfig):
    name = 'jobsearch'

    def ready(self):

        # Check to see if configuration file is available
        from python_miscelaneous import configuration
        import pathlib
        config = configuration.get_configuration('jobSearch_config',
                                                 location_path=pathlib.Path('~/jobSearch'),
                                                 config_type=configuration.CONFIGURATION_TYPE_JSON)
        if not config:
            pass
