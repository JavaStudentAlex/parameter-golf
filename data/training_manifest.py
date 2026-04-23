import json
from pathlib import Path

def validate_dataset_tokenizer_pair(data_path: str, tokenizer_path: str) -> tuple[str, int, int | None]:
    """
    Validates that the dataset shards and tokenizer match the manifest.
    Both CUDA and MLX trainers use this to fail fast on mismatches.
    """
    dataset_dir = Path(data_path).resolve()
    # Shards are named fineweb_train_*.bin
    actual_train_files = len(list(dataset_dir.glob("fineweb_train_*.bin")))
    
    # Manifest is expected at data/manifest.json, which is 1 level above datasets/NAME
    # or dataset_dir.parents[1] if datasets/NAME is used.
    # The common case in this repo is data/datasets/NAME/fineweb_train_*.bin
    # so manifest is at dataset_dir.parents[1] ("data/manifest.json")
    if len(dataset_dir.parents) < 2:
        return dataset_dir.name, actual_train_files, None
        
    manifest_path = dataset_dir.parents[1] / "manifest.json"
    if not manifest_path.is_file():
        # Fallback to local data/manifest.json if relative path didn't work
        manifest_path = Path("data/manifest.json").resolve()
        if not manifest_path.is_file():
            return dataset_dir.name, actual_train_files, None

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dataset_dir.name, actual_train_files, None

    dataset_entry = next((x for x in manifest.get("datasets", []) if x.get("name") == dataset_dir.name), None)
    if dataset_entry is None:
        return dataset_dir.name, actual_train_files, None

    tokenizer_name = dataset_entry.get("tokenizer_name")
    tokenizer_entry = (
        next((x for x in manifest.get("tokenizers", []) if x.get("name") == tokenizer_name), None)
        if tokenizer_name
        else None
    )
    
    # Check tokenizer name match
    expected_name = Path((tokenizer_entry or {}).get("model_path") or (tokenizer_entry or {}).get("path") or "").name
    if expected_name and Path(tokenizer_path).name != expected_name:
        raise ValueError(f"Dataset '{dataset_dir.name}' expects tokenizer '{expected_name}', got '{Path(tokenizer_path).name}'")
    
    # Check shard count
    expected_train_files = (dataset_entry.get("stats") or {}).get("files_train")
    if expected_train_files is not None:
        expected_train_files = int(expected_train_files)
        if actual_train_files > expected_train_files:
            raise ValueError(
                f"Dataset '{dataset_dir.name}' has more train shards than expected: found {actual_train_files}, "
                f"manifest says {expected_train_files}"
            )
            
    return dataset_dir.name, actual_train_files, expected_train_files
