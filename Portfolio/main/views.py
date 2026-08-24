from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from .form import EmailForm
import requests
from django.conf import settings


def index(request):
    return render(request, 'main/index.html')


def email_contact(request):
    if request.method == 'POST':
        form = EmailForm(request.POST, request.FILES)

        if form.is_valid():
            full_name = form.cleaned_data['fullName']
            company_name = form.cleaned_data['companyName']
            user_email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            sms = form.cleaned_data['sms']
            attachments = request.FILES.getlist('attachments')

            if len(attachments) > 5:
                messages.error(request, "You can upload a max of 5 files!")
                return redirect('index')


            message = f"""
                Name: {full_name}
                Company: {company_name}
                Email: {user_email}
                
                Message:
                {sms}
            """

            email_message = EmailMessage(
                subject=subject,
                body=message,
                to=['semnik280997@gmail.com'],
                reply_to=[user_email],
            )

            for attachment in attachments:
                email_message.attach(
                    attachment.name,
                    attachment.read(),
                    attachment.content_type
                )

            email_message.send()

            telegram_message = f"""📩 New message from website

            Name: {full_name}
            Company: {company_name}
            Email: {user_email}

            Subject: {subject}

            Message:
            {sms}
            """

            send_telegram_message(telegram_message)

            messages.success(request, "Email sent successfully!")

            return redirect('index')

    return redirect('index')

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": text,
    }

    response = requests.post(url, data=data, timeout=10)
    response.raise_for_status()