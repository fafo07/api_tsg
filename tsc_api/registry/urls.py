from django.urls import path
from rest_framework.routers import DefaultRouter

from tsc_api.registry.views import (
    AdverseEventDetailView,
    ContactCreateView,
    ContactDetailView,
    CountryViewSet,
    FindingViewSet,
    GeneticTestDetailView,
    ManifestationDetailView,
    ManifestationFindingsView,
    PatientAdverseEventListCreateView,
    PatientContactListCreateView,
    PatientContactUpsertDeleteView,
    PatientGeneticTestListCreateView,
    PatientListCreateView,
    PatientManifestationListCreateView,
    PatientManifestationTreatmentCreateView,
    PatientRetrieveUpdateView,
    PatientTreatmentListView,
    SystemViewSet,
    TreatmentDetailView,
)

router = DefaultRouter(trailing_slash=False)
router.register(r'countries', CountryViewSet, basename='countries')
router.register(r'systems', SystemViewSet, basename='systems')
router.register(r'findings', FindingViewSet, basename='findings')

urlpatterns = [
    path('patients', PatientListCreateView.as_view(), name='patients-list-create'),
    path('patients/<int:patient_id>', PatientRetrieveUpdateView.as_view(), name='patients-detail-update'),
    path('patients/<int:patient_id>/genetic-tests', PatientGeneticTestListCreateView.as_view(), name='patient-genetic-tests'),
    path('genetic-tests/<int:test_id>', GeneticTestDetailView.as_view(), name='genetic-test-detail'),
    path('patients/<int:patient_id>/manifestations', PatientManifestationListCreateView.as_view(), name='patient-manifestations'),
    path('manifestations/<int:manifestation_id>', ManifestationDetailView.as_view(), name='manifestation-detail'),
    path('manifestations/<int:manifestation_id>/findings', ManifestationFindingsView.as_view(), name='manifestation-findings'),
    path('patients/<int:patient_id>/treatments', PatientTreatmentListView.as_view(), name='patient-treatments'),
    path('patients/<int:patient_id>/manifestations/<int:manifestation_id>/treatments', PatientManifestationTreatmentCreateView.as_view(), name='patient-manifestation-treatment-create'),
    path('treatments/<int:treatment_id>', TreatmentDetailView.as_view(), name='treatment-detail'),
    path('patients/<int:patient_id>/adverse-events', PatientAdverseEventListCreateView.as_view(), name='patient-adverse-events'),
    path('adverse-events/<int:ae_id>', AdverseEventDetailView.as_view(), name='adverse-event-detail'),
    path('contacts', ContactCreateView.as_view(), name='contacts-post'),
    path('contacts/<int:contact_id>', ContactDetailView.as_view(), name='contacts-detail'),
    path('patients/<int:patient_id>/contacts', PatientContactListCreateView.as_view(), name='patient-contacts-list-create'),
    path('patients/<int:patient_id>/contacts/<int:contact_id>', PatientContactUpsertDeleteView.as_view(), name='patient-contacts-upsert-delete'),
]

urlpatterns += router.urls
