import argparse
import base64
import hashlib
import shlex
from pathlib import Path
from getpass import getpass


MAGIC = "ZTPNG1"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def encode_png_to_ztpng(png_path: Path, ztpng_path: Path, password: str) -> None:
    png_bytes = png_path.read_bytes()
    checksum = hashlib.sha256(png_bytes).hexdigest()
    b64_data = base64.b64encode(png_bytes).decode("ascii")
    password_hash = hash_password(password)

    content = [
        MAGIC,
        f"filename:{png_path.name}",
        f"size:{len(png_bytes)}",
        f"sha256:{checksum}",
        f"password:{password_hash}",
        "",
        b64_data,
        "",
    ]
    ztpng_path.write_text("\n".join(content), encoding="utf-8")


def decode_ztpng_to_png(ztpng_path: Path, png_path: Path, password: str) -> None:
    text = ztpng_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0].strip() != MAGIC:
        raise ValueError("Invalid .ztpng file: missing ZTPNG1 header")

    size_line = next((line for line in lines if line.startswith("size:")), None)
    hash_line = next((line for line in lines if line.startswith("sha256:")), None)
    password_line = next((line for line in lines if line.startswith("password:")), None)

    if size_line is None or hash_line is None or password_line is None:
        raise ValueError("Invalid .ztpng file: missing metadata")

    saved_password_hash = password_line.split(":", 1)[1].strip()

    if hash_password(password) != saved_password_hash:
        raise ValueError("Wrong password")

    data_start = None
    for i, line in enumerate(lines):
        if line.strip() == "" and i + 1 < len(lines):
            data_start = i + 1
            break

    if data_start is None:
        raise ValueError("Invalid .ztpng file: base64 data not found")

    b64_data = "".join(lines[data_start:]).strip()
    png_bytes = base64.b64decode(b64_data)

    expected_size = int(size_line.split(":", 1)[1].strip())
    expected_hash = hash_line.split(":", 1)[1].strip()
    actual_hash = hashlib.sha256(png_bytes).hexdigest()

    if len(png_bytes) != expected_size:
        raise ValueError("Data size mismatch: .ztpng file may be corrupted")

    if actual_hash != expected_hash:
        raise ValueError("SHA256 mismatch: .ztpng file may be corrupted")

    png_path.write_bytes(png_bytes)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert PNG <-> ZTPNG (text format)."
    )
    subparsers = parser.add_subparsers(dest="command")

    encode_parser = subparsers.add_parser("encode", help="Convert PNG to .ztpng")
    encode_parser.add_argument("input_png", type=Path, help="Path to source PNG")
    encode_parser.add_argument("output_ztpng", type=Path, help="Path to output .ztpng")

    decode_parser = subparsers.add_parser("decode", help="Convert .ztpng back to PNG")
    decode_parser.add_argument("input_ztpng", type=Path, help="Path to source .ztpng")
    decode_parser.add_argument("output_png", type=Path, help="Path to output PNG")

    return parser


def _suggest_output_path(input_path: Path, target: str) -> Path:
    target = target.lower().strip()

    if target == "ztpng":
        return input_path.with_suffix(".ztpng")

    if target == "png":
        return input_path.with_suffix(".png")

    raise ValueError("Target must be 'ztpng' or 'png'")


def interactive_console() -> None:
    print("ZTPNG console mode")
    print("Type commands:")
    print(r'  "C:\path\image.png" in ztpng')
    print(r'  "C:\path\file.ztpng" in png')
    print("Type 'exit' to quit.")

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not raw:
            continue

        if raw.lower() in {"exit", "quit"}:
            return

        try:
            parts = shlex.split(raw, posix=False)

            if len(parts) != 3 or parts[1].lower() != "in":
                raise ValueError("Expected: <path> in <ztpng|png>")

            src = Path(parts[0].strip().strip('"'))
            target = parts[2].lower().strip()

            if not src.exists():
                raise FileNotFoundError(f"File not found: {src}")

            dst = _suggest_output_path(src, target)

            if target == "ztpng":
                password = getpass("Create password: ")
                confirm_password = getpass("Confirm password: ")

                if password != confirm_password:
                    raise ValueError("Passwords do not match")

                if len(password) < 1:
                    raise ValueError("Password cannot be empty")

                encode_png_to_ztpng(src, dst, password)
                print(f"OK: {src} -> {dst}")

            elif target == "png":
                password = getpass("Enter password: ")
                decode_ztpng_to_png(src, dst, password)
                print(f"OK: {src} -> {dst}")

            else:
                raise ValueError("Target must be 'ztpng' or 'png'")

        except Exception as e:
            print(f"ERROR: {e}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        interactive_console()
        return

    if args.command == "encode":
        if not args.input_png.exists():
            raise FileNotFoundError(f"Input file not found: {args.input_png}")

        password = getpass("Create password: ")
        confirm_password = getpass("Confirm password: ")

        if password != confirm_password:
            raise ValueError("Passwords do not match")

        encode_png_to_ztpng(args.input_png, args.output_ztpng, password)
        print(f"Encoded: {args.input_png} -> {args.output_ztpng}")

    elif args.command == "decode":
        if not args.input_ztpng.exists():
            raise FileNotFoundError(f"Input file not found: {args.input_ztpng}")

        password = getpass("Enter password: ")
        decode_ztpng_to_png(args.input_ztpng, args.output_png, password)
        print(f"Decoded: {args.input_ztpng} -> {args.output_png}")


if __name__ == "__main__":
    main()