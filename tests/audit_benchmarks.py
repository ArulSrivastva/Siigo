"""
Benchmark Corpora Exact Audit & Grounding Table
"""
from pathlib import Path

def audit_benchmarks():
    base = Path("data/benchmarks")
    folders = [f for f in base.iterdir() if f.is_dir()]
    
    print("| Benchmark Folder | Physical Files | Total Disk Size | Honest Classification | Purpose in Architecture |")
    print("|---|---|---|---|---|")
    for f in folders:
        files = list(f.glob("**/*"))
        regular_files = [x for x in files if x.is_file()]
        total_size_mb = sum(x.stat().st_size for x in regular_files) / (1024 * 1024)
        
        if f.name == "ami_annotations":
            status = f"**Downloaded ({len(regular_files):,d} files, {total_size_mb:.1f} MB)**"
            purpose = "Action & decision annotations for spoken meeting transcripts"
        elif f.name == "code-mixed-nlp":
            status = f"**Code repo only ({len(regular_files)} files, {total_size_mb:.1f} MB)**"
            purpose = "HingCorpus scripts (Full 52.9M dataset remains hosted on Hugging Face)"
        elif f.name == "dravidian_codemix":
            status = f"**Curated Sample ({len(regular_files)} file)**"
            purpose = "Tanglish operational sample (Not the full 35k YouTube dataset)"
        elif f.name == "indicvoices":
            status = f"**Manifest Only ({len(regular_files)} file)**"
            purpose = "Audio evaluation manifest (Audio clips streamable via Hugging Face token)"
        elif f.name == "lince":
            status = f"**Sample Only ({len(regular_files)} file)**"
            purpose = "Hindi-English LID/POS tag alignment sample"
        else:
            status = f"{len(regular_files)} files"
            purpose = "General evaluation"
            
        print(f"| `{f.name}` | {len(regular_files)} | {total_size_mb:.1f} MB | {status} | {purpose} |")

if __name__ == "__main__":
    audit_benchmarks()
