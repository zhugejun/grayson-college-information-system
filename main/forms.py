from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import models


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
            raise forms.ValidationError(msg)

        # clean passwords
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            msg = "Passwords don't match"
            raise forms.ValidationError(msg)

        # check duplicates before continue
        username = email.replace('@grayson.edu', '')
        matching_users = User.objects.filter(username=username)

        if self.instance:
            matching_users = matching_users.exclude(
                pk=self.instance.pk)
        if matching_users:
            msg = f'User {username} already exists.'
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
    
    def clean(self):
        try:
            cleaned_data = super(LoginForm, self).clean()
            return cleaned_data
        except:
            self.add_error("username", "Invalid username or password.")
            self.add_error("password", "Invalid username or password.")
