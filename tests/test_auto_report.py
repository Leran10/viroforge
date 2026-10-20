"""Tests for the auto-generated HTML diagnostic report."""

import json
from pathlib import Path

import pytest

from viroforge.cli.auto_report import generate_auto_report


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a minimal dataset directory with metadata and composition."""
    ds = tmp_path / "gut_10x"
    ds.mkdir()

    metadata_dir = ds / "metadata"
    metadata_dir.mkdir()
    fastq_dir = ds / "fastq"
    fastq_dir.mkdir()
    fasta_dir = ds / "fasta"
    fasta_dir.mkdir()

    metadata = {
        "metadata_version": "1.1",
        "generation_info": {
            "timestamp": "2026-09-21T12:00:00",
            "viroforge_version": "0.22.0",
            "random_seed": 42,
        },
        "collection": {
            "id": 1,
            "name": "Gut Virome - Adult Healthy",
            "description": "Western diet adult gut",
            "n_viral_genomes": 133,
            "n_contaminants": 66,
            "total_sequences": 199,
        },
        "configuration": {
            "coverage": 10,
            "read_length": 150,
            "insert_size": 350,
            "platform": "novaseq",
            "molecule_type": "dna",
            "vlp_protocol": "tangential_flow",
            "contamination_level": "realistic",
            "amplification": "linker",
            "dark_matter": {
                "dark_matter_fraction": 0.30,
                "dark_matter_genomes": 66,
                "known_viral_genomes": 133,
                "total_genomes": 199,
            },
        },
        "enrichment_stats": {
            "viral_fraction": 0.82,
            "contamination_fraction": 0.18,
            "n_viral_genomes": 133,
            "n_contaminants": 66,
            "viral_enrichment": {"mean_enrichment_factor": 4.2},
            "contamination_reduction": {
                "reduction_by_type": {
                    "host_dna": {"reduction_factor": 0.95},
                    "reagent_bacteria": {"reduction_factor": 0.90},
                }
            },
        },
        "amplification_stats": {
            "method": "linker",
            "gc_bias_range": "0.7-1.3",
        },
        "adapter_stats": {
            "emergent_adapter_rate": 0.03,
            "reads_readthrough": 450,
            "adapter_type": "truseq",
        },
        "low_complexity_stats": {
            "rate": 0.01,
            "reads_modified": 150,
            "artifact_counts": {"homopolymer": 80, "dinucleotide": 70},
        },
        "duplicate_stats": {
            "rate": 0.30,
            "duplicates_created": 4500,
        },
    }
    (metadata_dir / "gut_10x_metadata.json").write_text(
        json.dumps(metadata, indent=2)
    )

    comp_lines = [
        "genome_id\tgenome_name\tsequence_type\trelative_abundance\tgc_content",
        "GCF_001\tCrAssphage\tviral\t0.15\t0.30",
        "GCF_002\tBacteroides phage\tviral\t0.08\t0.42",
        "GCF_003\tLactobacillus phage\tviral\t0.05\t0.38",
    ]
    (metadata_dir / "gut_10x_composition.tsv").write_text("\n".join(comp_lines))

    (fastq_dir / "gut_10x_R1.fastq").write_text("@read1\nACGT\n+\nIIII\n")
    (fastq_dir / "gut_10x_R2.fastq").write_text("@read1\nACGT\n+\nIIII\n")
    (fasta_dir / "gut_10x.fasta").write_text(">GCF_001\nACGT\n")

    return ds


def test_report_generated(sample_dataset):
    report = generate_auto_report(sample_dataset)
    assert report is not None
    assert report.exists()
    assert report.name == "gut_10x_report.html"


def test_report_contains_key_sections(sample_dataset):
    report = generate_auto_report(sample_dataset)
    html = report.read_text()
    assert "ViroForge Dataset Report" in html
    assert "Generation Summary" in html
    assert "Genome Composition" in html
    assert "VLP Enrichment" in html
    assert "Artifact Injection" in html
    assert "Output Files" in html


def test_report_contains_metadata_values(sample_dataset):
    report = generate_auto_report(sample_dataset)
    html = report.read_text()
    assert "Gut Virome - Adult Healthy" in html
    assert "NOVASEQ" in html
    assert "10x" in html
    assert "0.22.0" in html
    assert "42" in html


def test_report_contains_composition(sample_dataset):
    report = generate_auto_report(sample_dataset)
    html = report.read_text()
    assert "CrAssphage" in html
    assert "15.0000%" in html


def test_report_contains_artifacts(sample_dataset):
    report = generate_auto_report(sample_dataset)
    html = report.read_text()
    assert "Adapter Read-Through" in html
    assert "Low-Complexity" in html
    assert "PCR Duplicates" in html


def test_report_contains_dark_matter(sample_dataset):
    report = generate_auto_report(sample_dataset)
    html = report.read_text()
    assert "Dark Matter" in html
    assert "66" in html


def test_report_contains_file_inventory(sample_dataset):
    report = generate_auto_report(sample_dataset)
    html = report.read_text()
    assert "gut_10x_R1.fastq" in html
    assert "gut_10x.fasta" in html


def test_report_self_contained(sample_dataset):
    """Report should not reference external CDNs."""
    report = generate_auto_report(sample_dataset)
    html = report.read_text()
    assert "cdn.jsdelivr.net" not in html
    assert "cdnjs.cloudflare.com" not in html


def test_report_returns_none_for_missing_metadata(tmp_path):
    ds = tmp_path / "empty_dataset"
    ds.mkdir()
    assert generate_auto_report(ds) is None


def test_report_html_escapes_special_chars(tmp_path):
    ds = tmp_path / "test_escape"
    ds.mkdir()
    md = ds / "metadata"
    md.mkdir()
    metadata = {
        "generation_info": {"timestamp": "2026-01-01", "viroforge_version": "0.22.0"},
        "collection": {
            "name": 'Test <script>alert("xss")</script>',
            "id": 99,
            "n_viral_genomes": 1,
            "n_contaminants": 0,
            "total_sequences": 1,
        },
        "configuration": {"platform": "novaseq"},
        "enrichment_stats": {},
    }
    (md / "test_escape_metadata.json").write_text(json.dumps(metadata))
    report = generate_auto_report(ds)
    html = report.read_text()
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
