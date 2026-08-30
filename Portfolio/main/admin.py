from django.contrib import admin
from main.models import Certificate, Experience, Project, TechStack, Education, Resume


class ExperienceAdmin(admin.ModelAdmin):
    class Media:
        js = ("js/dates_admin.js",)


class TechStackInline(admin.TabularInline):
    model = TechStack
    extra = 1


class ProjectAdmin(admin.ModelAdmin):
    inlines = [TechStackInline]


admin.site.register(Certificate)
admin.site.register(Experience, ExperienceAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(TechStack)
admin.site.register(Education)
admin.site.register(Resume)


admin.site.site_title = "Admin Panel"
admin.site.site_header = "Administration Panel"
admin.site.index_title = "Welcome to Admin Panel"