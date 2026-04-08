# 21 CFR Part 11 Compliance Notes

## Overview

21 CFR Part 11 (Electronic Records; Electronic Signatures) sets FDA requirements
for systems that create, modify, maintain, archive, retrieve, or transmit electronic
records and electronic signatures that are required to be maintained under FDA
regulations.

This document describes which Part 11 requirements are addressed by the current MVP
scaffold and what additional work is required for full compliance certification.

---

## Requirements Addressed by the MVP

### 1. Audit Trail (§11.10(e))

**Requirement:** Computer-generated, date/time stamped audit trails must record
operator entries and actions that create, modify, or delete electronic records.

**Implementation:**
- The `audit_logs` table is append-only. Application code contains no `UPDATE` or
  `DELETE` operations against this table.
- Every service method that modifies data calls `audit_service.log_action()`, which
  records: `entity_type`, `entity_id`, `action`, `actor_id`, `actor_username`,
  `old_value`, `new_value`, `ip_address`, and a server-generated `timestamp`.
- The `timestamp` column uses `server_default=func.now()` — the database server
  sets the timestamp, it is never accepted from the client.
- `actor_username` is denormalized into every row so that the audit record remains
  accurate even if a user account is later deleted.
- The `/audit` endpoint exposes paginated, filterable audit logs to authorized users
  (admin and reviewer roles only).

### 2. Unique User Identification (§11.10(d) / §11.300(a))

**Requirement:** Each system user must have a unique ID. Shared login credentials
are prohibited.

**Implementation:**
- Every `User` record has a UUID primary key, a unique `username`, and a unique `email`.
- Database-level `UNIQUE` constraints on both `username` and `email` prevent duplicates.
- JWT tokens encode the user's UUID (`sub` claim) — tokens cannot be forged without
  the `SECRET_KEY`.
- The `actor_id` and `actor_username` fields in `AuditLog` tie every action to a
  specific individual.

### 3. Access Controls (§11.10(d))

**Requirement:** Limit system access to authorized individuals.

**Implementation:**
- All API endpoints (except `/health`) require a valid JWT access token.
- The `require_roles()` dependency enforces role-based access control (RBAC).
  Defined roles: `admin`, `scientist`, `technician`, `research_associate`, `reviewer`.
- Administrative endpoints (user management, audit log) are restricted to the `admin`
  and/or `reviewer` roles.
- Experiments in `approved` or `archived` status are write-locked at the service layer
  (`experiment_service.LOCKED_STATUSES`) to prevent post-approval modifications.

### 4. Electronic Signatures with Meaning (§11.50 / §11.70)

**Requirement:** Electronic signatures must be linked to their respective electronic
records. Each signature must include the meaning of the signature (e.g., review,
approval, authorship).

**Implementation:**
- The `Signature` model stores: `signer_id`, `experiment_id`, `signature_type`
  (completion / review / approval), and `meaning` (a required free-text field
  capturing the legal meaning of the signature).
- The `meaning` field has a minimum length of 10 characters — the form cannot be
  submitted without a substantive meaning statement.
- `ip_address` and `user_agent` are captured for each signature.
- The reviewer-cannot-equal-owner constraint is enforced in `review_service.add_signature()`
  for review-type signatures.
- Signatures are linked to specific experiment records by `experiment_id` foreign key.

### 5. Server-side Timestamps

**Requirement:** Date/time stamps must be computer-generated and accurate.

**Implementation:**
- `AuditLog.timestamp` uses `server_default=func.now()` — set by the PostgreSQL
  server, never from application code or client input.
- All `created_at` / `updated_at` / `signed_at` fields use `server_default=func.now()`.

### 6. Record Integrity — Approved Experiments

**Implementation:**
- Experiments in `approved` or `archived` status raise HTTP 409 if any update is
  attempted (`experiment_service.LOCKED_STATUSES`).
- Status transitions are validated against `ALLOWED_TRANSITIONS` — only defined
  state machine paths are permitted.

---

## What Is Needed for Full Compliance

The following items are required for a validated, production-ready Part 11 system
and are **not yet implemented** in this MVP scaffold:

### A. Validated System Documentation (§11.10(a))

