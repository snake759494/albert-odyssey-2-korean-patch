"""Apply Albert Odyssey 2 v0.6 with input, patch and output hash verification."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

SOURCE_SIZE = 2097152
SOURCE_MD5 = '17ee32db6de1524535d2f2e995380f70'
SOURCE_SHA = '7c6fe76fe1a414407435c7393f4d9b50a885fa6055cd9d94549725884497698b'
PATCH_SHA = '3603f4843c4d3d90ebf173a8577c6dc1ae561369dd02779075fe5b8d2b9001ef'
OUTPUT_SHA = '0b00d3e6dc2f20bb9602ad359a6ba44780cdacbe1a89b846ecf576eb84776ac5'

def digest(path, kind='sha256'):
    h = hashlib.new(kind)
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('xdelta', 'source', 'patch', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    source, patch, output, exe = (p.resolve() for p in (args.source, args.patch, args.output, args.xdelta))
    if output.exists() or output in (source, patch, exe):
        raise ValueError('Output must be a new file, different from all inputs.')
    if source.stat().st_size != SOURCE_SIZE or digest(source, 'md5') != SOURCE_MD5 or digest(source) != SOURCE_SHA:
        raise ValueError('Original ROM hash mismatch. Use the unmodified Japanese ROM listed in README.')
    if digest(patch) != PATCH_SHA:
        raise ValueError('Patch SHA-256 mismatch.')
    print('Input and patch verified. Applying...', flush=True)
    # Reserve a new file atomically. Stream decoded output into it, never overwrite an existing path.
    with output.open('xb') as out:
        subprocess.run([str(exe), '-d', '-c', '-s', str(source), str(patch)], stdout=out, check=True)
    if output.stat().st_size != 4194304 or digest(output) != OUTPUT_SHA:
        raise ValueError('Output verification failed. Do not use the resulting file.')
    print('PASS: output SHA-256 = ' + OUTPUT_SHA)

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
