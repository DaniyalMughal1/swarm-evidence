#!/usr/bin/env python3
"""Retrieve public caption tracks listed in the research manifest, without video."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=Path('work/recordings'))
    parser.add_argument('--list-only', action='store_true', help='List links without downloading.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    recordings = json.loads((root / 'research/recordings.json').read_text())
    if args.list_only:
        for recording in recordings:
            print(f"{recording['id']} {recording['url']}")
        return
    executable = shutil.which('yt-dlp')
    if not executable:
        parser.error('Install yt-dlp before fetching public captions; no downloads performed.')
    args.destination.mkdir(parents=True, exist_ok=True)
    failures = []
    for recording in recordings:
        print(f"Fetching captions for {recording['id']}: {recording['title']}", flush=True)
        result = subprocess.run([
            executable, '--skip-download', '--no-simulate', '--write-subs',
            '--sub-langs', 'transcript', '--socket-timeout', '20', '--retries', '1',
            '--output', str(args.destination / f"{recording['id']}-%(title)s.%(ext)s"),
            recording['url'],
        ], check=False)
        found = list(args.destination.glob(f"{recording['id']}-*.vtt"))
        if result.returncode or not found:
            failures.append(recording['id'])
    if failures:
        raise SystemExit('Caption retrieval incomplete for: ' + ', '.join(failures))
    print('All 11 caption tracks available. Keep downloaded transcripts out of Git.')


if __name__ == '__main__':
    main()
