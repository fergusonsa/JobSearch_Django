from django.contrib import admin

import jobsearch.models


admin.site.register(jobsearch.models.CompanyAliases)
admin.site.register(jobsearch.models.JobPostings)
admin.site.register(jobsearch.models.RecruitingCompanies)