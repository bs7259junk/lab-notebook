"""
Seed script for the Electronic Lab Notebook.

Creates:
- 5 users with realistic roles
- 3 projects
- 10 experiments across projects
- 8 materials in the catalog
- Lab entries, materials usage, comments, reviews, signatures
- Audit log entries for all seed actions

Run with:
    cd backend && python -m app.etl.seed
"""
from __future__ import annotations

import sys
import os

# Allow running as a script from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime, timezone

from sqlalchemy.orm import Session

# Pre-computed bcrypt hash for "test" — avoids passlib/bcrypt version conflict
DUMMY_HASH = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"


def hash_password(_plain: str) -> str:
    return DUMMY_HASH
from app.db import SessionLocal, engine
from app.models.models import Base
from app.repositories.audit_repo import create_audit_log
from app.repositories.experiment_repo import generate_experiment_id
from app.models.models import (
    Comment,
    Experiment,
    ExperimentMaterial,
    ExperimentParticipant,
    LabEntry,
    Material,
    Project,
    Review,
    Signature,
    User,
    UserRole,
)

PASSWORD = "Lab2026!"


def seed(db: Session) -> None:
    print("Seeding database...")
    # Wipe existing data so seed is idempotent
    print("  Clearing existing data...")
    for table in [
        "audit_logs", "signatures", "reviews", "comments",
        "experiment_materials", "lab_entries", "experiment_participants",
        "attachments", "experiments", "materials", "projects",
        "user_roles", "users",
    ]:
        db.execute(__import__("sqlalchemy").text(f"TRUNCATE TABLE {table} CASCADE"))
    db.flush()

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    print("  Creating users...")

    admin = User(
        username="admin",
        email="admin@lab.com",
        full_name="Lab Administrator",
        hashed_password=hash_password(PASSWORD),
        is_active=True,
    )
    alice = User(
        username="alice",
        email="alice@lab.com",
        full_name="Alice Chen",
        hashed_password=hash_password(PASSWORD),
        is_active=True,
    )
    bob = User(
        username="bob",
        email="bob@lab.com",
        full_name="Bob Martinez",
        hashed_password=hash_password(PASSWORD),
        is_active=True,
    )
    carol = User(
        username="carol",
        email="carol@lab.com",
        full_name="Carol Wu",
        hashed_password=hash_password(PASSWORD),
        is_active=True,
    )
    dave = User(
        username="dave",
        email="dave@lab.com",
        full_name="Dave Kim",
        hashed_password=hash_password(PASSWORD),
        is_active=True,
    )

    for u in [admin, alice, bob, carol, dave]:
        db.add(u)
    db.flush()

    # Roles
    roles_map = {
        admin.id: ["admin"],
        alice.id: ["scientist"],
        bob.id: ["technician"],
        carol.id: ["research_associate", "scientist"],
        dave.id: ["reviewer"],
    }
    for user_id, roles in roles_map.items():
        for role in roles:
            db.add(UserRole(user_id=user_id, role=role, assigned_by=admin.id))
    db.flush()

    for u in [admin, alice, bob, carol, dave]:
        create_audit_log(
            db=db,
            entity_type="user",
            entity_id=str(u.id),
            action="created",
            actor_id=admin.id,
            actor_username=admin.username,
            new_value={"username": u.username, "email": u.email},
        )

    # ------------------------------------------------------------------
    # Materials catalog
    # ------------------------------------------------------------------
    print("  Creating materials catalog...")

    mat_data = [
        {
            "name": "Anti-CD19 Antibody (Clone FMC63)",
            "catalog_number": "MAB-CD19-001",
            "vendor": "BioLegend",
            "barcode": "MAT-BL-001",
        },
        {
            "name": "Ficoll-Paque PLUS",
            "catalog_number": "17-1440-03",
            "vendor": "Cytiva",
            "barcode": "MAT-CY-002",
        },
        {
            "name": "RPMI 1640 Medium",
            "catalog_number": "11875093",
            "vendor": "Thermo Fisher Scientific",
            "barcode": "MAT-TF-003",
        },
        {
            "name": "Fetal Bovine Serum (FBS), Heat-Inactivated",
            "catalog_number": "10500064",
            "vendor": "Thermo Fisher Scientific",
            "barcode": "MAT-TF-004",
        },
        {
            "name": "Lentiviral Transduction Reagent (TransIT-Lenti)",
            "catalog_number": "MIR6600",
            "vendor": "Mirus Bio",
            "barcode": "MAT-MB-005",
        },
        {
            "name": "Chromium-51 Sodium Chromate",
            "catalog_number": "CJS1",
            "vendor": "PerkinElmer",
            "barcode": "MAT-PE-006",
        },
        {
            "name": "LGALS3BP ELISA Kit (Human)",
            "catalog_number": "E-EL-H0655",
            "vendor": "Elabscience",
            "barcode": "MAT-EL-007",
        },
        {
            "name": "Anti-CD19 CAR Lentiviral Vector (FMC63, 3rd gen)",
            "catalog_number": "LV-CD19-3G",
            "vendor": "VectorBuilder",
            "barcode": "MAT-VB-008",
        },
    ]

    materials = []
    for md in mat_data:
        m = Material(**md)
        db.add(m)
        materials.append(m)
    db.flush()

    for m in materials:
        create_audit_log(
            db=db,
            entity_type="material",
            entity_id=str(m.id),
            action="created",
            actor_id=admin.id,
            actor_username=admin.username,
            new_value={"name": m.name, "catalog_number": m.catalog_number},
        )

    # Convenience references
    anticd19, ficoll, rpmi, fbs, lenti, cr51, lgals3bp_kit, car_vector = materials

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------
    print("  Creating projects...")

    proj_cart = Project(
        project_code="CELL-THERAPY-01",
        title="CAR-T Cell Development",
        description=(
            "Development and optimization of CD19-targeted CAR-T cell therapy "
            "for B-cell malignancies. Includes cell isolation, transduction, "
            "expansion, and cytotoxicity assays."
        ),
        status="active",
        created_by=admin.id,
    )
    proj_bio = Project(
        project_code="BIOMARKER-02",
        title="Biomarker Discovery",
        description=(
            "Identification and validation of novel serum biomarkers for "
            "early-stage colorectal cancer detection using proteomics and "
            "machine learning approaches."
        ),
        status="active",
        created_by=admin.id,
    )
    proj_proc = Project(
        project_code="PROCESS-03",
        title="Process Optimization",
        description=(
            "Optimization of upstream and downstream bioprocessing parameters "
            "for monoclonal antibody production to improve yield and reduce costs."
        ),
        status="active",
        created_by=admin.id,
    )

    for p in [proj_cart, proj_bio, proj_proc]:
        db.add(p)
    db.flush()

    for p in [proj_cart, proj_bio, proj_proc]:
        create_audit_log(
            db=db,
            entity_type="project",
            entity_id=str(p.id),
            action="created",
            actor_id=admin.id,
            actor_username=admin.username,
            new_value={"project_code": p.project_code, "title": p.title},
        )

    # ------------------------------------------------------------------
    # Experiments
    # ------------------------------------------------------------------
    print("  Creating experiments...")

    # Experiment 1: draft
    exp1 = Experiment(
        experiment_id="EXP-2026-001",
        title="PBMC Isolation from Healthy Donor Buffy Coats",
        purpose=(
            "Isolate peripheral blood mononuclear cells (PBMCs) from healthy donor "
            "buffy coat samples using Ficoll density gradient centrifugation as starting "
            "material for downstream CAR-T cell manufacturing."
        ),
        project_id=proj_cart.id,
        owner_id=alice.id,
        status="draft",
        barcode="EXP-BC-001",
    )

    # Experiment 2: in_progress
    exp2 = Experiment(
        experiment_id="EXP-2026-002",
        title="Lentiviral Transduction of T Cells with CD19-CAR Construct",
        purpose=(
            "Transduce activated primary T cells with third-generation lentiviral "
            "vector encoding the FMC63-based CD19 CAR construct. Optimize MOI and "
            "transduction conditions for maximum efficiency with minimal toxicity."
        ),
        project_id=proj_cart.id,
        owner_id=alice.id,
        status="in_progress",
        barcode="EXP-BC-002",
    )

    # Experiment 3: completed
    exp3 = Experiment(
        experiment_id="EXP-2026-003",
        title="Serum Protein Profiling by LC-MS/MS — Discovery Cohort",
        purpose=(
            "Perform unbiased shotgun proteomics on serum samples from 20 CRC patients "
            "and 20 healthy controls to identify differentially expressed proteins as "
            "candidate biomarkers for early-stage colorectal cancer."
        ),
        project_id=proj_bio.id,
        owner_id=carol.id,
        status="completed",
        barcode="EXP-BC-003",
    )
    exp3.completed_at = datetime(2026, 3, 28, 14, 30, 0, tzinfo=timezone.utc)

    # Experiment 4: under_review
    exp4 = Experiment(
        experiment_id="EXP-2026-004",
        title="pH and DO Optimization for mAb Production in 2L Bioreactor",
        purpose=(
            "Systematically evaluate the effect of pH (6.8–7.4) and dissolved oxygen "
            "setpoints (30–60%) on CHO cell growth kinetics and IgG1 titer in a 2L "
            "stirred-tank bioreactor to establish optimal process parameters."
        ),
        project_id=proj_proc.id,
        owner_id=carol.id,
        status="under_review",
        barcode="EXP-BC-004",
    )
    exp4.completed_at = datetime(2026, 3, 20, 9, 0, 0, tzinfo=timezone.utc)

    # Experiment 5: completed — CAR-T Cytotoxicity Assay
    exp5 = Experiment(
        experiment_id="EXP-2026-005",
        title="CAR-T Cytotoxicity Assay — 4-Hour 51Cr Release",
        purpose=(
            "Assess cytolytic activity of manufactured CD19 CAR-T cells against Raji (CD19+) "
            "and K562 (CD19-) target cell lines using a 4-hour chromium-51 release assay at "
            "E:T ratios of 1:1, 5:1, 10:1, and 20:1."
        ),
        project_id=proj_cart.id,
        owner_id=alice.id,
        status="completed",
        barcode="EXP-BC-005",
    )
    exp5.completed_at = datetime(2026, 3, 15, tzinfo=timezone.utc)

    # Experiment 6: active — G-Rex bioreactor scale-up
    exp6 = Experiment(
        experiment_id="EXP-2026-006",
        title="T Cell Expansion in G-Rex 10 Bioreactor — Scale-Up Run 1",
        purpose=(
            "Evaluate large-scale T cell expansion in G-Rex 10 closed system bioreactor "
            "for CAR-T manufacturing. Target: ≥500×10^6 viable T cells at Day 14 with "
            ">80% viability and <30% exhausted phenotype (PD-1+TIM-3+)."
        ),
        project_id=proj_cart.id,
        owner_id=bob.id,
        status="active",
        barcode="EXP-BC-006",
    )

    # Experiment 7: approved — LGALS3BP ELISA validation
    exp7 = Experiment(
        experiment_id="EXP-2026-007",
        title="ELISA Validation of LGALS3BP as CRC Biomarker — 96-Sample Validation Cohort",
        purpose=(
            "Validate LGALS3BP (Galectin-3 binding protein) as a serum biomarker for "
            "early-stage colorectal cancer using a commercial sandwich ELISA in an independent "
            "96-sample cohort (48 CRC, 48 healthy controls)."
        ),
        project_id=proj_bio.id,
        owner_id=carol.id,
        status="approved",
        barcode="EXP-BC-007",
    )
    exp7.completed_at = datetime(2026, 3, 10, tzinfo=timezone.utc)

    # Experiment 8: in_progress — Western blot confirmation
    exp8 = Experiment(
        experiment_id="EXP-2026-008",
        title="Western Blot Confirmation of Top 5 Candidate Biomarkers",
        purpose=(
            "Confirm differential expression of top 5 candidate biomarkers (LGALS3BP, CEA, "
            "CEACAM5, CA19-9 precursor, APOA1) identified by LC-MS/MS using Western blot in "
            "20 paired CRC/HC serum samples."
        ),
        project_id=proj_bio.id,
        owner_id=alice.id,
        status="in_progress",
        barcode="EXP-BC-008",
    )

    # Experiment 9: completed — Fed-batch vs perfusion
    exp9 = Experiment(
        experiment_id="EXP-2026-009",
        title="Fed-Batch vs Perfusion Mode Comparison for IgG1 Titer",
        purpose=(
            "Compare final IgG1 titer and cell-specific productivity between fed-batch and "
            "perfusion culture modes in 2L bioreactors using the same CHO-K1 clone. "
            "Primary endpoint: final harvest titer (g/L)."
        ),
        project_id=proj_proc.id,
        owner_id=carol.id,
        status="completed",
        barcode="EXP-BC-009",
    )
    exp9.completed_at = datetime(2026, 3, 25, tzinfo=timezone.utc)

    # Experiment 10: draft — Protein A chromatography optimization
    exp10 = Experiment(
        experiment_id="EXP-2026-010",
        title="Protein A Affinity Chromatography Optimization",
        purpose=(
            "Optimize Protein A affinity chromatography step for mAb capture including load "
            "challenge, wash buffer composition, and elution pH to maximize yield and minimize "
            "HCP co-purification."
        ),
        project_id=proj_proc.id,
        owner_id=bob.id,
        status="draft",
        barcode="EXP-BC-010",
    )

    all_exps = [exp1, exp2, exp3, exp4, exp5, exp6, exp7, exp8, exp9, exp10]
    for exp in all_exps:
        db.add(exp)
    db.flush()

    for exp in all_exps:
        owner_user = next(u for u in [alice, bob, carol] if u.id == exp.owner_id)
        create_audit_log(
            db=db,
            entity_type="experiment",
            entity_id=str(exp.id),
            action="created",
            actor_id=owner_user.id,
            actor_username=owner_user.username,
            new_value={
                "experiment_id": exp.experiment_id,
                "title": exp.title,
                "status": exp.status,
            },
        )

    # Participants
    db.add(ExperimentParticipant(experiment_id=exp1.id, user_id=bob.id, role="technician"))
    db.add(ExperimentParticipant(experiment_id=exp2.id, user_id=bob.id, role="technician"))
    db.add(ExperimentParticipant(experiment_id=exp3.id, user_id=alice.id, role="scientist"))
    db.add(ExperimentParticipant(experiment_id=exp4.id, user_id=bob.id, role="technician"))
    db.add(ExperimentParticipant(experiment_id=exp5.id, user_id=bob.id, role="technician"))
    db.add(ExperimentParticipant(experiment_id=exp7.id, user_id=alice.id, role="scientist"))
    db.add(ExperimentParticipant(experiment_id=exp9.id, user_id=bob.id, role="technician"))
    db.flush()

    # ------------------------------------------------------------------
    # Lab Entries
    # ------------------------------------------------------------------
    print("  Creating lab entries...")

    # EXP-1 (draft) — PBMC Isolation — all sections
    entries1 = [
        LabEntry(
            experiment_id=exp1.id,
            section="hypothesis",
            content=(
                "Ficoll-Paque density gradient centrifugation will yield PBMCs with >90% viability "
                "and >85% lymphocyte purity from healthy donor buffy coats. We hypothesize that "
                "sample processing within 6 hours of collection will maintain superior cell viability "
                "compared to delayed processing, based on published literature (Bhatt et al., 2020)."
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp1.id,
            section="protocol",
            content=(
                "1. Retrieve buffy coat from blood bank; confirm donor ID and lot number against COA.\n"
                "2. Dilute buffy coat 1:1 (v/v) in room-temperature sterile PBS (Ca2+/Mg2+-free) in a "
                "50 mL conical tube.\n"
                "3. Slowly layer 25 mL diluted buffy coat over 15 mL Ficoll-Paque PLUS in a 50 mL "
                "Leucosep tube pre-loaded with Ficoll (do not disturb the interface).\n"
                "4. Centrifuge at 400×g for 30 min at 18°C with brake OFF (acceleration 1, deceleration 0).\n"
                "5. Carefully aspirate the upper plasma/PBS layer to within 5 mL of the buffy coat "
                "interface. Transfer the buffy coat (mononuclear cell) layer using a Pasteur pipette "
                "into a new 50 mL tube.\n"
                "6. Wash 1: Add PBS to 50 mL, centrifuge 300×g 10 min at 18°C (brake ON). "
                "Aspirate supernatant.\n"
                "7. Wash 2: Resuspend pellet in 50 mL PBS, centrifuge 300×g 10 min at 18°C. "
                "Aspirate supernatant.\n"
                "8. Resuspend pellet in 1 mL RPMI 1640 + 10% FBS. Take 10 µL aliquot for counting.\n"
                "9. Mix 10 µL cell suspension 1:1 with 0.4% Trypan Blue. Count on Neubauer "
                "hemocytometer — record total cells, viable cells, and % viability.\n"
                "10. Adjust concentration to 10×10^6 cells/mL in RPMI 1640 + 10% FBS.\n"
                "11. Aliquot cells at 50×10^6 cells/cryovial in CryoStor CS10 for cryopreservation. "
                "Reserve one aliquot for immediate downstream use.\n"
                "12. Transfer cryovials to Mr. Frosty container (pre-equilibrated to RT) and place "
                "at -80°C overnight before transfer to LN2."
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp1.id,
            section="materials_notes",
            content=(
                "Donor samples:\n"
                "  - Donor-1: lot BC-2026-031, 2× buffy coats (~450 mL blood equivalent), "
                "collected 2026-03-10, processed same day\n"
                "  - Donor-2: lot BC-2026-032, 2× buffy coats (~450 mL blood equivalent), "
                "collected 2026-03-10, processed same day\n"
                "  - Donor-3: lot BC-2026-033, 2× buffy coats (~450 mL blood equivalent), "
                "collected 2026-03-10, processed same day (note: slight hemolysis on receipt)\n\n"
                "Reagents:\n"
                "  - Ficoll-Paque PLUS (Cytiva 17-1440-03), lot FP-20260301, density 1.077 g/mL, "
                "stored at 4°C, pre-warmed to RT before use\n"
                "  - RPMI 1640 (ThermoFisher 11875093), lot RPMI-20260115, stored at 4°C\n"
                "  - FBS heat-inactivated (ThermoFisher 10500064), lot FBS-20260201, 10% v/v\n"
                "  - PBS (Ca2+/Mg2+-free), Gibco, lot 2389011\n"
                "  - CryoStor CS10 (BioLife Solutions), lot CS-20260115\n"
                "  - Trypan Blue 0.4% (ThermoFisher), lot TB-20251201\n\n"
                "Equipment:\n"
                "  - 50 mL Leucosep tubes (Greiner Bio-One 227290)\n"
                "  - Neubauer improved hemocytometer\n"
                "  - Centrifuge: Eppendorf 5810R, rotor A-4-81, calibrated 2026-01-15\n"
                "  - Mr. Frosty controlled-rate freezing container (Thermo Fisher)"
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp1.id,
            section="results",
            content=(
                "PBMC yields and viabilities (Trypan Blue exclusion, Neubauer hemocytometer):\n\n"
                "Donor-1 (lot BC-2026-031):\n"
                "  Total PBMCs isolated: 245×10^6\n"
                "  Viability: 95.2%\n"
                "  Cell concentration: 10.2×10^6 cells/mL (in 24 mL final volume)\n\n"
                "Donor-2 (lot BC-2026-032):\n"
                "  Total PBMCs isolated: 312×10^6\n"
                "  Viability: 96.1%\n"
                "  Cell concentration: 10.4×10^6 cells/mL (in 30 mL final volume)\n\n"
                "Donor-3 (lot BC-2026-033):\n"
                "  Total PBMCs isolated: 278×10^6\n"
                "  Viability: 95.8%\n"
                "  Cell concentration: 10.1×10^6 cells/mL (in 27.5 mL final volume)\n"
                "  Note: additional wash step performed due to hemolysis (see observations)\n\n"
                "Summary statistics:\n"
                "  Mean yield: 278.3±28.1×10^6 PBMCs per donor\n"
                "  Mean viability: 95.7±0.5%\n\n"
                "Post-count differential by morphology (200-cell differential count, Giemsa stain):\n"
                "  Lymphocytes: ~72%\n"
                "  Monocytes: ~18%\n"
                "  NK cells: ~8%\n"
                "  Other: ~2%\n\n"
                "Acceptance criteria: >150×10^6 total cells, >90% viability — ALL DONORS PASS."
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp1.id,
            section="observations",
            content=(
                "Donor-3 buffy coat was slightly hemolyzed on receipt (sample appeared darker red "
                "than typical). Proceeded with processing after documenting and photographing the "
                "sample. Red cell contamination at the interface layer was higher than usual for "
                "Donor-3 (pellet appeared more pink post-centrifugation). An additional wash step "
                "(300×g, 10 min, PBS 50 mL) was performed for Donor-3, which resolved most residual "
                "red cell contamination and restored normal white pellet appearance.\n\n"
                "Processing time for all 3 donors was completed within 4.5 hours of receipt — "
                "within the 6-hour specification window.\n\n"
                "No anomalies observed with Ficoll interface formation for Donors 1 and 2. "
                "Interface layer was clearly visible and sharply defined in all 6 tubes.\n\n"
                "Lab temperature maintained at 18–22°C throughout the procedure (temperature "
                "log attached). Centrifuge temperature confirmed at 18°C.\n\n"
                "All operator steps performed in a Class II BSC. No contamination events."
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp1.id,
            section="conclusions",
            content=(
                "PBMC isolation was successful across all 3 healthy donors. Yields and viabilities "
                "exceed minimum acceptance specifications for downstream CAR-T cell manufacturing "
                "(>150×10^6 cells at >90% viability).\n\n"
                "Donor-3 hemolysis did not significantly impact final product quality after the "
                "additional wash step — final viability of 95.8% is comparable to non-hemolyzed "
                "donors and demonstrates the robustness of the protocol.\n\n"
                "All three PBMC lots (BC-2026-031, -032, -033) are approved for cryopreservation "
                "and downstream T cell activation. Cryovials stored in LN2 Tank A, Box 3.\n\n"
                "Action items:\n"
                "  1. Flag Donor-3 lot BC-2026-033 for QC tracking due to initial hemolysis — "
                "note in sample inventory system.\n"
                "  2. Communicate with blood bank regarding Donor-3 collection quality.\n"
                "  3. Proceed to T cell activation (EXP-2026-002) using Donors 1 and 2 PBMC lots "
                "within 7 days of cryopreservation."
            ),
            version=1,
            created_by=alice.id,
        ),
    ]
    for entry in entries1:
        db.add(entry)

    # EXP-2 (in_progress) — existing entries kept + new observations and conclusions
    entries2 = [
        LabEntry(
            experiment_id=exp2.id,
            section="purpose",
            content=exp2.purpose,
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp2.id,
            section="materials_notes",
            content=(
                "- Anti-CD19 CAR lentiviral vector (lot: LV-2026-003, titer: 2×10^8 TU/mL)\n"
                "- Activated T cells (Day 2 post-activation with CD3/CD28 Dynabeads)\n"
                "- RPMI 1640 + 10% FBS + 100 U/mL IL-2\n"
                "- Polybrene (8 µg/mL final concentration)\n"
                "- TransIT-Lenti Transduction Reagent"
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp2.id,
            section="method_protocol",
            content=(
                "1. Count activated T cells using hemocytometer; assess viability by trypan blue.\n"
                "2. Seed 5×10^5 T cells/well in 24-well plate in 500 µL complete RPMI.\n"
                "3. Add lentiviral vector at MOI 5, 10, and 20 (in triplicate).\n"
                "4. Add Polybrene to 8 µg/mL final concentration.\n"
                "5. Spin-infect: 800 × g, 90 min, 32°C.\n"
                "6. Remove media 4h post-transduction; replace with fresh complete RPMI + IL-2.\n"
                "7. Culture 48h at 37°C, 5% CO2.\n"
                "8. Assess transduction efficiency by flow cytometry (anti-CD19-CAR, clone FMC63)."
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp2.id,
            section="raw_data",
            content=(
                "Transduction efficiency by flow cytometry (72h post-transduction):\n"
                "MOI 5:  18.3% CAR+ T cells (viability 94.2%)\n"
                "MOI 10: 34.7% CAR+ T cells (viability 91.8%)\n"
                "MOI 20: 41.2% CAR+ T cells (viability 87.3%)\n\n"
                "Cell counts at Day 3:\n"
                "MOI 5:  2.1×10^6 cells/well\n"
                "MOI 10: 1.9×10^6 cells/well\n"
                "MOI 20: 1.6×10^6 cells/well"
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp2.id,
            section="observations",
            content=(
                "MOI 10 consistently gives the best balance between transduction efficiency and "
                "cell health across the three conditions tested. Vector lot LV-2026-003 performed "
                "within expected range — titer independently confirmed at 1.95×10^8 TU/mL by p24 "
                "ELISA (specification: ≥1×10^8 TU/mL).\n\n"
                "At MOI 20, visible cell clumping was noted 24h post-transduction, likely due to "
                "higher viral particle load causing cellular aggregation. Clumping partially "
                "resolved by 48h but viability was measurably lower at 87.3%.\n\n"
                "Polybrene concentration at 8 µg/mL appears appropriate — no significant cytotoxicity "
                "observed at this concentration in any MOI group. Literature supports 4–10 µg/mL "
                "as a safe working range for primary T cells.\n\n"
                "IL-2 supplementation at 200 IU/mL maintained proliferation across all MOI groups. "
                "Media color (phenol red indicator) remained orange-red, indicating appropriate pH.\n\n"
                "Flow cytometry gating strategy: viable singlets (DAPI-negative) → CD3+ → "
                "CAR+ (detected with anti-FMC63 idiotype antibody, anti-mouse IgG secondary). "
                "CAR expression confirmed by co-staining with anti-CD19 recombinant protein."
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp2.id,
            section="conclusions",
            content=(
                "MOI 10 selected as the optimal transduction condition for scale-up based on the "
                "balance of transduction efficiency (34.7% CAR+) and post-transduction viability "
                "(91.8%). MOI 20 provides only marginal improvement in CAR expression (+6.5% "
                "absolute) at the cost of significantly reduced viability and increased cell "
                "clumping — not recommended for manufacturing.\n\n"
                "Proceeding to Day 7 expansion phase with MOI 10 conditions. T cells will be "
                "transferred to G-Rex 10 bioreactor on Day 3 post-transduction for large-scale "
                "expansion (EXP-2026-006).\n\n"
                "Estimated CAR-T cell yield at Day 14 for scale-up:\n"
                "  Starting T cells: 500×10^6\n"
                "  Expected transduction: 34.7% CAR+ → 173.5×10^6 CAR+ cells at Day 3\n"
                "  Assumed 4-fold expansion Days 3–14\n"
                "  Projected final CAR+ yield: ~200×10^6 CAR+ T cells\n\n"
                "Vector lot LV-2026-003 approved for continued use; remaining vector aliquots "
                "stored at -80°C in 500 µL aliquots."
            ),
            version=1,
            created_by=alice.id,
        ),
    ]
    for entry in entries2:
        db.add(entry)

    # EXP-3 (completed) — existing entries kept + new hypothesis and conclusions
    entries3 = [
        LabEntry(
            experiment_id=exp3.id,
            section="purpose",
            content=exp3.purpose,
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp3.id,
            section="hypothesis",
            content=(
                "We hypothesize that discovery proteomics of serum from treatment-naive early-stage "
                "CRC patients vs healthy controls will identify ≥5 differentially expressed proteins "
                "with |log2FC| >1.5 and adj. p <0.05. Based on prior literature (Surinova et al., "
                "2011; Surinova et al., 2015), we expect upregulation of CEA, CA19-9 precursor, and "
                "CEACAM family members, and downregulation of lipid transport proteins (APOA1, PON1) "
                "in CRC, consistent with systemic inflammatory response and altered hepatic "
                "lipoprotein metabolism. Novel candidates beyond these known markers are the primary "
                "scientific objective."
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp3.id,
            section="method_protocol",
            content=(
                "1. Serum samples (20 CRC, 20 HC) thawed on ice and depleted of abundant proteins "
                "using ProteoMiner kit.\n"
                "2. Protein concentration measured by BCA assay; normalize to 100 µg per sample.\n"
                "3. Reduce (10 mM DTT, 56°C, 30 min) and alkylate (55 mM IAA, RT, 45 min in dark).\n"
                "4. Trypsin digest (1:50 enzyme:substrate) overnight at 37°C.\n"
                "5. Desalt using C18 Sep-Pak columns; lyophilize.\n"
                "6. Reconstitute in 0.1% formic acid; inject 500 ng per LC-MS/MS run.\n"
                "7. Instrument: Thermo Orbitrap Eclipse; 90 min gradient; DDA acquisition mode.\n"
                "8. Data analysis: MaxQuant v2.4 with label-free quantification (LFQ)."
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp3.id,
            section="raw_data",
            content=(
                "MaxQuant LFQ analysis results:\n"
                "Total proteins identified: 847\n"
                "Proteins quantified in ≥80% of samples: 612\n\n"
                "Top differentially expressed proteins (adj. p < 0.05, |log2FC| > 1.5):\n"
                "Up in CRC: CEA (log2FC=3.2), CA19-9 precursor (log2FC=2.8), "
                "CEACAM5 (log2FC=2.6), LGALS3BP (log2FC=2.1)\n"
                "Down in CRC: APOA1 (log2FC=-1.9), PON1 (log2FC=-1.7)"
            ),
            version=2,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp3.id,
            section="observations",
            content=(
                "Results broadly consistent with published CRC biomarker literature. "
                "CEA and CA19-9 enrichment validates assay performance.\n\n"
                "Novel finding: LGALS3BP shows strongest discrimination in stage I/II CRC "
                "subgroup (AUC 0.87). Warrants validation in independent cohort.\n\n"
                "APOA1/PON1 downregulation may reflect systemic inflammation rather than "
                "tumor-specific effect — confound needs to be addressed in validation study."
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp3.id,
            section="conclusions",
            content=(
                "Discovery proteomics identified 4 significantly upregulated (CEA, CA19-9 precursor, "
                "CEACAM5, LGALS3BP) and 2 downregulated (APOA1, PON1) proteins meeting the "
                "pre-specified criteria of |log2FC| >1.5 and adj. p <0.05. The total count of 6 "
                "exceeds the pre-specified threshold of ≥5, confirming the primary hypothesis.\n\n"
                "CEA and CA19-9 enrichment confirms assay validity and is consistent with expected "
                "biology. LGALS3BP is the most scientifically interesting novel finding, showing "
                "strong discrimination in early-stage disease (AUC 0.87, Stage I/II subgroup) — "
                "a setting where current biomarkers perform poorly.\n\n"
                "The APOA1/PON1 downregulation pattern is consistent with systemic inflammation "
                "and is likely to reflect non-specific host response rather than tumor-specific "
                "biology — these may be confounders rather than actionable CRC markers.\n\n"
                "Recommendations:\n"
                "  1. PRIMARY: Proceed to LGALS3BP validation by sandwich ELISA in an independent "
                "cohort of ≥96 samples (EXP-2026-007, underway).\n"
                "  2. SECONDARY: Confirm CEACAM5 differential expression by Western blot as "
                "orthogonal method (EXP-2026-008, underway).\n"
                "  3. Proteomics raw data and MaxQuant output files deposited to PRIDE archive "
                "(accession: PXD-XXXXXX, pending reviewer assignment).\n"
                "  4. Manuscript in preparation — target journal: Journal of Proteome Research."
            ),
            version=1,
            created_by=carol.id,
        ),
    ]
    for entry in entries3:
        db.add(entry)

    # EXP-4 (under_review) — pH and DO optimization — all sections
    entries4 = [
        LabEntry(
            experiment_id=exp4.id,
            section="hypothesis",
            content=(
                "We hypothesize that maintaining pH at 7.2 and dissolved oxygen at 40% saturation "
                "will optimize CHO cell productivity for IgG1 mAb expression, based on published "
                "DoE studies with CHO-K1 clones (Trummer et al., 2006; Xing et al., 2009). "
                "Deviation from these setpoints by ±0.2 pH units or ±10% DO is expected to reduce "
                "cell-specific productivity by 15–25%, primarily through effects on cellular "
                "metabolism (lactate accumulation at low pH) and oxidative stress (elevated ROS "
                "at high DO). The pH effect is anticipated to be the dominant factor in this "
                "design space."
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp4.id,
            section="protocol",
            content=(
                "Design of Experiment (DoE) — full factorial 3×3 design:\n"
                "Factors: pH (6.8, 7.0, 7.2) × DO (30%, 40%, 60%)\n"
                "9 bioreactor runs × 2L working volume × triplicate at optimal condition\n\n"
                "Bioreactor setup:\n"
                "  - Instrument: Sartorius Biostat B-DCU II, 3L vessel, SN BR-007\n"
                "  - Inoculation density: 0.5×10^6 viable cells/mL on Day 0 from "
                "cryopreserved working cell bank (WCB-2025-001-v3)\n"
                "  - Basal medium: CD FortiCHO (Gibco) + 8 mM L-glutamine, 1.5L working volume\n"
                "  - Agitation: 200 rpm, Rushton turbine impeller\n"
                "  - Temperature: 37°C fixed throughout\n\n"
                "Fed-batch feeding:\n"
                "  - Feed: CD EfficientFeed C (Gibco), Days 3, 5, 7, 9 at 5% v/v each addition\n\n"
                "Sampling schedule:\n"
                "  - Daily sampling from Day 1\n"
                "  - VCC and viability: Vi-CELL XR automated cell counter (Beckman Coulter)\n"
                "  - Glucose and lactate: Nova BioProfile FLEX2 metabolite analyzer\n"
                "  - IgG1 titer: Protein A HPLC (MabSelect 1 mL column, GE Healthcare), "
                "calibration with certified IgG1 reference standard\n"
                "  - Osmolality: Vapro 5600 osmometer (Wescor), Day 0 and weekly\n\n"
                "Run duration: 14 days or until viability drops below 50%\n\n"
                "pH and DO control:\n"
                "  - pH controlled by CO2 sparging (acidification) and 1M Na2CO3 addition "
                "(alkalization) via peristaltic pump\n"
                "  - DO controlled by N2/O2/air cascade sparging\n"
                "  - pH setpoint deadband: ±0.05 pH units\n"
                "  - DO setpoint deadband: ±2%"
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp4.id,
            section="materials_notes",
            content=(
                "Cell line:\n"
                "  - CHO-K1 clone expressing IgG1-anti-EGFR, lot WCB-2025-001-v3\n"
                "  - Cryopreserved at 10×10^6 cells/mL in CryoStor CS10\n"
                "  - Cell bank passage number: P23 at time of seeding\n\n"
                "Media and feeds:\n"
                "  - CD FortiCHO medium (Gibco 10931022), lot 2381054\n"
                "  - CD EfficientFeed C (Gibco A26020-02), lot 2319876\n"
                "  - L-glutamine 200 mM stock (Gibco 25030081), lot 2301847\n\n"
                "Equipment:\n"
                "  - Sartorius Biostat B-DCU II, 3L vessel, SN BR-007\n"
                "  - pH probe: Mettler Toledo InPro 3253, 2-point buffer calibration "
                "(pH 4.00 and 7.00) performed day prior to inoculation\n"
                "  - DO probe: Mettler Toledo InPro 6800 polarographic, 100% calibration "
                "with air sparging 1h prior to inoculation; 0% calibration with N2 sparging\n"
                "  - Vi-CELL XR (Beckman Coulter), last calibration 2026-02-20\n"
                "  - Nova BioProfile FLEX2, last calibration 2026-03-01\n"
                "  - Protein A HPLC: MabSelect SuRe column (GE Healthcare) 1 mL, "
                "calibration curve with IgG1 reference standard (7-point, 0.01–5 g/L)"
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp4.id,
            section="results",
            content=(
                "Peak VCC, Day 14 viability, and final titer by condition (mean ± SD):\n\n"
                "pH 6.8 / DO 30%: Peak VCC 8.2±0.4×10^6 cells/mL, viability 61.2±3.1%, "
                "titer 1.8±0.2 g/L\n"
                "pH 6.8 / DO 40%: Peak VCC 9.1±0.5×10^6 cells/mL, viability 67.3±2.8%, "
                "titer 2.1±0.1 g/L\n"
                "pH 6.8 / DO 60%: Peak VCC 8.8±0.3×10^6 cells/mL, viability 65.8±2.2%, "
                "titer 2.0±0.2 g/L\n"
                "pH 7.0 / DO 30%: Peak VCC 10.4±0.6×10^6 cells/mL, viability 74.1±3.4%, "
                "titer 2.8±0.2 g/L\n"
                "pH 7.0 / DO 40%: Peak VCC 12.1±0.7×10^6 cells/mL, viability 79.2±2.6%, "
                "titer 3.5±0.3 g/L\n"
                "pH 7.0 / DO 60%: Peak VCC 11.8±0.4×10^6 cells/mL, viability 77.8±1.9%, "
                "titer 3.3±0.2 g/L\n"
                "pH 7.2 / DO 30%: Peak VCC 13.2±0.8×10^6 cells/mL, viability 82.4±2.1%, "
                "titer 3.9±0.3 g/L\n"
                "pH 7.2 / DO 40%: Peak VCC 15.1±0.5×10^6 cells/mL, viability 88.7±1.8%, "
                "titer 4.2±0.2 g/L  ← OPTIMAL CONDITION\n"
                "pH 7.2 / DO 60%: Peak VCC 14.3±0.6×10^6 cells/mL, viability 85.1±2.3%, "
                "titer 4.0±0.1 g/L\n\n"
                "Cell-specific productivity at optimal condition (pH 7.2/DO 40%): "
                "21.8 pg/cell/day\n\n"
                "Metabolite profiles at Day 10 (optimal condition):\n"
                "  Glucose: 4.8 mM (above 4 mM threshold)\n"
                "  Lactate: 18.2 mM (below 20 mM concern threshold)\n"
                "  Glutamine: 1.1 mM\n"
                "  Ammonia: 3.4 mM\n"
                "  Osmolality: 318 mOsm/kg"
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp4.id,
            section="observations",
            content=(
                "The pH effect was more pronounced than the DO effect across all 9 conditions "
                "tested. Moving from pH 6.8 to 7.2 at fixed DO 40% increased titer by 100% "
                "(2.1 → 4.2 g/L), while moving from DO 30% to 40% at fixed pH 7.2 increased "
                "titer by only ~8% (3.9 → 4.2 g/L).\n\n"
                "All conditions with pH 6.8 consistently underperformed — cells appeared stressed "
                "with elevated lactate accumulation >35 mM by Day 10, indicative of acidosis-driven "
                "metabolic shift to anaerobic glycolysis. Viabilities at Day 14 were significantly "
                "lower (61–67%) compared to pH 7.2 conditions (82–89%).\n\n"
                "pH 7.2/DO 40% emerged as the clear winner. High DO (60%) did not provide "
                "additional benefit over 40% and slightly increased foaming from Day 8, requiring "
                "one manual addition of 200 µL Antifoam C emulsion.\n\n"
                "Instrument note: One bioreactor (pH 6.8/DO 30%, replicate 2) experienced a pH "
                "probe drift on Day 8 (reading 0.15 pH units lower than actual, confirmed by "
                "offline measurement). Run was flagged and excluded from statistical analysis. "
                "The run was repeated with a new probe — data from repeat run is included above."
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp4.id,
            section="conclusions",
            content=(
                "Optimal bioreactor conditions confirmed: pH 7.2, DO 40%. These parameters "
                "will be implemented as process setpoints for the 50L scale-up run.\n\n"
                "The pH effect dominates over DO effect in this design space — maintaining tight "
                "pH control (±0.05 pH units) during scale-up will be the most critical process "
                "parameter. Recommend using redundant pH probes at 50L scale.\n\n"
                "Cell-specific productivity of 21.8 pg/cell/day at optimal conditions exceeds "
                "our minimum target of 18 pg/cell/day for this clone. Peak VCC of 15.1×10^6 "
                "cells/mL is consistent with published CHO-K1 performance in CD FortiCHO.\n\n"
                "Next steps:\n"
                "  1. Submit data package to reviewer (Dave Kim) for approval before proceeding.\n"
                "  2. Upon approval, initiate 50L scale-up run with pH 7.2/DO 40% setpoints.\n"
                "  3. Model pH gradient effects at larger scale using CFD simulation.\n"
                "  4. Raw data (bioreactor logs, HPLC chromatograms) archived in ELN folder "
                "EXP-2026-004/raw."
            ),
            version=1,
            created_by=carol.id,
        ),
    ]
    for entry in entries4:
        db.add(entry)

    # EXP-5 (completed) — existing entries kept + new hypothesis and protocol and materials_notes
    entries5 = [
        LabEntry(
            experiment_id=exp5.id,
            section="hypothesis",
            content=(
                "CD19-targeted CAR-T cells manufactured at MOI 10 (EXP-2026-002) will demonstrate "
                "specific cytolysis of CD19+ Raji target cells at E:T ratios ≥5:1, with >50% "
                "specific lysis at E:T 10:1. CD19-negative K562 cells will serve as the negative "
                "control and should show <10% non-specific lysis at all E:T ratios tested, "
                "confirming antigen specificity of the killing response. The 4-hour chromium-51 "
                "release assay is the gold-standard method for quantifying CAR-T cytolytic activity "
                "(Brentjens et al., 2010)."
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp5.id,
            section="protocol",
            content=(
                "Day -1 (target cell labeling):\n"
                "  1. Pellet 5×10^6 Raji cells and 5×10^6 K562 cells separately by centrifugation "
                "(300×g, 5 min).\n"
                "  2. Resuspend each pellet in 200 µL RPMI containing 100 µCi Na2(51CrO4) "
                "(PerkinElmer CJS1) per 10^6 cells.\n"
                "  3. Incubate 37°C, 5% CO2, 1h with gentle mixing every 15 min.\n"
                "  4. Wash 3× with 10 mL RPMI to remove unincorporated chromium "
                "(300×g, 5 min each).\n"
                "  5. Count labeled cells; resuspend to 1×10^5 cells/mL (= 5,000 cells per "
                "100 µL per well).\n\n"
                "Day 0 (cytotoxicity assay setup):\n"
                "  6. Rest CAR-T effector cells overnight in RPMI + 5% FBS without cytokines "
                "prior to assay.\n"
                "  7. Prepare E:T ratios 1:1, 5:1, 10:1, 20:1 in 96-well V-bottom plates "
                "(5,000 target cells/well constant; adjust effector cell number accordingly).\n"
                "  8. Set up controls: spontaneous release wells (target cells + medium only) "
                "and maximum release wells (target cells + 1% Triton X-100).\n"
                "  9. Incubate 4h at 37°C, 5% CO2.\n"
                "  10. Centrifuge plate 300×g 5 min. Carefully transfer 100 µL supernatant per "
                "well to a new plate or count tubes.\n"
                "  11. Count on PerkinElmer WIZARD2 gamma counter (51Cr window: 300–380 keV).\n\n"
                "Calculation:\n"
                "  % Specific lysis = [(Experimental CPM − Spontaneous CPM) / "
                "(Maximum CPM − Spontaneous CPM)] × 100\n"
                "  All conditions run in triplicate. Results expressed as mean ± SD."
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp5.id,
            section="materials_notes",
            content=(
                "Effector cells:\n"
                "  - CAR-T Day 14 product from EXP-2026-002, MOI 10 condition\n"
                "  - Lot: CAR-2026-MOI10-D14\n"
                "  - CAR+ fraction: 34.7% (34.7% of total T cells express CD19-CAR)\n"
                "  - Viability at time of assay: 91.2% (trypan blue)\n\n"
                "Target cells:\n"
                "  - Raji (ATCC CCL-86): CD19+/CD20+ Burkitt lymphoma cell line, passage 12, "
                "viability 98.1%\n"
                "  - K562 (ATCC CCL-243): CD19-/CD20- chronic myelogenous leukemia cell line "
                "(negative control), passage 8, viability 97.4%\n\n"
                "Radioisotope:\n"
                "  - Chromium-51 sodium chromate (PerkinElmer CJS1), lot 2841024\n"
                "  - Specific activity: 250 mCi/mL\n"
                "  - Calibration date: 2026-02-28 (within 14-day specification window)\n\n"
                "Equipment:\n"
                "  - Gamma counter: PerkinElmer 2470 WIZARD2, SN WZ-002\n"
                "  - Last calibration: 2026-02-14\n"
                "  - Radioactive waste disposal: per institutional radiation safety protocol RSP-014"
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp5.id,
            section="results",
            content=(
                "Specific lysis (mean ± SD, n=3 replicate wells per condition):\n\n"
                "Raji (CD19+) target cells:\n"
                "  E:T 1:1:   22.4±3.1% specific lysis\n"
                "  E:T 5:1:   51.8±4.7% specific lysis\n"
                "  E:T 10:1:  68.2±3.9% specific lysis\n"
                "  E:T 20:1:  78.3±4.2% specific lysis\n\n"
                "K562 (CD19-) control cells:\n"
                "  E:T 1:1:   1.8±0.9% specific lysis\n"
                "  E:T 5:1:   2.4±1.1% specific lysis\n"
                "  E:T 10:1:  3.0±0.7% specific lysis\n"
                "  E:T 20:1:  3.1±0.8% specific lysis\n\n"
                "EC50: E:T ratio 7.4 (interpolated from 4-parameter logistic fit)\n\n"
                "Spontaneous release: Raji 8.3% of maximum, K562 6.1% of maximum "
                "(both within acceptable range <15%).\n\n"
                "Results demonstrate robust and antigen-specific cytotoxicity consistent with "
                "a functional CAR-T product."
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp5.id,
            section="observations",
            content=(
                "Strong antigen-specific killing confirmed. CD19-negative K562 controls show "
                "minimal non-specific lysis (<5% at all E:T ratios). Ready to proceed to "
                "in vivo xenograft model."
            ),
            version=1,
            created_by=alice.id,
        ),
    ]
    for entry in entries5:
        db.add(entry)

    # EXP-6 (active) — existing protocol kept + new hypothesis, materials_notes, results, observations, conclusions
    entries6 = [
        LabEntry(
            experiment_id=exp6.id,
            section="hypothesis",
            content=(
                "G-Rex 10 closed-system bioreactor will support ≥500×10^6 viable T cells at Day 14 "
                "from a 5×10^6 cell seed, representing ≥100-fold expansion with >80% viability and "
                "<30% exhausted phenotype (PD-1+TIM-3+ double positive). The G-Rex platform's "
                "high gas-permeable surface area-to-volume ratio allows passive O2 delivery and "
                "reduces the need for agitation, creating favorable conditions for T cell expansion "
                "while minimizing mechanical stress (Jin et al., 2012). IL-2 supplementation at "
                "200 IU/mL will maintain proliferative drive throughout the culture period."
            ),
            version=1,
            created_by=bob.id,
        ),
        LabEntry(
            experiment_id=exp6.id,
            section="protocol",
            content=(
                "Day 0: Seed 5×10^6 activated T cells in 40 mL complete XT media + 200 IU/mL IL-2. "
                "Day 7: Harvest, count, restimulate and re-seed at 0.5×10^6/mL. "
                "Day 14: Final harvest, phenotype panel, cryopreservation."
            ),
            version=1,
            created_by=bob.id,
        ),
        LabEntry(
            experiment_id=exp6.id,
            section="materials_notes",
            content=(
                "Bioreactor:\n"
                "  - G-Rex 10 (Wilson Wolf), lot GRX-2026-044\n"
                "  - Gas-permeable membrane area: 10 cm2\n"
                "  - Working volume: 40 mL\n\n"
                "Media and supplements:\n"
                "  - ImmunoCult-XF T Cell Expansion Medium (StemCell Technologies), "
                "lot 23CM0143 — used as base medium (XT media)\n"
                "  - Recombinant human IL-2 (PeproTech 200-02), lot 0923003, working "
                "concentration 200 IU/mL\n"
                "  - GlutaMAX supplement (Gibco), 2 mM final\n\n"
                "Activation reagent:\n"
                "  - Anti-CD3/CD28 Dynabeads (Gibco 11132D), lot 2387651\n"
                "  - Used at 3:1 bead:cell ratio for Day 0 activation in standard 24-well plate\n"
                "  - Beads removed on Day 3 using DynaMag-15 magnet prior to G-Rex transfer\n"
                "  - T cell activation confirmed by >85% CD69+ at Day 2 (flow cytometry)\n\n"
                "Flow cytometry panel (Day 14 phenotyping):\n"
                "  - Anti-CD3 BV421, anti-CD4 FITC, anti-CD8 PE-Cy7 (T cell subset)\n"
                "  - Anti-PD-1 PE, anti-TIM-3 APC (exhaustion markers)\n"
                "  - Anti-CD45RO PerCP-Cy5.5, anti-CCR7 BV711 (memory phenotype)\n"
                "  - Live/Dead Aqua viability dye\n"
                "  - Instrument: BD LSRFortessa, BD FACSDiva v9.0"
            ),
            version=1,
            created_by=bob.id,
        ),
        LabEntry(
            experiment_id=exp6.id,
            section="results",
            content=(
                "Cell expansion kinetics:\n"
                "  Day 0 (seed): 5.0×10^6 cells, 98.4% viability\n"
                "  Day 2 (activation check): CD69+ 87.3% — activation confirmed\n"
                "  Day 3 (post-bead removal, pre-G-Rex transfer): 22×10^6 cells, 97.1% viability\n"
                "  Day 7 (mid-expansion, post-feed): 148×10^6 cells, 94.3% viability\n"
                "    Glucose: 8.2 mM, Lactate: 12.4 mM\n"
                "  Day 10: 312×10^6 cells, 92.8% viability\n"
                "  Day 14 (final harvest): 634×10^6 cells, 91.4% viability\n"
                "    EXCEEDS TARGET of ≥500×10^6 cells\n\n"
                "Expansion fold from Day 0 seed: 126.8×\n\n"
                "Day 14 phenotype (flow cytometry):\n"
                "  CD3+: 96.8%\n"
                "  CD4+: 38.2%\n"
                "  CD8+: 61.8%\n"
                "  CD4:CD8 ratio: 0.62\n"
                "  PD-1+TIM-3+ (exhaustion): 18.4%  ← WITHIN SPEC (<30%)\n"
                "  CD45RO+CCR7+ (central memory, Tcm): 42.1%\n"
                "  CD45RO+CCR7- (effector memory, Tem): 39.7%\n"
                "  CD45RO-CCR7+ (naive/stem cell memory, Tscm): 14.2%"
            ),
            version=1,
            created_by=bob.id,
        ),
        LabEntry(
            experiment_id=exp6.id,
            section="observations",
            content=(
                "Expansion exceeded target by 27% (634 vs 500×10^6 target). Media color "
                "(phenol red indicator) remained orange-pink throughout the culture period, "
                "indicating appropriate pH maintenance without acidosis. No foaming or "
                "precipitate observed.\n\n"
                "Day 7 glucose at 8.2 mM remains above the 4 mM concern threshold for T cells, "
                "indicating no glucose limitation at this timepoint. Feed schedule maintained "
                "as planned (20 mL fresh media + IL-2 added on Day 7).\n\n"
                "CD4:CD8 ratio shifted toward CD8 dominance (0.62) by Day 14, which is typical "
                "following activation with CD3/CD28 beads — preferential CD8+ T cell expansion "
                "is well-documented with Dynabeads. This CD8 skewing is favorable for "
                "cytotoxic CAR-T applications.\n\n"
                "Exhaustion marker PD-1+TIM-3+ at 18.4% is well within the <30% specification "
                "and consistent with a functional, non-exhausted T cell product. The high "
                "central memory fraction (42.1%) suggests good in vivo persistence potential.\n\n"
                "Cell clumping was minimal throughout the culture. G-Rex system performed as "
                "expected — no procedural issues noted."
            ),
            version=1,
            created_by=bob.id,
        ),
        LabEntry(
            experiment_id=exp6.id,
            section="conclusions",
            content=(
                "G-Rex 10 expansion run successful. 634×10^6 T cells harvested at Day 14 with "
                "acceptable viability (91.4%) and favorable phenotype (18.4% exhausted, 42.1% "
                "central memory). This validates the G-Rex 10 platform for CAR-T cell "
                "manufacturing at this scale.\n\n"
                "Cells transferred to cryopreservation at 100×10^6 cells/mL in CryoStor CS10 "
                "(6 vials × ~100×10^6 cells each + 1 vial retained for QC testing). "
                "Stored in LN2 Tank B, Box 1.\n\n"
                "Next steps:\n"
                "  1. Release testing: sterility (14-day compendial), mycoplasma (PCR), "
                "identity (CD3+, CAR+), viability post-thaw.\n"
                "  2. Proceed to G-Rex 100 scale-up in next experiment targeting "
                "≥5×10^9 cells for clinical-scale manufacturing demonstration.\n"
                "  3. Combine expanded T cells with CAR transduction (EXP-2026-002 MOI 10 "
                "conditions) for full manufacturing process run."
            ),
            version=1,
            created_by=bob.id,
        ),
    ]
    for entry in entries6:
        db.add(entry)

    # EXP-7 (approved) — existing results kept + new hypothesis, protocol, materials_notes, observations, conclusions
    entries7 = [
        LabEntry(
            experiment_id=exp7.id,
            section="hypothesis",
            content=(
                "The commercial LGALS3BP sandwich ELISA will validate the LC-MS/MS discovery "
                "finding from EXP-2026-003: serum LGALS3BP will be significantly elevated in "
                "early-stage CRC patients compared to healthy controls, with an expected "
                "2–3-fold increase based on the discovery cohort log2FC of 2.1. We predict "
                "AUC >0.85 based on the discovery cohort AUC of 0.87 (Stage I/II subgroup), "
                "with sensitivity >80% and specificity >80% at the optimal cutoff. "
                "Stage I/II early detection is the primary clinical utility of interest."
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp7.id,
            section="protocol",
            content=(
                "Sample preparation:\n"
                "  1. Thaw 96 serum samples (48 CRC, 48 HC) on ice.\n"
                "  2. Centrifuge 2,000×g 5 min to remove any particulates.\n"
                "  3. Dilute each sample 1:100 in ELISA assay diluent provided in kit.\n"
                "  4. Prepare samples in duplicate.\n\n"
                "ELISA procedure (Elabscience E-EL-H0655 sandwich ELISA kit):\n"
                "  5. Add 100 µL diluted samples and standards (8-point curve, 0–100 ng/mL, "
                "in duplicate) to pre-coated 96-well plates.\n"
                "  6. Incubate 90 min at 37°C, sealed.\n"
                "  7. Wash 3× with 1× wash buffer (300 µL/well each wash).\n"
                "  8. Add 100 µL biotin-conjugated detection antibody. Incubate 60 min at 37°C.\n"
                "  9. Wash 3×. Add 100 µL avidin-HRP conjugate. Incubate 30 min at 37°C.\n"
                "  10. Wash 5×. Add 90 µL TMB substrate solution. Incubate 15 min at RT in dark.\n"
                "  11. Add 50 µL H2SO4 stop solution. Read OD450 (reference 570 nm) within 5 min.\n\n"
                "Data analysis:\n"
                "  - Standard curve: 4-parameter logistic (4PL) fitting in GraphPad Prism 10\n"
                "  - Group comparison: Mann-Whitney U test (non-parametric, two-tailed)\n"
                "  - ROC curve analysis with AUC, sensitivity, specificity at Youden index cutoff\n"
                "  - Subgroup analysis by CRC stage (I, II, III, IV)\n"
                "  - Intra-assay CV: calculated per plate. Inter-assay CV: calculated across 4 plates\n"
                "  - Samples with CV >15%: flagged for repeat"
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp7.id,
            section="materials_notes",
            content=(
                "ELISA kit:\n"
                "  - LGALS3BP Human ELISA Kit (Elabscience E-EL-H0655), lot E-2026-0312\n"
                "  - ULOQ: 100 ng/mL; LLOQ: 0.78 ng/mL\n"
                "  - Kit expiry: 2026-12-31\n\n"
                "Sample cohort:\n"
                "  CRC patients (n=48):\n"
                "    Stage I: n=12, Stage II: n=18, Stage III: n=12, Stage IV: n=6\n"
                "    Median age 62y (range 41–79), 54% male\n"
                "    All treatment-naive at time of blood collection\n"
                "  Healthy controls (n=48):\n"
                "    Age/sex-matched (median age 61y, range 40–78, 52% male)\n"
                "    No personal or family history of CRC, no IBD\n"
                "  Samples sourced from Biobank BB-2024 (approved, IRB-2024-089)\n\n"
                "Equipment:\n"
                "  - Plate reader: SpectraMax iD3 (Molecular Devices), SN MDS-014\n"
                "    Wavelength: 450 nm; reference wavelength: 570 nm\n"
                "  - Automated plate washer: BioTek 405LS\n"
                "  - GraphPad Prism 10.2.3 (statistical analysis and curve fitting)"
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp7.id,
            section="results",
            content=(
                "LGALS3BP median: CRC 24.7 µg/mL (IQR 18.2–33.1) vs HC 11.3 µg/mL (IQR 8.6–15.4), "
                "p<0.0001 Mann-Whitney. ROC AUC: 0.91 (95% CI 0.85–0.97). Optimal cutoff 17.5 µg/mL: "
                "sensitivity 87.5%, specificity 85.4%."
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp7.id,
            section="observations",
            content=(
                "Intra-assay CV: mean 4.2%, maximum 9.1% across all plates — all wells within "
                "the acceptance criterion of <15%. Inter-assay CV across 4 plates: 7.8%, "
                "acceptable for a multi-plate study of this size.\n\n"
                "Standard curve performance: R²=0.998 (4PL fit), confirming excellent curve "
                "quality across all 4 plates. Slope and asymptote parameters were consistent "
                "plate-to-plate (CV <10% for each parameter).\n\n"
                "Two CRC samples (CRC-034, CRC-041) were initially above the ULOQ — both "
                "were diluted to 1:400 and re-run. Calculated concentrations post-dilution "
                "correction: 218 µg/mL and 195 µg/mL respectively (Stage III and Stage IV).\n\n"
                "One HC sample (HC-022) had high CV (18.2%) on first run — repeated from "
                "frozen aliquot, new CV 6.4%. Original measured value used in final analysis.\n\n"
                "LGALS3BP levels showed marked elevation in all CRC stages including Stage I:\n"
                "  Stage I median: 18.9 µg/mL vs HC 11.3 µg/mL (p=0.003)\n"
                "  Stage II median: 22.1 µg/mL (p<0.0001)\n"
                "  Stage III median: 29.4 µg/mL (p<0.0001)\n"
                "  Stage IV median: 38.4 µg/mL (highest, p<0.0001)\n\n"
                "Stage I detection AUC: 0.84 (95% CI 0.72–0.96) — clinically meaningful for "
                "early detection utility."
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp7.id,
            section="conclusions",
            content=(
                "LGALS3BP ELISA validation is successful. AUC 0.91 (95% CI 0.85–0.97) exceeds "
                "the pre-specified success criterion of AUC >0.85. Sensitivity 87.5% and "
                "specificity 85.4% at the optimal cutoff of 17.5 µg/mL are clinically meaningful "
                "thresholds for a screening-adjunct biomarker.\n\n"
                "The Stage I subgroup AUC of 0.84 is particularly notable — detecting CRC at "
                "Stage I, when surgical cure rates are >90%, is the primary unmet need in CRC "
                "diagnostics. These results strongly support LGALS3BP as a promising early "
                "detection biomarker.\n\n"
                "The 2.2-fold median increase (24.7 vs 11.3 µg/mL) in the validation cohort "
                "is consistent with the discovery cohort log2FC of 2.1 (EXP-2026-003), "
                "confirming reproducibility across independent sample sets.\n\n"
                "Next steps:\n"
                "  1. Advance to prospective clinical validation study (target n=300, "
                "multi-center, IRB amendment in preparation).\n"
                "  2. Investigate LGALS3BP in combination with CEA for improved sensitivity/specificity.\n"
                "  3. Manuscript in preparation — target journal: Clinical Cancer Research.\n"
                "  4. Patent application being evaluated (technology transfer office contacted)."
            ),
            version=1,
            created_by=carol.id,
        ),
    ]
    for entry in entries7:
        db.add(entry)

    # EXP-8 (in_progress) — existing protocol kept + new hypothesis, materials_notes, results, observations
    entries8 = [
        LabEntry(
            experiment_id=exp8.id,
            section="hypothesis",
            content=(
                "Western blot will confirm the LC-MS/MS differential expression findings from "
                "EXP-2026-003 for all 5 candidate proteins (LGALS3BP, CEA, CEACAM5, CA19-9 "
                "precursor, APOA1) in at least 80% of samples tested (16/20 paired CRC/HC). "
                "Concordance with MS data of ≥80% per marker will be considered validation "
                "of the proteomics discovery. Western blot provides orthogonal, antibody-based "
                "confirmation of protein identity and approximate molecular weight, "
                "complementing the mass accuracy of LC-MS/MS identification."
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp8.id,
            section="protocol",
            content=(
                "1. Run 12% SDS-PAGE with 10 µg protein per lane. "
                "2. Transfer to PVDF membrane (100V, 1h). "
                "3. Block 5% BSA/TBST 1h RT. "
                "4. Primary antibodies overnight at 4°C. "
                "5. Secondary HRP-conjugated antibody 1h RT. "
                "6. ECL detection. "
                "Antibodies: anti-LGALS3BP (Abcam ab87792), anti-CEA (Cell Signaling 4435S), "
                "anti-CEACAM5 (R&D Systems MAB1643)."
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp8.id,
            section="materials_notes",
            content=(
                "Protein samples:\n"
                "  - 20 paired serum samples from EXP-2026-003 (10 CRC, 10 HC)\n"
                "  - Protein quantification by BCA assay; 10 µg protein per lane\n"
                "  - Samples denatured in 4× LDS sample buffer + 10× reducing agent, "
                "95°C 10 min\n\n"
                "Electrophoresis and transfer:\n"
                "  - NuPAGE 4-12% Bis-Tris protein gels (Invitrogen NP0321BOX), lot 2387651\n"
                "  - MOPS SDS running buffer (Invitrogen NP0001)\n"
                "  - iBlot 2 dry transfer system (Thermo Fisher), PVDF mini stacks, "
                "P0 program 7 min\n"
                "  - Blocking: 5% BSA in TBST (0.1% Tween-20), 1h RT with rocking\n\n"
                "Primary antibodies (all in 5% BSA/TBST):\n"
                "  - Anti-LGALS3BP: Abcam ab87792 (rabbit polyclonal), 1:1000, overnight 4°C, "
                "expected band: ~65 kDa\n"
                "  - Anti-CEA: Cell Signaling Technology 4435S (rabbit mAb), 1:1000, "
                "overnight 4°C, expected band: ~180 kDa (glycosylated)\n"
                "  - Anti-CEACAM5: R&D Systems MAB1643 (mouse mAb), 1:500, overnight 4°C, "
                "expected band: ~150–200 kDa\n"
                "  - Anti-CA19-9 precursor: Abcam ab275961 (rabbit polyclonal), 1:500, "
                "overnight 4°C, expected band: ~55 kDa\n"
                "  - Anti-APOA1: Cell Signaling Technology 3A1A2 (rabbit mAb), 1:2000, "
                "overnight 4°C, expected band: ~28 kDa\n"
                "  - Loading control: Anti-β-actin (Abcam ab8226, mouse mAb), 1:5000, 1h RT\n\n"
                "Secondary antibodies:\n"
                "  - HRP-conjugated goat anti-rabbit IgG (Cell Signaling 7074S), 1:5000, 1h RT\n"
                "  - HRP-conjugated goat anti-mouse IgG (Cell Signaling 7076S), 1:5000, 1h RT\n\n"
                "Detection:\n"
                "  - Pierce ECL Plus Western Blotting Substrate (Thermo Fisher 32132)\n"
                "  - ChemiDoc MP Imaging System (Bio-Rad), chemiluminescence mode\n"
                "  - Densitometry: Image Lab 6.1 (Bio-Rad), normalized to β-actin"
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp8.id,
            section="results",
            content=(
                "Preliminary results — first 10 of 20 samples processed:\n\n"
                "LGALS3BP (~65 kDa):\n"
                "  8/10 CRC samples show clear upregulation vs matched HC control.\n"
                "  Densitometry (β-actin normalized): CRC median 2.84-fold vs HC.\n"
                "  Consistent with LC-MS/MS log2FC=2.1 from EXP-2026-003.\n"
                "  2 CRC samples show modest increase (1.3–1.5-fold) — possible inter-patient "
                "variability or low-expression subgroup.\n\n"
                "CEA (~180 kDa, heavily glycosylated):\n"
                "  9/10 CRC samples: clear positive band at expected MW.\n"
                "  HC samples: faint to absent.\n"
                "  Strong concordance with MS data. Confirms antibody specificity.\n\n"
                "CEACAM5 (~150–200 kDa):\n"
                "  7/10 CRC samples upregulated.\n"
                "  3 CRC samples show only modest increase (1.2–1.4-fold) vs MS prediction "
                "of >2.6-fold. Possible antibody cross-reactivity or epitope masking.\n"
                "  Further investigation needed (see observations).\n\n"
                "APOA1 (~28 kDa):\n"
                "  9/10 HC samples show strong band; 8/10 CRC show clearly reduced intensity.\n"
                "  Median fold-reduction in CRC: 0.47× vs HC. Good concordance with MS data.\n\n"
                "CA19-9 precursor (~55 kDa):\n"
                "  CURRENT STATUS: non-specific bands observed at 35 kDa in addition to "
                "expected 55 kDa band. Antibody (Abcam ab275961) performance suboptimal.\n"
                "  Alternative antibody (Abcam ab135948) ordered — to be tested in next run.\n\n"
                "Remaining 10 samples queued for next blot run (scheduled 2026-04-14)."
            ),
            version=1,
            created_by=alice.id,
        ),
        LabEntry(
            experiment_id=exp8.id,
            section="observations",
            content=(
                "CA19-9 antibody non-specific banding at 35 kDa is a concern and likely "
                "represents a cross-reactive serum protein. The expected 55 kDa band is "
                "visible but cannot be confidently quantified against the non-specific "
                "background. Testing alternative antibody clone ab135948 in next run.\n\n"
                "CEACAM5 partial discordance with LC-MS/MS data may reflect differential "
                "antibody epitope accessibility in denatured (WB) vs native (MS tryptic "
                "peptide) conditions. CEACAM5 is heavily glycosylated and the R&D Systems "
                "MAB1643 targets a protein epitope in the N-terminal domain — denaturation "
                "may not fully expose this epitope in all samples.\n\n"
                "Overall concordance for 4/5 markers (LGALS3BP, CEA, APOA1, and preliminary "
                "CEACAM5) is promising. β-actin loading control is uniform across all "
                "20 lanes (CV <8%), confirming equal protein loading.\n\n"
                "Film exposure times used: LGALS3BP 2 min, CEA 30 sec (strong signal), "
                "CEACAM5 5 min, APOA1 1 min, CA19-9 3 min (suboptimal due to non-specific bands)."
            ),
            version=1,
            created_by=alice.id,
        ),
    ]
    for entry in entries8:
        db.add(entry)

    # EXP-9 (completed) — existing entries kept + new hypothesis, protocol, materials_notes, conclusions
    entries9 = [
        LabEntry(
            experiment_id=exp9.id,
            section="hypothesis",
            content=(
                "Perfusion culture mode will achieve ≥50% higher final IgG1 titer compared to "
                "fed-batch by Day 14, owing to continuous nutrient replenishment and metabolic "
                "waste removal. Cell-specific productivity (pg/cell/day) is expected to be "
                "similar between modes, with titer difference driven primarily by higher steady-state "
                "viable cell density in perfusion. Lactate accumulation — a known suppressor of "
                "cell-specific productivity at concentrations >25 mM — will be the key differentiator "
                "between modes (Lao & Toth, 1997)."
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp9.id,
            section="protocol",
            content=(
                "Six 2L bioreactors (Sartorius Biostat B-DCU II): 3× fed-batch, 3× perfusion\n"
                "Cell line: CHO-K1 IgG1-anti-EGFR (same clone as EXP-2026-004, lot WCB-2025-001-v3)\n"
                "Inoculation: 0.5×10^6 viable cells/mL in 1.5L CD FortiCHO + 8 mM glutamine\n\n"
                "Fed-batch arm:\n"
                "  - Bolus feeds of CD EfficientFeed C (5% v/v) on Days 3, 5, 7, 9\n"
                "  - pH 7.2 setpoint (per EXP-2026-004 optimization), DO 40%\n"
                "  - Daily sampling from Day 1\n\n"
                "Perfusion arm:\n"
                "  - ATF2 hollow fiber filter (Repligen XCell ATF2, 0.2 µm polysulfone)\n"
                "  - Perfusion rate: 0.5 reactor volumes (RV)/day Days 1–3, ramping linearly "
                "to 2 RV/day by Day 7, maintained at 2 RV/day Days 7–14\n"
                "  - Bleed strategy: VCC-based bleed from Day 5 targeting steady-state "
                "VCC of 60×10^6 cells/mL\n"
                "  - pH 7.2, DO 40% (same setpoints as fed-batch)\n"
                "  - Daily sampling from Day 1\n\n"
                "Analysis:\n"
                "  - VCC/viability: Vi-CELL XR (daily)\n"
                "  - Metabolites: Cedex Bio Analyzer offline (glucose, lactate, glutamine, "
                "ammonia, osmolality)\n"
                "  - IgG1 titer: Protein A HPLC (daily from Day 5)\n"
                "Run duration: Day 14 harvest for both arms"
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp9.id,
            section="materials_notes",
            content=(
                "Perfusion hardware:\n"
                "  - ATF2 hollow fiber filter: Repligen XCell ATF2, polysulfone, 0.2 µm, "
                "lot ATF-2026-001\n"
                "  - ATF controller: Repligen XCell ATF controller 2.0\n"
                "  - Bleed reservoir: 20L polycarbonate carboy, pre-sterilized by autoclave\n\n"
                "Media and feeds: same lots as EXP-2026-004 (CD FortiCHO lot 2381054, "
                "EfficientFeed C lot 2319876)\n\n"
                "Process analytical technology:\n"
                "  - Bioreactor online: DASGIP DO/pH probes (Eppendorf)\n"
                "  - Offline metabolites: Cedex Bio Analyzer (Roche), lot CEX-2026-001, "
                "last calibration 2026-03-20\n"
                "  - Titer: Protein A HPLC (same setup as EXP-2026-004)\n\n"
                "Quality: Both arms run in GMP-like conditions with complete batch records. "
                "Raw data archived in ELN folder EXP-2026-009/raw."
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp9.id,
            section="results",
            content=(
                "Fed-batch Day 14 titer: 4.2 g/L ± 0.3 (n=3 bioreactors). "
                "Perfusion Day 14 titer: 6.8 g/L ± 0.4 (n=3 bioreactors). "
                "Cell-specific productivity: fed-batch 18.4 pg/cell/day, perfusion 22.1 pg/cell/day. "
                "Perfusion mode shows 62% higher titer. Statistical significance: p=0.003 (two-tailed t-test)."
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp9.id,
            section="observations",
            content=(
                "Perfusion mode significantly outperforms fed-batch for this clone. Main concern is "
                "operational complexity and increased media cost. Recommend cost-benefit analysis "
                "before process lock."
            ),
            version=1,
            created_by=carol.id,
        ),
        LabEntry(
            experiment_id=exp9.id,
            section="conclusions",
            content=(
                "Perfusion mode significantly outperforms fed-batch: 62% higher titer (6.8 vs "
                "4.2 g/L), higher peak VCC (68×10^6 vs 18×10^6 cells/mL), and modestly improved "
                "cell-specific productivity (22.1 vs 18.4 pg/cell/day, p=0.041).\n\n"
                "The titer difference is attributable to both higher viable cell density AND slightly "
                "higher cell-specific productivity in perfusion — consistent with the hypothesis that "
                "better metabolite control drives productivity improvements. Lactate in perfusion "
                "never exceeded 8 mM (vs peak 28 mM in fed-batch on Day 10–12), confirming the "
                "metabolic control advantage.\n\n"
                "Key trade-offs:\n"
                "  Perfusion advantages: 62% more product, lower peak lactate, higher cell density\n"
                "  Perfusion disadvantages: ~3× media volume consumption, ATF system complexity, "
                "higher capital equipment cost, greater operator oversight requirement\n\n"
                "Economic analysis:\n"
                "  - Break-even analysis pending with manufacturing team (target: 2 weeks)\n"
                "  - Preliminary estimate: perfusion media cost ~$4,200/run vs ~$1,400/run fed-batch "
                "at current catalog pricing; product value at ~$4,000/g titer differential "
                "worth ~$10,400 — favorable economics at batch scale\n\n"
                "Recommendation: Advance perfusion to 50L scale evaluation for final process "
                "decision. Proceed to EXP-2026-010 (Protein A chromatography optimization) "
                "using perfusion harvest material."
            ),
            version=1,
            created_by=carol.id,
        ),
    ]
    for entry in entries9:
        db.add(entry)

    # EXP-10 (draft) — Protein A chromatography optimization — all sections
    entries10 = [
        LabEntry(
            experiment_id=exp10.id,
            section="hypothesis",
            content=(
                "Optimizing the Protein A affinity chromatography step — specifically load "
                "challenge (10–40 mg/mL resin), wash buffer osmolarity (150–500 mM NaCl), "
                "and elution pH (3.0–3.8) — will increase IgG1 step yield from the current "
                "baseline of ~85% to ≥92% while reducing host cell protein (HCP) "
                "co-purification to <500 ppm. Based on published Protein A optimization work "
                "(Ghose et al., 2006; Zhu et al., 2019), we expect wash osmolarity to have "
                "the strongest impact on HCP removal, while elution pH will primarily affect "
                "step yield and eluate pool quality. Higher load challenge may reduce step "
                "yield at breakthrough conditions but will improve resin utilization economics."
            ),
            version=1,
            created_by=bob.id,
        ),
        LabEntry(
            experiment_id=exp10.id,
            section="protocol",
            content=(
                "DoE design: 3-factor central composite design (CCD), face-centered\n"
                "Factor 1 (A): Load challenge — 10, 25, 40 mg IgG1/mL resin\n"
                "Factor 2 (B): Intermediate wash NaCl concentration — 150, 325, 500 mM\n"
                "Factor 3 (C): Elution pH — 3.0, 3.4, 3.8\n"
                "Total runs: 20 (8 factorial + 6 axial + 6 center point replicates)\n\n"
                "Column setup:\n"
                "  - MabSelect SuRe 1 mL HiTrap column (Cytiva)\n"
                "  - Pre-equilibrated with 5 CV PBS pH 7.4 at 150 cm/h\n\n"
                "Chromatography method per run:\n"
                "  1. Equilibration: 5 CV PBS pH 7.4, 150 cm/h\n"
                "  2. Load: Clarified perfusion harvest (EXP-2026-009 material) diluted to "
                "target load challenge in PBS; load flow rate 150 cm/h\n"
                "  3. Post-load wash 1: 5 CV PBS pH 7.4, 300 cm/h\n"
                "  4. Intermediate wash (factor B): 5 CV 20 mM sodium phosphate pH 7.4 + "
                "[150/325/500 mM NaCl], 300 cm/h\n"
                "  5. Elution: 10 CV 100 mM sodium acetate [pH 3.0/3.4/3.8], 100 cm/h; "
                "collect 0.5 mL fractions across elution peak\n"
                "  6. Strip: 5 CV 0.1 M phosphoric acid, 150 cm/h\n"
                "  7. Re-equilibration: 5 CV PBS pH 7.4\n\n"
                "Analysis per run:\n"
                "  - IgG1 titer of load, flow-through, and eluate: Protein A HPLC\n"
                "  - Step yield calculation: (eluate titer × eluate volume) / "
                "(load titer × load volume) × 100%\n"
                "  - HCP: Cygnus CHO-HCP ELISA (kit F550), reported in ppm = "
                "ng HCP/mg IgG1\n"
                "  - Leached Protein A: Cygnus F400 ELISA\n"
                "  - Turbidity (A340) and SEC-HPLC for aggregation assessment\n\n"
                "Resin reuse study (separate from DoE):\n"
                "  - Run standard conditions (center point) for 10 consecutive cycles\n"
                "  - Monitor dynamic binding capacity (DBC) at 10% breakthrough (UV method)\n"
                "  - Accept criterion: DBC ≥90% of cycle 1 value through cycle 10"
            ),
            version=1,
            created_by=bob.id,
        ),
        LabEntry(
            experiment_id=exp10.id,
            section="materials_notes",
            content=(
                "Resin:\n"
                "  - MabSelect SuRe (Cytiva), 1 mL HiTrap pre-packed columns\n"
                "  - Lot: 10289473\n"
                "  - DBC specification: ≥35 mg IgG1/mL resin\n"
                "  - Storage buffer: 20% ethanol, stored at 4°C\n\n"
                "Load material:\n"
                "  - EXP-2026-009 Day 14 perfusion harvest, lot PROC-PERF-2026-001\n"
                "  - Titer: 6.62 g/L (measured by Protein A HPLC pre-clarification)\n"
                "  - Clarification: 0.2 µm PES membrane filter, 4°C storage, use within 72h\n\n"
                "Analytics:\n"
                "  - CHO-HCP ELISA: Cygnus Technologies F550, lot E-0423\n"
                "    Detection range: 1.6–100 ng/mL; samples diluted to fit within range\n"
                "  - Protein A ELISA: Cygnus Technologies F400, lot P-0312\n"
                "    LLOQ: 1 ng/mL leached Protein A\n\n"
                "Instrument:\n"
                "  - ÄKTA Pure 25 FPLC (Cytiva), SN AP-2026-003\n"
                "  - Last PM and calibration: 2026-03-01\n"
                "  - Fraction collector: Fraction collector F9-R, 0.5 mL fractions\n"
                "  - UNICORN 7.5 software for method control and data acquisition"
            ),
            version=1,
            created_by=bob.id,
        ),
    ]
    for entry in entries10:
        db.add(entry)

    db.flush()

    # ------------------------------------------------------------------
    # Materials usage on experiments
    # ------------------------------------------------------------------
    print("  Adding experiment materials...")

    em1 = ExperimentMaterial(
        experiment_id=exp1.id,
        material_id=ficoll.id,
        material_name=ficoll.name,
        lot_number="FP-20260301",
        quantity_used=25.0,
        unit="mL",
        added_by=bob.id,
    )
    em2 = ExperimentMaterial(
        experiment_id=exp1.id,
        material_id=rpmi.id,
        material_name=rpmi.name,
        lot_number="RPMI-20260115",
        quantity_used=500.0,
        unit="mL",
        added_by=bob.id,
    )
    em3 = ExperimentMaterial(
        experiment_id=exp2.id,
        material_id=anticd19.id,
        material_name=anticd19.name,
        lot_number="CD19-2026-A01",
        quantity_used=10.0,
        unit="µg",
        added_by=alice.id,
        notes="Used for flow cytometry validation of transduction",
    )
    em4 = ExperimentMaterial(
        experiment_id=exp2.id,
        material_id=lenti.id,
        material_name=lenti.name,
        lot_number="LV-2026-003",
        quantity_used=200.0,
        unit="µL",
        added_by=alice.id,
        notes="Titer: 2×10^8 TU/mL. Stored at -80°C, single-use aliquots.",
    )
    em5 = ExperimentMaterial(
        experiment_id=exp2.id,
        material_id=fbs.id,
        material_name=fbs.name,
        lot_number="FBS-2026-HI-07",
        quantity_used=50.0,
        unit="mL",
        added_by=bob.id,
    )
    # Manual entry (no catalog material)
    em6 = ExperimentMaterial(
        experiment_id=exp2.id,
        material_id=None,
        material_name="Polybrene (Hexadimethrine Bromide)",
        lot_number="PB-SIGMA-2026",
        quantity_used=4.0,
        unit="µg",
        added_by=alice.id,
        notes="8 µg/mL final concentration in 500 µL wells",
    )
    em7 = ExperimentMaterial(
        experiment_id=exp5.id,
        material_id=cr51.id,
        material_name=cr51.name,
        lot_number="CR51-PE-2026-01",
        quantity_used=100.0,
        unit="µCi",
        added_by=alice.id,
        notes="Handled under radiological safety protocols per SOP-RAD-002",
    )
    em8 = ExperimentMaterial(
        experiment_id=exp7.id,
        material_id=lgals3bp_kit.id,
        material_name=lgals3bp_kit.name,
        lot_number="EL-H0655-2026-03",
        quantity_used=1.0,
        unit="kit (96-well)",
        added_by=carol.id,
    )
    em9 = ExperimentMaterial(
        experiment_id=exp6.id,
        material_id=car_vector.id,
        material_name=car_vector.name,
        lot_number="LV-CD19-3G-2026-02",
        quantity_used=500.0,
        unit="µL",
        added_by=bob.id,
        notes="Titer: 1.5×10^9 TU/mL. Large-scale transduction aliquot.",
    )

    for em in [em1, em2, em3, em4, em5, em6, em7, em8, em9]:
        db.add(em)
    db.flush()

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------
    print("  Adding comments...")

    c1 = Comment(
        experiment_id=exp2.id,
        author_id=bob.id,
        comment_type="general",
        content=(
            "T cell activation confirmed by CD69 upregulation (>85% CD69+ at Day 2). "
            "Beads removed prior to transduction as per SOP-TC-004."
        ),
    )
    c2 = Comment(
        experiment_id=exp2.id,
        author_id=alice.id,
        comment_type="general",
        content=(
            "MOI 10 appears to be the optimal balance between transduction efficiency (34.7%) "
            "and cell viability. Will proceed with MOI 10 for scale-up experiments. "
            "MOI 20 shows diminishing returns with increased toxicity."
        ),
    )
    c3 = Comment(
        experiment_id=exp3.id,
        author_id=carol.id,
        comment_type="general",
        content=(
            "Sample batch 2 (CRC-11 through CRC-20) had slightly lower protein yields "
            "after ProteoMiner depletion. Results normalized by LFQ, confirmed consistent "
            "with batch 1 after QC."
        ),
    )
    c4 = Comment(
        experiment_id=exp4.id,
        author_id=dave.id,
        comment_type="review",
        content=(
            "Initial review: pH data appears consistent with prior runs. "
            "Please provide the raw bioreactor logs as an attachment before I finalize the review."
        ),
    )

    for c in [c1, c2, c3, c4]:
        db.add(c)
    db.flush()

    for c in [c1, c2, c3, c4]:
        create_audit_log(
            db=db,
            entity_type="comment",
            entity_id=str(c.id),
            action="created",
            actor_id=c.author_id,
            actor_username=next(
                u.username for u in [admin, alice, bob, carol, dave] if u.id == c.author_id
            ),
            new_value={"experiment_id": str(c.experiment_id), "type": c.comment_type},
        )

    # ------------------------------------------------------------------
    # Review for EXP-4
    # ------------------------------------------------------------------
    print("  Creating reviews...")

    review4 = Review(
        experiment_id=exp4.id,
        reviewer_id=dave.id,
        status="in_review",
        comments="Under active review. Awaiting bioreactor log attachment.",
    )
    db.add(review4)
    db.flush()

    create_audit_log(
        db=db,
        entity_type="review",
        entity_id=str(review4.id),
        action="created",
        actor_id=carol.id,
        actor_username="carol",
        new_value={
            "experiment_id": str(exp4.id),
            "reviewer_id": str(dave.id),
            "status": "in_review",
        },
    )

    # Status transition audit for EXP-4 (completed → under_review)
    create_audit_log(
        db=db,
        entity_type="experiment",
        entity_id=str(exp4.id),
        action="status_changed",
        actor_id=carol.id,
        actor_username="carol",
        old_value={"status": "completed"},
        new_value={"status": "under_review"},
    )

    # Review for EXP-7 (approved)
    review7 = Review(
        experiment_id=exp7.id,
        reviewer_id=dave.id,
        status="approved",
        comments=(
            "Excellent validation results. AUC >0.9 meets our pre-specified success criterion. "
            "Recommend proceeding to clinical study design."
        ),
    )
    db.add(review7)
    db.flush()

    create_audit_log(
        db=db,
        entity_type="review",
        entity_id=str(review7.id),
        action="created",
        actor_id=carol.id,
        actor_username="carol",
        new_value={
            "experiment_id": str(exp7.id),
            "reviewer_id": str(dave.id),
            "status": "approved",
        },
    )

    create_audit_log(
        db=db,
        entity_type="experiment",
        entity_id=str(exp7.id),
        action="status_changed",
        actor_id=dave.id,
        actor_username="dave",
        old_value={"status": "under_review"},
        new_value={"status": "approved"},
    )

    # ------------------------------------------------------------------
    # Signatures
    # ------------------------------------------------------------------
    print("  Adding signatures...")

    # EXP-3: completion signature by carol
    sig3 = Signature(
        experiment_id=exp3.id,
        signer_id=carol.id,
        signature_type="completion",
        meaning="I confirm that the above experiment was conducted as described and the data recorded is accurate and complete.",
        ip_address="10.0.1.42",
        user_agent="Mozilla/5.0 (seed script)",
    )
    db.add(sig3)
    db.flush()

    create_audit_log(
        db=db,
        entity_type="signature",
        entity_id=str(sig3.id),
        action="signed",
        actor_id=carol.id,
        actor_username="carol",
        new_value={
            "experiment_id": str(exp3.id),
            "signature_type": "completion",
            "meaning": sig3.meaning,
        },
    )

    # EXP-5: completion signature by alice
    sig5 = Signature(
        experiment_id=exp5.id,
        signer_id=alice.id,
        signature_type="completion",
        meaning="I confirm that the above experiment was conducted as described and the data recorded is accurate and complete.",
        ip_address="10.0.1.41",
        user_agent="Mozilla/5.0 (seed script)",
    )
    db.add(sig5)
    db.flush()

    create_audit_log(
        db=db,
        entity_type="signature",
        entity_id=str(sig5.id),
        action="signed",
        actor_id=alice.id,
        actor_username="alice",
        new_value={
            "experiment_id": str(exp5.id),
            "signature_type": "completion",
            "meaning": sig5.meaning,
        },
    )

    # EXP-7: completion signature by carol
    sig7_completion = Signature(
        experiment_id=exp7.id,
        signer_id=carol.id,
        signature_type="completion",
        meaning="I confirm that the above experiment was conducted as described and the data recorded is accurate and complete.",
        ip_address="10.0.1.42",
        user_agent="Mozilla/5.0 (seed script)",
    )
    db.add(sig7_completion)
    db.flush()

    create_audit_log(
        db=db,
        entity_type="signature",
        entity_id=str(sig7_completion.id),
        action="signed",
        actor_id=carol.id,
        actor_username="carol",
        new_value={
            "experiment_id": str(exp7.id),
            "signature_type": "completion",
            "meaning": sig7_completion.meaning,
        },
    )

    # EXP-7: review signature by dave
    sig7_review = Signature(
        experiment_id=exp7.id,
        signer_id=dave.id,
        signature_type="review",
        meaning="I have reviewed the above experiment record and approve its content as accurate and compliant.",
        ip_address="10.0.1.44",
        user_agent="Mozilla/5.0 (seed script)",
    )
    db.add(sig7_review)
    db.flush()

    create_audit_log(
        db=db,
        entity_type="signature",
        entity_id=str(sig7_review.id),
        action="signed",
        actor_id=dave.id,
        actor_username="dave",
        new_value={
            "experiment_id": str(exp7.id),
            "signature_type": "review",
            "meaning": sig7_review.meaning,
        },
    )

    # EXP-9: completion signature by carol
    sig9 = Signature(
        experiment_id=exp9.id,
        signer_id=carol.id,
        signature_type="completion",
        meaning="I confirm that the above experiment was conducted as described and the data recorded is accurate and complete.",
        ip_address="10.0.1.42",
        user_agent="Mozilla/5.0 (seed script)",
    )
    db.add(sig9)
    db.flush()

    create_audit_log(
        db=db,
        entity_type="signature",
        entity_id=str(sig9.id),
        action="signed",
        actor_id=carol.id,
        actor_username="carol",
        new_value={
            "experiment_id": str(exp9.id),
            "signature_type": "completion",
            "meaning": sig9.meaning,
        },
    )

    db.commit()
    print("Seed complete.")
    print("\nSeeded users (all password: Lab2026!):")
    for u, roles_list in [
        (admin, ["admin"]),
        (alice, ["scientist"]),
        (bob, ["technician"]),
        (carol, ["research_associate", "scientist"]),
        (dave, ["reviewer"]),
    ]:
        print(f"  {u.username:10s}  {u.email:25s}  roles: {', '.join(roles_list)}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}", file=sys.stderr)
        raise
    finally:
        db.close()
