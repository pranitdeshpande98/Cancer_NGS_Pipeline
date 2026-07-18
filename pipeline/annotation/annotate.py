import json
import requests

VCF_PATH = "../../data/variants_genomic.vcf"
OFFSET = 43044291   # local position 1 == true chr17 position 43,044,292
CHROM = "17"
BATCH_SIZE = 200
VEP_URL = "https://rest.ensembl.org/vep/human/region"


def parse_vcf(path):
    """Read a VCF and return a list of (true_genomic_pos, ref, alt) tuples."""
    variants = []
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            local_pos = int(fields[1])
            ref = fields[3]
            alt = fields[4]
            true_pos = local_pos + OFFSET
            variants.append((true_pos, ref, alt))
    return variants


def to_vep_strings(variants):
    """Convert variants into the minimal VCF-like string format VEP's API expects,
    keeping only simple single-base substitutions for now."""
    lines = []
    for true_pos, ref, alt in variants:
        if len(ref) == 1 and len(alt) == 1:
            lines.append(f"{CHROM} {true_pos} . {ref} {alt} . . .")
    return lines


def query_vep(batch):
    """Send one batch of variants to Ensembl's VEP API and return the parsed JSON response."""
    resp = requests.post(
        VEP_URL,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json={"variants": batch},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    variants = parse_vcf(VCF_PATH)
    print(f"Parsed {len(variants)} variants from VCF")

    vep_lines = to_vep_strings(variants)
    print(f"{len(vep_lines)} are simple SNPs we can send to VEP (indels skipped for now)")

    results = []
    for i in range(0, len(vep_lines), BATCH_SIZE):
        batch = vep_lines[i:i + BATCH_SIZE]
        results.extend(query_vep(batch))

    with open("annotated_variants.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} annotated variants to annotated_variants.json")

    flagged = 0
    for r in results:
        for cv in r.get("colocated_variants", []):
            if "clin_sig" in cv:
                flagged += 1
                print(f"Known variant {cv.get('id')} at {r.get('seq_region_name')}:{r.get('start')} "
                      f"-- clinical significance: {cv['clin_sig']}")
    if flagged == 0:
        print("No variants matched a known clinically annotated entry "
              "(expected -- these mutations were randomly simulated, not real disease variants).")


if __name__ == "__main__":
    main()