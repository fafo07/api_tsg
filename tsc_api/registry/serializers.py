from django.db import transaction
from django.utils import timezone
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


class PatientReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'


class PatientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ('full_name', 'date_of_birth', 'country', 'family_history', 'diagnosis_date')

    def create(self, validated_data):
        validated_data.setdefault('created_at', timezone.now())
        return super().create(validated_data)


class PatientUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ('full_name', 'date_of_birth', 'country', 'family_history', 'diagnosis_date')
        extra_kwargs = {field: {'required': False} for field in fields}


class GeneticTestReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneticTest
        fields = '__all__'


class GeneticTestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneticTest
        fields = ('test_date', 'gene', 'variant', 'lab_name', 'notes')


class GeneticTestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneticTest
        fields = ('test_date', 'gene', 'variant', 'lab_name', 'notes')
        extra_kwargs = {field: {'required': False} for field in fields}


class ManifestationReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manifestation
        fields = '__all__'


class ManifestationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manifestation
        fields = ('system', 'evaluation_date', 'notes')


class ManifestationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manifestation
        fields = ('system', 'evaluation_date', 'notes')
        extra_kwargs = {field: {'required': False} for field in fields}


class ManifestationFindingSerializer(serializers.ModelSerializer):
    finding_code = serializers.CharField(source='finding_id', read_only=True)

    class Meta:
        model = ManifestationFinding
        fields = ('manifestation', 'finding', 'finding_code', 'is_present')


class TreatmentReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
        fields = '__all__'


class TreatmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
        fields = ('medication', 'dose', 'indication', 'start_date', 'end_date', 'status', 'notes')

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({'end_date': 'end_date must be greater than or equal to start_date.'})

        patient_id = self.context.get('patient_id')
        manifestation_id = self.context.get('manifestation_id')
        if not manifestation_id:
            raise serializers.ValidationError({'manifestation_id': 'manifestation_id is required by route.'})

        try:
            manifestation = Manifestation.objects.get(manifestation_id=manifestation_id)
        except Manifestation.DoesNotExist as exc:
            raise serializers.ValidationError({'manifestation_id': 'Manifestation not found.'}) from exc

        if patient_id and manifestation.patient_id != patient_id:
            raise serializers.ValidationError({'manifestation_id': 'Manifestation must belong to the same patient.'})

        attrs['manifestation'] = manifestation
        return attrs


class TreatmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
        fields = ('medication', 'dose', 'indication', 'start_date', 'end_date', 'status', 'notes')
        extra_kwargs = {field: {'required': False} for field in fields}

    def validate(self, attrs):
        start_date = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({'end_date': 'end_date must be greater than or equal to start_date.'})
        return attrs


class AdverseEventReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdverseEvent
        fields = '__all__'


class AdverseEventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdverseEvent
        fields = ('event_date', 'event_name', 'severity', 'action_taken', 'notes', 'treatment')

    def validate(self, attrs):
        patient_id = self.context.get('patient_id')
        treatment = attrs.get('treatment')
        if treatment is not None and patient_id and treatment.patient_id != patient_id:
            raise serializers.ValidationError({'treatment': 'Treatment must belong to the same patient.'})
        return attrs


class AdverseEventUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdverseEvent
        fields = ('event_date', 'event_name', 'severity', 'action_taken', 'notes', 'treatment')
        extra_kwargs = {field: {'required': False} for field in fields}

    def validate(self, attrs):
        treatment = attrs.get('treatment', getattr(self.instance, 'treatment', None))
        patient = getattr(self.instance, 'patient', None)
        if treatment is not None and patient and treatment.patient_id != patient.patient_id:
            raise serializers.ValidationError({'treatment': 'Treatment must belong to the same patient.'})
        return attrs


class ContactReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


class ContactCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('full_name', 'relationship', 'phone', 'email', 'address', 'notes')

    def create(self, validated_data):
        validated_data.setdefault('created_at', timezone.now())
        return super().create(validated_data)


class ContactUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('full_name', 'relationship', 'phone', 'email', 'address', 'notes')
        extra_kwargs = {field: {'required': False} for field in fields}


class PatientContactReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientContact
        fields = ('patient', 'contact', 'is_primary')


class PatientContactCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientContact
        fields = ('patient', 'contact', 'is_primary')
        extra_kwargs = {
            'patient': {'required': False, 'write_only': True},
            'contact': {'required': False, 'write_only': True},
        }

    def create(self, validated_data):
        validated_data.pop('patient', None)
        validated_data.pop('contact', None)
        patient = self.context['patient']
        contact = self.context['contact']
        with transaction.atomic():
            if PatientContact.objects.filter(patient=patient, contact=contact).exists():
                raise serializers.ValidationError({'non_field_errors': ['Patient/contact relation already exists.']})
            if validated_data.get('is_primary'):
                PatientContact.objects.filter(patient=patient).update(is_primary=False)
            return PatientContact.objects.create(patient=patient, contact=contact, **validated_data)


class PatientContactUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientContact
        fields = ('patient', 'contact', 'is_primary')
        extra_kwargs = {
            'patient': {'required': False, 'write_only': True},
            'contact': {'required': False, 'write_only': True},
            'is_primary': {'required': False},
        }

    def update(self, instance, validated_data):
        validated_data.pop('patient', None)
        validated_data.pop('contact', None)
        with transaction.atomic():
            if validated_data.get('is_primary'):
                PatientContact.objects.filter(patient=instance.patient).exclude(contact=instance.contact).update(is_primary=False)
            is_primary = validated_data.get('is_primary', instance.is_primary)
            PatientContact.objects.filter(patient_id=instance.patient_id, contact_id=instance.contact_id).update(is_primary=is_primary)
            instance.is_primary = is_primary
            return instance


class PatientContactCreateWithContactSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    relationship = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    address = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_primary = serializers.BooleanField(default=False)


class ManifestationFindingBulkItemSerializer(serializers.Serializer):
    finding_code = serializers.CharField()
    is_present = serializers.BooleanField()


class ManifestationFindingsReplaceSerializer(serializers.Serializer):
    findings = ManifestationFindingBulkItemSerializer(many=True, required=True)
