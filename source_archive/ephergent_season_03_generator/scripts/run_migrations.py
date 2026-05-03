# Explanation: New migration runner that the deploy script expects. It creates the Flask app, runs MigrationService.migrate_all(),
# writes a JSON result file (path from MIGRATION_RESULT_FILE env or ./migration_result.json) with timestamps and exit code,
# and exits with 0 on full success, 2 on partial (some items already present), 1 on exception.

#!/usr/bin/env python3
"""Run file-based data migrations into the database.

This script is intended to be run by the deploy script as the application user
inside the project's virtualenv. It writes a JSON summary file and exits with
an appropriate exit code so automation can detect success/failure.

Exit codes:
 - 0 : success (everything migrated)
 - 2 : partial (some items skipped / already present) — migration ran but not everything migrated
 - 1 : error (exception raised)
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Ensure project root is importable when run from other working dirs
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ephergent_generator import create_app
from ephergent_generator.services.migration_service import MigrationService


def iso_now():
    return datetime.utcnow().isoformat() + "Z"


def main():
    start = iso_now()
    result = None
    error = None
    exit_code = 1

    # Default result file (can be overridden by MIGRATION_RESULT_FILE env var)
    result_file = os.environ.get('MIGRATION_RESULT_FILE', str(PROJECT_ROOT / 'migration_result.json'))

    # Determine config (respect FLASK_ENV if set)
    config_name = os.environ.get('FLASK_ENV', 'production')

    try:
        app = create_app(config_name)
        with app.app_context():
            # Run migration service
            result = MigrationService.migrate_all()

            overall_success = bool(result.get('overall_success', False))

            # Decide exit code: 0 full success, 2 partial/missing items, keep 1 for unexpected
            if overall_success:
                exit_code = 0
            else:
                # If the service returned results but overall_success is False, treat as partial (2)
                exit_code = 2

    except Exception as e:
        error = str(e)
        result = {'success': False, 'error': error}
        exit_code = 1

    finished = iso_now()

    out = {
        'started_at': start,
        'finished_at': finished,
        'success': (exit_code == 0),
        'exit_code': exit_code,
        'result': result,
    }

    try:
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"Wrote migration result to: {result_file}")
    except Exception as e:
        print(f"Failed to write migration result file {result_file}: {e}", file=sys.stderr)
        # If writing the file fails, ensure we still exit with the earlier code

    # Print a short summary to stdout for logs
    print(f"Migration finished. success={out['success']} exit_code={out['exit_code']}")

    # Exit with the appropriate code so the deploy scripts can detect success/failure
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

