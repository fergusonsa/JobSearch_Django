from django import forms

class JobSearchForm(forms.Form):
    
    company = forms.CharField(label='Company Name', max_length=70, required=False)
    insertedDateStart = forms.DateField(widget=forms.SelectDateWidget(),label='After Inserted Date', required=False)
    postedDateStart = forms.DateField(widget=forms.SelectDateWidget(), label='After Posted Date', required=False)
    postedDateEnd = forms.DateField(widget=forms.SelectDateWidget(),label='Before Posted Date', required=False)
    location = forms.CharField(label='Location', max_length=70, required=False)
    sort_by = forms.ChoiceField(label='Sort By', required=False,
                                choices=[('distance_from_home', 'Distance from home'),
                                         ('-company', 'Company'),
                                         ('-locale', 'Locale'),
                                         ('-posteddate', 'Date Posted'),
                                         ('-inserteddate', 'Date Scraped')])
    
class CompanySearchForm(forms.Form):
    company = forms.CharField(label='Company Name', max_length=70, required=False)

