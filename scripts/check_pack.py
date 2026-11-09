#!/usr/bin/env python3
"""Check the handoff inventory and local links; this does not validate experiments."""
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit


def main():
    root = Path(__file__).resolve().parents[1]
    errors = []
    readings = json.loads((root / 'research/readings.json').read_text())
    recordings = json.loads((root / 'research/recordings.json').read_text())
    expected = {'General': 6, 'Track 1': 6, 'Track 2': 5, 'Track 3': 7, 'Track 4': 8}
    if Counter(row['group'] for row in readings) != expected:
        errors.append('Reading group counts do not match all 32 event readings.')
    if len({r['event_url'] for r in readings}) != 32:
        errors.append('Missing or duplicate suggested-reading URLs.')
    if len(recordings) != 11 or len({r['url'] for r in recordings}) != 11:
        errors.append('Missing or duplicate recording URLs.')
    if sum(r['duration_seconds'] for r in recordings) != 31749:
        errors.append('Recording durations do not match the retrieved metadata.')
    for row in recordings:
        if not row['transcript_retrieved'] or not re.fullmatch(r'[0-9a-f]{64}', row['transcript_sha256']):
            errors.append(f"Missing transcript provenance: {row['id']}")
    for row in readings:
        for key in ['summary', 'caution', 'access', 'project_implication']:
            if not row.get(key):
                errors.append(f"Missing {key} for {row['id']}")
    required = ['README.md', 'CLAUDE.md', 'CLAUDE_HANDOFF.md', 'AGENTS.md',
                'docs/PROJECT_PLAN.md', 'docs/IMPLEMENTATION_SPEC.md',
                'docs/EVENT_BRIEF.md', 'docs/ADAPTION_SETUP.md',
                'docs/READING_GUIDE.md', 'docs/RECORDINGS.md',
                'docs/RELATED_WORK.md', 'docs/RESEARCH_COVERAGE.md',
                'docs/SUBMISSION_CHECKLIST.md', 'report/REPORT_OUTLINE.md']
    for name in required:
        if not (root / name).is_file():
            errors.append(f'Missing deliverable: {name}')
    for path in root.rglob('*.md'):
        if any(part in {'.venv', '.git', 'node_modules'} for part in path.relative_to(root).parts):
            continue
        if '.git' in path.parts:
            continue
        text = path.read_text()
        for destination in re.findall(r'\]\(([^\s)]+)\)', text):
            parsed = urlsplit(destination)
            if parsed.scheme or destination.startswith('#'):
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.exists():
                errors.append(f'Broken local link in {path.relative_to(root)}: {destination}')
        if '/Users/' in text or 'X-Amz-Signature=' in text:
            errors.append(f'Local path or signed URL in public prose: {path.relative_to(root)}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print('PASS: 32 readings, 11 recordings (8:49:09), provenance, required documents and local links.')
    print('Scope: preparation-pack validation only. No experiment results or final report are validated.')


if __name__ == '__main__':
    main()
