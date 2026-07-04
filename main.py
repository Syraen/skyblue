from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

import models
from database import engine, get_db
from pydantic import BaseModel
import datetime

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agencia de Viajes CRM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas for request/response
class ClientBase(BaseModel):
    name: str
    email: str
    phone: str | None = None
    passport_number: str | None = None
    notes: str | None = None

class ClientCreate(ClientBase):
    pass

class ClientResponse(ClientBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PaymentCreate(BaseModel):
    amount: int
    method: str
    trip_id: int

class AssignmentCreate(BaseModel):
    type: str
    identifier: str
    description: str | None = None
    trip_id: int

class TripCreate(BaseModel):
    destination: str
    client_id: int
    package_name: str | None = None
    total_price: int = 0
    currency: str = "MXN"
    transport_type: str | None = None

class SupplierCreate(BaseModel):
    name: str
    category: str
    contact_info: str | None = None
    email: str | None = None
    phone: str | None = None

class ExchangeRateCreate(BaseModel):
    from_currency: str
    to_currency: str
    rate: float

class LeadCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None
    destination: str | None = None
    budget: int = 0

class LeadStageUpdate(BaseModel):
    stage: str

class PackageTemplateCreate(BaseModel):
    name: str
    destination: str
    description: str
    price: int
    transport_type: str

class SurveyCreate(BaseModel):
    score: int
    feedback: str | None = None
    trip_id: int

class AppointmentCreate(BaseModel):
    title: str
    date: datetime.datetime
    description: str | None = None
    event_type: str = "reunion"
    client_id: int | None = None
    assigned_user_id: int | None = None
    company_id: int | None = None

class CompanyCreate(BaseModel):
    name: str
    email: str
    password: str
    crm_type: str # 'travel', 'gym', 'school'
    description: str | None = None
    logo_url: str | None = None

class CompanyUpdate(BaseModel):
    name: str
    email: str
    description: str | None = None
    logo_url: str | None = None

class CompanyPasswordChange(BaseModel):
    current_password: str
    new_password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    company_id: int | None = None

class CompanyLogin(BaseModel):
    email: str
    password: str

# --- School CRM Schemas ---
class SchoolStudentCreate(BaseModel):
    name: str
    email: str
    grade: str
    company_id: int

class SchoolTeacherCreate(BaseModel):
    name: str
    email: str
    specialty: str
    company_id: int

class SchoolClassCreate(BaseModel):
    name: str
    grade: str
    schedule_time: str
    teacher_id: int
    company_id: int

class SchoolGradeUpdate(BaseModel):
    grade_value: float

class DocumentCreate(BaseModel):
    name: str
    file_type: str
    url: str

class AIItineraryRequest(BaseModel):
    destination: str
    preferences: str | None = None

# Startup seed event
from database import SessionLocal
from sqlalchemy import text
@app.on_event("startup")
def startup_populate():
    db = SessionLocal()
    try:
        # Auto-migrate event_type column for appointments
        try:
            db.execute(text("ALTER TABLE appointments ADD COLUMN event_type VARCHAR DEFAULT 'reunion'"))
            db.commit()
        except Exception:
            db.rollback()

        # Auto-migrate assigned_user_id column for appointments
        try:
            db.execute(text("ALTER TABLE appointments ADD COLUMN assigned_user_id INTEGER"))
            db.commit()
        except Exception:
            db.rollback()

        # Auto-migrate company_id column for appointments
        try:
            db.execute(text("ALTER TABLE appointments ADD COLUMN company_id INTEGER"))
            db.commit()
        except Exception:
            db.rollback()

        # Auto-migrate company_id column for users
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN company_id INTEGER"))
            db.commit()
        except Exception:
            db.rollback()

        # Auto-migrate columns for notifications
        try:
            db.execute(text("ALTER TABLE notifications ADD COLUMN company_id INTEGER"))
            db.commit()
        except Exception:
            db.rollback()

        try:
            db.execute(text("ALTER TABLE notifications ADD COLUMN assigned_user_id INTEGER"))
            db.commit()
        except Exception:
            db.rollback()

        seed_data = [
            ("SkyBlue Travel MTY", "viajes@skyblue.com", "admin", "travel", "Agencia de viajes premium con diseño de itinerarios con IA, mapas y bóveda digital de documentos.", "✈️"),
            ("SkyBlue Gym Elite", "gym@skyblue.com", "admin", "gym", "Centro de entrenamiento de alto rendimiento. Control de membresías, casilleros interactivos y accesos QR.", "💪"),
            ("SkyBlue Academic School", "escuela@skyblue.com", "admin", "school", "Gestión escolar integral. Control de calificaciones, asignación de pupitres interactiva y credenciales QR.", "🎓"),
            ("Samsung Electronics Logística", "samsung@skyblue.com", "admin", "travel", "Gestión corporativa de viajes de negocios, vuelos y hospedaje internacional para directores y ejecutivos de Samsung.", "📱"),
            ("KIA Motors Centro Técnico", "kia@skyblue.com", "admin", "school", "Centro de capacitación técnica e industrial de KIA. Control de alumnos, salones y asignación de pupitres de ensamble.", "🚗"),
            ("Nike Training Center", "nike@skyblue.com", "admin", "gym", "Gimnasio privado y centro de entrenamiento de atletas patrocinados. Membresías VIP y lockers inteligentes.", "👟"),
            ("Tesla Monterrey Hub", "tesla@skyblue.com", "admin", "travel", "Organización de itinerarios y logística de viajes ejecutivos para el equipo de la Gigafactory Monterrey.", "⚡")
        ]
        for name, email, password, crm_type, desc, logo in seed_data:
            exists = db.query(models.TenantCompany).filter(models.TenantCompany.email == email).first()
            if not exists:
                comp = models.TenantCompany(name=name, email=email, password=password, crm_type=crm_type, description=desc, logo_url=logo)
                db.add(comp)
        db.commit()

        # Seed default users if none exist
        exists_user = db.query(models.User).first()
        if not exists_user:
            mty = db.query(models.TenantCompany).filter(models.TenantCompany.email == "viajes@skyblue.com").first()
            mty_id = mty.id if mty else None
            
            user1 = models.User(username="agente_carlos", email="carlos@skyblue.com", hashed_password="admin", company_id=mty_id)
            user2 = models.User(username="agente_sofia", email="sofia@skyblue.com", hashed_password="admin", company_id=mty_id)
            user3 = models.User(username="soporte_tecnico", email="soporte@skyblue.com", hashed_password="admin", company_id=None)
            db.add_all([user1, user2, user3])
            db.commit()
        
        # Seed default inventory items
        exists_inv = db.query(models.InventoryItem).first()
        if not exists_inv:
            inv1 = models.InventoryItem(item_name="Laptop Pro 16", sku="LAP16-PRO", stock=4, reorder_point=5, price=1800.0, status="Low Stock")
            inv2 = models.InventoryItem(item_name="Monitor UltraWide 34", sku="MON34-UW", stock=12, reorder_point=3, price=450.0, status="In Stock")
            inv3 = models.InventoryItem(item_name="Teclado Mecánico RGB", sku="KB-MECH", stock=25, reorder_point=10, price=89.0, status="In Stock")
            db.add_all([inv1, inv2, inv3])

        # Seed default transactions
        exists_tx = db.query(models.TransactionRecord).first()
        if not exists_tx:
            tx1 = models.TransactionRecord(description="Servidor AWS Cargo Mensual", amount=850.00, category="Infraestructura", status="Reconciled")
            tx2 = models.TransactionRecord(description="Suscripción Stripe Reembolso", amount=-150.00, category="Ventas", status="Pending Verification")
            db.add_all([tx1, tx2])

        # Automatically seed travel clients, trips, leads, etc., if they don't exist
        exists_client = db.query(models.Client).first()
        if not exists_client:
            seed_data(db)
        else:
            # Check if María Rodríguez is present. If not, add her and her trips.
            exists_maria = db.query(models.Client).filter(models.Client.email == "maria.rodriguez@example.com").first()
            if not exists_maria:
                client_repeat = models.Client(
                    name="María Rodríguez", 
                    email="maria.rodriguez@example.com", 
                    phone="555-0909", 
                    passport_number="MX999888", 
                    preferences="Viajera frecuente. Prefiere hoteles boutique de 5 estrellas, tours gastronómicos y siempre solicita asientos en primera clase/business."
                )
                db.add(client_repeat)
                db.commit()
                db.refresh(client_repeat)
                
                trip_repeat_1 = models.Trip(destination="Orlando, US", status="Booked", package_name="Disney Mágico Familiar", total_price=45000, transport_type="Plane", client_id=client_repeat.id, start_date=datetime.datetime(2023, 5, 10), end_date=datetime.datetime(2023, 5, 17))
                trip_repeat_2 = models.Trip(destination="Tokio, JP", status="Booked", package_name="Tokio Imperial y Tradición", total_price=120000, transport_type="Plane", client_id=client_repeat.id, start_date=datetime.datetime(2024, 10, 12), end_date=datetime.datetime(2024, 10, 24))
                trip_repeat_3 = models.Trip(destination="Madrid, ES", status="Quote", package_name="Escapada Cultural Madrid", total_price=35000, transport_type="Plane", client_id=client_repeat.id, start_date=datetime.datetime(2025, 2, 1), end_date=datetime.datetime(2025, 2, 8))
                
                db.add_all([trip_repeat_1, trip_repeat_2, trip_repeat_3])
                db.commit()
                
                p_repeat_1_1 = models.Payment(amount=45000, method="Transfer", trip_id=trip_repeat_1.id)
                p_repeat_2_1 = models.Payment(amount=60000, method="Card", trip_id=trip_repeat_2.id)
                db.add_all([p_repeat_1_1, p_repeat_2_1])
                
                a_rep_1 = models.Assignment(type="Seat", identifier="02B", description="Primera Clase Pasillo", trip_id=trip_repeat_1.id)
                a_rep_2 = models.Assignment(type="Room", identifier="101", description="Master Suite", trip_id=trip_repeat_1.id)
                a_rep_3 = models.Assignment(type="Seat", identifier="01A", description="Primera Clase Ventanilla", trip_id=trip_repeat_2.id)
                a_rep_4 = models.Assignment(type="Room", identifier="903", description="Penthouse Vista Imperial", trip_id=trip_repeat_2.id)
                db.add_all([a_rep_1, a_rep_2, a_rep_3, a_rep_4])
                
                db.commit()

        # Seed default calendar events if none exist
        exists_appt = db.query(models.Appointment).first()
        if not exists_appt:
            now = datetime.datetime.now()
            c_maria = db.query(models.Client).filter(models.Client.email == "maria.rodriguez@example.com").first()
            c_juan = db.query(models.Client).filter(models.Client.email == "juan@example.com").first()
            c_elena = db.query(models.Client).filter(models.Client.email == "elena@example.com").first()
            
            appt1 = models.Appointment(title="Cobranza: María Rodríguez - Depósito Japón", date=now + datetime.timedelta(days=1), description="Recordatorio de cobro del 50% restante ($60,000 MXN) para el viaje a Tokio.", event_type="cobranza", client_id=c_maria.id if c_maria else None)
            appt2 = models.Appointment(title="Contacto: Juan Pérez - Confirmar Pasaporte", date=now + datetime.timedelta(days=2), description="Verificar fecha de vencimiento de pasaporte para vuelo a Cancún.", event_type="contacto", client_id=c_juan.id if c_juan else None)
            appt3 = models.Appointment(title="Reunión: Elena Torres - Itinerario París", date=now + datetime.timedelta(days=3), description="Reunión en zoom para definir visitas guiadas en París.", event_type="reunion", client_id=c_elena.id if c_elena else None)
            appt4 = models.Appointment(title="Evento: Lanzamiento de Campaña Verano 2025", date=now - datetime.timedelta(days=2), description="Presentación de nuevos paquetes de playa.", event_type="evento")
            db.add_all([appt1, appt2, appt3, appt4])
            db.commit()

        db.commit()
    except Exception as e:
        print("Error seeding default data:", e)
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Travel Agency CRM API"}

@app.get("/clients", response_model=List[ClientResponse])
def get_clients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    clients = db.query(models.Client).offset(skip).limit(limit).all()
    return clients

@app.post("/clients", response_model=ClientResponse)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    db_client = models.Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@app.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if not user or user_data.password != "admin": # Mock password check
        if user_data.username == "admin" and user_data.password == "admin":
            return {"access_token": "mock_token", "token_type": "bearer", "username": "admin"}
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    return {"access_token": "mock_token", "token_type": "bearer", "username": user.username}

# --- Tenant Company Endpoints ---

@app.get("/companies")
def get_companies(db: Session = Depends(get_db)):
    return db.query(models.TenantCompany).all()

@app.post("/companies")
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    db_company = models.TenantCompany(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@app.post("/companies/login")
def login_company(login_data: CompanyLogin, db: Session = Depends(get_db)):
    company = db.query(models.TenantCompany).filter(models.TenantCompany.email == login_data.email).first()
    if company and company.password == login_data.password:
        if not getattr(company, "is_active", True):
            raise HTTPException(status_code=403, detail="Esta cuenta ha sido bloqueada por el Super Administrador.")
        return {
            "access_token": "tenant_token_" + str(company.id),
            "token_type": "bearer",
            "username": company.name,
            "crm_type": company.crm_type,
            "company_id": company.id,
            "user_id": None
        }

    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if user and user.hashed_password == login_data.password:
        if not getattr(user, "is_active", True):
            raise HTTPException(status_code=403, detail="Esta cuenta de usuario ha sido desactivada.")
        
        linked_company = db.query(models.TenantCompany).filter(models.TenantCompany.id == user.company_id).first()
        return {
            "access_token": "user_token_" + str(user.id),
            "token_type": "bearer",
            "username": user.username,
            "crm_type": linked_company.crm_type if linked_company else "travel",
            "company_id": user.company_id,
            "user_id": user.id
        }

    raise HTTPException(status_code=400, detail="Credenciales incorrectas")

@app.put("/companies/{company_id}/toggle-status")
def toggle_company_status(company_id: int, db: Session = Depends(get_db)):
    company = db.query(models.TenantCompany).filter(models.TenantCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    company.is_active = not getattr(company, "is_active", True)
    db.commit()
    db.refresh(company)
    return {"message": "Estado actualizado", "is_active": company.is_active}

@app.put("/companies/{company_id}/role")
def update_company_role(company_id: int, role_data: dict, db: Session = Depends(get_db)):
    company = db.query(models.TenantCompany).filter(models.TenantCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    new_role = role_data.get("role", "admin")
    company.role = new_role
    db.commit()
    db.refresh(company)
    return {"message": "Rol actualizado", "role": company.role}

@app.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(models.TenantCompany).filter(models.TenantCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    db.delete(company)
    db.commit()
    return {"message": "Empresa eliminada exitosamente"}

@app.get("/companies/{company_id}")
def get_company_details(company_id: int, db: Session = Depends(get_db)):
    company = db.query(models.TenantCompany).filter(models.TenantCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return company

@app.put("/companies/{company_id}")
def update_company(company_id: int, company_data: CompanyUpdate, db: Session = Depends(get_db)):
    company = db.query(models.TenantCompany).filter(models.TenantCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    company.name = company_data.name
    company.email = company_data.email
    company.description = company_data.description
    company.logo_url = company_data.logo_url
    db.commit()
    db.refresh(company)
    return company

@app.put("/companies/{company_id}/change-password")
def change_company_password(company_id: int, pass_data: CompanyPasswordChange, db: Session = Depends(get_db)):
    company = db.query(models.TenantCompany).filter(models.TenantCompany.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if company.password != pass_data.current_password:
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")
    company.password = pass_data.new_password
    db.commit()
    return {"message": "Contraseña actualizada exitosamente"}

@app.get("/companies/{company_id}/users")
def get_company_users(company_id: int, db: Session = Depends(get_db)):
    return db.query(models.User).filter(models.User.company_id == company_id).all()

@app.post("/companies/{company_id}/users")
def create_company_user(company_id: int, user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        (models.User.username == user_data.username) | (models.User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario o correo ya está registrado.")
    
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=user_data.password,
        company_id=company_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users")
def list_all_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

@app.post("/users")
def create_global_user(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=user_data.password,
        company_id=user_data.company_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(user)
    db.commit()
    return {"message": "Usuario eliminado exitosamente"}

# --- Trip Endpoints ---

@app.get("/trips")
def get_trips(db: Session = Depends(get_db)):
    trips = db.query(models.Trip).all()
    result = []
    for trip in trips:
        result.append({
            "id": trip.id,
            "destination": trip.destination,
            "status": trip.status,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
            "package_name": trip.package_name,
            "total_price": trip.total_price,
            "currency": trip.currency,
            "transport_type": trip.transport_type,
            "client": {
                "id": trip.client.id,
                "name": trip.client.name,
                "email": trip.client.email,
                "phone": trip.client.phone
            } if trip.client else None
        })
    return result

@app.get("/trips/{trip_id}")
def get_trip_details(trip_id: int, db: Session = Depends(get_db)):
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Manually building response to include relationships
    return {
        "id": trip.id,
        "destination": trip.destination,
        "status": trip.status,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "package_name": trip.package_name,
        "total_price": trip.total_price,
        "transport_type": trip.transport_type,
        "client": trip.client,
        "hotels": trip.hotels,
        "payments": trip.payments,
        "assignments": trip.assignments,
        "documents": trip.documents,
        "tasks": trip.tasks,
        "timeline": trip.timeline_events
    }

@app.post("/trips")
def create_trip(trip: TripCreate, db: Session = Depends(get_db)):
    db_trip = models.Trip(**trip.model_dump())
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip

@app.post("/payments")
def add_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    db_payment = models.Payment(**payment.model_dump())
    db.add(db_payment)
    
    # Create Timeline Event
    trip = db.query(models.Trip).filter(models.Trip.id == payment.trip_id).first()
    event = models.TimelineEvent(
        event_type="Payment",
        description=f"Pago registrado: ${payment.amount} via {payment.method}",
        client_id=trip.client_id,
        trip_id=trip.id
    )
    db.add(event)
    
    # Create Notification
    notif = models.Notification(
        title="Nuevo Pago",
        message=f"Se ha registrado un pago de ${payment.amount} para el viaje a {trip.destination}."
    )
    db.add(notif)
    
    db.commit()
    db.refresh(db_payment)
    return db_payment

@app.post("/assignments")
def add_assignment(assignment: AssignmentCreate, db: Session = Depends(get_db)):
    # Avoid duplicate assignments for the same seat on the same trip
    existing = db.query(models.Assignment).filter(
        models.Assignment.trip_id == assignment.trip_id,
        models.Assignment.type == assignment.type,
        models.Assignment.identifier == assignment.identifier
    ).first()
    
    if existing:
        existing.description = assignment.description
        db.commit()
        db.refresh(existing)
        return existing
        
    db_assignment = models.Assignment(**assignment.model_dump())
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@app.delete("/assignments/{assignment_id}")
def delete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    db.delete(assignment)
    db.commit()
    return {"status": "ok", "message": "Asignación eliminada exitosamente"}

@app.post("/seed")
def seed_data(db: Session = Depends(get_db)):
    # Clear existing data (optional, but good for clean examples)
    # db.query(models.Assignment).delete()
    # db.query(models.Payment).delete()
    # ...
    
    # Create Clients
    client1 = models.Client(name="Juan Pérez", email="juan@example.com", phone="555-0101", passport_number="MX123456", preferences="Prefiere hoteles vista al mar y traslados privados.")
    client2 = models.Client(name="Elena Torres", email="elena@example.com", phone="555-0202", passport_number="MX987654", preferences="Viaja siempre con su mascota. Prefiere vuelos matutinos.")
    client3 = models.Client(name="Roberto Gómez", email="roberto@example.com", phone="555-0303", preferences="Busca siempre ofertas de último minuto.")
    client_repeat = models.Client(name="María Rodríguez", email="maria.rodriguez@example.com", phone="555-0909", passport_number="MX999888", preferences="Viajera frecuente. Prefiere hoteles boutique de 5 estrellas, tours gastronómicos y siempre solicita asientos en primera clase/business.")
    
    db.add_all([client1, client2, client3, client_repeat])
    db.commit()
    
    # Create Trips
    trip1 = models.Trip(destination="Cancún, MX", status="Booked", package_name="Paquete Familiar Playa", total_price=25000, transport_type="Plane", client_id=client1.id, start_date=datetime.datetime(2024, 7, 15), end_date=datetime.datetime(2024, 7, 22))
    trip2 = models.Trip(destination="París, FR", status="Quote", package_name="Luna de Miel Premium", total_price=85000, transport_type="Plane", client_id=client2.id, start_date=datetime.datetime(2024, 9, 10), end_date=datetime.datetime(2024, 9, 20))
    trip3 = models.Trip(destination="Mazatlán, MX", status="Contact", package_name="Escapada Fin de Semana", total_price=12000, transport_type="Bus", client_id=client3.id)
    
    # Repeat client trips: 1st trip (past), 2nd trip (active), 3rd trip (quote)
    trip_repeat_1 = models.Trip(destination="Orlando, US", status="Booked", package_name="Disney Mágico Familiar", total_price=45000, transport_type="Plane", client_id=client_repeat.id, start_date=datetime.datetime(2023, 5, 10), end_date=datetime.datetime(2023, 5, 17))
    trip_repeat_2 = models.Trip(destination="Tokio, JP", status="Booked", package_name="Tokio Imperial y Tradición", total_price=120000, transport_type="Plane", client_id=client_repeat.id, start_date=datetime.datetime(2024, 10, 12), end_date=datetime.datetime(2024, 10, 24))
    trip_repeat_3 = models.Trip(destination="Madrid, ES", status="Quote", package_name="Escapada Cultural Madrid", total_price=35000, transport_type="Plane", client_id=client_repeat.id, start_date=datetime.datetime(2025, 2, 1), end_date=datetime.datetime(2025, 2, 8))
    
    db.add_all([trip1, trip2, trip3, trip_repeat_1, trip_repeat_2, trip_repeat_3])
    db.commit()
    
    # Create Payments
    p1 = models.Payment(amount=5000, method="Transfer", trip_id=trip1.id)
    p2 = models.Payment(amount=10000, method="Card", trip_id=trip1.id)
    p3 = models.Payment(amount=20000, method="Transfer", trip_id=trip2.id)
    
    # Payments for repeat client
    p_repeat_1_1 = models.Payment(amount=45000, method="Transfer", trip_id=trip_repeat_1.id) # Fully paid
    p_repeat_2_1 = models.Payment(amount=60000, method="Card", trip_id=trip_repeat_2.id)      # Partially paid
    
    db.add_all([p1, p2, p3, p_repeat_1_1, p_repeat_2_1])
    
    # Create Assignments
    a1 = models.Assignment(type="Seat", identifier="14A", description="Asiento Ventanilla", trip_id=trip1.id)
    a2 = models.Assignment(type="Room", identifier="402", description="Vista al Mar", trip_id=trip1.id)
    
    # Assignments for repeat client
    a_rep_1 = models.Assignment(type="Seat", identifier="02B", description="Primera Clase Pasillo", trip_id=trip_repeat_1.id)
    a_rep_2 = models.Assignment(type="Room", identifier="101", description="Master Suite", trip_id=trip_repeat_1.id)
    a_rep_3 = models.Assignment(type="Seat", identifier="01A", description="Primera Clase Ventanilla", trip_id=trip_repeat_2.id)
    a_rep_4 = models.Assignment(type="Room", identifier="903", description="Penthouse Vista Imperial", trip_id=trip_repeat_2.id)
    
    db.add_all([a1, a2, a_rep_1, a_rep_2, a_rep_3, a_rep_4])

    # Create Documents
    d1 = models.Document(name="Pasaporte - Juan Pérez", file_type="PDF", url="#", trip_id=trip1.id)
    d2 = models.Document(name="Visa Americana - Juan Pérez", file_type="Image", url="#", trip_id=trip1.id)
    db.add_all([d1, d2])

    # Create Tasks
    t1 = models.Task(title="Confirmar traslado aeropuerto", due_date=datetime.datetime.utcnow() + datetime.timedelta(days=2), trip_id=trip1.id)
    t2 = models.Task(title="Enviar itinerario final", due_date=datetime.datetime.utcnow() + datetime.timedelta(days=5), trip_id=trip1.id, completed=True)
    t3 = models.Task(title="Solicitar dieta especial para vuelo", due_date=datetime.datetime.utcnow() + datetime.timedelta(days=1), trip_id=trip2.id)
    db.add_all([t1, t2, t3])
    
    # Create Suppliers
    s1 = models.Supplier(name="Hotel Riviera Maya", category="Hotel", contact_info="Recepción 24/7", email="reservas@riviera.com", phone="998-123-4567")
    s2 = models.Supplier(name="Aeroméxico", category="Airline", contact_info="Soporte Agencias", email="agencias@aeromexico.com")
    db.add_all([s1, s2])

    # Create Notifications
    n1 = models.Notification(title="Tarea Vencida", message="La tarea 'Confirmar traslado' de Juan Pérez ha vencido.")
    n2 = models.Notification(title="Nuevo Cliente", message="Elena Torres se ha registrado en el sistema.", is_read=True)
    db.add_all([n1, n2])

    # Create Appointments/Calendar Events
    now = datetime.datetime.now()
    appt1 = models.Appointment(title="Cobranza: María Rodríguez - Depósito Japón", date=now + datetime.timedelta(days=1), description="Recordatorio de cobro del 50% restante ($60,000 MXN) para el viaje a Tokio.", event_type="cobranza", client_id=client_repeat.id)
    appt2 = models.Appointment(title="Contacto: Juan Pérez - Confirmar Pasaporte", date=now + datetime.timedelta(days=2), description="Verificar fecha de vencimiento de pasaporte para vuelo a Cancún.", event_type="contacto", client_id=client1.id)
    appt3 = models.Appointment(title="Reunión: Elena Torres - Itinerario París", date=now + datetime.timedelta(days=3), description="Reunión en zoom para definir visitas guiadas en París.", event_type="reunion", client_id=client2.id)
    appt4 = models.Appointment(title="Evento: Lanzamiento de Campaña Verano 2025", date=now - datetime.timedelta(days=2), description="Presentación de nuevos paquetes de playa.", event_type="evento")
    db.add_all([appt1, appt2, appt3, appt4])

    db.commit()
    
    # Create WhatsApp Conversations
    conv1 = models.WhatsAppConversation(client_id=client1.id, last_message="Hola, ¿me confirmas el horario del vuelo?")
    db.add(conv1)
    db.commit()
    
    m1 = models.WhatsAppMessage(conversation_id=conv1.id, text="Hola, ¿me confirmas el horario del vuelo?", sender="client")
    m2 = models.WhatsAppMessage(conversation_id=conv1.id, text="¡Hola Juan! Claro, tu vuelo sale a las 10:30 AM.", sender="agent")
    db.add_all([m1, m2])
    
    # Create Exchange Rates
    r1 = models.ExchangeRate(from_currency="USD", to_currency="MXN", rate=17.5)
    db.add(r1)

    # Create Leads
    l1 = models.Lead(name="Carlos Slim", email="carlos@telmex.com", destination="Maldivas", budget=150000, stage="Quotation")
    l2 = models.Lead(name="Sofia Vergara", email="sofia@hollywood.com", destination="Ibiza", budget=200000, stage="Contact")
    db.add_all([l1, l2])

    # Create Package Templates
    pkg1 = models.PackageTemplate(name="Europa Clásica", destination="París-Madrid-Roma", description="15 días de cultura y gastronomía", price=45000, transport_type="Plane")
    pkg2 = models.PackageTemplate(name="Aventura en Chiapas", destination="Chiapas, MX", description="Selva y cascadas con todo incluido", price=15000, transport_type="Bus")
    db.add_all([pkg1, pkg2])
    
    db.commit()
    return {"message": "Database seeded with EVERYTHING!"}

# --- Supplier Endpoints ---
@app.get("/suppliers")
def get_suppliers(db: Session = Depends(get_db)):
    return db.query(models.Supplier).all()

@app.post("/suppliers")
def create_supplier(supplier: SupplierCreate, db: Session = Depends(get_db)):
    db_supplier = models.Supplier(**supplier.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

# --- Notification Endpoints ---
@app.get("/notifications")
def get_notifications(company_id: int | None = None, user_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Notification)
    if company_id:
        query = query.filter(models.Notification.company_id == company_id)
    if user_id:
        query = query.filter((models.Notification.assigned_user_id == user_id) | (models.Notification.assigned_user_id.is_(None)))
    return query.order_by(models.Notification.created_at.desc()).limit(20).all()

@app.post("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int, db: Session = Depends(get_db)):
    notif = db.query(models.Notification).filter(models.Notification.id == notif_id).first()
    if notif:
        notif.is_read = True
        notif.is_read = True
        db.commit()
    return {"status": "ok"}

@app.post("/notifications/read-all")
def mark_all_notifications_read(db: Session = Depends(get_db)):
    db.query(models.Notification).update({models.Notification.is_read: True})
    db.commit()
    return {"status": "ok"}

# --- Accounting Endpoints ---
@app.get("/accounting/summary")
def get_accounting_summary(db: Session = Depends(get_db)):
    payments = db.query(models.Payment).all()
    total_revenue = sum(p.amount for p in payments)
    
    trips = db.query(models.Trip).all()
    total_projected = sum(t.total_price for t in trips)
    
    recent_payments = db.query(models.Payment).order_by(models.Payment.date.desc()).limit(5).all()
    
    # Calculate total commissions (assuming 10% average or from field)
    total_commissions = sum((t.total_price * t.commission_percentage / 100) for t in trips if t.status == "Booked")
    
    return {
        "total_revenue": total_revenue,
        "total_projected": total_projected,
        "pending_balance": total_projected - total_revenue,
        "total_commissions": total_commissions,
        "recent_payments": recent_payments
    }

# --- Calendar Endpoints ---
@app.get("/calendar/events")
def get_calendar_events(company_id: int | None = None, db: Session = Depends(get_db)):
    trips = db.query(models.Trip).all()
    events = []
    for trip in trips:
        if trip.start_date:
            import datetime as dt
            # Classify trip as past or upcoming
            is_past = trip.start_date < dt.datetime.now()
            events.append({
                "id": f"trip-{trip.id}",
                "title": f"Viaje: {trip.destination}",
                "start": trip.start_date.isoformat(),
                "end": trip.end_date.isoformat() if trip.end_date else None,
                "type": "trip_past" if is_past else "trip_upcoming",
                "status": trip.status
            })
    
    appointments_query = db.query(models.Appointment)
    if company_id:
        appointments_query = appointments_query.filter(models.Appointment.company_id == company_id)
        
    appointments = appointments_query.all()
    for appt in appointments:
        events.append({
            "id": f"appt-{appt.id}",
            "title": appt.title,
            "start": appt.date.isoformat(),
            "type": appt.event_type or "reunion",
            "description": appt.description,
            "client_id": appt.client_id,
            "assigned_user_id": appt.assigned_user_id
        })
        
    return events

@app.post("/calendar/events")
def create_calendar_event(event: AppointmentCreate, db: Session = Depends(get_db)):
    db_appt = models.Appointment(
        title=event.title,
        date=event.date,
        description=event.description,
        event_type=event.event_type,
        client_id=event.client_id,
        assigned_user_id=event.assigned_user_id,
        company_id=event.company_id
    )
    db.add(db_appt)
    db.commit()
    db.refresh(db_appt)
    
    # Create system notification
    user_name = "Sin asignar"
    if event.assigned_user_id:
        user = db.query(models.User).filter(models.User.id == event.assigned_user_id).first()
        if user:
            user_name = user.username
            
    client_name = ""
    if event.client_id:
        client = db.query(models.Client).filter(models.Client.id == event.client_id).first()
        if client:
            client_name = f" para {client.name}"
            
    notif_msg = f"Recordatorio: '{event.title}' agendado para el {event.date.strftime('%d/%m/%Y %H:%M')}{client_name}. Asignado a: {user_name}."
    if event.description:
        notif_msg += f" Notas: {event.description}"
        
    db_notif = models.Notification(
        title=f"Recordatorio: {event.title}",
        message=notif_msg,
        company_id=event.company_id,
        assigned_user_id=event.assigned_user_id
    )
    db.add(db_notif)
    db.commit()
    
    return db_appt

# --- Client Profile Endpoints ---
@app.get("/clients/{client_id}/profile")
def get_client_profile(client_id: int, db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    total_spent = sum(sum(p.amount for p in trip.payments) for trip in client.trips)
    
    return {
        "id": client.id,
        "name": client.name,
        "email": client.email,
        "phone": client.phone,
        "passport_number": client.passport_number,
        "notes": client.notes,
        "preferences": client.preferences,
        "created_at": client.created_at,
        "trips": [{
            "id": t.id,
            "destination": t.destination,
            "status": t.status,
            "total_price": t.total_price,
            "paid": sum(p.amount for p in t.payments)
        } for t in client.trips],
        "total_spent": total_spent
    }

# --- Settings Endpoints ---
@app.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    rates = db.query(models.ExchangeRate).all()
    return {"exchange_rates": rates}

@app.post("/settings/exchange-rates")
def update_exchange_rate(rate_data: ExchangeRateCreate, db: Session = Depends(get_db)):
    rate = db.query(models.ExchangeRate).filter(
        models.ExchangeRate.from_currency == rate_data.from_currency,
        models.ExchangeRate.to_currency == rate_data.to_currency
    ).first()
    
    if rate:
        rate.rate = rate_data.rate
        rate.updated_at = datetime.datetime.utcnow()
    else:
        rate = models.ExchangeRate(**rate_data.model_dump())
        db.add(rate)
        
    db.commit()
    return rate

# --- Leads Endpoints ---
@app.get("/leads")
def get_leads(db: Session = Depends(get_db)):
    return db.query(models.Lead).order_by(models.Lead.created_at.desc()).all()

@app.post("/leads")
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    db_lead = models.Lead(**lead.model_dump())
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

@app.put("/leads/{lead_id}/stage")
def update_lead_stage(lead_id: int, stage_data: LeadStageUpdate, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.stage = stage_data.stage
    db.commit()
    return lead

# --- Package Templates Endpoints ---
@app.get("/packages")
def get_packages(db: Session = Depends(get_db)):
    return db.query(models.PackageTemplate).all()

@app.post("/packages")
def create_package(package: PackageTemplateCreate, db: Session = Depends(get_db)):
    db_package = models.PackageTemplate(**package.model_dump())
    db.add(db_package)
    db.commit()
    db.refresh(db_package)
    return db_package

# --- Public Trip Portal Endpoint ---
@app.get("/public/trips/{token}")
def get_public_trip(token: str, db: Session = Depends(get_db)):
    trip = db.query(models.Trip).filter(models.Trip.share_token == token).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found or link expired")
    
    # Return minimal data for public view
    return {
        "destination": trip.destination,
        "start_date": trip.start_date,
        "end_date": trip.end_date,
        "package_name": trip.package_name,
        "transport_type": trip.transport_type,
        "hotels": trip.hotels,
        "assignments": trip.assignments,
        "client_name": trip.client.name,
        "status": trip.status,
        "total_price": trip.total_price,
        "paid": sum(p.amount for p in trip.payments)
    }

# --- Surveys Endpoints ---
@app.post("/surveys")
def create_survey(survey: SurveyCreate, db: Session = Depends(get_db)):
    db_survey = models.Survey(**survey.model_dump())
    db.add(db_survey)
    db.commit()
    db.refresh(db_survey)
    return db_survey

# --- Document Endpoints ---
@app.post("/trips/{trip_id}/documents")
def add_document(trip_id: int, doc: DocumentCreate, db: Session = Depends(get_db)):
    db_doc = models.Document(**doc.model_dump(), trip_id=trip_id)
    db.add(db_doc)
    
    trip = db.query(models.Trip).filter(models.Trip.id == trip_id).first()
    if trip:
        e = models.TimelineEvent(
            event_type="Document Upload",
            description=f"Se subió un nuevo documento: {doc.name}",
            client_id=trip.client_id,
            trip_id=trip_id
        )
        db.add(e)
        
    db.commit()
    db.refresh(db_doc)
    return db_doc

# --- Global Search Endpoint ---
@app.get("/search")
def global_search(q: str, db: Session = Depends(get_db)):
    search_term = f"%{q}%"
    
    clients = db.query(models.Client).filter(models.Client.name.ilike(search_term)).limit(5).all()
    trips = db.query(models.Trip).filter(models.Trip.destination.ilike(search_term)).limit(5).all()
    leads = db.query(models.Lead).filter(models.Lead.name.ilike(search_term)).limit(5).all()
    
    return {
        "clients": [{"id": c.id, "name": c.name, "type": "client"} for c in clients],
        "trips": [{"id": t.id, "destination": t.destination, "type": "trip"} for t in trips],
        "leads": [{"id": l.id, "name": l.name, "type": "lead"} for l in leads]
    }

# --- AI Mock Endpoint ---
@app.post("/ai/generate-itinerary")
def generate_itinerary(req: AIItineraryRequest):
    # This is a mock response that simulates AI generation
    import time
    time.sleep(2) # Simulate processing delay
    
    return {
        "destination": req.destination,
        "description": f"Sumérgete en la belleza de {req.destination}. Un viaje diseñado especialmente considerando: {req.preferences or 'tus gustos únicos'}. Descubre lugares escondidos, gastronomía local y crea recuerdos inolvidables.",
        "suggested_items": [
            {"type": "Flight", "title": f"Vuelo Redondo a {req.destination}", "cost": 15000, "notes": "Vuelo directo con equipaje incluido."},
            {"type": "Hotel", "title": "Hotel Boutique Centro", "cost": 12000, "notes": "Estancia de 5 noches con desayuno buffet."},
            {"type": "Activity", "title": "Tour Privado Local", "cost": 3500, "notes": "Recorrido de 4 horas con guía experto."}
        ]
    }

# --- School CRM Endpoints ---

@app.get("/school/students")
def get_school_students(company_id: int = None, db: Session = Depends(get_db)):
    query = db.query(models.SchoolStudent)
    if company_id:
        query = query.filter(models.SchoolStudent.company_id == company_id)
    return query.all()

@app.post("/school/students")
def create_school_student(student: SchoolStudentCreate, db: Session = Depends(get_db)):
    db_student = models.SchoolStudent(**student.model_dump())
    db_student.qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=Student-{student.email}"
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

@app.get("/school/teachers")
def get_school_teachers(company_id: int = None, db: Session = Depends(get_db)):
    query = db.query(models.SchoolTeacher)
    if company_id:
        query = query.filter(models.SchoolTeacher.company_id == company_id)
    return query.all()

@app.post("/school/teachers")
def create_school_teacher(teacher: SchoolTeacherCreate, db: Session = Depends(get_db)):
    db_teacher = models.SchoolTeacher(**teacher.model_dump())
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

@app.get("/school/classes")
def get_school_classes(company_id: int = None, db: Session = Depends(get_db)):
    query = db.query(models.SchoolClass)
    if company_id:
        query = query.filter(models.SchoolClass.company_id == company_id)
    
    classes = query.all()
    # Build a response that includes students in the class (students who have grades for this class)
    result = []
    for cls in classes:
        # Find students in the same grade
        students_in_grade = db.query(models.SchoolStudent).filter(
            models.SchoolStudent.grade == cls.grade,
            models.SchoolStudent.company_id == cls.company_id
        ).all()
        
        # Build student list with their grades for this specific class
        class_students = []
        for student in students_in_grade:
            grade_record = db.query(models.SchoolGrade).filter(
                models.SchoolGrade.student_id == student.id,
                models.SchoolGrade.class_id == cls.id
            ).first()
            
            class_students.append({
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "currentGrade": grade_record.grade_value if grade_record else 0.0
            })
            
        result.append({
            "id": cls.id,
            "name": cls.name,
            "grade": cls.grade,
            "time": cls.schedule_time,
            "teacher_id": cls.teacher_id,
            "students": class_students
        })
    return result

@app.post("/school/classes")
def create_school_class(cls: SchoolClassCreate, db: Session = Depends(get_db)):
    db_cls = models.SchoolClass(**cls.model_dump())
    db.add(db_cls)
    db.commit()
    db.refresh(db_cls)
    return db_cls

@app.put("/school/grades/{class_id}/{student_id}")
def update_school_grade(class_id: int, student_id: int, grade_data: SchoolGradeUpdate, db: Session = Depends(get_db)):
    grade = db.query(models.SchoolGrade).filter(
        models.SchoolGrade.class_id == class_id,
        models.SchoolGrade.student_id == student_id
    ).first()
    
    if grade:
        grade.grade_value = grade_data.grade_value
    else:
        grade = models.SchoolGrade(
            class_id=class_id,
            student_id=student_id,
            grade_value=grade_data.grade_value
        )
        db.add(grade)
        
    db.commit()
    
    # Update student's overall average
    all_grades = db.query(models.SchoolGrade).filter(models.SchoolGrade.student_id == student_id).all()
    if all_grades:
        avg = sum(g.grade_value for g in all_grades) / len(all_grades)
        student = db.query(models.SchoolStudent).filter(models.SchoolStudent.id == student_id).first()
        if student:
            student.average = avg
            db.commit()
            
    return {"message": "Grade updated successfully"}
