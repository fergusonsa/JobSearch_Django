from django import forms


class DateInput(forms.DateInput):
    input_type = 'date'


class JobSearchForm(forms.Form):
    
    company = forms.CharField(label='Company Name', max_length=70, required=False)
    insertedDateStart = forms.DateField(widget=DateInput(),
                                        label='After Inserted Date',
                                        required=False)
    postedDateStart = forms.DateField(widget=DateInput(), label='After Posted Date', required=False)
    postedDateEnd = forms.DateField(widget=DateInput(), label='Before Posted Date', required=False)
    location = forms.CharField(label='Location', max_length=70, required=False)
    sort_by = forms.ChoiceField(label='Sort By', required=False,
                                choices=[('distance_from_home', 'Distance from home'),
                                         ('-company', 'Company'),
                                         ('-locale', 'Locale'),
                                         ('-posted_date', 'Date Posted'),
                                         ('-inserted_date', 'Date Scraped')])


class CompanySearchForm(forms.Form):
    company = forms.CharField(label='Company Name', max_length=70, required=False)
