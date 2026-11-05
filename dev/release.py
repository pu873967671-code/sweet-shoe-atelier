#!/usr/bin/env python3
"""Validate a staged CrazyGames upload before replacing the last good release."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'qa'))
from fitting_acceptance import validate_pair
# Keep unaccepted source cameras excluded; crystalsandal now has its own
# complete registered kit and current native/saved-flow acceptance.
UNRELEASED_STYLES = {'dorsay', 'flowersandal', 'wrapsandal'}
FITTING_SCENES = {'salon', 'mirror_lounge', 'car', 'vanity', 'balcony'}
FITTING_VIEWPORTS = {(800, 450), (390, 844), (1336, 790)}
FITTING_CROP = {'x': 0, 'y': 100, 'width': 610, 'height': 500}


def verify_archive(archive_path, root):
    """Bind the archive to current workspace bytes; never trust a stale PASS."""
    archive_path, root = Path(archive_path), Path(root).resolve()
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate release archive entries')
        for name in names:
            path = PurePosixPath(name)
            if (not path.parts or path.as_posix() != name or path.is_absolute() or '..' in path.parts or '\\' in name
                    or path.parts[0] not in {'index.html', 'style.css', 'js', 'assets'}
                    or any('candidate' in part.lower() for part in path.parts)
                    or any(style in name for style in UNRELEASED_STYLES)):
                raise ValueError('Forbidden release entry: ' + name)
            source = root.joinpath(*path.parts)
            if not source.is_file() or not source.resolve().is_relative_to(root):
                raise ValueError('Missing workspace release entry: ' + name)
            if archive.read(name) != source.read_bytes():
                raise ValueError('Stale staged release bytes: ' + name)
        if archive.testzip() is not None:
            raise ValueError('Release archive CRC failure')
    size = archive_path.stat().st_size
    if size >= 20 * 1024 * 1024:
        raise ValueError('Release exceeds the 20 MiB upload budget')
    return {'sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(),
            'files': len(names), 'bytes': size}


def create_evidence_directory(output, sha256):
    # Never overwrite evidence from an earlier accepted run of identical bytes.
    parent = Path(output).parent / 'release-evidence' / sha256
    parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix='run-', dir=parent))


def validate_acceptance(acceptance, binding, catalog):
    if acceptance.get('status') != 'PASS' or any(acceptance.get(key) for key in ['page_errors', 'asset_errors', 'console_errors']):
        raise ValueError('Isolated upload did not report a clean PASS')
    if any(acceptance.get('archive', {}).get(key) != value for key, value in binding.items()):
        raise ValueError('Isolated upload archive binding does not match the staged release')
    if acceptance.get('registry_audit', {}).get('styles') != catalog:
        raise ValueError('Isolated upload catalog does not match the workspace')
    validate_fitting_acceptance(acceptance)


def validate_fitting_acceptance(acceptance):
    """Require current extracted-upload framing evidence before publication."""
    audit = acceptance.get('fitting_audit')
    if not isinstance(audit, dict) or audit.get('version') != 1:
        raise ValueError('Missing current isolated fitting audit')
    if audit.get('crop') != FITTING_CROP:
        raise ValueError('Isolated fitting crop does not match the approved 610x500 camera')
    scenes, viewports = audit.get('scenes'), audit.get('viewports')
    if (not isinstance(scenes, list) or len(scenes) != len(FITTING_SCENES)
            or any(not isinstance(scene, str) for scene in scenes)
            or set(scenes) != FITTING_SCENES):
        raise ValueError('Isolated fitting audit must cover all five scenes exactly once')
    if (not isinstance(viewports, list) or len(viewports) != len(FITTING_VIEWPORTS)
            or any(not isinstance(viewport, list) or len(viewport) != 2
                   or any(type(value) is not int for value in viewport) for viewport in viewports)
            or {tuple(viewport) for viewport in viewports} != FITTING_VIEWPORTS):
        raise ValueError('Isolated fitting audit must cover compact, portrait and desktop viewports')
    fitting = acceptance.get('fitting')
    sock = fitting.get('sock') if isinstance(fitting, dict) else None
    if sock not in {'none', 'frill', 'lace', 'sheer', 'knee', 'thigh', 'blacksheer', 'pantyhose', 'opaque', 'fishnet'}:
        raise ValueError('Isolated fitting audit has no valid saved hosiery selection')
    sock_color = fitting.get('color')
    if sock_color not in {'pink', 'mint', 'cream', 'white', 'black'}:
        raise ValueError('Isolated fitting audit has no valid saved hosiery colour')
    cases, seen, scales, geometry = audit.get('cases'), set(), {}, {}
    expected = {(scene, viewport) for scene in FITTING_SCENES for viewport in FITTING_VIEWPORTS}
    if not isinstance(cases, list) or len(cases) != len(expected):
        raise ValueError('Isolated fitting audit needs every scene and viewport combination')
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError('Malformed isolated fitting case')
        viewport, scene = case.get('viewport'), case.get('scene')
        if (not isinstance(scene, str) or not isinstance(viewport, list) or len(viewport) != 2
                or any(type(value) is not int for value in viewport)):
            raise ValueError('Malformed isolated fitting scene or viewport')
        key = scene, tuple(viewport)
        if key not in expected or key in seen:
            raise ValueError('Duplicate or unexpected isolated fitting scene/viewport case')
        seen.add(key)
        if (type(case.get('feet')) is not int or case.get('feet') != 2 or case.get('fallback') is not False
                or type(case.get('platformCount')) is not int or case.get('platformCount') != 0 or case.get('zoomEnabled') is not False
                or case.get('backgroundDecoded') is not True or case.get('adjacent') is not True):
            raise ValueError('Isolated fitting case violates complete pair, baked backdrop, disabled zoom or dock adjacency')
        if case.get('sock') != sock or case.get('sockColor') != sock_color:
            raise ValueError('Isolated fitting case lost the saved hosiery selection')
        if (case.get('crop') != FITTING_CROP or case.get('fixedFraming') != '610x500'
                or case.get('platformBaked') != 'true' or case.get('sceneReady') is not True):
            raise ValueError('Isolated fitting case lost the approved cropped baked scene')
        validate_pair(case)
        scale = case.get('normalizedScale')
        if type(scale) not in (int, float) or not math.isfinite(scale) or scale <= 0:
            raise ValueError('Isolated fitting case has invalid normalized scale')
        scales.setdefault(scene, []).append(scale)
        normalized = case.get('normalizedGeometry')
        if (not isinstance(normalized, list) or len(normalized) != 6
                or any(type(value) not in (int, float) or not math.isfinite(value) for value in normalized)):
            raise ValueError('Isolated fitting case has invalid normalized pair/platform geometry')
        geometry.setdefault(scene, []).append(normalized)
    if seen != expected:
        raise ValueError('Isolated fitting scene/viewport coverage is incomplete')
    if any(max(values) / min(values) > 1.015 for values in scales.values()):
        raise ValueError('Isolated fitting resize changed the normalized feet scale')
    if any(max(values) - min(values) >= .003
           for scene_cases in geometry.values() for values in zip(*scene_cases)):
        raise ValueError('Isolated fitting resize changed normalized pair/platform geometry')
    share = acceptance.get('png_share')
    if not isinstance(share, dict) or share.get('size') != [1220, 1000] or share.get('opaque') is not True:
        raise ValueError('Isolated fitting needs an opaque 1220x1000 cropped PNG share')
    resize = acceptance.get('resize_roundtrip')
    if (not isinstance(resize, dict) or resize.get('from') != [390, 844]
            or resize.get('to') != [1336, 790]):
        raise ValueError('Isolated fitting needs a portrait/desktop resize roundtrip')
    delta = resize.get('maximumNormalizedDelta')
    if type(delta) not in (int, float) or not math.isfinite(delta) or not 0 <= delta < .003:
        raise ValueError('Isolated fitting resize roundtrip changed the approved composition')


def _prepared_file(destination, data):
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='.' + destination.name + '.', dir=destination.parent)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return Path(name)


def publish_release(staged, output, report_path, report, root=ROOT):
    """Publish only after final verification; restore both outputs on write failure."""
    output, report_path = Path(output).resolve(), Path(report_path).resolve()
    if output == report_path:
        raise ValueError('ZIP and release report must have different paths')
    binding = verify_archive(staged, root)
    settled = dict(report, status='PASS', archive=str(output), **binding)
    destinations = [(output, Path(staged).read_bytes()),
                    (report_path, (json.dumps(settled, indent=2) + '\n').encode())]
    pending, backups, replaced = {}, {}, []
    try:
        for path, data in destinations:
            pending[path] = _prepared_file(path, data)
            backups[path] = _prepared_file(path, path.read_bytes()) if path.exists() else None
        for path, _ in destinations:
            os.replace(pending[path], path)
            replaced.append(path)
    except BaseException:
        for path in reversed(replaced):
            if backups[path] is None:
                path.unlink(missing_ok=True)
            else:
                os.replace(backups[path], path)
        raise
    finally:
        for path in [*pending.values(), *(p for p in backups.values() if p is not None)]:
            path.unlink(missing_ok=True)
    return settled


def run_step(name, command, root, steps):
    print('Checking ' + name + '…', flush=True)
    result = subprocess.run(command, cwd=root, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(name + ' failed:\n' + (result.stdout + result.stderr)[-6000:])
    steps.append({'name': name, 'status': 'PASS', 'output': result.stdout.strip()[-2000:]})


def run_release(output, report_path, root=ROOT):
    root, output, report_path = Path(root).resolve(), Path(output).resolve(), Path(report_path).resolve()
    if output == report_path:
        raise ValueError('ZIP and release report must have different paths')
    output.parent.mkdir(parents=True, exist_ok=True)
    steps = []
    with tempfile.TemporaryDirectory(prefix='.atelier-release-', dir=output.parent) as directory:
        temporary = Path(directory)
        staged = temporary / 'upload.zip'
        run_step('staged package', [sys.executable, 'dev/package.py', '--output', str(staged)], root, steps)
        scripts = sorted(path for path in root.rglob('*.js')
                         if 'dist' not in path.relative_to(root).parts and '.git' not in path.relative_to(root).parts)
        for script in scripts:
            result = subprocess.run(['node', '--check', str(script)], cwd=root, text=True, capture_output=True)
            if result.returncode:
                raise RuntimeError('JavaScript syntax failed: ' + str(script.relative_to(root)) + '\n' + result.stderr)
        steps.append({'name': 'all JavaScript syntax', 'status': 'PASS', 'files': len(scripts)})
        for name, command in [
            ('smoke', ['node', 'smoke-test.js']),
            ('startup', ['node', 'qa/startup-test.js']),
            ('audio', ['node', 'qa/audio-test.js']),
            ('pacing', ['node', 'qa/pacing-test.js']),
            ('cloud startup/save recovery', [sys.executable, 'qa/cloud-startup.py']),
            ('release rejection/recovery', [sys.executable, 'qa/release-test.py']),
            ('package rejection/recovery', [sys.executable, 'qa/package-test.py']),
        ]:
            run_step(name, command, root, steps)
        staged_binding = verify_archive(staged, root)
        evidence = create_evidence_directory(output, staged_binding['sha256'])
        run_step('isolated upload', [sys.executable, 'qa/upload-test.py', '--zip', str(staged),
                                    '--sock', 'knee', '--sock-color', 'white',
                                    '--report-dir', str(evidence)], root, steps)
        acceptance = json.loads((evidence / 'report.json').read_text())
        binding = verify_archive(staged, root)
        catalog = json.loads(subprocess.check_output(
            ['node', '-e', "console.log(JSON.stringify(require('./game.js').opts.heel.map(([id])=>id)))"],
            cwd=root, text=True))
        validate_acceptance(acceptance, binding, catalog)
        report = {'created_utc': datetime.now(timezone.utc).isoformat(),
                  'catalog_ids': catalog, 'steps': steps, 'upload_acceptance': acceptance,
                  'evidence_directory': str(evidence)}
        settled = publish_release(staged, output, report_path, report, root)
    print(f"PASS: {settled['files']} files, {settled['bytes'] / 1024 / 1024:.2f} MiB; SHA256 {settled['sha256']}")
    print('Release: ' + str(output))
    print('Evidence: ' + str(report_path))
    return settled


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/sweet-shoe-atelier-crazygames.zip')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        run_release(args.output, args.report or args.output.parent / 'release-report.json')
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, subprocess.SubprocessError) as error:
        parser.exit(1, 'Release rejected; last good ZIP/report preserved.\n' + str(error) + '\n')


if __name__ == '__main__':
    main()
