import pytest
import os
import json
from pathlib import Path
from data.training_manifest import validate_dataset_tokenizer_pair

def test_validate_dataset_tokenizer_pair_no_manifest(tmp_path):
    # Setup a dummy dataset dir
    dataset_dir = tmp_path / "data" / "datasets" / "test_dataset"
    dataset_dir.mkdir(parents=True)
    
    # Create some dummy shards
    (dataset_dir / "fineweb_train_000001.bin").touch()
    
    # No manifest exists at tmp_path / "data" / "manifest.json"
    name, count, expected = validate_dataset_tokenizer_pair(str(dataset_dir), "tok.model")
    
    assert name == "test_dataset"
    assert count == 1
    assert expected is None

def test_validate_dataset_tokenizer_pair_mismatch(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    datasets_dir = data_dir / "datasets"
    datasets_dir.mkdir()
    dataset_dir = datasets_dir / "test_dataset"
    dataset_dir.mkdir()
    
    manifest_path = data_dir / "manifest.json"
    manifest_content = {
        "datasets": [
            {
                "name": "test_dataset",
                "tokenizer_name": "test_tokenizer",
                "stats": {"files_train": 2}
            }
        ],
        "tokenizers": [
            {
                "name": "test_tokenizer",
                "model_path": "correct_tokenizer.model"
            }
        ]
    }
    manifest_path.write_text(json.dumps(manifest_content))
    
    # Create 3 shards (manifest says 2)
    (dataset_dir / "fineweb_train_000001.bin").touch()
    (dataset_dir / "fineweb_train_000002.bin").touch()
    (dataset_dir / "fineweb_train_000003.bin").touch()
    
    # Mismatch in tokenizer name
    with pytest.raises(ValueError, match="expects tokenizer 'correct_tokenizer.model', got 'wrong.model'"):
        validate_dataset_tokenizer_pair(str(dataset_dir), "wrong.model")
        
    # Mismatch in shard count (using correct tokenizer name)
    with pytest.raises(ValueError, match="has more train shards than expected"):
        validate_dataset_tokenizer_pair(str(dataset_dir), "correct_tokenizer.model")

def test_validate_dataset_tokenizer_pair_success(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    datasets_dir = data_dir / "datasets"
    datasets_dir.mkdir()
    dataset_dir = datasets_dir / "test_dataset"
    dataset_dir.mkdir()
    
    manifest_path = data_dir / "manifest.json"
    manifest_content = {
        "datasets": [
            {
                "name": "test_dataset",
                "tokenizer_name": "test_tokenizer",
                "stats": {"files_train": 5}
            }
        ],
        "tokenizers": [
            {
                "name": "test_tokenizer",
                "model_path": "correct_tokenizer.model"
            }
        ]
    }
    manifest_path.write_text(json.dumps(manifest_content))
    
    # Create 2 shards (manifest says 5 is max)
    (dataset_dir / "fineweb_train_000001.bin").touch()
    (dataset_dir / "fineweb_train_000002.bin").touch()
    
    name, count, expected = validate_dataset_tokenizer_pair(str(dataset_dir), "path/to/correct_tokenizer.model")
    
    assert name == "test_dataset"
    assert count == 2
    assert expected == 5
