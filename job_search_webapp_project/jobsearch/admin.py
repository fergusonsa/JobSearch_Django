from django.contrib import admin

import jobsearch.models


admin.site.register(jobsearch.models.Companyaliases)
admin.site.register(jobsearch.models.Jobpostings)
admin.site.register(jobsearch.models.Recruitingcompanies)