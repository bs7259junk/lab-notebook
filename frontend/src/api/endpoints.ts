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

export const getProject = (id: number) => apiFetch<Project>(`/api/projects/${id}`);

export const createProject = (data: { title: string; description?: string }) =>
  apiFetch<Project>('/projects', { method: 'POST', body: JSON.stringify(data) });

// Experiments
export interface ExperimentFilters {
  project_id?: number;
  status?: string;
  search?: string;
}

export const getExperiments = (filters?: ExperimentFilters) => {
  const params = new URLSearchParams();
  if (filters?.project_id) params.set('project_id', String(filters.project_id));
  if (filters?.status) params.set('status', filters.status);
  if (filters?.search) params.set('search', filters.search);
  const qs = params.toString();
  return apiFetch<Experiment[]>(`/api/experiments${qs ? `?${qs}` : ''}`);
};

export const getExperiment = (id: number) =>
  apiFetch<ExperimentDetail>(`/api/experiments/${id}`);

export const createExperiment = (data: {
  title: string;
  purpose?: string;
  project_id?: number;
}) =>
  apiFetch<Experiment>('/experiments', { method: 'POST', body: JSON.stringify(data) });

export const transitionStatus = (id: number, new_status: string, comment?: string) =>
  apiFetch<Experiment>(`/api/experiments/${id}/status`, {
    method: 'POST',
    body: JSON.stringify({ new_status, comment }),
  });

// Lab Entries
export const getLabEntry = (experimentId: number, section: string) =>
  apiFetch<LabEntry>(`/api/experiments/${experimentId}/entries/${section}`);

export const updateLabEntry = (experimentId: number, section: string, content: string) =>
  apiFetch<LabEntry>(`/api/experiments/${experimentId}/entries/${section}`, {
    method: 'PUT',
    body: JSON.stringify({ content }),
  });

// Materials
export const addMaterial = (
  experimentId: number,
  data: {
    material_name: string;
    lot_number?: string;
    quantity_used?: number;
    unit?: string;
    barcode?: string;
  }
) =>
  apiFetch<ExperimentMaterial>(`/api/experiments/${experimentId}/materials`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

// Attachments
export const getAttachments = (experimentId: number) =>
  apiFetch<Attachment[]>(`/api/experiments/${experimentId}/attachments`);

export const uploadAttachment = (experimentId: number, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return apiFetch<Attachment>(`/api/experiments/${experimentId}/attachments`, {
    method: 'POST',
    body: formData,
  });
};

export const downloadAttachment = (experimentId: number, attachmentId: number) =>
  `/api/experiments/${experimentId}/attachments/${attachmentId}/download`;

// Comments
export const getComments = (experimentId: number) =>
  apiFetch<Comment[]>(`/api/experiments/${experimentId}/comments`);

export const addComment = (experimentId: number, content: string, parent_id?: number) =>
  apiFetch<Comment>(`/api/experiments/${experimentId}/comments`, {
    method: 'POST',
    body: JSON.stringify({ content, parent_id }),
  });

// Reviews
export const getReviews = (experimentId: number) =>
  apiFetch<Review[]>(`/api/experiments/${experimentId}/reviews`);

export const createReview = (experimentId: number, reviewer_id: number) =>
  apiFetch<Review>(`/api/experiments/${experimentId}/reviews`, {
    method: 'POST',
    body: JSON.stringify({ reviewer_id }),
  });

export const updateReview = (
  experimentId: number,
  reviewId: number,
  data: { status: string; comments?: string }
) =>
  apiFetch<Review>(`/api/experiments/${experimentId}/reviews/${reviewId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

// Signatures
export const getSignatures = (experimentId: number) =>
  apiFetch<Signature[]>(`/api/experiments/${experimentId}/signatures`);

export const signExperiment = (
  experimentId: number,
  signature_type: string,
  meaning: string
) =>
  apiFetch<Signature>(`/api/experiments/${experimentId}/signatures`, {
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
export const getAuditLog = (entityId: number) =>
  apiFetch<AuditLog[]>(`/api/audit?entity_id=${entityId}`);

// Barcode
export const lookupBarcode = (barcode: string) =>
  apiFetch<Experiment>(`/api/barcodes/experiments/${barcode}`);
