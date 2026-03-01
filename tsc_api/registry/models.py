from django.db import models


class Country(models.Model):
    country_code = models.CharField(max_length=2, primary_key=True)
    country_name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'countries'


class System(models.Model):
    system_code = models.CharField(max_length=50, primary_key=True)
    system_name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'systems'


class FindingCatalog(models.Model):
    finding_code = models.CharField(max_length=50, primary_key=True)
    system = models.ForeignKey(System, on_delete=models.DO_NOTHING, db_column='system_code', related_name='findings')
    finding_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'findings_catalog'


class Patient(models.Model):
    patient_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.DO_NOTHING, db_column='country_code', related_name='patients')
    family_history = models.TextField(blank=True, null=True)
    diagnosis_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'patients'


class GeneticTest(models.Model):
    test_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patient_id', related_name='genetic_tests')
    test_date = models.DateField(blank=True, null=True)
    gene = models.CharField(max_length=100)
    variant = models.CharField(max_length=255, blank=True, null=True)
    lab_name = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'genetic_tests'


class Manifestation(models.Model):
    manifestation_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patient_id', related_name='manifestations')
    system = models.ForeignKey(System, on_delete=models.DO_NOTHING, db_column='system_code', related_name='manifestations')
    evaluation_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'manifestations'


class ManifestationFinding(models.Model):
    pk = models.CompositePrimaryKey('manifestation', 'finding')
    manifestation = models.ForeignKey(Manifestation, on_delete=models.CASCADE, db_column='manifestation_id', related_name='manifestation_findings')
    finding = models.ForeignKey(FindingCatalog, on_delete=models.DO_NOTHING, db_column='finding_code', related_name='manifestation_findings')
    is_present = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'manifestation_findings'
        unique_together = (('manifestation', 'finding'),)


class Treatment(models.Model):
    treatment_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patient_id', related_name='treatments')
    manifestation = models.ForeignKey(Manifestation, on_delete=models.DO_NOTHING, db_column='manifestation_id', related_name='treatments')
    medication = models.CharField(max_length=255)
    dose = models.CharField(max_length=100, blank=True, null=True)
    indication = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'treatments'


class AdverseEvent(models.Model):
    ae_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patient_id', related_name='adverse_events')
    treatment = models.ForeignKey(Treatment, on_delete=models.SET_NULL, db_column='treatment_id', null=True, blank=True, related_name='adverse_events')
    event_date = models.DateField(blank=True, null=True)
    event_name = models.CharField(max_length=255)
    severity = models.CharField(max_length=50, blank=True, null=True)
    action_taken = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'adverse_events'


class Contact(models.Model):
    contact_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'contacts'


class PatientContact(models.Model):
    pk = models.CompositePrimaryKey('patient', 'contact')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='patient_id', related_name='patient_contacts')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, db_column='contact_id', related_name='patient_contacts')
    is_primary = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'patient_contacts'
        unique_together = (('patient', 'contact'),)


class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)

    class Meta:
        managed = False
        db_table = 'roles'


class RegistryUser(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.DO_NOTHING, db_column='role_id', related_name='users')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    last_login_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False
