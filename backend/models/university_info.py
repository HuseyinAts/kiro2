"""
Task 104: University Information Models

Database models for campus information, city living costs, dormitory info, and scholarships
"""

from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    ForeignKey,
    Text,
    ARRAY,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from .database import Base
from enum import Enum


# ============================================================
# Enumerations
# ============================================================


class CampusType(str, Enum):
    """Type of campus"""

    MAIN_CAMPUS = "main_campus"
    SATELLITE_CAMPUS = "satellite_campus"
    MEDICAL_CAMPUS = "medical_campus"
    RESEARCH_CAMPUS = "research_campus"


class AccommodationType(str, Enum):
    """Type of accommodation"""

    STATE_DORMITORY = "state_dormitory"
    UNIVERSITY_DORMITORY = "university_dormitory"
    PRIVATE_DORMITORY = "private_dormitory"
    APARTMENT = "apartment"
    SHARED_APARTMENT = "shared_apartment"


class ScholarshipType(str, Enum):
    """Type of scholarship"""

    FULL_SCHOLARSHIP = "full_scholarship"
    PARTIAL_SCHOLARSHIP = "partial_scholarship"
    MERIT_BASED = "merit_based"
    NEED_BASED = "need_based"
    SPORTS = "sports"
    ACADEMIC_EXCELLENCE = "academic_excellence"
    SPECIAL_TALENT = "special_talent"


# ============================================================
# Task 104.1: Campus Information
# ============================================================


