from django import forms
from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User
from core.models import CustomUser

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]
