from django import forms

class JobSearchForm(forms.Form):
    company = forms.CharField(label='Company Name', max_length=70, required=False)
    postedDateStart = forms.DateField(label='Start Date ', required=False)
    postedDateEnd = forms.DateField(label='End Date ', required=False)
    location = forms.CharField(label='Location', max_length=70, required=False)
    
class CompanySearchForm(forms.Form):
    company = forms.CharField(label='Company Name', max_length=70, required=False)