class CampusInfo(Base):
    """
    Campus information model

    Stores details about university campuses including facilities,
    student life, clubs, and amenities
    """

    __tablename__ = "campus_info"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    university_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("universities.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Basic info
    campus_name = Column(String(255), nullable=False)
    campus_type = Column(SQLEnum(CampusType), default=CampusType.MAIN_CAMPUS)
    city = Column(String(100), nullable=False)
    district = Column(String(100))
    address = Column(Text)

    # Size
    total_area_sqm = Column(Integer)  # Total campus area in square meters
    building_count = Column(Integer)

    # Facilities
    libraries = Column(
        JSONB, default=list
    )  # [{"name": "Central Library", "capacity": 500, "study_rooms": 20}]
    sports_facilities = Column(
        ARRAY(String), default=list
    )  # ["Football field", "Swimming pool", "Gym"]
    laboratories = Column(
        JSONB, default=list
    )  # [{"name": "Chemistry Lab", "type": "science", "equipment": [...]}]
    dining_facilities = Column(
        JSONB, default=list
    )  # [{"name": "Main Cafeteria", "capacity": 800, "meal_options": [...]}]

    # Student services
    health_center = Column(Boolean, default=False)
    counseling_center = Column(Boolean, default=False)
    career_center = Column(Boolean, default=False)
    international_office = Column(Boolean, default=False)

    # Technology
    wifi_available = Column(Boolean, default=True)
    computer_labs = Column(Integer, default=0)
    online_resources = Column(Boolean, default=True)

    # Student life
    student_clubs = Column(
        JSONB, default=list
    )  # [{"name": "Robotics Club", "category": "technology", "members": 50}]
    total_student_clubs = Column(Integer, default=0)
    cultural_centers = Column(
        ARRAY(String), default=list
    )  # ["Theater", "Art Gallery", "Music Center"]
    events_per_year = Column(Integer)

    # Transportation
    public_transport_access = Column(Boolean, default=True)
    shuttle_service = Column(Boolean, default=False)
    parking_spaces = Column(Integer)
    bicycle_friendly = Column(Boolean, default=False)

    # Accessibility
    wheelchair_accessible = Column(Boolean, default=True)
    disability_support = Column(Boolean, default=False)

    # Additional info
    description = Column(Text)
    highlights = Column(ARRAY(String), default=list)
    photos = Column(ARRAY(String), default=list)  # URLs to campus photos

    # Contact
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes
    __table_args__ = (
        Index("idx_campus_info_university", "university_id"),
        Index("idx_campus_info_city", "city"),
        Index("idx_campus_info_type", "campus_type"),
    )


# ============================================================
# Task 104.2: City Living Costs
# ============================================================


class CityLivingCost(Base):
    """
    City living cost model

    Stores cost of living data for cities including accommodation,
    food, transportation, and other expenses
    """

    __tablename__ = "city_living_costs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Location
    city = Column(String(100), nullable=False)
    region = Column(String(100))

    # Accommodation costs (monthly, in TRY)
    rent_studio_min = Column(Integer)
    rent_studio_max = Column(Integer)
    rent_studio_avg = Column(Integer)

    rent_1br_min = Column(Integer)
    rent_1br_max = Column(Integer)
    rent_1br_avg = Column(Integer)

    rent_2br_min = Column(Integer)
    rent_2br_max = Column(Integer)
    rent_2br_avg = Column(Integer)

    # Shared accommodation
    shared_room_min = Column(Integer)
    shared_room_max = Column(Integer)
    shared_room_avg = Column(Integer)

    # Utilities (monthly, in TRY)
    utilities_min = Column(Integer)  # Electricity, water, gas, internet
    utilities_max = Column(Integer)
    utilities_avg = Column(Integer)

    # Food costs (monthly, in TRY)
    food_budget_min = Column(Integer)  # Groceries and eating out
    food_budget_max = Column(Integer)
    food_budget_avg = Column(Integer)

    meal_restaurant_avg = Column(Integer)  # Average restaurant meal cost
    meal_inexpensive_avg = Column(Integer)  # Average cheap meal cost
    groceries_weekly_avg = Column(Integer)  # Average weekly grocery cost

    # Transportation costs (monthly, in TRY)
    public_transport_monthly = Column(Integer)  # Monthly pass
    public_transport_single = Column(Integer)  # Single ticket
    taxi_start_fare = Column(Integer)
    taxi_per_km = Column(Integer)
    student_transport_discount = Column(Float)  # Percentage discount

    # Other expenses (monthly, in TRY)
    entertainment_min = Column(Integer)
    entertainment_max = Column(Integer)
    entertainment_avg = Column(Integer)

    books_supplies_avg = Column(Integer)  # Textbooks, supplies
    personal_care_avg = Column(Integer)  # Haircut, toiletries, etc.
    phone_internet_avg = Column(Integer)  # Mobile phone plan

    # Total estimates (monthly, in TRY)
    total_min_budget = Column(Integer)  # Minimum monthly budget for a student
    total_avg_budget = Column(Integer)  # Average monthly budget
    total_comfortable_budget = Column(Integer)  # Comfortable monthly budget

    # Additional info
    cost_of_living_index = Column(Float)  # Relative to national average (100 = average)
    student_discount_available = Column(Boolean, default=True)
    notes = Column(Text)

    # Time period
    year = Column(Integer, nullable=False, default=2024)
    month = Column(Integer)  # Optional: specific month for the data
    currency = Column(String(10), default="TRY")

    # Data source
    data_source = Column(String(255))
    sample_size = Column(Integer)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes
    __table_args__ = (
        Index("idx_city_living_cost_city", "city"),
        Index("idx_city_living_cost_year", "year"),
        Index("idx_city_living_cost_city_year", "city", "year"),
    )


# ============================================================
# Task 104.3: Dormitory Information
# ============================================================


class DormitoryInfo(Base):
    """
    Dormitory information model

    Stores details about dormitories including capacity, costs,
    facilities, and application procedures
    """

    __tablename__ = "dormitory_info"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    university_id = Column(
        PGUUID(as_uuid=True), ForeignKey("universities.id", ondelete="CASCADE")
    )

    # Basic info
    name = Column(String(255), nullable=False)
    accommodation_type = Column(SQLEnum(AccommodationType), nullable=False)
    city = Column(String(100), nullable=False)
    district = Column(String(100))
    address = Column(Text)

    # Capacity
    total_capacity = Column(Integer)
    available_spaces = Column(Integer)
    gender = Column(String(20))  # "male", "female", "mixed"

    # Room types
    room_types = Column(
        JSONB, default=list
    )  # [{"type": "double", "count": 100, "price": 2500}]
    single_rooms = Column(Integer, default=0)
    double_rooms = Column(Integer, default=0)
    triple_rooms = Column(Integer, default=0)
    quad_rooms = Column(Integer, default=0)

    # Costs (monthly, in TRY)
    price_min = Column(Integer)
    price_max = Column(Integer)
    price_avg = Column(Integer)

    deposit_required = Column(Integer)  # One-time deposit
    meals_included = Column(Boolean, default=False)
    meal_plan_cost = Column(Integer)  # Additional monthly cost if not included

    # Facilities
    wifi_included = Column(Boolean, default=True)
    laundry_facilities = Column(Boolean, default=True)
    study_rooms = Column(Boolean, default=False)
    common_areas = Column(Boolean, default=True)
    kitchen_access = Column(Boolean, default=False)
    gym = Column(Boolean, default=False)
    library = Column(Boolean, default=False)
    prayer_room = Column(Boolean, default=False)

    # Room amenities
    furniture_included = Column(Boolean, default=True)
    air_conditioning = Column(Boolean, default=False)
    heating = Column(Boolean, default=True)
    private_bathroom = Column(Boolean, default=False)

    # Security
    security_24_7 = Column(Boolean, default=True)
    cctv = Column(Boolean, default=False)
    key_card_access = Column(Boolean, default=False)

    # Rules
    curfew = Column(String(100))  # "23:00" or "none"
    visitors_allowed = Column(Boolean, default=True)
    smoking_allowed = Column(Boolean, default=False)
    pets_allowed = Column(Boolean, default=False)

    # Application
    application_period_start = Column(String(50))  # "June 1"
    application_period_end = Column(String(50))  # "August 30"
    application_requirements = Column(ARRAY(String), default=list)
    priority_criteria = Column(
        ARRAY(String), default=list
    )  # ["distance", "GPA", "income"]

    # Distance
    distance_to_campus_km = Column(Float)
    transportation_to_campus = Column(
        ARRAY(String), default=list
    )  # ["bus", "shuttle", "metro"]

    # Additional info
    description = Column(Text)
    amenities = Column(ARRAY(String), default=list)
    photos = Column(ARRAY(String), default=list)

    # Contact
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))

    # Ratings
    cleanliness_rating = Column(Float)  # 1.0 - 5.0
    location_rating = Column(Float)
    facilities_rating = Column(Float)
    value_rating = Column(Float)
    overall_rating = Column(Float)

    # Metadata
    verified = Column(Boolean, default=False)
    year = Column(Integer, default=2024)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes
    __table_args__ = (
        Index("idx_dormitory_info_university", "university_id"),
        Index("idx_dormitory_info_city", "city"),
        Index("idx_dormitory_info_type", "accommodation_type"),
        Index("idx_dormitory_info_price", "price_avg"),
    )


