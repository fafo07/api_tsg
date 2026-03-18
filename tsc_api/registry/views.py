import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView


logger = logging.getLogger(__name__)

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
    AdverseEventCreateSerializer,
    AdverseEventReadSerializer,
    AdverseEventUpdateSerializer,
    ContactCreateSerializer,
    ContactReadSerializer,
    ContactUpdateSerializer,
    CountrySerializer,
    FindingCatalogSerializer,
    GeneticTestCreateSerializer,
    GeneticTestReadSerializer,
    GeneticTestUpdateSerializer,
    ManifestationCreateSerializer,
    ManifestationFindingBulkItemSerializer,
    ManifestationFindingsReplaceSerializer,
    ManifestationFindingSerializer,
    ManifestationReadSerializer,
    ManifestationUpdateSerializer,
    PatientContactCreateSerializer,
    PatientContactCreateWithContactSerializer,
    PatientContactReadSerializer,
    PatientContactUpdateSerializer,
    PatientCreateSerializer,
    PatientReadSerializer,
    PatientUpdateSerializer,
    SystemSerializer,
    TreatmentCreateSerializer,
    TreatmentReadSerializer,
    TreatmentUpdateSerializer,
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

    def get_serializer_class(self):
        return PatientReadSerializer if self.request.method == 'GET' else PatientCreateSerializer


class PatientRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Patient.objects.all()
    lookup_field = 'patient_id'

    def get_serializer_class(self):
        return PatientReadSerializer if self.request.method == 'GET' else PatientUpdateSerializer


class PatientGeneticTestListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        return GeneticTestReadSerializer if self.request.method == 'GET' else GeneticTestCreateSerializer

    def get_queryset(self):
        return GeneticTest.objects.filter(patient_id=self.kwargs['patient_id']).order_by('-test_date')

    def perform_create(self, serializer):
        serializer.save(patient_id=self.kwargs['patient_id'])


class GeneticTestDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GeneticTest.objects.all()
    lookup_field = 'test_id'

    def get_serializer_class(self):
        return GeneticTestReadSerializer if self.request.method == 'GET' else GeneticTestUpdateSerializer


class PatientManifestationListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        return ManifestationReadSerializer if self.request.method == 'GET' else ManifestationCreateSerializer

    def get_queryset(self):
        return Manifestation.objects.filter(patient_id=self.kwargs['patient_id']).order_by('-evaluation_date')

    def perform_create(self, serializer):
        logger.debug(
            'Create manifestation payload. patient_id=%s payload=%s',
            self.kwargs['patient_id'],
            dict(self.request.data),
        )
        serializer.save(patient_id=self.kwargs['patient_id'])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        if serializer.errors:
            logger.warning(
                'Create manifestation serializer errors. patient_id=%s errors=%s payload=%s',
                kwargs.get('patient_id'),
                serializer.errors,
                dict(request.data),
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)


