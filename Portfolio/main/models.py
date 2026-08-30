from django.db import models
import os
import uuid

# Certificate Model---------------
def upload_to_static(instance, filename):
    extension = os.path.splitext(filename)[1]
    filename = f"{uuid.uuid4()}{extension}"
    return os.path.join("images", filename)

def upload_pdf_to_static(instance, filename):
    extension = os.path.splitext(filename)[1]
    filename = f"{uuid.uuid4()}{extension}"
    return os.path.join("files", filename)


class Certificate(models.Model):
    image = models.ImageField("Certificate Image", upload_to="certificates/", blank=True, null=True)
    pdf = models.FileField("Certificate PDF", upload_to=upload_pdf_to_static, blank=True, null=True)
    name = models.CharField('College Name', max_length=50, default="Undefined")
    major = models.CharField('Major', max_length=50, default="Undefined")
    date = models.DateField("Date of obtaining")
    location = models.CharField('Location', max_length=50, default="Undefined")

    def __str__(self):
        return self.name
# ---------------------------Certificate Model END---------------------------------

# Experience Model-------------
class Experience(models.Model):
    company_name = models.CharField('Company Name', max_length=80, default="Undefined")
    start_date = models.DateField("Start Date")
    end_date = models.DateField("End Date", blank=True, null=True)
    is_present = models.BooleanField('Is present?', default=False)
    description = models.TextField('Description', max_length=800, default="Undefined")

    def __str__(self):
        return self.company_name
# --------------Experience Model END-------------


# Projects Model---------------------------------
class Project(models.Model):
    image = models.ImageField("Project Image", upload_to="projects/", blank=True, null=True)
    github_repo = models.URLField("Github Repo", blank=True, null=True)
    github_live = models.URLField("Github Live", blank=True, null=True)
    project_title = models.CharField('Project Title', max_length=50, default="Undefined")
    short_description = models.CharField('Short Description', max_length=100, default="Undefined")
    long_description = models.TextField('Long Description', blank=True, null=True)

    def __str__(self):
        return self.project_title

class TechStack(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tech_stack"
    )
    name = models.CharField(
        "Technology",
        max_length=50
    )

    def __str__(self):
        return self.name
# -----------------------Projects Model END--------------------------------------


# Education Model--------------------------------------
class Education(models.Model):
    image = models.ImageField("Project Image", upload_to="colleges/", blank=True, null=True)
    college_name = models.CharField('College Name', max_length=50, default="Undefined")
    major = models.CharField('Major', max_length=50, default="Undefined")
    degree = models.CharField('Degree', max_length=30, default="Undefined")
    start_date = models.DateField("Start Date")
    end_date = models.DateField("End Date", blank=True, null=True)
    is_present = models.BooleanField('Is present?', default=False)
    location = models.CharField('Location', max_length=50, default="Undefined")
    website = models.URLField("Website", blank=True, null=True)

    def __str__(self):
        return self.college_name
# -------------------------Education Model--------------------------------------


# Resume------------------------------------------
class Resume(models.Model):
    document = models.FileField("Resume Document", upload_to="resumes/")