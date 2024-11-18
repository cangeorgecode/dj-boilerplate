# Django Boilerplate
Disclaimer: The code may look like a steaming pile of dog crap, so be aware. 

# What is this?
I have always wanted to build an SaaS and make money online. I thought it would be more efficient if I could re-use some of the code for features that are common across all SaaS's. The boilerplate here consists of:

- Built-in authentication system 
- Stripe payment
- Tailwind CSS
- HTMX for async functions

# How to use?
- You need to have python and Node.js installed on your computer
- To install Node.js, go to: https://nodejs.org/en/download/package-manager
- ```git clone https://github.com/cangeorgecode/dj-boilerplate.git```
- Start your virtual environment
- cd into the directory and install requirements.txt
- ``` pip install -r requirements.txt ```

- Install and start Tailwind
``` python manage.py tailwind install```
``` python manage.py tailwind start```

- Create a superuser to access the admin panel
``` python manage.py createsuperuser ```

- In a new terminal, migrate
``` python manage.py migrate ```
``` python manage.py runserver```

# Environment variables you need:

## From your email service provider
EMAIL_HOST_USER  
EMAIL_HOST_PASSWORD

## From Stripe
STRIPE_PUBLISHABLE_KEY  
STRIPE_SECRET_KEY  
STRIPE_WEBHOOK_SECRET

## Price ID from Stripe
HOBBYIST_YEARLY  
PRO_LIFETIME

# Contact me
The best way to contact me is through X (@joji_jiji)

# License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.