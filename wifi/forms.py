from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(label='phone_number', max_length=15)

    class Meta:
        model = User
        fields = ['phone_number','username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
    
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class ResolvePaymentForm(forms.Form):
    mpesa_code = forms.CharField(label='Mpesa Transaction Code', max_length=12, widget=forms.TextInput(attrs={'placeholder': 'eg. NDE18APSTL'}))
    phone_number = forms.CharField(label='Phone Number', max_length=13, widget=forms.TextInput(attrs={'placeholder': 'eg. 0700480980, Number used to Pay'}))

class ContactAdminForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Leave your message here...'}))

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Old Password'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'New Password'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm New Password'})

    class Meta:
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']
