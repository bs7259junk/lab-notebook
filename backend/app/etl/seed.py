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

    # EXP-2 (in_progress) — full set of entries
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
    ]
    for entry in entries2:
        db.add(entry)

    # EXP-3 (completed) — all sections
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
    ]
    for entry in entries3:
        db.add(entry)

    # EXP-5 (completed) — cytotoxicity assay entries
    entries5 = [
        LabEntry(
            experiment_id=exp5.id,
            section="results",
            content=(
                "Specific lysis at E:T 20:1: Raji 78.3±4.2%, K562 3.1±0.8% (background). "
                "EC50 calculated as E:T 7.4. Results demonstrate robust and antigen-specific "
                "cytotoxicity consistent with functional CAR-T product."
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

    # EXP-6 (active) — bioreactor scale-up entry
    entries6 = [
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
    ]
    for entry in entries6:
        db.add(entry)

    # EXP-7 (approved) — LGALS3BP ELISA validation entries
    entries7 = [
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
    ]
    for entry in entries7:
        db.add(entry)

    # EXP-8 (in_progress) — Western blot entries
    entries8 = [
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
    ]
    for entry in entries8:
        db.add(entry)

    # EXP-9 (completed) — fed-batch vs perfusion entries
    entries9 = [
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
    ]
    for entry in entries9:
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
