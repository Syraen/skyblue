from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
import datetime, uuid
from database import Base

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    passport_number = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    preferences = Column(String, nullable=True) # JSON or simple string
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    trips = relationship("Trip", back_populates="client")

class Trip(Base):
    __tablename__ = "trips"
    
    id = Column(Integer, primary_key=True, index=True)
    destination = Column(String)
    status = Column(String, default="Contact") 
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    package_name = Column(String, nullable=True)
    total_price = Column(Integer, default=0)
    currency = Column(String, default="MXN") # MXN or USD
    transport_type = Column(String, nullable=True) # Plane, Bus, etc.
    share_token = Column(String, default=lambda: str(uuid.uuid4()), unique=True)
    commission_percentage = Column(Integer, default=10)
    client_id = Column(Integer, ForeignKey("clients.id"))
    
    client = relationship("Client", back_populates="trips")
    hotels = relationship("Hotel", back_populates="trip")
    payments = relationship("Payment", back_populates="trip")
    assignments = relationship("Assignment", back_populates="trip")
    documents = relationship("Document", back_populates="trip")
    tasks = relationship("Task", back_populates="trip")
    timeline_events = relationship("TimelineEvent", back_populates="trip")

class Hotel(Base):
    __tablename__ = "hotels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    checkin_date = Column(DateTime)
    checkout_date = Column(DateTime)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    
    trip = relationship("Trip", back_populates="hotels")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer)
    currency = Column(String, default="MXN")
    date = Column(DateTime, default=datetime.datetime.utcnow)
    method = Column(String) # Cash, Card, Transfer
    trip_id = Column(Integer, ForeignKey("trips.id"))
    
    trip = relationship("Trip", back_populates="payments")

class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String) # Seat, Room
    identifier = Column(String) # e.g., "12A", "305"
    description = Column(String, nullable=True) # e.g., "Asiento Avión", "Habitación Doble"
    trip_id = Column(Integer, ForeignKey("trips.id"))
    
    trip = relationship("Trip", back_populates="assignments")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String) # e.g., "Pasaporte Juan"
    file_type = Column(String) # e.g., "PDF", "Image"
    url = Column(String) # Mock URL
    trip_id = Column(Integer, ForeignKey("trips.id"))
    
    trip = relationship("Trip", back_populates="documents")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    due_date = Column(DateTime)
    completed = Column(Boolean, default=False)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)
    
    trip = relationship("Trip", back_populates="tasks")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    date = Column(DateTime)
    description = Column(String, nullable=True)
    event_type = Column(String, default="reunion", nullable=True) # reunion, cobranza, contacto, evento
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("tenant_companies.id"), nullable=True)
    
    assigned_user = relationship("User")
    company = relationship("TenantCompany")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    message = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    company_id = Column(Integer, ForeignKey("tenant_companies.id"), nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    company = relationship("TenantCompany")
    assigned_user = relationship("User")

class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String) # Payment, Task, Created, etc.
    description = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    client_id = Column(Integer, ForeignKey("clients.id"))
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)
    
    client = relationship("Client")
    trip = relationship("Trip", back_populates="timeline_events")

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    category = Column(String) # Hotel, Airline, Tour, etc.
    contact_info = Column(String)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    payments = relationship("SupplierPayment", back_populates="supplier")

class SupplierPayment(Base):
    __tablename__ = "supplier_payments"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer)
    currency = Column(String, default="MXN")
    date = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(String)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)

    supplier = relationship("Supplier", back_populates="payments")

class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    id = Column(Integer, primary_key=True, index=True)
    from_currency = Column(String) # e.g., "USD"
    to_currency = Column(String)   # e.g., "MXN"
    rate = Column(Integer)         # Use integer for fixed point if needed, or float
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String, nullable=True)
    destination = Column(String, nullable=True)
    budget = Column(Integer, default=0)
    stage = Column(String, default="Contact") # Contact, Qualified, Quotation, Negotiation, Closed
    notes = Column(String, nullable=True)
    proposal_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PackageTemplate(Base):
    __tablename__ = "package_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    destination = Column(String)
    description = Column(String)
    price = Column(Integer)
    transport_type = Column(String)

class Survey(Base):
    __tablename__ = "surveys"
    id = Column(Integer, primary_key=True, index=True)
    score = Column(Integer) # 1-5
    feedback = Column(String, nullable=True)
    trip_id = Column(Integer, ForeignKey("trips.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class WhatsAppConversation(Base):
    __tablename__ = "whatsapp_conversations"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    last_message = Column(String)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    client = relationship("Client")
    messages = relationship("WhatsAppMessage", back_populates="conversation")

class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("whatsapp_conversations.id"))
    text = Column(String)
    sender = Column(String) # 'client' or 'agent'
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    conversation = relationship("WhatsAppConversation", back_populates="messages")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("tenant_companies.id"), nullable=True)
    
    company = relationship("TenantCompany")

class TenantCompany(Base):
    __tablename__ = "tenant_companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String) # Simple plain text password for demo login purposes
    crm_type = Column(String) # 'travel', 'gym', 'school'
    description = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="admin") # 'admin', 'user'

# --- School CRM Models ---
class SchoolStudent(Base):
    __tablename__ = "school_students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True) # Removed unique=True to allow same email in different schools
    grade = Column(String)
    average = Column(Float, default=0.0)
    qr_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    company_id = Column(Integer, ForeignKey("tenant_companies.id"), nullable=True)
    
    grades = relationship("SchoolGrade", back_populates="student")

class SchoolTeacher(Base):
    __tablename__ = "school_teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    specialty = Column(String)
    company_id = Column(Integer, ForeignKey("tenant_companies.id"), nullable=True)
    
    classes = relationship("SchoolClass", back_populates="teacher")

class SchoolClass(Base):
    __tablename__ = "school_classes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    grade = Column(String)
    schedule_time = Column(String)
    teacher_id = Column(Integer, ForeignKey("school_teachers.id"))
    company_id = Column(Integer, ForeignKey("tenant_companies.id"), nullable=True)
    
    teacher = relationship("SchoolTeacher", back_populates="classes")
    grades = relationship("SchoolGrade", back_populates="school_class")

class SchoolGrade(Base):
    __tablename__ = "school_grades"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("school_students.id"))
    class_id = Column(Integer, ForeignKey("school_classes.id"))
    grade_value = Column(Float, default=0.0)
    
    student = relationship("SchoolStudent", back_populates="grades")
    school_class = relationship("SchoolClass", back_populates="grades")

class InventoryItem(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, index=True)
    sku = Column(String, unique=True, index=True)
    stock = Column(Integer, default=0)
    reorder_point = Column(Integer, default=5)
    price = Column(Float, default=0.0)
    status = Column(String, default="In Stock")

class TransactionRecord(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(String)
    amount = Column(Float, default=0.0)
    category = Column(String)
    status = Column(String, default="Pending Verification")

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String)
    agent = Column(String)
    action_type = Column(String)
    description = Column(String)
    payload = Column(String) # JSON string
    status = Column(String, default="Pending")
    processed_at = Column(String, nullable=True)

class SystemLog(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String)
    agent = Column(String)
    message = Column(String)

class ChatMessage(Base):
    __tablename__ = "whatsapp_messages_octopus"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String)
    sender = Column(String)
    phone = Column(String)
    message = Column(String)
    direction = Column(String)
    agent = Column(String)

