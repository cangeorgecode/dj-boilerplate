from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, get_user_model, authenticate, login
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from core.models import CustomUser, Subscription
import stripe
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import update_session_auth_hash
import logging
from dotenv import load_dotenv
import os

load_dotenv()

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'core/index.html')

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'You have successfully registered! Please login below')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'registration/registration.html', {'form': form})

def check_username(request):
    username = request.GET.get('username')
    if get_user_model().objects.filter(username=username).exists():
        return HttpResponse('<span class="text-red-500">Username taken</span>', status=200)
    return HttpResponse('<span class="text-green-500">Username available</span>', status=200)

@login_required
def profile(request):
    user = request.user
    try:
        subscription = Subscription.objects.get(user=user)
        stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
        plan = subscription.plan
        billing_cycle = subscription.billing_cycle
        next_payment_date = stripe_subscription.current_period_end
        has_subscription = True
    except Subscription.DoesNotExist:
        plan = None
        billing_cycle = None
        next_payment_date = None
        has_subscription = False
    except stripe.error.StripeError as e:
        plan = None
        billing_cycle = None
        next_payment_date = None
        has_subscription = None

    context = {
        'plan': plan,
        'billing_cycle': billing_cycle,
        'next_payment_date': next_payment_date,
        'has_subscription': has_subscription,
    }
    return render(request, 'core/profile.html', context)

def custom_logout(request):
    logout(request)
    messages.success(request, 'Bye')
    return redirect('index')

def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data['email']
            associated_users = CustomUser.objects.filter(email=data)
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "registration/password_reset_email.html"
                    context = {
                        "email": user.email,
                        'domain': request.get_host(),
                        'site_name': 'Your Site Name',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    email = render_to_string(email_template_name, context)
                    try:
                        send_mail(subject, email, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)
                        print(f"Email sent to {user.email}")
                    except Exception as e:
                        return render(request, 'registration/password_reset_done.html', {'error': str(e)})
                return redirect("password_reset_done")
    else:
        form = PasswordResetForm()
    return render(request, "registration/password_reset_form.html", {"form": form})

def password_reset_done(request):
    return render(request, 'registration/password_reset_done.html')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password has been set. You may go ahead and log in now.")
                return redirect('login')
        else:
            form = SetPasswordForm(user)
        return render(request, 'registration/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'Password reset link is invalid, possibly because it has already been used. Please request a new password reset.')
        return redirect('password_reset')

def password_reset_complete(request):
    return render(request, 'registration/password_reset_complete.html')

# ///// Stripe Checkout /////

@login_required
def create_checkout_session(request):
    user = request.user
    plan = request.GET.get('plan')  # e.g., 'basic_monthly', 'premium_annually'
    billing_cycle = request.GET.get('billing_cycle')  # e.g., 'monthly', 'annually'

    # Map plans to Stripe Price IDs
    price_ids = {
        'hobbyist_yearly': os.getenv('HOBBYIST_YEARLY'), # Input your own price_id from Stripe
        'pro_lifetime': os.getenv('PRO_LIFETIME'), # Input your own price_id from Stripe
    }

    price_id = price_ids.get(f'{plan}_{billing_cycle}')
    if not price_id:
        return render(request, 'core/error.html', {'message': 'Invalid plan or billing cycle'})

    # Determine the mode based on the billing cycle
    mode = 'subscription' if billing_cycle != 'lifetime' else 'payment'

    # Create a stripe checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode=mode,
        success_url=f'{settings.BASE_URL}/success/',
        cancel_url=f'{settings.BASE_URL}/cancel/',
        customer_email=user.email,
        client_reference_id=user.id,  # Pass the user ID to the webhook
        metadata={
            'plan': plan,
            'billing_cycle': billing_cycle,
        },
    )

    return redirect(session.url, code=303)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error("Invalid payload: %s", e)
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error("Invalid signature: %s", e)
        return HttpResponse(status=400)

    logger.info(f"Webhook received: {event.type}")

    if event.type == 'checkout.session.completed':
        session = event.data.object
        user_id = session.client_reference_id
        plan = session.metadata.plan  # Pass the plan as metadata from the checkout session
        billing_cycle = session.metadata.billing_cycle  # Pass the billing cycle as metadata from the checkout session

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            logger.error(f"User with ID {user_id} does not exist")
            return HttpResponse(status=400)

        try:
            subscription = Subscription.objects.get(user=user)
            # Update the existing subscription with the new plan and billing cycle
            subscription.plan = plan
            subscription.billing_cycle = billing_cycle
            subscription.is_lifetime = (billing_cycle == 'lifetime')
            subscription.save()
        except Subscription.DoesNotExist:
            # Create a new subscription
            customer = stripe.Customer.create(email=user.email)
            subscription = Subscription.objects.create(
                user=user,
                stripe_customer_id=customer.id,
                plan=plan,
                billing_cycle=billing_cycle,
                is_lifetime=(billing_cycle == 'lifetime')
            )

        if session.mode == 'subscription':
            stripe_subscription_id = session.subscription
            subscription.stripe_subscription_id = stripe_subscription_id
            subscription.save()
            logger.info(f"Subscription ID {stripe_subscription_id} saved for user {user.username}")
        else:
            logger.info(f"No subscription ID for user {user.username}")

    # ... (rest of the webhook handling remains the same)

    return HttpResponse(status=200)

def success(request):
    return render(request, 'core/success.html')

def cancel(request):
    return render(request, 'core/cancel.html')

def subscribe(request):
    return render(request, 'core/subscribe.html')

# Update billing information on Stripe

@login_required
def stripe_billing_portal(request):
    user = request.user
    subscription = Subscription.objects.get(user=user)
    customer_id = subscription.stripe_customer_id

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=request.build_absolute_uri('/accounts/profile/'),  # URL to redirect after updating billing info
    )
    return redirect(session.url)

