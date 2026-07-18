# NGS Cancer Variant Pipeline & Dashboard

An end-to-end cancer genomics pipeline and web application: simulated next-generation sequencing (NGS) reads are aligned, variant-called, and annotated against real clinical significance data for **BRCA1** — one of the most clinically significant breast/ovarian cancer genes — with results served through a REST API and visualized in a React dashboard.

Built as a portfolio project demonstrating the full stack expected of a software engineer working in cancer genomics/bioinformatics infrastructure: containerized bioinformatics tooling, a relational database, a Flask API, a React frontend, and CI/CD.

## Why BRCA1

Rather than using a generic or synthetic reference, this pipeline uses the real genomic coordinates and sequence for BRCA1 (GRCh38, chr17:43,044,292–43,170,245), and annotates called variants against **Ensembl VEP / ClinVar**, real clinical databases used in actual cancer genetics practice. During development, the annotation step correctly identified several ClinVar-catalogued variants by coincidence within randomly simulated mutations — including one flagged as clinically **pathogenic** — validating that the pipeline's annotation logic works against genuine clinical data, not just toy examples.

## Architecture

```
 ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
 │   Simulate   │ ───▶ │    Align     │ ───▶ │ Call Variants│ ───▶ │   Annotate   │
 │   (wgsim)    │      │  (BWA-MEM)   │      │ (GATK        │      │ (Ensembl VEP │
 │              │      │              │      │ HaplotypeCaller)    │  / ClinVar)  │
 └──────────────┘      └──────────────┘      └──────────────┘      └──────┬───────┘
  Dockerized bioinformatics tools, orchestrated by orchestrate.py           │
                                                                            ▼
                                                                  ┌──────────────────┐
                                                                  │   PostgreSQL      │
                                                                  │  (runs, variants) │
                                                                  └────────┬──────────┘
                                                                           │
                                                                  ┌────────▼──────────┐
                                                                  │   Flask REST API   │
                                                                  └────────┬──────────┘
                                                                           │
                                                                  ┌────────▼──────────┐
                                                                  │  React Dashboard   │
                                                                  │ (stats, variant     │
                                                                  │  track, tables)     │
                                                                  └────────────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| Pipeline tools | BWA, samtools, wgsim, GATK4 (HaplotypeCaller) |
| Annotation | Ensembl VEP REST API (ClinVar clinical significance) |
| Containerization | Docker (custom image for alignment tools, official GATK image) |
| Orchestration | Python (`subprocess`-based pipeline runner with JSON status tracking) |
| Database | PostgreSQL |
| Backend API | Flask, psycopg2 |
| Frontend | React (Vite), custom SVG data visualization |
| CI/CD | GitHub Actions (Docker build, pipeline smoke test, backend/frontend checks) |

## Pipeline Stages

1. **Simulate** — `wgsim` generates synthetic paired-end FASTQ reads from the BRCA1 reference at ~30x coverage, with a known set of planted mutations (ground truth for validation).
2. **Align** — `BWA-MEM` aligns reads to the reference, producing a sorted, indexed BAM file with read groups.
3. **Call Variants** — `GATK HaplotypeCaller` identifies variants (SNPs/indels) from the aligned reads, producing a VCF.
4. **Annotate** — A Python script queries the Ensembl VEP REST API for each variant, retrieving predicted consequence and, where available, real ClinVar clinical significance.

All four stages run inside Docker containers and are orchestrated end-to-end by `pipeline/orchestrate.py`, which records the status of every stage to `pipeline_status.json`.

## Running It

### Prerequisites
- Docker Desktop
- Python 3.10+
- Node.js 18+
- PostgreSQL (via Docker, see below)

### 1. Build the pipeline tools image
```bash
cd pipeline
docker build -t ngs-tools .
```

### 2. Run the pipeline
```bash
python orchestrate.py
```
This simulates reads, aligns, and calls variants against the BRCA1 reference, producing `variants_genomic.vcf` in `data/`.

### 3. Annotate variants
```bash
cd pipeline/annotation
python -m venv venv && venv\Scripts\activate
pip install requests
python annotate.py
```

### 4. Start Postgres and the backend API
```bash
docker run --name ngs-postgres -e POSTGRES_PASSWORD=devpassword -e POSTGRES_DB=ngs_pipeline -p 5433:5432 -d postgres:16
cd backend
python -m venv venv && venv\Scripts\activate
pip install flask psycopg2-binary flask-cors
Get-Content schema.sql -Raw | docker exec -i ngs-postgres psql -U postgres -d ngs_pipeline
python app.py
```

### 5. Start the frontend
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173`.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/stats` | Aggregate counts (runs, variants, pathogenic findings) |
| POST | `/runs` | Create a new pipeline run |
| GET | `/runs` | List all runs |
| POST | `/runs/<id>/variants` | Bulk insert variants for a run |
| GET | `/runs/<id>/variants` | List variants for a run |

## Dashboard

The React dashboard shows aggregate pipeline statistics, a table of pipeline runs, and — for any selected run — a genomic variant track (styled after the "lollipop plot" visualizations used by tools like cBioPortal) showing each variant's real position along BRCA1, color-coded by clinical significance, alongside a detailed variant table.

![Dashboard screenshot](docs/screenshot.png)
*(add a screenshot of the dashboard here)*

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`) runs on every push:
- Builds the pipeline Docker image
- Runs a real alignment smoke test (simulate + align + verify mapping rate)
- Checks Python syntax across backend/pipeline code
- Builds the React frontend for production

## Possible Extensions

- Deploy to AWS/GCP/Azure (containerized services + managed Postgres)
- Extend annotation to handle indels, not just SNPs
- Support additional cancer genes beyond BRCA1
- Real (non-simulated) public sequencing datasets (e.g., 1000 Genomes, GIAB)