- **System Validation (IQ/OQ/PQ):** Installation Qualification, Operational
  Qualification, and Performance Qualification documentation must be produced and
  approved before the system is used for regulated activities.
- **Validation Summary Report** with test scripts and results.
- **Software Development Life Cycle (SDLC)** documentation.
- **21 CFR Part 11 Assessment Report** mapping each regulation subsection to a
  specific system control.

### B. Password Complexity and Account Controls (§11.300(b-e))

- Enforce minimum password length (≥12 chars), complexity rules (upper/lower/digit/special).
- Password expiration policy (e.g., every 90 days) with enforcement.
- Account lockout after N failed login attempts (e.g., 5) — currently not implemented.
- Password history enforcement (prevent reuse of last N passwords).

### C. Session Timeout (§11.10(d))

- Inactive sessions must be automatically terminated.
- The backend should track last-activity timestamps and invalidate tokens after a
  configurable idle period (e.g., 15–30 minutes).
- The frontend must handle session expiry gracefully with a re-authentication prompt.
- Consider implementing a token revocation/blocklist mechanism (e.g., using Redis)
  rather than relying solely on JWT expiry.

### D. Audit Log Retention (§11.10(e))

- Audit records must be retained for the lifetime of the record plus any additional
  period required by applicable regulations (often ≥5–10 years).
- Implement automated archival to durable, tamper-evident storage.
- Consider write-once (WORM) storage for audit logs in cloud deployments.
- Regular audit log integrity checks (e.g., hash-chaining or cryptographic signatures
  on log batches).

### E. Backup and Recovery (§11.10(c))

- Documented backup procedures with tested recovery processes.
- Point-in-time recovery capability for the PostgreSQL database.
- Off-site backup replication.
- Documented Recovery Time Objective (RTO) and Recovery Point Objective (RPO).

### F. Training Records (§11.10(i))

- The system should track that each user has completed required training before
  granting access.
- Training records must be maintained and auditable.

### G. System Access Controls — Additional (§11.10(d))

- Multi-factor authentication (MFA) for privileged roles (admin, reviewer).
- Role assignment approval workflow — currently admin can assign roles without a
  second approver.
- Periodic access review reminders/enforcement.

### H. Electronic Signature Binding (§11.70)

- Electronic signatures must be linked to their electronic records in a way that
  prevents removal, copying, or transferring of the signature.
- Consider adding a cryptographic hash of the experiment record at the time of
  signing, stored in `Signature.record_hash` (to be added), to detect any
  post-signature tampering.

### I. Closed vs. Open System Controls (§11.30)

- If the system is accessible over the internet (open system), additional controls
  are required including encryption in transit (TLS 1.2+) enforced at the network
  layer.
- Document the network architecture and confirm end-to-end encryption.

### J. 21 CFR Part 11 Procedures and Controls (§11.10(k))

- Written policies covering: use of open and closed systems, authority checks,
  device checks, personnel training, accountability provisions.
- Incident response procedures for potential record falsification.

---

## Summary Table

| Requirement | §11 Section | MVP Status |
|---|---|---|
| Audit trail (append-only, timestamped) | §11.10(e) | Implemented |
| Unique user IDs | §11.10(d), §11.300(a) | Implemented |
| JWT authentication | §11.10(d) | Implemented |
| Role-based access control | §11.10(d) | Implemented |
| Electronic signatures with meaning | §11.50, §11.70 | Implemented |
| Reviewer ≠ author enforcement | §11.70 | Implemented |
| Write-lock approved records | §11.10(e) | Implemented |
| Server-side timestamps | §11.10(e) | Implemented |
| Password complexity enforcement | §11.300(b) | Not yet |
| Account lockout | §11.300(b) | Not yet |
| Session timeout | §11.10(d) | Not yet |
| Token revocation | §11.10(d) | Not yet |
| Signature record hash binding | §11.70 | Not yet |
| Audit log retention/archival | §11.10(e) | Not yet |
| Backup and recovery | §11.10(c) | Not yet |
| System validation documentation | §11.10(a) | Not yet |
| Training records | §11.10(i) | Not yet |
| MFA for privileged roles | §11.10(d) | Not yet |
