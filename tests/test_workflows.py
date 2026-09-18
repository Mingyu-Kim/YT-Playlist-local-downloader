"""Keep repository automation within the explicitly free-only runner policy."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def test_hosted_jobs_are_public_only_and_standard():
    allowed={'ubuntu-latest','windows-2022','macos-15','macos-15-intel'}
    for path in (ROOT/'.github/workflows').glob('*.yml'):
        text=path.read_text(encoding='utf-8')
        jobs=text.split('\njobs:\n',1)[1]
        for job in re.split(r'(?m)^  [a-zA-Z_][\w-]*:\n',jobs)[1:]:
            if 'runs-on:' in job or 'uses: ./.github/workflows/' in job:
                assert 'github.event.repository.private == false' in job,path
            for runner in re.findall(r'^    runs-on: (.+)$',job,re.M):
                assert runner in allowed or runner=='${{ matrix.os }}',path
            for runner in re.findall(r'^          - os: (.+)$',job,re.M):
                assert runner in allowed,path
        assert 'actions/upload-artifact@' not in text,path
        assert 'actions/cache@' not in text,path


def test_release_uploads_directly_and_stays_draft():
    native=(ROOT/'.github/workflows/native-build.yml').read_text()
    release=(ROOT/'.github/workflows/release.yml').read_text()
    assert 'gh release upload' in native
    assert 'gh release create' in release and '--draft --verify-tag' in release
    assert 'needs: build' in release and '.zip -sources.zip .sha256' in release
    assert 'permissions:\n  contents: read' not in native  # Caller controls read/write scope.
