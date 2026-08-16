"""Embedding comparison entry point with the required candidate list."""

MODELS = ["nomic-embed-text", "qwen3-embedding:0.6b", "bge-m3"]

if __name__ == "__main__":
    print("AFIYATI EMBEDDING BENCHMARK")
    for model in MODELS:
        print(f"- {model}")
    print("NOT EVALUATED — DATA REQUIRED")

