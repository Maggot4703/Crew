import argparse
import logging
import os
import sys


def create_cli_parser():
    parser = argparse.ArgumentParser(description="Crew CLI")
    subparsers = parser.add_subparsers(dest="command")

    # deepseek-code
    parser_deepseek = subparsers.add_parser(
        "deepseek-code", help="Run DeepSeek code query"
    )
    parser_deepseek.add_argument(
        "--prompt", type=str, required=True, help="Prompt for DeepSeek code query"
    )

    # read-csv
    parser_csv = subparsers.add_parser("read-csv", help="Read a CSV file")
    parser_csv.add_argument(
        "--csv-path", type=str, required=True, help="Path to CSV file"
    )

    # read-excel
    parser_excel = subparsers.add_parser("read-excel", help="Read an Excel file")
    parser_excel.add_argument(
        "--excel-path", type=str, required=True, help="Path to Excel file"
    )
    parser_excel.add_argument(
        "--sheet", type=str, default=None, help="Sheet name or index (optional)"
    )

    # crop-csv
    parser_crop = subparsers.add_parser(
        "crop-csv", help="Crop images using CSV annotations"
    )
    parser_crop.add_argument(
        "--image-path", type=str, required=True, help="Path to image file"
    )
    parser_crop.add_argument(
        "--annotations-csv", type=str, required=True, help="Path to annotations CSV"
    )
    parser_crop.add_argument(
        "--output-dir", type=str, required=True, help="Output directory for crops"
    )
    parser_crop.add_argument(
        "--output-format", type=str, default=None, help="Output image format (optional)"
    )
    parser_crop.add_argument(
        "--quality", type=int, default=95, help="Image quality (default: 95)"
    )

    return parser


# DeepSeek integration
try:
    from deepseek_integration import deepseek_code_query
except ImportError:
    from .deepseek_integration import deepseek_code_query

from file_utils import read_csv_builtin, read_csv_pandas, read_excel
from utils import crop_from_annotations, process_csv_data, process_excel_data

# Command registry for CLI handlers
COMMAND_REGISTRY = {}


def cli_command(name):
    def decorator(func):
        COMMAND_REGISTRY[name] = func
        return func

    return decorator


def run_cli(args: argparse.Namespace) -> int:
    logger = logging.getLogger("cli")
    file_handler = logging.FileHandler("crew_app.log", mode="a")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    handler = COMMAND_REGISTRY.get(args.command)
    if handler:
        return handler(args, logger)
    logger.error(f"Unknown command: {args.command}")
    print(f"[ERROR] Unknown command: {args.command}", file=sys.stderr)
    return 1


# CLI command handlers
@cli_command("deepseek-code")
def handle_deepseek_code(args, logger):
    logger.info(f"Running deepseek-code with prompt: {args.prompt}")
    result = deepseek_code_query(args.prompt)
    print(result)
    return 0


@cli_command("read-csv")
def handle_read_csv(args, logger):
    logger.info(f"Running read-csv with path: {args.csv_path}")
    if not os.path.isfile(args.csv_path):
        logger.error(f"CSV file not found: {args.csv_path}")
        print(f"[ERROR] CSV file not found: {args.csv_path}", file=sys.stderr)
        return 1
    try:
        process_csv_data(args.csv_path)
    except FileNotFoundError:
        logger.error(f"File not found: {args.csv_path}")
        print(f"[ERROR] File not found: {args.csv_path}", file=sys.stderr)
        return 1
    except PermissionError:
        logger.error(f"Permission denied: {args.csv_path}")
        print(f"[ERROR] Permission denied: {args.csv_path}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        print(f"[ERROR] Failed to read CSV: {e}", file=sys.stderr)
        return 1
    logger.info(f"Successfully read CSV: {args.csv_path}")
    return 0


@cli_command("read-excel")
def handle_read_excel(args, logger):
    logger.info(f"Running read-excel with path: {args.excel_path}")
    if not os.path.isfile(args.excel_path):
        logger.error(f"Excel file not found: {args.excel_path}")
        print(f"[ERROR] Excel file not found: {args.excel_path}", file=sys.stderr)
        return 1
    try:
        process_excel_data(args.excel_path, sheet_name=args.sheet)
    except FileNotFoundError:
        logger.error(f"File not found: {args.excel_path}")
        print(f"[ERROR] File not found: {args.excel_path}", file=sys.stderr)
        return 1
    except PermissionError:
        logger.error(f"Permission denied: {args.excel_path}")
        print(f"[ERROR] Permission denied: {args.excel_path}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Failed to read Excel: {e}")
        print(f"[ERROR] Failed to read Excel: {e}", file=sys.stderr)
        return 1
    logger.info(f"Successfully read Excel: {args.excel_path}")
    return 0


@cli_command("crop-csv")
def handle_crop_csv(args, logger):
    logger.info(
        f"Running crop-csv with image: {args.image_path}, annotations: {args.annotations_csv}, output: {args.output_dir}"
    )
    if not os.path.isfile(args.image_path):
        logger.error(f"Image file not found: {args.image_path}")
        print(f"[ERROR] Image file not found: {args.image_path}", file=sys.stderr)
        return 1
    if not os.path.isfile(args.annotations_csv):
        logger.error(f"Annotations CSV not found: {args.annotations_csv}")
        print(
            f"[ERROR] Annotations CSV not found: {args.annotations_csv}",
            file=sys.stderr,
        )
        return 1
    try:
        saved = crop_from_annotations(
            args.image_path,
            args.annotations_csv,
            args.output_dir,
            output_format=args.output_format,
            quality=args.quality,
        )
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"[ERROR] File not found: {e}", file=sys.stderr)
        return 1
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        print(f"[ERROR] Permission denied: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Failed to crop images: {e}")
        print(f"[ERROR] Failed to crop images: {e}", file=sys.stderr)
        return 1
    if not saved:
        logger.warning(
            f"No crops were saved for image: {args.image_path} with annotations: {args.annotations_csv}"
        )
        print(
            f"[ERROR] No crops were saved. Please check the annotation CSV and image file.",
            file=sys.stderr,
        )
        return 1
    logger.info(f"Saved {len(saved)} crop(s) to {args.output_dir}")
    print(f"Saved {len(saved)} crop(s)")
    return 0
