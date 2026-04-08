export type ExperimentStatus =
  | 'draft'
  | 'active'
  | 'completed'
  | 'signed'
  | 'in_review'
  | 'approved'
  | 'archived';

export interface Project {
  id: number;
  project_id: string;
  title: string;
  description: string | null;
  status: string;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

export interface Experiment {
  id: number;
  experiment_id: string;
  title: string;
  purpose: string | null;
  status: ExperimentStatus;
  project_id: number | null;
  owner_id: number;
  version: number;
  barcode: string | null;
  created_at: string;
  updated_at: string;
  project?: Project;
  owner?: User;
}

export interface LabEntry {
  id: number;
  experiment_id: number;
  section: string;
  content: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ExperimentMaterial {
  id: number;
  experiment_id: number;
  material_name: string;
  lot_number: string | null;
  quantity_used: number | null;
  unit: string | null;
  barcode: string | null;
  created_at: string;
}

export interface Attachment {
  id: number;
  experiment_id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  content_type: string;
  uploader_id: number;
  created_at: string;
  uploader?: User;
}

export interface Comment {
  id: number;
  experiment_id: number;
  author_id: number;
  content: string;
  parent_id: number | null;
  created_at: string;
  updated_at: string;
  author?: User;
}

export interface Review {
  id: number;
  experiment_id: number;
  reviewer_id: number;
  status: 'pending' | 'in_review' | 'approved' | 'returned';
  comments: string | null;
  created_at: string;
  updated_at: string;
  reviewer?: User;
}

export interface Signature {
  id: number;
  experiment_id: number;
  signer_id: number;
  signature_type: string;
  meaning: string;
  signed_at: string;
  signer?: User;
}

export interface AuditLog {
  id: number;
  entity_type: string;
  entity_id: number;
  action: string;
  actor_username: string;
  timestamp: string;
  old_value: string | null;
  new_value: string | null;
}

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  roles: string[];
  created_at?: string;
}

export interface ExperimentDetail extends Experiment {
  entries: LabEntry[];
  materials: ExperimentMaterial[];
  participants: User[];
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}
