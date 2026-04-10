export type ExperimentStatus =
  | 'draft'
  | 'active'
  | 'completed'
  | 'signed'
  | 'in_review'
  | 'under_review'
  | 'approved'
  | 'archived';

export interface Project {
  id: string;
  project_code: string;
  title: string;
  description: string | null;
  status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface Experiment {
  id: string;
  experiment_id: string;
  title: string;
  purpose: string | null;
  status: ExperimentStatus;
  project_id: string | null;
  owner_id: string;
  version: number;
  barcode: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface LabEntry {
  id: string;
  experiment_id: string;
  section: string;
  content: string;
  version: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ExperimentMaterial {
  id: string;
  experiment_id: string;
  material_name: string;
  lot_number: string | null;
  quantity_used: number | null;
  unit: string | null;
  barcode: string | null;
  notes: string | null;
  added_by: string;
  added_at: string;
}

export interface Attachment {
  id: string;
  experiment_id: string;
  filename: string;
  stored_filename: string;
  file_size_bytes: number;
  content_type: string;
  uploaded_by: string;
  uploaded_at: string;
  description: string | null;
}

export interface Comment {
  id: string;
  experiment_id: string;
  author_id: string;
  comment_type: string;
  content: string;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface Review {
  id: string;
  experiment_id: string;
  reviewer_id: string;
  status: 'pending' | 'in_review' | 'approved' | 'returned';
  comments: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface Signature {
  id: string;
  experiment_id: string;
  signer_id: string;
  signature_type: string;
  meaning: string;
  signed_at: string;
  ip_address: string | null;
}

export interface AuditLog {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor_username: string | null;
  timestamp: string;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
}

export interface UserRole {
  id: string;
  role: string;
  assigned_at: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  roles: UserRole[];
  created_at?: string;
  updated_at?: string;
}

export interface ExperimentDetail extends Experiment {
  entries?: LabEntry[];
  materials?: ExperimentMaterial[];
  participants?: Array<{ id: string; user_id: string; role: string; added_at: string }>;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
