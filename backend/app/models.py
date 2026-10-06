import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class ConnectedAccount(Base):
    __tablename__ = "connected_accounts"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    access_token_encrypted = Column(Text, nullable=True)
    refresh_token_encrypted = Column(Text, nullable=True)
    token_uri = Column(String, nullable=True)
    client_id = Column(String, nullable=True)
    scopes = Column(Text, nullable=True)
    status = Column(String, default="disconnected")  # connected, error, disconnected
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class MailboxSyncState(Base):
    __tablename__ = "mailbox_sync_state"

    id = Column(String, primary_key=True, default=generate_uuid)
    account_email = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, default="idle")  # idle, discovering, processing, complete, error
    total_discovered = Column(Integer, default=0)
    scanned_count = Column(Integer, default=0)
    irrelevant_count = Column(Integer, default=0)
    supplier_email_count = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    products_extracted_count = Column(Integer, default=0)
    pdfs_saved_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    current_speed = Column(Float, default=0.0)  # msgs/sec
    elapsed_seconds = Column(Float, default=0.0)
    eta_seconds = Column(Float, default=0.0)
    estimated_completion = Column(DateTime, nullable=True)
    next_page_token = Column(String, nullable=True)
    last_history_id = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class Email(Base):
    __tablename__ = "emails"

    id = Column(String, primary_key=True, default=generate_uuid)
    gmail_message_id = Column(String, unique=True, nullable=False, index=True)
    gmail_thread_id = Column(String, nullable=False, index=True)
    account_email = Column(String, nullable=False, index=True)
    sender = Column(String, nullable=False, index=True)
    sender_domain = Column(String, nullable=False, index=True)
    recipient = Column(String, nullable=True)
    subject = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    body_html_sanitized = Column(Text, nullable=True)
    received_at = Column(DateTime, nullable=False, index=True)
    classification = Column(String, default="unclassified", index=True)  # relevant, irrelevant, uncertain
    classification_reason = Column(String, nullable=True)
    processing_status = Column(String, default="pending", index=True)  # pending, processing, processed, review_required, failed, ignored
    product_count = Column(Integer, default=0)
    pdf_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    source_email_link = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    products = relationship("Product", back_populates="email", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="email", cascade="all, delete-orphan")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, index=True)
    domain = Column(String, unique=True, nullable=False, index=True)
    primary_email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    country = Column(String, nullable=True)
    product_count = Column(Integer, default=0)
    email_count = Column(Integer, default=0)
    catalogue_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    products = relationship("Product", back_populates="supplier")
    attachments = relationship("Attachment", back_populates="supplier")


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=generate_uuid)
    email_id = Column(String, ForeignKey("emails.id"), nullable=False, index=True)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=True, index=True)
    name = Column(String, nullable=False, index=True)
    title = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)
    brand = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    model = Column(String, nullable=True, index=True)
    sku = Column(String, nullable=True, index=True)
    series = Column(String, nullable=True)
    variant = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    quotation_ref = Column(String, nullable=True)
    quantity = Column(Float, nullable=True)
    available_quantity = Column(Float, nullable=True)
    moq = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    unit_price = Column(Float, nullable=True)
    price = Column(Float, nullable=True, index=True)
    tier_pricing = Column(Text, nullable=True)
    total_price = Column(Float, nullable=True)
    currency = Column(String, nullable=True, index=True)
    discount = Column(String, nullable=True)
    taxes = Column(String, nullable=True)
    shipping_charges = Column(String, nullable=True)
    tooling_cost = Column(String, nullable=True)
    dimensions = Column(String, nullable=True)
    weight = Column(String, nullable=True)
    material = Column(String, nullable=True)
    capacity = Column(String, nullable=True)
    voltage = Column(String, nullable=True)
    current = Column(String, nullable=True)
    power = Column(String, nullable=True)
    speed_rpm = Column(String, nullable=True)
    pressure = Column(String, nullable=True)
    temperature_range = Column(String, nullable=True)
    ip_rating = Column(String, nullable=True)
    certifications = Column(String, nullable=True)
    country_of_origin = Column(String, nullable=True)
    hs_code = Column(String, nullable=True)
    warranty = Column(String, nullable=True)
    lead_time = Column(String, nullable=True)
    shipping_terms = Column(String, nullable=True)
    incoterms = Column(String, nullable=True)
    payment_terms = Column(String, nullable=True)
    quotation_validity = Column(String, nullable=True)
    contact_details = Column(Text, nullable=True)
    catalogue_link = Column(String, nullable=True)
    source_email_link = Column(String, nullable=True)
    received_at = Column(DateTime, nullable=False, index=True)
    confidence_score = Column(Float, default=1.0)
    review_status = Column(String, default="confirmed", index=True)  # confirmed, needs_review, user_approved
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    email = relationship("Email", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    dynamic_attributes = relationship("ProductAttribute", back_populates="product", cascade="all, delete-orphan")


class ProductAttribute(Base):
    __tablename__ = "product_attributes"

    id = Column(String, primary_key=True, default=generate_uuid)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    attribute_name = Column(String, nullable=False, index=True)
    attribute_value = Column(Text, nullable=False)
    unit = Column(String, nullable=True)
    source_email_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    product = relationship("Product", back_populates="dynamic_attributes")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(String, primary_key=True, default=generate_uuid)
    email_id = Column(String, ForeignKey("emails.id"), nullable=False, index=True)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=True, index=True)
    gmail_attachment_id = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    is_pdf = Column(Boolean, default=False, index=True)
    storage_path = Column(String, nullable=True)
    drive_file_id = Column(String, nullable=True)
    web_view_link = Column(String, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    email = relationship("Email", back_populates="attachments")
    supplier = relationship("Supplier", back_populates="attachments")


class PdfLink(Base):
    __tablename__ = "pdf_links"

    id = Column(String, primary_key=True, default=generate_uuid)
    attachment_id = Column(String, ForeignKey("attachments.id"), nullable=False)
    email_id = Column(String, nullable=False, index=True)
    supplier_id = Column(String, nullable=True, index=True)
    filename = Column(String, nullable=False)
    web_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=utc_now)


class ReviewItem(Base):
    __tablename__ = "review_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    email_id = Column(String, ForeignKey("emails.id"), nullable=False, index=True)
    product_id = Column(String, nullable=True)
    issue_type = Column(String, nullable=False)  # ambiguous_price, multiple_models, format_uncertainty
    uncertainty_reason = Column(Text, nullable=False)
    candidate_values = Column(JSON, nullable=True)
    confidence = Column(Float, default=0.5)
    status = Column(String, default="pending", index=True)  # pending, resolved, dismissed
    created_at = Column(DateTime, default=utc_now)
    resolved_at = Column(DateTime, nullable=True)


class SheetSyncState(Base):
    __tablename__ = "sheet_sync_state"

    id = Column(String, primary_key=True, default=generate_uuid)
    spreadsheet_id = Column(String, nullable=True)
    spreadsheet_url = Column(String, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    products_synced = Column(Integer, default=0)
    emails_synced = Column(Integer, default=0)
    attachments_synced = Column(Integer, default=0)
    status = Column(String, default="idle")  # idle, syncing, complete, error
    error_message = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    job_type = Column(String, nullable=False, index=True)
    gmail_message_id = Column(String, nullable=False, index=True)
    status = Column(String, default="queued", index=True)  # queued, running, completed, failed
    retries = Column(Integer, default=0)
    checkpoint_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_type = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)

