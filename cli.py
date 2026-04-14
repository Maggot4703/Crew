import sys
import os
import argparse
import logging
try:
    from .image_utils import (
        overlay_grid,
        process_images,
        crop_from_annotations,
        _build_save_kwargs,
        DEFAULT_GRID_SIZE,
        DEFAULT_GRID_COLOR,
    )
    from .file_utils import (
        read_csv_builtin,
        read_csv_pandas,
        read_excel,
    )
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
    from image_utils import (
        overlay_grid,
        process_images,
        crop_from_annotations,
        _build_save_kwargs,
        DEFAULT_GRID_SIZE,
        DEFAULT_GRID_COLOR,
    )
    from file_utils import (
        read_csv_builtin,
        read_csv_pandas,
        read_excel,
    )

class CrewArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(f"[ERROR] {message}\n")
        self.print_help(sys.stderr)
        self.exit(2)

def create_cli_parser() -> argparse.ArgumentParser:
    parser = CrewArgumentParser(description="Crew utility CLI")
    parser.add_argument('--verbose', action='store_true', help='Enable verbose (DEBUG) logging')
    subparsers = parser.add_subparsers(dest="command")

    grid_image = subparsers.add_parser("grid-image", help="Overlay a grid on one image")
    grid_image.add_argument("image_path")
    grid_image.add_argument("output_path")
    grid_image.add_argument("--grid-width", type=int, default=DEFAULT_GRID_SIZE[0])
    grid_image.add_argument("--grid-height", type=int, default=DEFAULT_GRID_SIZE[1])
    grid_image.add_argument("--grid-color", default=DEFAULT_GRID_COLOR)
    grid_image.add_argument("--labels", action="store_true")
    grid_image.add_argument("--output-format", choices=["png", "jpg", "jpeg", "webp"])
    grid_image.add_argument("--quality", type=int, default=95)

    grid_folder = subparsers.add_parser(
        "grid-folder", help="Overlay a grid for all images in a folder"
    )
    grid_folder.add_argument("input_dir")
    grid_folder.add_argument("output_dir")
    grid_folder.add_argument("--grid-width", type=int, default=DEFAULT_GRID_SIZE[0])
    grid_folder.add_argument("--grid-height", type=int, default=DEFAULT_GRID_SIZE[1])
    grid_folder.add_argument("--grid-color", default=DEFAULT_GRID_COLOR)
    grid_folder.add_argument("--labels", action="store_true")
    grid_folder.add_argument("--output-format", choices=["png", "jpg", "jpeg", "webp"])
    grid_folder.add_argument("--quality", type=int, default=95)

    read_csv_cmd = subparsers.add_parser("read-csv", help="Read CSV and print preview")
    read_csv_cmd.add_argument("csv_path")

    read_excel_cmd = subparsers.add_parser(
        "read-excel", help="Read Excel and print preview"
    )
    read_excel_cmd.add_argument("excel_path")
    read_excel_cmd.add_argument("--sheet")

    crop_csv = subparsers.add_parser(
        "crop-csv",
        help="Crop image regions from CSV annotations with columns name,x,y,width,height",
    )
    crop_csv.add_argument("image_path")
    crop_csv.add_argument("annotations_csv")
    crop_csv.add_argument("output_dir")
    crop_csv.add_argument("--output-format", choices=["png", "jpg", "jpeg", "webp"])
    crop_csv.add_argument("--quality", type=int, default=95)

    return parser

def run_cli(args: argparse.Namespace) -> int:
    # Set logging level based on --verbose flag
    if getattr(args, 'verbose', False):
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Verbose logging enabled (DEBUG level)")
    else:
        logging.getLogger().setLevel(logging.INFO)
    if args.command == "grid-image":
        image = overlay_grid(
            args.image_path,
            grid_color=args.grid_color,
            grid_size=(args.grid_width, args.grid_height),
            show_labels=args.labels,
        )
        if image is None:
            print(f"[ERROR] Could not process image: {args.image_path}. Please check the file path and format.", file=sys.stderr)
            return 1

        extension = os.path.splitext(args.output_path)[1]
        if args.output_format:
            extension = f".{args.output_format}"
            args.output_path = os.path.splitext(args.output_path)[0] + extension

        try:
            save_kwargs = _build_save_kwargs(extension or ".png", args.quality)
            image.save(args.output_path, **save_kwargs)
            print(f"Saved: {args.output_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save output image: {args.output_path}. {e}", file=sys.stderr)
            return 1
        return 0

    if args.command == "grid-folder":
        saved = process_images(
            args.input_dir,
            args.output_dir,
            grid_size=(args.grid_width, args.grid_height),
            grid_color=args.grid_color,
            show_labels=args.labels,
            output_format=args.output_format,
            quality=args.quality,
        )
        if not saved:
            print(f"[ERROR] No images were processed. Please check the input directory and file formats.", file=sys.stderr)
            return 1
        print(f"Processed {len(saved)} file(s)")
        return 0

    if args.command == "read-csv":
        if not os.path.isfile(args.csv_path):
            print(f"[ERROR] CSV file not found: {args.csv_path}", file=sys.stderr)
            return 1
        try:
            process_csv_data(args.csv_path)
        except Exception as e:
            print(f"[ERROR] Failed to read CSV: {e}", file=sys.stderr)
            return 1
        return 0

    if args.command == "read-excel":
        if not os.path.isfile(args.excel_path):
            print(f"[ERROR] Excel file not found: {args.excel_path}", file=sys.stderr)
            return 1
        try:
            process_excel_data(args.excel_path, sheet_name=args.sheet)
        except Exception as e:
            print(f"[ERROR] Failed to read Excel: {e}", file=sys.stderr)
            return 1
        return 0

    if args.command == "crop-csv":
        if not os.path.isfile(args.image_path):
            print(f"[ERROR] Image file not found: {args.image_path}", file=sys.stderr)
            return 1
        if not os.path.isfile(args.annotations_csv):
            print(f"[ERROR] Annotations CSV not found: {args.annotations_csv}", file=sys.stderr)
            return 1
        saved = crop_from_annotations(
            args.image_path,
            args.annotations_csv,
            args.output_dir,
            output_format=args.output_format,
            quality=args.quality,
        )
        if not saved:
            print(f"[ERROR] No crops were saved. Please check the annotation CSV and image file.", file=sys.stderr)
            return 1
        print(f"Saved {len(saved)} crop(s)")
        return 0

    return 1
