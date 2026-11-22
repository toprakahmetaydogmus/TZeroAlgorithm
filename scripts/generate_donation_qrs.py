#!/usr/bin/env python3
"""
T-Zero Offline Vector QR Code Generator for Web3 Sponsorship & Donations.
100% Zero-Leak Certified: 0 external API calls, pure local vector SVG generation.
"""

from pathlib import Path
import shutil
import sys
import qrcode
import qrcode.image.svg

QR_CONFIGS = [
    {
        "filename": "qr_ethereum.svg",
        "data": "ethereum:0xF36Cd453f9F2bE91647C006C46ff66fB41d9F0c5",
        "title": "Ethereum / EVM Address",
    },
    {
        "filename": "qr_bitcoin.svg",
        "data": "bitcoin:bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s?label=T-Zero%20Sponsorship",
        "title": "Bitcoin BIP-21 URI",
    },
    {
        "filename": "qr_tron.svg",
        "data": "tron:TE7uKxZJ414u938gWf6bYh9QvRk2141517",
        "title": "Tron / TRC-20 Address",
    },
]


def generate_qr_svgs(workspace_dir: Path = None):
    """Generates standalone SVG QR codes into assets/ and mirrors to benchmark-site/assets/."""
    if workspace_dir is None:
        workspace_dir = Path(__file__).resolve().parent.parent

    assets_dir = workspace_dir / "assets"
    benchmark_assets_dir = workspace_dir / "benchmark-site" / "assets"

    assets_dir.mkdir(parents=True, exist_ok=True)
    benchmark_assets_dir.mkdir(parents=True, exist_ok=True)

    generated_files = []

    for cfg in QR_CONFIGS:
        filename = cfg["filename"]
        data = cfg["data"]
        title = cfg["title"]

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
            image_factory=qrcode.image.svg.SvgPathImage,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image()

        out_path = assets_dir / filename
        with open(out_path, "wb") as f:
            img.save(f)

        # Mirror to benchmark-site/assets/
        mirror_path = benchmark_assets_dir / filename
        shutil.copy2(out_path, mirror_path)

        generated_files.append((out_path, mirror_path))
        print(f"  [OK] Generated {filename} ({title}) -> {out_path.stat().st_size} bytes")

    print(f"\n[SUCCESS] Successfully generated {len(generated_files)} offline SVG QR codes.")
    return generated_files


if __name__ == "__main__":
    generate_qr_svgs()
