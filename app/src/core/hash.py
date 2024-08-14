"""
Module that handles the hashing of files.

Useful functions:
- compare_hash_from_path: Compare the hash of a file with a given hash code.
- get_hasher: Get the hash of a file, stored in a xxhash.xxh64 object.
- compare_hash: Compare the hash stored in the hasher object with the given hash code.
"""

import base64
from pathlib import Path

import xxhash

def get_hasher(file_path: Path) -> xxhash.xxh64:
    """
    Get the hash of a file, stored in a xxhash.xxh64 object.
    """
    assert isinstance(file_path, Path), f"file_name must be a Path, given {type(file_path)} instead"
    assert file_path != Path(), "file_path must not be empty"

    chunk_size: int = 256 * 1024
    hasher: xxhash.xxh64 = xxhash.xxh64()
    if file_path.is_file():
        with file_path.open('rb') as file:
            while chunk := file.read(chunk_size):
                hasher.update(chunk)
    return hasher

def compare_hash(hasher: xxhash.xxh64, hash_code: str) -> bool:
    """
    Compare the hash stored in the hasher object with the given hash code.
    """
    assert isinstance(hasher, xxhash.xxh64), f"hasher must be a xxhash.xxh64, given {type(hasher)} instead"
    assert isinstance(hash_code, str), f"hash_code must be a string, given {type(hash_code)} instead"
    assert hash_code != '', "hash_code must not be empty"

    big_endian_hash: bytes = hasher.digest()
    big_endian_int: int = int.from_bytes(big_endian_hash, byteorder='big')
    little_endian_hash: bytes = big_endian_int.to_bytes(len(big_endian_hash), 'little')
    base64_little_endian: str = base64.b64encode(little_endian_hash).decode('utf-8')
    return base64_little_endian == hash_code

def compare_hash_from_path(file_path: Path, hash_code: str) -> bool:
    """
    Compare the hash of a file with a given hash code.
    """
    assert isinstance(file_path, Path), f"file_path must be a Path, given {type(file_path)} instead"
    assert file_path != Path(), "file_path must not be empty"
    assert file_path.is_file(), f"file {file_path} does not exist"
    assert isinstance(hash_code, str), f"hash_code must be a string, given {type(hash_code)} instead"
    assert hash_code != '', "hash_code must not be empty"

    file_hasher: xxhash.xxh64 = get_hasher(file_path)
    return compare_hash(file_hasher, hash_code)
