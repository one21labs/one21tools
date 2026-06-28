#!/usr/bin/env python3
"""
Skill Packaging Script

Creates .skill ZIP file for upload to Claude.ai.
Validates skill before packaging - will not package invalid skills.

Usage:
    python package.py <skill-folder> [output-directory]
    python package.py /path/to/my-skill ./dist

Output:
    Creates <skill-name>.skill in output directory (default: current dir)

Upload:
    Claude.ai > Settings > Capabilities > Skills > Upload
"""
import sys
import argparse
import zipfile
from pathlib import Path
from validate import validate_skill

EXCLUDE = ['__pycache__', '.pyc', '.git', '.DS_Store', '.pytest_cache', 'tests']


def main():
    parser = argparse.ArgumentParser(description="Package skill into .skill file")
    parser.add_argument("skill_folder", type=Path)
    parser.add_argument("output_directory", type=Path, nargs='?', default=Path('.'))
    args = parser.parse_args()
    
    skill_path = args.skill_folder.resolve()
    output_dir = args.output_directory.resolve()
    
    # Validate first
    result = validate_skill(skill_path)
    if not result.valid:
        print(f"[FAIL] {result.error}")
        return 1

    # Package
    skill_name = skill_path.name
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{skill_name}.skill"

    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fp in skill_path.rglob('*'):
            if fp.is_file() and not any(p in str(fp) for p in EXCLUDE):
                arcname = f"{skill_name}/{fp.relative_to(skill_path)}"
                zf.write(fp, arcname)

    print(f"[OK] {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
