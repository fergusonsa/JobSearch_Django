from django import forms

class JobSearchForm(forms.Form):
    company = forms.CharField(label='Company Name', max_length=70)
    postedDateStart = forms.DateField(label='Start Date ')
    postedDateEnd = forms.DateField(label='End Date ')
    
    
class CompanySearchForm(forms.Form):
    company = forms.CharField(label='Company Name', max_length=70)

