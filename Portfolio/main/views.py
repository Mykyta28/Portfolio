from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from .form import EmailForm
import requests
from django.conf import settings
from .models import Certificate, Experience, Project, Education, Resume


def index(request):
    experience_list = Experience.objects.all()
    project_list = Project.objects.all()
    certificate_list = Certificate.objects.all()
    education_list = Education.objects.all()
    resume = Resume.objects.first()
    return render(
        request,
        'main/index.html',
        {'certificate_list': certificate_list,
         'experience_list': experience_list,
         'project_list': project_list,
         'education_list': education_list,
         'resume': resume,
         })


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

            try:
                send_telegram_message(telegram_message)


                for attachment in attachments:
                    attachment.seek(0)
                    send_telegram_file(attachment)

            except Exception as e:
                print(f"Telegram error: {e}")

            messages.success(
                request,
                "Email sent successfully!"
            )

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


def send_telegram_file(file):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument"

    files = {
        "document": (
            file.name,
            file.read(),
            file.content_type
        )
    }

    data = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
    }

    response = requests.post(
        url,
        data=data,
        files=files,
        timeout=30
    )

    response.raise_for_status()