# Password update

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            return redirect('password_change_done')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/password_change_form.html', {'form': form})

def password_change_done(request):
    return render(request, 'registration/password_change_done.html')

@login_required
def receipt(request):
    user = request.user
    try:
        subscription = Subscription.objects.get(user=user)
        logger.info(f"Subscription found for user {user.username}: {subscription.stripe_subscription_id}")
        # Retrieving customer using email
        customers = stripe.Customer.list(email=user.email)
        logger.info(f"Customers matching email {user.email}: {customers.data}")
        if customers.data:
            customer_id = customers.data[0].id
            invoices = stripe.Invoice.list(customer=customer_id, limit=1)
            logger.info(f"Invoices for user {user.username}: {invoices.data}")
            if invoices.data:
                invoice = invoices.data[0]
                receipt_url = invoice.hosted_invoice_url
                logger.info(f"Retrieved invoice data: {invoice}")
                if receipt_url:
                    logger.info(f"Receipt URL for user {user.username}: {receipt_url}")
                    return redirect(receipt_url)
                else:
                    logger.error(f"No hosted invoice URL found for user {user.username}")
                    return render(request, 'core/error.html', {'message': 'No hosted invoice URL found for your subscription.'})
            else:
                logger.error(f"No invoices found for user {user.username}")
                return render(request, 'core/error.html', {'message': 'No invoices found for your subscription.'})
        else:
            logger.error(f"No customers found with email {user.email}")
            return render(request, 'core/error.html', {'message': 'No customers found with your email.'})
    except Subscription.DoesNotExist:
        logger.error(f"Subscription for user {user.username} does not exist")
        return render(request, 'core/error.html', {'message': 'You are not subscribed to any plan.'})
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error for user {user.username}: {str(e)}")
        return render(request, 'core/error.html', {'message': str(e)})
    
# Upgrade subscription for yearly subscribed users
@login_required()
def upgrade_subscription(request):
    user = request.user
    try:
        subscription = Subscription.objects.get(user=user)
        if subscription.billing_cycle != 'yearly':
            return render(request, 'core/error.html', {'message': 'You are not eligible to upgrade.'})

        # Define the price ID for lifetime access
        lifetime_price_id = 'price_1QBoq4Hew8paPTildt62U0Wx'  # Replace with your actual price ID

        # Create a stripe checkout session for the upgrade
        session = stripe.checkout.Session.create(
            customer=subscription.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': lifetime_price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),
            cancel_url=request.build_absolute_uri('/cancel/'),
        )

        return redirect(session.url, code=303)
    except Subscription.DoesNotExist:
        return render(request, 'core/error.html', {'message': 'You are not subscribed to any plan.'})
    except stripe.error.StripeError as e:
        return render(request, 'core/error.html', {'message': str(e)})

# Cancel subscription
@login_required()
def cancel_subscription(request):
    user = request.user
    try:
        subscription = Subscription.objects.get(user=user)
        if subscription.billing_cycle != 'yearly':
            return render(request, 'core/error.html', {'message': 'You do not have a yearly subscription to cancel.'})

        # Cancel the Stripe subscription
        stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
        stripe_subscription.cancel_at_period_end = True
        stripe_subscription.save()

        # Update the Subscription model
        subscription.stripe_subscription_id = None
        subscription.plan = None
        subscription.billing_cycle = None
        subscription.save()

        return render(request, 'core/success.html', {'message': 'Your subscription has been canceled.'})
    except Subscription.DoesNotExist:
        return render(request, 'core/error.html', {'message': 'You are not subscribed to any plan.'})
    except stripe.error.StripeError as e:
        return render(request, 'core/error.html', {'message': str(e)})