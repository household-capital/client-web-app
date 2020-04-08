# Python Imports
import os
import csv
from datetime import datetime
from urllib.request import urlopen

# Django Imports
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import UpdateView, ListView, TemplateView, View, CreateView

# Local Application Imports
from apps.lib.api_LinkedIn import LinkedInParser
from apps.lib.site_Utilities import HouseholdLoginRequiredMixin
from .models import Organisation, OrganisationType, Contact
from .forms import ContactDetailsForm, OrganisationDetailsForm



class ContactListView(HouseholdLoginRequiredMixin, ListView):
    paginate_by = 50
    template_name = 'relationship/contactList.html'
    context_object_name = 'object_list'
    model = Contact

    classificationList=['2','4','6','100']

    def get_queryset(self, **kwargs):
        # overrides queryset to filter search parameter
        queryset = super(ContactListView, self).get_queryset().order_by('org__orgType',"org__Name",'surname')

        if self.request.GET.get('filter') in self.classificationList:
            if int(self.request.GET.get('filter'))<7:
                queryset = queryset.filter(classification=int(self.request.GET.get('filter')))
            else:
                queryset = queryset.filter(classification__gte=7)

        if self.request.GET.get('filter')=='Recent':
            queryset=queryset.order_by('-updated')

        if self.request.GET.get('filter') == 'SeriesB':

            queryset = queryset.exclude(equityStatus=4).exclude(equityStatus__isnull=True).order_by("org__orgName")


        if self.request.GET.get('search'):
            search = self.request.GET.get('search')
            queryset = queryset.filter(
                Q(firstName__icontains=search) |
                Q(surname__icontains=search) |
                Q(notes__icontains=search) |
                Q(relationshipNotes__icontains=search) |
                Q(org__orgName__icontains=search) |
                Q(org__orgType__orgType__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ContactListView, self).get_context_data(**kwargs)
        context['title'] = 'Contact List'
        context['hideNavbar'] = True

        if self.request.GET.get('search'):
            context['search'] = self.request.GET.get('search')
        else:
            context['search'] = ""

        return context


# Contact Detail View
class ContactDetailView(HouseholdLoginRequiredMixin, UpdateView):
    template_name = "relationship/contactDetail.html"
    form_class = ContactDetailsForm
    model = Contact

    def get_object(self, queryset=None):
        if "contId" in self.kwargs:
            queryset = Contact.objects.filter(contId=self.kwargs['contId'])
            obj = queryset.get()
            return obj

    def get_context_data(self, **kwargs):
        context = super(ContactDetailView, self).get_context_data(**kwargs)
        context['title'] = 'Contact'
        context['hideNavbar']=True

        if "contId" in self.kwargs:
            obj = self.get_object()
            context['isUpdate'] = True
            context['obj']=obj
        return context

    def form_valid(self, form):

        contactDict = form.cleaned_data
        obj = form.save()
        obj.user=self.request.user
        if form.cleaned_data['relationshipOwners']:
            obj.relationshipOwners = form.cleaned_data['relationshipOwners'].replace(" ","/",).replace("-","/").replace(",","/")
        obj.save()

        getData=False
        if obj.inProfileUrl:
            if obj.inDate:
                if (datetime.date(timezone.now()) - obj.inDate).days>90:
                    getData=True
            else:
                getData = True

        if getData:
            linkedInData=self.getLinkedInData(obj.inProfileUrl)
            if linkedInData:
                obj.inName = linkedInData['name']
                obj.inDescription = linkedInData['title']

                filename = obj.firstName + obj.surname + ".jpeg"
                file_obj = open(settings.MEDIA_ROOT + '/relationshipImages/' + filename, 'wb')
                if linkedInData['picUrl']:
                    file_obj.write(urlopen(linkedInData['picUrl']).read())
                    obj.inPic = settings.MEDIA_URL + '/relationshipImages/' + filename

                file_obj.close()
                obj.inDate = datetime.strftime(timezone.now(), "%Y-%m-%d")
                obj.save()

        messages.success(self.request, "Contact Upated")

        return HttpResponseRedirect(reverse_lazy('relationship:contactDetail', kwargs={'contId': str(obj.contId)}))

    def getLinkedInData(self,profileUrl):
        username = os.getenv("LINKEDIN_USERNAME")
        password = os.getenv("LINKEDIN_PASSWORD")
        parser = LinkedInParser(username, password)
        return parser.retrieveData(profileUrl)


# Enquiry Delete View (Delete View)
class ContactDelete(HouseholdLoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        if "contId" in kwargs:
            Contact.objects.filter(contId=self.kwargs['contId']).delete()
            messages.success(self.request, "Contact deleted")

        return HttpResponseRedirect(reverse_lazy('relationship:contactList'))


# Organisation Create View
class OrganisationCreateView(HouseholdLoginRequiredMixin, CreateView):
    template_name = "relationship/organisationDetail.html"
    form_class = OrganisationDetailsForm
    model = Organisation


    def get_context_data(self, **kwargs):
        context = super(OrganisationCreateView, self).get_context_data(**kwargs)
        context['title'] = 'New Organisation'
        context['hideNavbar'] = True

        return context

    def form_valid(self, form):

        contactDict = form.cleaned_data
        obj = form.save(commit=False)
        obj.user=self.request.user
        obj.save()
        messages.success(self.request, "Organisation Created")

        return HttpResponseRedirect(reverse_lazy('relationship:contactList'))


class ExportCSV(HouseholdLoginRequiredMixin,ListView):

    def get(self, request, *args, **kwargs):

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="RelationshipExtract.csv"'

        writer = csv.writer(response)
        writer.writerow(['Firstname', 'Surname', 'Owner', 'OrgName', 'OrgType', 'Role', 'Location','Classification','Email','ContactNotes','RelationshipNotes','SeriesBStatus','SeriesBRequests'])

        qs=Contact.objects.all()

        for contact in qs:

            row=[]
            row.append(contact.firstName)
            row.append(contact.surname)
            row.append(contact.relationshipOwners)
            row.append(contact.org.orgName)
            row.append(contact.org.orgType.orgType)
            row.append(contact.role)
            row.append(contact.enumLocation)
            row.append(contact.enumClassification)
            row.append(contact.email)
            row.append(contact.notes)
            row.append(contact.relationshipNotes)
            row.append(contact.enumEquityStatus)
            row.append(contact.requestNotes)
            writer.writerow(row)

        return response


class ExportStatusCSV(HouseholdLoginRequiredMixin,ListView):

    def get(self, request, *args, **kwargs):

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="RelationshipExtract.csv"'

        writer = csv.writer(response)
        writer.writerow(['Firstname', 'Surname', 'Owner', 'OrgName', 'OrgType', 'Role', 'Location','Classification','Email','ContactNotes','RelationshipNotes','SeriesBStatus', 'SeriesBRequests'])

        qs=Contact.objects.exclude(equityStatus=4).exclude(equityStatus__isnull=True).order_by("org__orgName")
        for contact in qs:

            row=[]
            row.append(contact.firstName)
            row.append(contact.surname)
            row.append(contact.relationshipOwners)
            row.append(contact.org.orgName)
            row.append(contact.org.orgType.orgType)
            row.append(contact.role)
            row.append(contact.enumLocation)
            row.append(contact.enumClassification)
            row.append(contact.email)
            row.append(contact.notes)
            row.append(contact.relationshipNotes)
            row.append(contact.enumEquityStatus)
            row.append(contact.requestNotes)
            writer.writerow(row)

        return response