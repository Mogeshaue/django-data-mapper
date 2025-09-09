from django.db import models
import json
import uuid
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings


class Institution(models.Model):
    name = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=150)
    Institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, null=True)
    department_head_email = models.EmailField(null=True, blank=True)
    zk_uid = models.CharField(max_length=30, null=True, blank=True)
    zk_department_code = models.CharField(max_length=50, null=True, blank=True, default=uuid.uuid4)
    parent_department = models.CharField(max_length=30, null=True, blank=True)

    def __str__(self):
        return self.name + " - " + (self.Institution.name if self.Institution else "No Institution")

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"


class Hostel_Block(models.Model):
    no_of_floors = models.IntegerField(null=True, blank=True, default=0)
    block_types = (("WH", "Women's Hostel"), ("MH", "Men's Hostel"))
    block_name = models.CharField(max_length=15, unique=True)
    block_type = models.CharField(max_length=25, choices=block_types)
    maintenance = models.BooleanField(default=False)

    def __str__(self):
        return self.block_name

    class Meta:
        verbose_name = "Hostel Block"
        verbose_name_plural = "Hostel Blocks"


class Hostel_Floor(models.Model):
    block = models.ForeignKey(Hostel_Block, on_delete=models.CASCADE, null=True, blank=True)
    floor_no = models.CharField(max_length=30, null=True)
    maintenance = models.BooleanField(default=False)
    no_of_rooms = models.IntegerField(null=True, blank=True)
    no_of_dorms = models.IntegerField(null=True, blank=True)
    no_of_rooms_occupied = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Floor {self.floor_no} - {self.block.block_name if self.block else 'No Block'}"

    class Meta:
        verbose_name = "Hostel Floor"
        verbose_name_plural = "Hostel Floors"


class Hostel_Room(models.Model):
    room_choices = (("4-sharing", "4-Sharing"), ("Dorm", "Dorm"))
    room_no = models.CharField(max_length=10, null=True, blank=True)
    floor = models.ForeignKey(Hostel_Floor, on_delete=models.CASCADE, null=False, blank=False)
    room_type = models.CharField(max_length=25, null=True, blank=True, choices=room_choices)
    room_capacity = models.IntegerField(null=True, blank=True)
    maintenance = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    not_available_reason = models.TextField(null=True, blank=True)
    no_of_students_occupied = models.IntegerField(null=True, blank=True, default=0)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.room_no if self.room_no else "Unnamed Room"

    class Meta:
        verbose_name = "Hostel Room"
        verbose_name_plural = "Hostel Rooms"


# Simplified location and transport models for UserRecord dependencies
class Location(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"


class Route(models.Model):
    route_name = models.CharField(max_length=100)
    route_code = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return self.route_name

    class Meta:
        verbose_name = "Route"
        verbose_name_plural = "Routes"


class Bus(models.Model):
    bus_number = models.CharField(max_length=20, unique=True)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, null=True, blank=True)
    capacity = models.IntegerField(default=50)
    
    def __str__(self):
        return self.bus_number

    class Meta:
        verbose_name = "Bus"
        verbose_name_plural = "Buses"


class UserGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "User Group"
        verbose_name_plural = "User Groups"


class Permission(models.Model):
    name = models.CharField(max_length=100)
    codename = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"


