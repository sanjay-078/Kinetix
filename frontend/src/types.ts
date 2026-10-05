export interface DashboardStats {
  cards: {
    products: number;
    suppliers: number;
    emails_processed: number;
    catalogues: number;
    needs_review: number;
  };
  live_progress: {
    status: string;
    account_email: string;
    total_discovered: number;
    scanned_count: number;
    irrelevant_count: number;
    supplier_email_count: number;
    processed_count: number;
    products_extracted_count: number;
    pdfs_saved_count: number;
    failure_count: number;
    retry_count: number;
    current_speed: number;
    elapsed_seconds: number;
    eta_seconds: number;
    estimated_completion: string | null;
    current_status_label: string;
  };
}

export interface ProductItem {
  id: string;
  name: string;
  model: string | null;
  sku: string | null;
  supplier: string;
  supplier_id: string | null;
  price: number | null;
  currency: string;
  quantity: number | null;
  moq: string | null;
  unit: string | null;
  lead_time: string | null;
  description: string | null;
  catalogue_link: string | null;
  source_email_link: string | null;
  received_at: string | null;
  dynamic_attributes_count?: number;
}

export interface SupplierItem {
  id: string;
  name: string;
  domain: string;
  primary_email: string | null;
  phone: string | null;
  country: string | null;
  product_count: number;
  email_count: number;
  catalogue_count: number;
}

export interface EmailItem {
  id: string;
  gmail_message_id: string;
  sender: string;
  sender_domain: string;
  subject: string;
  snippet: string;
  received_at: string | null;
  classification: string;
  classification_reason: string;
  processing_status: string;
  product_count: number;
  pdf_count: number;
  source_email_link: string;
}

export interface CatalogueItem {
  id: string;
  filename: string;
  supplier: string;
  supplier_id: string | null;
  email_id: string;
  mime_type: string;
  file_size: number;
  web_view_link: string;
  created_at: string | null;
}

export interface ReviewItem {
  id: string;
  email_id: string;
  product_id: string | null;
  issue_type: string;
  uncertainty_reason: string;
  candidate_values: any;
  confidence: number;
  status: string;
  created_at: string | null;
  email?: {
    subject: string;
    sender: string;
    source_email_link: string;
  };
}
