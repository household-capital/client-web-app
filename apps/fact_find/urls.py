#Django Imports
from django.urls import path


from . import views

app_name = 'fact_find'

urlpatterns = [
    path('<uuid:uid>', views.Main.as_view(), name='factfind'),
    path('pdfCaseSummary/<uuid:uid>', views.PdfCaseSummary.as_view(), name='pdfSummary'),
    path('generatePdf/<uuid:uid>', views.GeneratePdf.as_view(), name='generatePdf'),

]