class UserRecord(models.Model):
    ACADEMIC = "Academic"
    TEACHING = "Teaching"
    ACADEMIC_SUPPORT = "Academic Support"
    ADMIN = "Admin"
    EXTERNAL = "External"
    HOSTEL_ADMIN = "Hostel Admin"
    HOSTEL_WARDEN = "Hostel Warden"
    HOSTEL_STUDENT = "Hostel Student"
    GUEST = "Guest"

    TYPE_CHOICES = (
        ("HR", "HR"),
        ("Security Admin", "Security Admin"),
        ("Department Head", "Department Head"),
        ("Sub Admin", "Sub Admin"),
        ("External Sub Admin", "External Sub Admin"),
        ("Normal", "Normal"),
        ("Hostel Admin", "Hostel Admin"),
        ("Avenue Admin", "Avenue Admin"),
        ("Physical Department", "Physical Department"),
    )

    CATEGORY_CHOICES = (
        (ACADEMIC, "Academic"),
        (TEACHING, "Teaching"),
        (ACADEMIC_SUPPORT, "Academic Support"),
        (ADMIN, "Admin"),
        (EXTERNAL, "External"),
        (GUEST, "Guest"),
    )
    
    SUB_CHOICES = (
        ("Transport", "College Transport"),
        ("Own", "Own Transport"),
        ("Student", "Student"),
        ("Others", "Others"),
        ("Nil", "Nil"),
    )
    
    BLOOD_GROUP_CHOICES = (
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("O+", "O+"),
        ("O-", "O-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("A1B+", "A1B"),
        ("A1+", "A1+"),
        ("A1B-", "A1B-"),
        ("A1-", "A1-"),
        ("A2+", "A2+"),
    )

    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    GENDER_CHOICES = ((MALE, "Male"), (FEMALE, "Female"), (OTHER, "Other"))
    ADMISSION_TYPE = (("REGULAR", "REGULAR"), ("LATERAL", "LATERAL"))
    HOSTELER, DAYSCHOLAR = "Hostel", "Dayscholar"
    RESIDENCE_CHOICES = ((HOSTELER, "HOSTELER"), (DAYSCHOLAR, "DAYSCHOLAR"))

    name = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    uid = models.CharField(max_length=20, null=True, blank=True, default="Not_Set")
    email = models.EmailField(unique=True, null=True, blank=True)
    assigned_head = models.CharField(max_length=50, null=True, blank=True)
    user_groups = models.ManyToManyField(UserGroup, blank=True)
    is_data_validated = models.BooleanField(default=False)
    gender = models.CharField(choices=GENDER_CHOICES, null=True, blank=True, max_length=10)
    date_of_birth = models.DateField(null=True, blank=True)
    hostel_block = models.ForeignKey(Hostel_Block, null=True, blank=True, on_delete=models.SET_NULL)
    hostel_room_number = models.ForeignKey(Hostel_Room, null=True, blank=True, on_delete=models.SET_NULL)
    hostel_admin_type = models.CharField(max_length=50, null=True, blank=True)
    admission_type = models.CharField(null=False, blank=True, choices=ADMISSION_TYPE, max_length=20)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    institution_type = models.ForeignKey(Institution, null=True, blank=True, on_delete=models.SET_NULL)
    year_of_study = models.CharField(max_length=15, null=True, blank=True)
    bus_stop = models.ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL)
    bus_route = models.ForeignKey(Route, null=True, blank=True, on_delete=models.SET_NULL)
    bus_no = models.ForeignKey(Bus, on_delete=models.CASCADE, null=True, blank=True)
    residence = models.CharField(max_length=20, choices=RESIDENCE_CHOICES, null=True, blank=True, default=None)
    parent_phone_number = models.CharField(max_length=20, null=True, blank=True)
    parent_phone_number2 = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    blood_group = models.CharField(max_length=10, null=True, blank=True, choices=BLOOD_GROUP_CHOICES)
    Title = models.CharField(max_length=70, null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="Normal", null=True, blank=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=20, null=True, blank=True)
    sub_category = models.CharField(max_length=20, choices=SUB_CHOICES, default="Nil", null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    temp_rollno = models.CharField(max_length=10, null=True, blank=True)
    personal_mail_id = models.EmailField(null=True, blank=True)  # Removed unique=True to avoid conflicts
    aadhar_no = models.BigIntegerField(null=True, blank=True)  # Removed unique=True to avoid conflicts
    current_address = models.TextField(null=True, blank=True)
    photo = models.FileField(null=True, blank=True, default="../media/userPhotos/userPhoto.png")
    shortrange_RFID = models.CharField(null=True, blank=True, max_length=20)
    longrange_RFID = models.CharField(null=True, blank=True, max_length=20)
    fingerprints = models.JSONField(null=True, blank=True)
    biometric_uid = models.CharField(max_length=50, null=True, blank=True)
    password = models.CharField(max_length=128, default="", blank=True)
    biometric_photo = models.JSONField(null=True, blank=True)
    canApply = models.BooleanField(default=True, null=True, blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    others = models.JSONField(null=True, blank=True)
    id_proof = models.CharField(max_length=40, null=True, blank=True, default=None)
    auto_approve = models.BooleanField(default=False, null=True, blank=True)
    auto_tag = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name if self.name else f"User {self.uid}"

    class Meta:
        verbose_name = "User Record"
        verbose_name_plural = "User Records"


# Original test models for demonstration
class DynamicTestModel(models.Model):
    """A test model to demonstrate dynamic mapping capabilities"""
    name = models.CharField(max_length=100, help_text="Full name")
    email = models.EmailField(unique=True, help_text="Email address")
    age = models.IntegerField(null=True, blank=True, help_text="Age in years")
    is_active = models.BooleanField(default=True, help_text="Is the user active?")
    created_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, help_text="Optional description")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Dynamic Test Model"
        verbose_name_plural = "Dynamic Test Models"


class Company(models.Model):
    """Company model for testing relationships"""
    company_name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100, blank=True)
    founded_year = models.IntegerField(null=True, blank=True)
    website = models.URLField(blank=True)
    
    def __str__(self):
        return self.company_name
    
    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"


class Employee(models.Model):
    """Employee model to test foreign key relationships"""
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    employee_id = models.CharField(max_length=20, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees')
    position = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hire_date = models.DateField()
    is_manager = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
