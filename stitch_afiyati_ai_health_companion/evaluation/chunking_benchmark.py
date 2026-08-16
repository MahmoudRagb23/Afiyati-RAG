"""Chunking experiment entry point.

This benchmark intentionally refuses to produce numbers until official PDFs and
chunk/document-level relevance judgments are present. It lists the planned,
reproducible configurations so the same corpus and questions can be used after
data is supplied.
"""

CONFIGURATIONS = [
    {"strategy": "fixed", "child_tokens": 300, "overlap": 70},
    {"strategy": "fixed", "child_tokens": 450, "overlap": 70},
    {"strategy": "fixed", "child_tokens": 650, "overlap": 70},
    {"strategy": "fixed", "child_tokens": 800, "overlap": 70},
    {"strategy": "section_aware", "child_tokens": 450, "overlap": 70},
    {"strategy": "section_aware_parent_child", "child_tokens": 450, "parent_tokens": 850, "overlap": 70},
]

if __name__ == "__main__":
    print("AFIYATI CHUNKING BENCHMARK")
    for config in CONFIGURATIONS:
        print(config)
    print("NOT EVALUATED — DATA REQUIRED")

