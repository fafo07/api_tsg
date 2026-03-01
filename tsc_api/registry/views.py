from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from tsc_api.registry.models import (
    AdverseEvent,
    Contact,
    Country,
    FindingCatalog,
    GeneticTest,
    Manifestation,
    ManifestationFinding,
    PatientContact,
    Patient,
    System,
    Treatment,
)
from tsc_api.registry.serializers import (
    AdverseEventSerializer,
    ContactSerializer,
    CountrySerializer,
    FindingCatalogSerializer,
    GeneticTestSerializer,
    ManifestationFindingBulkItemSerializer,
    ManifestationFindingSerializer,
    ManifestationSerializer,
    PatientContactSerializer,
    PatientSerializer,
    SystemSerializer,
    TreatmentSerializer,
)


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    lookup_field = 'country_code'


class SystemViewSet(viewsets.ModelViewSet):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    lookup_field = 'system_code'


class FindingViewSet(viewsets.ModelViewSet):
    queryset = FindingCatalog.objects.all()
    serializer_class = FindingCatalogSerializer
    lookup_field = 'finding_code'
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']


class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.all().order_by('patient_id')
    serializer_class = PatientSerializer


class PatientRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    lookup_field = 'patient_id'


class PatientGeneticTestListCreateView(generics.ListCreateAPIView):
    serializer_class = GeneticTestSerializer

    def get_queryset(self):
        return GeneticTest.objects.filter(patient_id=self.kwargs['patient_id']).order_by('-test_date')

    def perform_create(self, serializer):
        serializer.save(patient_id=self.kwargs['patient_id'])


class GeneticTestDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GeneticTest.objects.all()
    serializer_class = GeneticTestSerializer
    lookup_field = 'test_id'


class PatientManifestationListCreateView(generics.ListCreateAPIView):
    serializer_class = ManifestationSerializer

    def get_queryset(self):
        return Manifestation.objects.filter(patient_id=self.kwargs['patient_id']).order_by('-evaluation_date')

    def perform_create(self, serializer):
        serializer.save(patient_id=self.kwargs['patient_id'])


class ManifestationDetailView(generics.RetrieveUpdateAPIView):
    queryset = Manifestation.objects.all()
    serializer_class = ManifestationSerializer
    lookup_field = 'manifestation_id'


class ManifestationFindingsView(APIView):
    def get(self, request, manifestation_id):
        findings = ManifestationFinding.objects.filter(manifestation_id=manifestation_id)
        return Response(ManifestationFindingSerializer(findings, many=True).data)

    def put(self, request, manifestation_id):
        manifestation = get_object_or_404(Manifestation, manifestation_id=manifestation_id)
        items = request.data.get('findings', [])
        ser = ManifestationFindingBulkItemSerializer(data=items, many=True)
        ser.is_valid(raise_exception=True)

        validated = ser.validated_data
        codes = [item['finding_code'] for item in validated]
        catalog = {f.finding_code: f for f in FindingCatalog.objects.filter(finding_code__in=codes)}

        for code in codes:
            finding = catalog.get(code)
            if finding is None:
                return Response({'detail': f'Finding {code} does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            if finding.system_id != manifestation.system_id:
                return Response({'detail': f'Finding {code} does not belong to manifestation system.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            ManifestationFinding.objects.filter(manifestation=manifestation).exclude(finding_code__in=codes).delete()
            for item in validated:
                ManifestationFinding.objects.update_or_create(
                    manifestation=manifestation,
                    finding=catalog[item['finding_code']],
                    defaults={'is_present': item['is_present']},
                )

        results = ManifestationFinding.objects.filter(manifestation=manifestation)
        return Response(ManifestationFindingSerializer(results, many=True).data)


class PatientTreatmentListView(generics.ListAPIView):
    serializer_class = TreatmentSerializer

    def get_queryset(self):
        return Treatment.objects.filter(patient_id=self.kwargs['patient_id']).order_by('-start_date')


class PatientManifestationTreatmentCreateView(generics.CreateAPIView):
    serializer_class = TreatmentSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['patient_id'] = self.kwargs['patient_id']
        context['manifestation_id'] = self.kwargs['manifestation_id']
        return context

    def perform_create(self, serializer):
        serializer.save(patient_id=self.kwargs['patient_id'])


class TreatmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    lookup_field = 'treatment_id'


class PatientAdverseEventListCreateView(generics.ListCreateAPIView):
    serializer_class = AdverseEventSerializer

    def get_queryset(self):
        return AdverseEvent.objects.filter(patient_id=self.kwargs['patient_id']).order_by('-event_date')

    def perform_create(self, serializer):
        serializer.save(patient_id=self.kwargs['patient_id'])


class AdverseEventDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AdverseEvent.objects.all()
    serializer_class = AdverseEventSerializer
    lookup_field = 'ae_id'


class ContactCreateView(generics.CreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


class ContactUpdateView(generics.UpdateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    lookup_field = 'contact_id'


class PatientContactListView(generics.ListAPIView):
    serializer_class = PatientContactSerializer

    def get_queryset(self):
        return PatientContact.objects.filter(patient_id=self.kwargs['patient_id']).select_related('contact')


class PatientContactUpsertDeleteView(APIView):
    def post(self, request, patient_id, contact_id):
        data = {**request.data, 'patient': patient_id, 'contact': contact_id}
        serializer = PatientContactSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, patient_id, contact_id):
        instance = get_object_or_404(PatientContact, patient_id=patient_id, contact_id=contact_id)
        serializer = PatientContactSerializer(instance, data={**request.data, 'patient': patient_id, 'contact': contact_id}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, patient_id, contact_id):
        instance = get_object_or_404(PatientContact, patient_id=patient_id, contact_id=contact_id)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
