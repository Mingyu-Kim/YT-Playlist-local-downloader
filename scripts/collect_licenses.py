"""Collect installed package notices while retaining paths and versions."""
import importlib.metadata as metadata
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / 'build/licenses'; out.mkdir(parents=True, exist_ok=True)
    inventory = []
    for dist in sorted(metadata.distributions(), key=lambda d:d.metadata['Name'].lower()):
        name = dist.metadata['Name']
        if name.lower() in ('pip','ruff','pytest','pluggy','iniconfig','pygments','imageio-ffmpeg'):continue
        inventory.append({'name':name, 'version':dist.version, 'license':dist.metadata.get('License-Expression') or dist.metadata.get('License', ''), 'project_urls':dist.metadata.get_all('Project-URL', [])})
        for entry in dist.files or []:
            path = Path(str(entry))
            if path.name.lower().startswith(('license', 'licence', 'copying', 'notice', 'authors')) and path.suffix.lower() not in ('.py','.pyc'):
                source = Path(dist.locate_file(entry))
                if not source.is_file():continue
                # Preserve the full package-relative location to avoid overwriting distinct notices.
                parts = [p for p in path.parts if p not in ('..', '/', '\\')]
                target = out / name / Path(*parts)
                target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
    if sys.platform == 'win32':
        shutil.copytree(ROOT/'licenses/native-windows',out/'native-windows',dirs_exist_ok=True)
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    if python_license.exists():shutil.copy2(python_license, out / 'PYTHON-LICENSE.txt')
    (ROOT / 'build/dependencies.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')


if __name__ == '__main__':main()
