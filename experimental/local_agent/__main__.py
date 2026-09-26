"""Entry point: ``python -m local_agent`` (with ``experimental`` on PYTHONPATH)."""

import sys

from local_agent import cli

sys.exit(cli.main())
