"""Durable CSV checkpoints and fail-closed protocol fingerprints."""
import hashlib
import json
from pathlib import Path


def atomic_csv(frame, path):
    """Replace a checkpoint only after serialization has completed successfully."""
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    try:
        frame.to_csv(temp, index=False)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def ensure_protocol(result_path, protocol, resume):
    """Bind existing checkpoint rows to the protocol that originally produced them."""
    result_path = Path(result_path)
    manifest = result_path.with_suffix('.protocol.json')
    if resume and result_path.exists() and not manifest.exists():
        raise ValueError('checkpoint has no protocol fingerprint; use a new output directory or tag')
    if manifest.exists() and json.loads(manifest.read_text()) != protocol:
        raise ValueError('checkpoint inputs/protocol changed; use a new output directory or tag')
    temp = manifest.with_suffix('.json.tmp')
    try:
        temp.write_text(json.dumps(protocol, indent=2), encoding='utf-8')
        temp.replace(manifest)
    finally:
        temp.unlink(missing_ok=True)