# ============================================================
# Task 104.4: Scholarship Programs
# ============================================================


class ScholarshipProgram(Base):
    """
    Scholarship program model

    Stores information about scholarship and financial aid programs
    including eligibility, amounts, and application procedures
    """

    __tablename__ = "scholarship_programs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    university_id = Column(
        PGUUID(as_uuid=True), ForeignKey("universities.id", ondelete="CASCADE")
    )

    # Basic info
    name = Column(String(255), nullable=False)
    scholarship_type = Column(SQLEnum(ScholarshipType), nullable=False)
    provider = Column(String(255))  # University, government, private foundation

    # Coverage
    coverage_percentage = Column(Float)  # 0-100 (percentage of tuition covered)
    covers_tuition = Column(Boolean, default=True)
    covers_accommodation = Column(Boolean, default=False)
    covers_meals = Column(Boolean, default=False)
    covers_books = Column(Boolean, default=False)
    covers_transportation = Column(Boolean, default=False)

    # Amount
    amount_min = Column(Integer)  # Minimum scholarship amount (in TRY)
    amount_max = Column(Integer)  # Maximum scholarship amount
    amount_avg = Column(Integer)  # Average scholarship amount
    monthly_stipend = Column(Integer)  # Additional monthly stipend (if any)

    # Eligibility
    min_exam_score = Column(Float)  # Minimum YKS score required
    min_high_school_gpa = Column(Float)  # Minimum high school GPA
    min_university_gpa = Column(
        Float
    )  # Minimum university GPA (for continuing students)
    income_limit = Column(Integer)  # Maximum family income (in TRY)

    citizenship_required = Column(String(100))  # "Turkish", "International", "Any"
    age_limit = Column(Integer)

    # Requirements
    eligibility_criteria = Column(ARRAY(String), default=list)
    required_documents = Column(ARRAY(String), default=list)
    special_requirements = Column(Text)

    # Application
    application_period_start = Column(String(50))
    application_period_end = Column(String(50))
    application_process = Column(Text)
    application_url = Column(String(255))

    # Selection
    selection_criteria = Column(
        JSONB, default=dict
    )  # {"academic": 60, "interview": 20, "essay": 20}
    number_of_recipients = Column(Integer)  # How many scholarships awarded per year
    acceptance_rate = Column(
        Float
    )  # Percentage of applicants who receive the scholarship

    # Duration
    renewable = Column(Boolean, default=True)
    max_duration_years = Column(Integer)  # Maximum years scholarship can be held
    renewal_requirements = Column(ARRAY(String), default=list)

    # Obligations
    service_obligation = Column(
        Boolean, default=False
    )  # Must work for provider after graduation
    service_duration_years = Column(Integer)  # Required years of service
    gpa_requirement = Column(Float)  # Minimum GPA to maintain scholarship

    # Additional benefits
    additional_benefits = Column(
        ARRAY(String), default=list
    )  # ["Mentorship", "Internship opportunities"]
    networking_opportunities = Column(Boolean, default=False)
    career_support = Column(Boolean, default=False)

    # Statistics
    total_recipients = Column(Integer)  # Total number of current recipients
    success_rate = Column(Float)  # Percentage of recipients who complete their degree

    # Additional info
    description = Column(Text)
    terms_and_conditions = Column(Text)

    # Contact
    contact_person = Column(String(255))
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))

    # Metadata
    active = Column(Boolean, default=True)
    year = Column(Integer, default=2024)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Indexes
    __table_args__ = (
        Index("idx_scholarship_program_university", "university_id"),
        Index("idx_scholarship_program_type", "scholarship_type"),
        Index("idx_scholarship_program_active", "active"),
        Index("idx_scholarship_program_coverage", "coverage_percentage"),
    )


