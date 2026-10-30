"""Verify immutable study sources plus explicit per-source amendment chains."""
import hashlib
import json
from pathlib import Path
import re


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def relative_path(value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('Source path must be relative and contained: ' + str(value))
    return path


def verify_sources(workspace, project, run, required_project_sources=()):
    workspace, project, run = Path(workspace), Path(project), Path(run)
    expected = {('workspace', str(relative_path(path))): digest
                for path, digest in json.loads((run / 'source_manifest.json').read_text())['sources'].items()}
    amendments_path = run / 'source_amendments.json'
    if amendments_path.exists():
        document = json.loads(amendments_path.read_text())
        if document.get('version') != 1:
            raise ValueError('Unsupported source amendments version')
        for amendment in document['amendments']:
            scope = amendment['scope']; path = str(relative_path(amendment['path']))
            if scope not in ('workspace', 'project') or not amendment.get('reason', '').strip():
                raise ValueError('Source amendment requires scope and reason')
            new = amendment['new_sha256']
            if not isinstance(new, str) or not re.fullmatch('[a-f0-9]{64}', new):
                raise ValueError('Invalid amendment digest: ' + path)
            key = (scope, path)
            if amendment['old_sha256'] != expected.get(key):
                raise ValueError('Broken source amendment chain: ' + scope + '/' + path)
            expected[key] = new
    for path in required_project_sources:
        if ('project', str(relative_path(path))) not in expected:
            raise RuntimeError('Operational source missing from amendments: ' + str(path))
    for (scope, path), digest in expected.items():
        source = (workspace if scope == 'workspace' else project) / path
        if not source.is_file() or sha256(source) != digest:
            raise RuntimeError('Source changed: ' + scope + '/' + path)
        if scope == 'project':
            snapshot = run / 'operations/project' / path
            if not snapshot.is_file() or sha256(snapshot) != digest:
                raise RuntimeError('Operational snapshot missing or changed: ' + path)
    return expected
