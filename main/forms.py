from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import models

from django_select2.forms import ModelSelect2MultipleWidget

from .models import Subject, Profile


class NewUserForm(UserCreationForm):

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super(NewUserForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

            if field_name == 'email':
                field.widget.attrs['placeholder'] = 'Enter your grayson email'
                field.widget.attrs['autofocus'] = 'autofocus'
            if field_name == 'password1':
                field.widget.attrs['placeholder'] = 'Enter your password'
            if field_name == 'password2':
                field.widget.attrs['placeholder'] = 'Enter your password again'

    def save(self, commit=True):

        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email'].replace('@grayson.edu', '')
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

    def clean(self):
        cleaned_data = super(NewUserForm, self).clean()

        # clean email
        email = self.cleaned_data['email']
        if '@grayson.edu' not in email:
            msg = 'Please use your Grayson email to signup.'
            # self._errors['email'] = msg
            raise forms.ValidationError(msg)

        # clean passwords
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            msg = "Passwords don't match"
            # self._errors['password'] = msg
            raise forms.ValidationError(msg)

        # check duplicates before continue
        username = email.replace('@grayson.edu', '')
        matching_users = User.objects.filter(username=username)

        if self.instance:
            matching_users = matching_users.exclude(
                pk=self.instance.pk)
        if matching_users:
            msg = f'User {username} already exists.'
            # self._errors['duplicate'] = msg
            raise forms.ValidationError(msg)
        else:
            return cleaned_data


class LoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'

            if field_name == 'username':
                field.widget.attrs['placeholder'] = 'Enter your grayson username'
            if field_name == 'password':
                field.widget.attrs['placeholder'] = 'Enter your password'


# class ProfileForm(forms.ModelForm):

#     class Meta:
#         model = Profile
#         fields = ('subjects',)
#         widgets = {'subjects': ModelSelect2MultipleWidget(
#             queryset=Subject.objects.all(),
#             search_fields=['name__icontains'],
#         )}
