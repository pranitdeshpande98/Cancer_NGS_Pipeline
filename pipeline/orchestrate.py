import subprocess
import json
import time

DATA_DIR = r"C:\Users\16674\Desktop\cancer_ngs_pipeline\data"
REFERENCE = "brca1_genomic.fasta"
NGS_IMAGE = "ngs-tools"
GATK_IMAGE = "broadinstitute/gatk"
STATUS_FILE = "pipeline_status.json"


def run_docker(image, command):
    """Run a shell command inside a Docker container, with the data folder mounted at /work."""
    full_cmd = [
        "docker", "run", "--rm",
        "-v", f"{DATA_DIR}:/work",
        image,
        "bash", "-c", command,
    ]
    return subprocess.run(full_cmd, capture_output=True, text=True)


class PipelineStatus:
    """Tracks and persists the status of each pipeline stage to a JSON file."""

    def __init__(self):
        self.stages = []

    def record(self, name, status, detail=""):
        self.stages.append({
            "stage": name,
            "status": status,
            "detail": detail,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        with open(STATUS_FILE, "w") as f:
            json.dump(self.stages, f, indent=2)


def run_stage(status, name, image, command):
    print(f"--- Running stage: {name} ---")
    status.record(name, "running")
    result = run_docker(image, command)
    if result.returncode != 0:
        print(result.stderr)
        status.record(name, "failed", result.stderr[-500:])
        raise RuntimeError(f"Stage '{name}' failed -- see output above")
    status.record(name, "success")
    print(f"--- Stage '{name}' succeeded ---")


def main():
    status = PipelineStatus()

    run_stage(status, "simulate_reads", NGS_IMAGE,
        f"wgsim -N 30000 -1 100 -2 100 -e 0.01 -r 0.001 -S 42 "
        f"{REFERENCE} reads_genomic_1.fastq reads_genomic_2.fastq > true_mutations_genomic.txt")

    run_stage(status, "index_reference", NGS_IMAGE,
        f"bwa index {REFERENCE} && samtools faidx {REFERENCE}")

    run_stage(status, "align", NGS_IMAGE,
        'bwa mem -R "@RG\\tID:sample1\\tSM:sample1\\tLB:lib1\\tPL:ILLUMINA" '
        f'{REFERENCE} reads_genomic_1.fastq reads_genomic_2.fastq > aligned_genomic.sam && '
        'samtools sort -o aligned_genomic.sorted.bam aligned_genomic.sam && '
        'samtools index aligned_genomic.sorted.bam')

    run_stage(status, "create_dict", GATK_IMAGE,
        f"cd /work && rm -f brca1_genomic.dict && gatk CreateSequenceDictionary -R {REFERENCE} -O brca1_genomic.dict")

    run_stage(status, "call_variants", GATK_IMAGE,
        f"cd /work && gatk HaplotypeCaller -R {REFERENCE} -I aligned_genomic.sorted.bam -O variants_genomic.vcf")

    print("\nPipeline complete. Run annotate.py separately (it needs its own venv with `requests` installed).")


if __name__ == "__main__":
    main()