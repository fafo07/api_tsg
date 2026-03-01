from django.db import transaction
from rest_framework import serializers

from tsc_api.registry.models import (
    AdverseEvent,
    Contact,
    Country,
    FindingCatalog,
    GeneticTest,
    Manifestation,
    ManifestationFinding,
    Patient,
    PatientContact,
    System,
    Treatment,
)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        fields = '__all__'


class FindingCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingCatalog
        fields = '__all__'


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'


class GeneticTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneticTest
        fields = '__all__'


class ManifestationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manifestation
        fields = '__all__'


class ManifestationFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManifestationFinding
        fields = ('manifestation', 'finding', 'is_present')


class TreatmentSerializer(serializers.ModelSerializer):
    manifestation_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Treatment
        fields = (
            'treatment_id',
            'patient',
            'manifestation',
            'manifestation_id',
            'medication',
            'dose',
            'indication',
            'start_date',
            'end_date',
            'status',
            'notes',
        )
        read_only_fields = ('manifestation',)

    def validate(self, attrs):
        manifestation_id = (
            attrs.get('manifestation_id')
            or self.context.get('manifestation_id')
            or (self.instance.manifestation_id if self.instance else None)
        )
        patient = attrs.get('patient') or getattr(self.instance, 'patient', None)

        if patient is None and self.context.get('patient_id'):
            patient = Patient.objects.filter(patient_id=self.context['patient_id']).first()

        if not manifestation_id:
            raise serializers.ValidationError({'manifestation_id': 'manifestation_id is required.'})

        try:
            manifestation = Manifestation.objects.get(manifestation_id=manifestation_id)
        except Manifestation.DoesNotExist as exc:
            raise serializers.ValidationError({'manifestation_id': 'Manifestation not found.'}) from exc

        if patient and manifestation.patient_id != patient.patient_id:
            raise serializers.ValidationError({'manifestation_id': 'Manifestation must belong to the same patient.'})

        attrs['manifestation'] = manifestation
        return attrs


class AdverseEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdverseEvent
        fields = '__all__'

    def validate(self, attrs):
        patient = attrs.get('patient') or getattr(self.instance, 'patient', None)
        treatment = attrs.get('treatment')

        if treatment is None and self.instance:
            treatment = self.instance.treatment

        if treatment is not None and patient and treatment.patient_id != patient.patient_id:
            raise serializers.ValidationError({'treatment': 'Treatment must belong to the same patient.'})

        return attrs


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


class PatientContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientContact
        fields = '__all__'

    def create(self, validated_data):
        with transaction.atomic():
            if validated_data.get('is_primary'):
                PatientContact.objects.filter(patient=validated_data['patient']).update(is_primary=False)
            return super().create(validated_data)

    def update(self, instance, validated_data):
        with transaction.atomic():
            if validated_data.get('is_primary'):
                PatientContact.objects.filter(patient=instance.patient).exclude(contact=instance.contact).update(is_primary=False)
            return super().update(instance, validated_data)


class ManifestationFindingBulkItemSerializer(serializers.Serializer):
    finding_code = serializers.CharField()
    is_present = serializers.BooleanField()
