import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider"]
)
# 0 = all tests passed = mutant survived.
# Anything else, including import/collection errors (exit code 4), = killed.
sys.exit(0 if result.returncode == 0 else 1)