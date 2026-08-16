from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

from app.core.config import Settings


KNOWN_CONDITIONS = {
    "hypertension",
    "type2_diabetes",
    "type_2_diabetes",
    "chronic_kidney_disease",
    "asthma",
    "cardiovascular",
    "obesity",
    "shared",
}
KNOWN_ORGANIZATIONS = {"nice", "who", "kdigo", "gina", "other_official"}
REQUIRED_METADATA = {
    "file",
    "condition",
    "organization",
    "guideline_id",
    "title",
    "publication_year",
    "version",
    "language",
    "source_type",
    "status",
    "source_url",
    "sha256",
}


def validate(root: Path) -> dict:
    root = root.resolve()
    manifest_path = root / "manifest.json"
    errors: list[str] = []
    warnings: list[str] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
        if not isinstance(manifest, list):
            raise ValueError("manifest root must be a JSON list")
    except (json.JSONDecodeError, ValueError) as exc:
        manifest = []
        errors.append(f"Invalid manifest: {exc}")

    pdfs = sorted(path for path in root.rglob("*.pdf") if path.is_file())
    actual = {path.relative_to(root).as_posix(): path for path in pdfs}
    entries = {str(item.get("file", "")).replace("\\", "/"): item for item in manifest if item.get("file")}
    missing_entries = sorted(set(actual) - set(entries))
    missing_files = sorted(set(entries) - set(actual))
    for value in missing_entries:
        errors.append(f"PDF missing manifest entry: {value}")
    for value in missing_files:
        errors.append(f"Manifest entry missing file: {value}")

    name_counts = Counter(path.name.lower() for path in pdfs)
    duplicate_filenames = sorted(name for name, count in name_counts.items() if count > 1)
    id_counts = Counter(str(item.get("guideline_id")) for item in manifest if item.get("guideline_id"))
    duplicate_ids = sorted(value for value, count in id_counts.items() if count > 1)
    for name in duplicate_filenames:
        errors.append(f"Duplicate filename: {name}")
    for guideline_id in duplicate_ids:
        errors.append(f"Duplicate guideline ID: {guideline_id}")

    unknown_diseases: set[str] = set()
    unknown_organizations: set[str] = set()
    for relative in actual:
        parts = relative.split("/")
        if parts and parts[0] not in KNOWN_CONDITIONS:
            unknown_diseases.add(parts[0])
        if len(parts) > 1 and parts[1] not in KNOWN_ORGANIZATIONS and parts[0] != "shared":
            unknown_organizations.add(parts[1])
    for item in manifest:
        relative = str(item.get("file", "<unknown>"))
        organization = str(item.get("organization", "")).lower()
        if organization and organization not in KNOWN_ORGANIZATIONS:
            unknown_organizations.add(organization)
        condition = item.get("condition")
        conditions = [condition] if isinstance(condition, str) else condition or []
        for value in conditions:
            if value not in KNOWN_CONDITIONS:
                unknown_diseases.add(str(value))
        missing = sorted(key for key in REQUIRED_METADATA if not item.get(key))
        if missing:
            errors.append(f"Missing required metadata ({', '.join(missing)}): {relative}")
        if item.get("status") not in {"current", "archive"}:
            errors.append(f"Invalid status '{item.get('status')}': {relative}")
        if item.get("source_type") != "clinical_guideline":
            errors.append(f"Invalid source_type '{item.get('source_type')}': {relative}")

    by_id: dict[str, set[str]] = {}
    for item in manifest:
        guideline_id = item.get("guideline_id")
        if guideline_id:
            by_id.setdefault(str(guideline_id), set()).add(str(item.get("status", "current")))
    conflicts = sorted(key for key, statuses in by_id.items() if "current" in statuses and "archive" in statuses)
    for key in conflicts:
        errors.append(f"Current/archive conflict: {key}")

    empty_pdfs: list[str] = []
    parsing_failures: list[str] = []
    checksum_failures: list[str] = []
    for relative, path in actual.items():
        if path.stat().st_size == 0:
            empty_pdfs.append(relative)
            errors.append(f"Empty PDF: {relative}")
            continue
        try:
            reader = PdfReader(path)
            if not reader.pages:
                empty_pdfs.append(relative)
                errors.append(f"PDF has no pages: {relative}")
        except Exception as exc:
            parsing_failures.append(relative)
            errors.append(f"Parsing failure: {relative}: {exc}")
            continue
        expected_hash = str(entries.get(relative, {}).get("sha256", "")).lower()
        if expected_hash:
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                checksum_failures.append(relative)
                errors.append(f"SHA-256 mismatch: {relative}")

    return {
        "valid": not errors,
        "pdfs_found": len(pdfs),
        "missing_manifest_entries": missing_entries,
        "manifest_entries_missing_files": missing_files,
        "duplicate_filenames": duplicate_filenames,
        "duplicate_guideline_ids": duplicate_ids,
        "unknown_disease_folders": sorted(unknown_diseases),
        "unknown_organizations": sorted(unknown_organizations),
        "missing_versions": sum(1 for item in manifest if not item.get("version")),
        "missing_publication_years": sum(1 for item in manifest if not item.get("publication_year")),
        "current_archive_conflicts": conflicts,
        "empty_pdfs": empty_pdfs,
        "parsing_failures": parsing_failures,
        "checksum_failures": checksum_failures,
        "errors": errors,
        "warnings": warnings,
    }


def print_report(report: dict) -> None:
    print("AFIYATI GUIDELINE VALIDATION")
    print("=" * 31)
    print(f"PDFs found: {report['pdfs_found']}")
    print(f"PDFs missing manifest entries: {len(report['missing_manifest_entries'])}")
    print(f"Manifest entries missing files: {len(report['manifest_entries_missing_files'])}")
    print(f"Duplicate filenames: {len(report['duplicate_filenames'])}")
    print(f"Duplicate guideline IDs: {len(report['duplicate_guideline_ids'])}")
    print(f"Unknown disease folders: {len(report['unknown_disease_folders'])}")
    print(f"Unknown organizations: {len(report['unknown_organizations'])}")
    print(f"Missing versions: {report['missing_versions']}")
    print(f"Missing publication years: {report['missing_publication_years']}")
    print(f"Current/archive conflicts: {len(report['current_archive_conflicts'])}")
    print(f"Empty PDFs: {len(report['empty_pdfs'])}")
    print(f"Parsing failures: {len(report['parsing_failures'])}")
    print(f"Checksum failures: {len(report['checksum_failures'])}")
    if report["errors"]:
        print("\nERRORS")
        for error in report["errors"]:
            print(f"- {error}")
    if report["warnings"]:
        print("\nWARNINGS")
        for warning in report["warnings"]:
            print(f"- {warning}")
    print(f"\nResult: {'VALID' if report['valid'] else 'INVALID — ingestion blocked'}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Afiyati clinical guideline files")
    parser.add_argument("--path", type=Path, default=Settings.from_env().data_dir / "guidelines")
    args = parser.parse_args()
    report = validate(args.path)
    print_report(report)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
