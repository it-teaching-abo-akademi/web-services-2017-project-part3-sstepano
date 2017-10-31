from django import forms
from assign4_stepanovicApp.pyoxr import OXRClient
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
#from assign4_stepanovicApp.models import MyUser




class createAuction(forms.Form):
    title = forms.CharField()
    description = forms.CharField(widget=forms.Textarea())
    minimum_price = forms.FloatField(help_text="EUR")
    deadline = forms.DateTimeField(widget=forms.DateTimeInput(format='%d-%m-%Y-%H:%M:%S', attrs={'placeholder': 'dd-mm-yyyy-hh:mm:ss'}), input_formats=['%d-%m-%Y-%H:%M:%S'])

class confirmAuction(forms.Form):
    CHOICES = [(x, x) for x in ("Yes", "No")]
    option = forms.ChoiceField(choices=CHOICES, label="Are you sure to create the auction")

def fetchRates():
    oxr_cli = OXRClient(app_id="29cc26b7eb844f14bc53c96a7a2843c8")
    result = oxr_cli.get_latest()
    rates = result["rates"]
    return rates

class currencyExchangeRate(forms.Form):
    rates = fetchRates()
    keys = rates.keys()
    CHOICES = [(x, x) for x in keys]
    option = forms.ChoiceField(choices=CHOICES, label="Currency", initial="EUR")

class MyUserForm(UserCreationForm):
    email = forms.EmailField(max_length=200, help_text='Required')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

