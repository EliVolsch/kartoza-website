#!/usr/bin/env python3
"""
Update all stats (Docker Hub and QGIS plugins) in Hugo content files.

This is a convenience wrapper that runs both update scripts.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run all stat update scripts."""
    import argparse

    parser = argparse.ArgumentParser(description='Update all stats in Hugo content')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would be updated without making changes')
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    dry_run_flag = ['--dry-run'] if args.dry_run else []

    print("=" * 70)
    print("UPDATING ALL STATS")
    print("=" * 70)

    # Docker stats
    docker_script = script_dir / 'update-docker-stats.py'
    subprocess.run([sys.executable, str(docker_script)] + dry_run_flag, cwd=script_dir.parent)

    print()

    # Plugin stats
    plugin_script = script_dir / 'update-plugin-stats.py'
    subprocess.run([sys.executable, str(plugin_script)] + dry_run_flag, cwd=script_dir.parent)

    print("\n" + "=" * 70)
    print("ALL STATS COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
