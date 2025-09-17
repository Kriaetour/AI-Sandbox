# fix_lint.py
import argparse
import subprocess
import sys
from pathlib import Path


def run_fixer(target_path: Path) -> None:
    """
    Runs the ruff linter/fixer on a given file or directory.

    Args:
        target_path: A Path object for the file or directory to fix.
    """
    if not target_path.exists():
        print(f"Error: Path '{target_path}' does not exist.", file=sys.stderr)
        return

    # The command to run.
    # '--fix' tells ruff to automatically fix any fixable errors.
    # '--exit-zero' ensures the command exits successfully even if there are unfixable errors.
    command = ["ruff", "check", str(target_path), "--fix", "--exit-zero"]

    try:
        print(f"🔍 Running linter/fixer on: {target_path}...")

        # Execute the command
        subprocess.run(command, check=True, capture_output=True, text=True)

        # Ruff is quiet if no changes are made. We'll print a confirmation.
        print(f"✅ Finished processing: {target_path}")

        # You can uncomment the line below to see ruff's detailed output
        # if result.stdout:
        #     print(result.stdout)

    except FileNotFoundError:
        print(
            "Error: 'ruff' command not found.",
            "Please ensure it is installed by running: pip install ruff",
            file=sys.stderr,
        )
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ An error occurred while processing {target_path}:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)


def main() -> None:
    """Main function to parse arguments and initiate the fixing process."""
    parser = argparse.ArgumentParser(
        description="A script to automatically fix common Python linter errors using 'ruff'."
    )
    parser.add_argument("paths", nargs="+", help="One or more file or directory paths to process.")
    args = parser.parse_args()

    for path_str in args.paths:
        path = Path(path_str)
        run_fixer(path)


if __name__ == "__main__":
    main()