class ManifestationDetailView(generics.RetrieveUpdateAPIView):
    queryset = Manifestation.objects.all()
    lookup_field = 'manifestation_id'

    def get_serializer_class(self):
        return ManifestationReadSerializer if self.request.method == 'GET' else ManifestationUpdateSerializer

    def update(self, request, *args, **kwargs):
        logger.debug(
            'Update manifestation payload. manifestation_id=%s payload=%s',
            kwargs.get('manifestation_id'),
            dict(request.data),
        )
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=False)
        if serializer.errors:
            logger.warning(
                'Update manifestation serializer errors. manifestation_id=%s errors=%s payload=%s',
                kwargs.get('manifestation_id'),
                serializer.errors,
                dict(request.data),
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class ManifestationFindingsView(APIView):
    @extend_schema(responses={200: ManifestationFindingSerializer(many=True)})
    def get(self, request, manifestation_id):
        findings = ManifestationFinding.objects.filter(manifestation_id=manifestation_id)
        return Response(ManifestationFindingSerializer(findings, many=True).data)

    @extend_schema(
        request=ManifestationFindingsReplaceSerializer,
        responses={200: ManifestationFindingSerializer(many=True)},
    )
    def put(self, request, manifestation_id):
        logger.debug('PUT manifestation findings payload. manifestation_id=%s payload=%s', manifestation_id, dict(request.data))
        manifestation = get_object_or_404(Manifestation, manifestation_id=manifestation_id)
        payload_serializer = ManifestationFindingsReplaceSerializer(data=request.data)
        payload_serializer.is_valid(raise_exception=False)
        if payload_serializer.errors:
            logger.warning(
                'PUT manifestation findings payload errors. manifestation_id=%s errors=%s payload=%s',
                manifestation_id,
                payload_serializer.errors,
                dict(request.data),
            )
            return Response(payload_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        items = payload_serializer.validated_data['findings']
        ser = ManifestationFindingBulkItemSerializer(data=items, many=True)
        ser.is_valid(raise_exception=False)
        if ser.errors:
            logger.warning(
                'PUT manifestation findings serializer errors. manifestation_id=%s errors=%s payload=%s',
                manifestation_id,
                ser.errors,
                items,
            )
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        validated = ser.validated_data
        codes = [item['finding_code'] for item in validated]
        if len(codes) != len(set(codes)):
            return Response({'detail': 'Duplicate finding_code values are not allowed.'}, status=status.HTTP_400_BAD_REQUEST)
        logger.debug('Manifestation findings bulk replace requested. manifestation_id=%s codes=%s', manifestation_id, codes)
        catalog = {f.finding_code: f for f in FindingCatalog.objects.filter(finding_code__in=codes)}

        for code in codes:
            finding = catalog.get(code)
            if finding is None:
                return Response({'detail': f'Finding {code} does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            if finding.system_id != manifestation.system_id:
                return Response({'detail': f'Finding {code} does not belong to manifestation system.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            current_qs = ManifestationFinding.objects.filter(manifestation=manifestation)
            logger.debug('Manifestation findings current queryset. manifestation_id=%s current_total=%s', manifestation_id, current_qs.count())
            delete_qs = ManifestationFinding.objects.filter(manifestation=manifestation).exclude(finding_id__in=codes)
            logger.debug('Manifestation findings to delete. manifestation_id=%s delete_count=%s', manifestation_id, delete_qs.count())
            delete_qs.delete()
            created_count = 0
            updated_count = 0
            for item in validated:
                finding = catalog[item['finding_code']]
                instance = ManifestationFinding.objects.filter(manifestation=manifestation, finding=finding).first()
                if instance:
                    if instance.is_present != item['is_present']:
                        instance.is_present = item['is_present']
                        instance.save(update_fields=['is_present'])
                    updated_count += 1
                else:
                    ManifestationFinding.objects.create(
                        manifestation=manifestation,
                        finding=finding,
                        is_present=item['is_present'],
                    )
                    created_count += 1

            logger.debug(
                'Manifestation findings upsert summary. manifestation_id=%s created=%s updated=%s',
                manifestation_id,
                created_count,
                updated_count,
            )

        results = ManifestationFinding.objects.filter(manifestation=manifestation)
        return Response(ManifestationFindingSerializer(results, many=True).data)


class PatientTreatmentListView(generics.ListAPIView):
    serializer_class = TreatmentReadSerializer

    def get_queryset(self):
        return Treatment.objects.filter(patient_id=self.kwargs['patient_id']).order_by('-start_date')


class PatientManifestationTreatmentCreateView(generics.CreateAPIView):
    serializer_class = TreatmentCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['patient_id'] = self.kwargs['patient_id']
        context['manifestation_id'] = self.kwargs['manifestation_id']
        return context

    def perform_create(self, serializer):
        logger.debug(
            'Create treatment payload. patient_id=%s manifestation_id=%s payload=%s',
            self.kwargs['patient_id'],
            self.kwargs['manifestation_id'],
            dict(self.request.data),
        )
        serializer.save(patient_id=self.kwargs['patient_id'])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        if serializer.errors:
            logger.warning(
                'Create treatment serializer errors. patient_id=%s manifestation_id=%s errors=%s payload=%s',
                kwargs.get('patient_id'),
                kwargs.get('manifestation_id'),
                serializer.errors,
                dict(request.data),
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)


class TreatmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Treatment.objects.all()
    lookup_field = 'treatment_id'

    def get_serializer_class(self):
        return TreatmentReadSerializer if self.request.method == 'GET' else TreatmentUpdateSerializer

    def update(self, request, *args, **kwargs):
        logger.debug('Update treatment payload. treatment_id=%s payload=%s', kwargs.get('treatment_id'), dict(request.data))
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=False)
        if serializer.errors:
            logger.warning(
                'Update treatment serializer errors. treatment_id=%s errors=%s payload=%s',
                kwargs.get('treatment_id'),
                serializer.errors,
                dict(request.data),
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class PatientAdverseEventListCreateView(generics.ListCreateAPIView):
    def get_serializer_class(self):
        return AdverseEventReadSerializer if self.request.method == 'GET' else AdverseEventCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['patient_id'] = self.kwargs['patient_id']
        return context

    def get_queryset(self):
        return AdverseEvent.objects.filter(patient_id=self.kwargs['patient_id']).order_by('-event_date')

    def perform_create(self, serializer):
        logger.debug(
            'Create adverse event payload. patient_id=%s payload=%s',
            self.kwargs['patient_id'],
            dict(self.request.data),
        )
        serializer.save(patient_id=self.kwargs['patient_id'])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        if serializer.errors:
            logger.warning(
                'Create adverse event serializer errors. patient_id=%s errors=%s payload=%s',
                kwargs.get('patient_id'),
                serializer.errors,
                dict(request.data),
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)


class AdverseEventDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AdverseEvent.objects.all()
    lookup_field = 'ae_id'

    def get_serializer_class(self):
        return AdverseEventReadSerializer if self.request.method == 'GET' else AdverseEventUpdateSerializer

    def update(self, request, *args, **kwargs):
        logger.debug('Update adverse event payload. ae_id=%s payload=%s', kwargs.get('ae_id'), dict(request.data))
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=False)
        if serializer.errors:
            logger.warning(
                'Update adverse event serializer errors. ae_id=%s errors=%s payload=%s',
                kwargs.get('ae_id'),
                serializer.errors,
                dict(request.data),
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class ContactCreateView(generics.CreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactCreateSerializer

    def create(self, request, *args, **kwargs):
        logger.debug('Create contact payload. payload=%s', dict(request.data))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=False)
        if serializer.errors:
            logger.warning('Create contact serializer errors. errors=%s payload=%s', serializer.errors, dict(request.data))
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)


class ContactDetailView(generics.RetrieveUpdateAPIView):
    queryset = Contact.objects.all()
    lookup_field = 'contact_id'

    def get_serializer_class(self):
        return ContactReadSerializer if self.request.method == 'GET' else ContactUpdateSerializer

    def update(self, request, *args, **kwargs):
        logger.debug('Update contact payload. contact_id=%s payload=%s', kwargs.get('contact_id'), dict(request.data))
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=False)
        if serializer.errors:
            logger.warning(
                'Update contact serializer errors. contact_id=%s errors=%s payload=%s',
                kwargs.get('contact_id'),
                serializer.errors,
                dict(request.data),
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class PatientContactListCreateView(generics.ListCreateAPIView):
    serializer_class = PatientContactReadSerializer

    def get_queryset(self):
        return PatientContact.objects.filter(patient_id=self.kwargs['patient_id']).select_related('contact')

    @extend_schema(request=PatientContactCreateWithContactSerializer, responses={201: PatientContactReadSerializer})
    def post(self, request, patient_id):
        payload = PatientContactCreateWithContactSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        patient = get_object_or_404(Patient, patient_id=patient_id)

        with transaction.atomic():
            contact_serializer = ContactCreateSerializer(data={
                'full_name': payload.validated_data['full_name'],
                'relationship': payload.validated_data.get('relationship'),
                'phone': payload.validated_data.get('phone'),
                'email': payload.validated_data.get('email'),
                'address': payload.validated_data.get('address'),
                'notes': payload.validated_data.get('notes'),
            })
            contact_serializer.is_valid(raise_exception=True)
            contact = contact_serializer.save()
            relation_serializer = PatientContactCreateSerializer(
                data={'is_primary': payload.validated_data.get('is_primary', False)},
                context={'patient': patient, 'contact': contact},
            )
            relation_serializer.is_valid(raise_exception=True)
            relation = relation_serializer.save()

        return Response(PatientContactReadSerializer(relation).data, status=status.HTTP_201_CREATED)


class PatientContactUpsertDeleteView(APIView):
    @extend_schema(request=PatientContactCreateSerializer, responses={201: PatientContactReadSerializer})
    def post(self, request, patient_id, contact_id):
        patient = get_object_or_404(Patient, patient_id=patient_id)
        contact = get_object_or_404(Contact, contact_id=contact_id)
        serializer = PatientContactCreateSerializer(data=request.data, context={'patient': patient, 'contact': contact})
        serializer.is_valid(raise_exception=True)
        relation = serializer.save()
        return Response(PatientContactReadSerializer(relation).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=PatientContactUpdateSerializer, responses={200: PatientContactReadSerializer})
    def put(self, request, patient_id, contact_id):
        logger.debug(
            'Update patient contact relation payload. patient_id=%s contact_id=%s payload=%s',
            patient_id,
            contact_id,
            dict(request.data),
        )
        instance = get_object_or_404(PatientContact, patient_id=patient_id, contact_id=contact_id)
        serializer = PatientContactUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=False)
        if serializer.errors:
            logger.warning(
                'Update patient contact relation serializer errors. patient_id=%s contact_id=%s errors=%s payload=%s',
                patient_id,
                contact_id,
                serializer.errors,
                dict(request.data),
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        updated = serializer.save()
        return Response(PatientContactReadSerializer(updated).data)

    def patch(self, request, patient_id, contact_id):
        return self.put(request, patient_id, contact_id)

    @extend_schema(responses={204: None})
    def delete(self, request, patient_id, contact_id):
        instance = get_object_or_404(PatientContact, patient_id=patient_id, contact_id=contact_id)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
