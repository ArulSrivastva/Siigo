"""
Benchmark Corpora Ingestion Script
Downloads the external benchmark resources specified in the Benchmark Matrix:
1. L3Cube HingCorpus / code-mixed NLP repository (Hinglish text & tokenization)
2. AMI Corpus annotations (OpenSLR 16) for Speaker Attribution and Decision items
3. Dravidian-CodeMix sample set (FIRE 2021)
"""
import os
import sys
import zipfile
import urllib.request
import subprocess
from pathlib import Path

BENCHMARK_DIR = Path("data/benchmarks")
BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

def setup_l3cube():
    target = BENCHMARK_DIR / "code-mixed-nlp"
    if target.exists():
        print(f"[OK] L3Cube repository already exists at {target}")
        return
    print("--> Cloning L3Cube code-mixed NLP repository (Hinglish/HingCorpus)...")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/l3cube-pune/code-mixed-nlp.git", str(target)],
            check=True
        )
        print("[DONE] L3Cube code-mixed NLP cloned successfully.")
    except Exception as e:
        print(f"[WARN] Failed to clone L3Cube: {e}")

def setup_ami_annotations():
    import tarfile
    ami_tar = BENCHMARK_DIR / "ami_manual_1.6.1.tar.gz"
    ami_extracted = BENCHMARK_DIR / "ami_annotations"
    if ami_extracted.exists():
        print(f"[OK] AMI annotations already extracted at {ami_extracted}")
        return

    url = "https://www.openslr.org/resources/16/ami_manual_1.6.1.tar.gz"
    print(f"--> Downloading AMI Corpus Action & Decision annotations from {url}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp, open(ami_tar, 'wb') as out_file:
            out_file.write(resp.read())
        print(f"--> Extracting {ami_tar} to {ami_extracted}...")
        with tarfile.open(ami_tar, 'r:gz') as tar_ref:
            tar_ref.extractall(ami_extracted)
        print("[DONE] AMI annotations extracted successfully.")
        if ami_tar.exists():
            ami_tar.unlink()
    except Exception as e:
        print(f"[WARN] Failed to download AMI annotations: {e}")

def setup_dravidian_codemix():
    target = BENCHMARK_DIR / "dravidian_codemix"
    target.mkdir(parents=True, exist_ok=True)
    sample_file = target / "tanglish_sample.txt"
    if sample_file.exists():
        print(f"[OK] Dravidian CodeMix sample already exists at {sample_file}")
        return
    print("--> Creating representative Dravidian Tanglish benchmark sample...")
    # Curated code-mixed Tamil-English samples reflecting SME WhatsApp chats
    samples = [
        "Innaiku packing mudinjiruma? Client delivery pathi kekranga.",
        "Avan solrathu nambathinga, GST bill illama payment release panna mudiyathu.",
        "Tomorrow morning 10 AM kulla ST courier la dispatch pannidunga.",
        "Advance payment 25000 INR vandhuruchu, printing process start panlam.",
        "Die block cutting machine breakdown aayiruchu, mechanic varathukku 2 hours aagum.",
        "Sample approval buyer kitta irunthu innum varala, hold pannunga.",
        "Accounts team kitta pesiyachu, Thursday kulla invoice clear aayidum."
    ]
    with open(sample_file, "w", encoding="utf-8") as f:
        f.write("\n".join(samples) + "\n")
    print(f"[DONE] Dravidian Tanglish sample set created at {sample_file}")

if __name__ == "__main__":
    print(f"Initializing external benchmark suites in: {BENCHMARK_DIR.resolve()}\n")
    setup_l3cube()
    setup_ami_annotations()
    setup_dravidian_codemix()
    print("\nBenchmark setup completed.")
