import { apiFetch } from './client';
import type {
  Project,
  Experiment,
  ExperimentDetail,
  LabEntry,
  ExperimentMaterial,
  Attachment,
  Comment,
  Review,
  Signature,
  AuditLog,
  User,
  LoginResponse,
} from '../types';

// Auth
export const login = (username: string, password: string) =>
  apiFetch<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
    skipAuth: true,
  });

// Projects
export const getProjects = () => apiFetch<Project[]>('/projects');

export const getProject = (id: string) => apiFetch<Project>(`/projects/${id}`);

export const createProject = (data: { project_code: string; title: string; description?: string }) =>
  apiFetch<Project>('/projects', { method: 'POST', body: JSON.stringify(data) });

export const updateProject = (id: string, data: { title?: string; description?: string }) =>
  apiFetch<Project>(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(data) });

// Experiments
export interface ExperimentFilters {
  project_id?: string;
  status?: string;
  search?: string;
}

export const getExperiments = (filters?: ExperimentFilters) => {
  const params = new URLSearchParams();
  if (filters?.project_id) params.set('project_id', filters.project_id);
  if (filters?.status) params.set('status', filters.status);
  if (filters?.search) params.set('search', filters.search);
  const qs = params.toString();
  return apiFetch<Experiment[]>(`/experiments${qs ? `?${qs}` : ''}`);
};

export const getExperiment = (id: string) =>
  apiFetch<ExperimentDetail>(`/experiments/${id}`);

export const getExperimentEntries = (id: string) =>
  apiFetch<LabEntry[]>(`/experiments/${id}/entries`);

export const createExperiment = (data: {
  title: string;
  purpose?: string;
  project_id?: string;
}) =>
  apiFetch<Experiment>('/experiments', { method: 'POST', body: JSON.stringify(data) });

export const transitionStatus = (id: string, new_status: string, comment?: string) =>
  apiFetch<Experiment>(`/experiments/${id}/status`, {
    method: 'POST',
    body: JSON.stringify({ new_status, comment }),
  });

// Lab Entries
export const getLabEntry = (experimentId: string, section: string) =>
  apiFetch<LabEntry>(`/experiments/${experimentId}/entries/${section}`);

export const updateLabEntry = (experimentId: string, section: string, content: string) =>
  apiFetch<LabEntry>(`/experiments/${experimentId}/entries/${section}`, {
    method: 'PUT',
    body: JSON.stringify({ content }),
  });

// Materials
export const getMaterials = (experimentId: string) =>
  apiFetch<ExperimentMaterial[]>(`/experiments/${experimentId}/materials`);

export const addMaterial = (
  experimentId: string,
  data: {
    material_name: string;
    lot_number?: string;
    quantity_used?: number;
    unit?: string;
    barcode?: string;
    notes?: string;
  }
) =>
  apiFetch<ExperimentMaterial>(`/experiments/${experimentId}/materials`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

// Attachments
export const getAttachments = (experimentId: string) =>
  apiFetch<Attachment[]>(`/experiments/${experimentId}/attachments`);

export const uploadAttachment = (experimentId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiFetch<Attachment>(`/experiments/${experimentId}/attachments`, {
    method: 'POST',
    body: formData,
  });
};

export const downloadAttachmentUrl = (attachmentId: string) =>
  `/attachments/${attachmentId}/download`;

// Comments
export const getComments = (experimentId: string) =>
  apiFetch<Comment[]>(`/experiments/${experimentId}/comments`);

export const addComment = (experimentId: string, content: string, comment_type = 'general') =>
  apiFetch<Comment>(`/experiments/${experimentId}/comments`, {
    method: 'POST',
    body: JSON.stringify({ content, comment_type }),
  });

// Reviews
export const getReviews = (experimentId: string) =>
  apiFetch<Review[]>(`/experiments/${experimentId}/reviews`);

export const createReview = (experimentId: string, reviewer_id: string) =>
  apiFetch<Review>(`/experiments/${experimentId}/reviews`, {
    method: 'POST',
    body: JSON.stringify({ reviewer_id }),
  });

export const updateReview = (
  reviewId: string,
  data: { status: string; comments?: string }
) =>
  apiFetch<Review>(`/reviews/${reviewId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

// Signatures
export const getSignatures = (experimentId: string) =>
  apiFetch<Signature[]>(`/experiments/${experimentId}/signatures`);

export const signExperiment = (
  experimentId: string,
  signature_type: string,
  meaning: string
) =>
  apiFetch<Signature>(`/experiments/${experimentId}/sign`, {
    method: 'POST',
    body: JSON.stringify({ signature_type, meaning }),
  });

// Users
export const getUsers = () => apiFetch<User[]>('/users');

export const createUser = (data: {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  roles?: string[];
}) =>
  apiFetch<User>('/users', { method: 'POST', body: JSON.stringify(data) });

// Audit Log
export const getAuditLog = (entityId: string) =>
  apiFetch<{ items: AuditLog[] }>(`/audit?entity_id=${entityId}`)
    .then(res => res.items);

// Barcode
export const lookupBarcode = (barcode: string) =>
  apiFetch<Experiment>(`/barcodes/lookup?barcode=${encodeURIComponent(barcode)}`);