# ============================================================
# Aggregate University Statistics
# ============================================================


class UniversityStatistics(Base):
    """
    Aggregate statistics for university information

    Pre-computed statistics combining campus, living costs,
    dormitories, and scholarships
    """

    __tablename__ = "university_statistics"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    university_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("universities.id", ondelete="CASCADE"),
        nullable=False,
    )
    year = Column(Integer, nullable=False, default=2024)

    # Campus statistics
    total_campuses = Column(Integer, default=0)
    total_campus_area_sqm = Column(Integer)
    total_student_clubs = Column(Integer, default=0)
    has_health_center = Column(Boolean, default=False)
    has_career_center = Column(Boolean, default=False)

    # Living cost statistics
    city = Column(String(100))
    avg_monthly_cost = Column(Integer)  # Average total monthly cost for students
    avg_rent = Column(Integer)
    cost_of_living_index = Column(Float)

    # Dormitory statistics
    total_dormitory_capacity = Column(Integer, default=0)
    avg_dormitory_cost = Column(Integer)
    dormitory_types = Column(ARRAY(String), default=list)

    # Scholarship statistics
    total_scholarships = Column(Integer, default=0)
    full_scholarships = Column(Integer, default=0)
    partial_scholarships = Column(Integer, default=0)
    avg_scholarship_amount = Column(Integer)
    scholarship_acceptance_rate = Column(Float)

    # Combined affordability score
    affordability_score = Column(Float)  # 1.0 - 10.0 (higher = more affordable)

    # Metadata
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_university_statistics_university", "university_id"),
        Index("idx_university_statistics_year", "year"),
        Index("idx_university_statistics_university_year", "university_id", "year"),
    )
