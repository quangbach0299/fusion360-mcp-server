#!/usr/bin/env python3
"""
Image to DXF Vectorizer Utility for Autodesk Fusion 360
Converts raster images / sketches into native AutoCAD DXF R12 format.
R12 is the most universally compatible DXF version for Fusion 360 Insert DXF.
Uses LINE entities (not LWPOLYLINE) for maximum Fusion 360 compatibility.
"""

import os
import sys
import argparse
import cv2
import numpy as np


def _write_dxf_r12(output_path: str, polylines: list, width: int, height: int):
    """
    Write a minimal DXF R12 (AC1009) file by hand.
    Uses LINE entities for maximum compatibility with Fusion 360's Insert DXF.
    """
    lines = []

    # --- HEADER section ---
    lines.append("  0\nSECTION\n  2\nHEADER")
    lines.append("  9\n$ACADVER\n  1\nAC1009")           # R12
    lines.append("  9\n$INSUNITS\n 70\n4")               # 4 = Millimeters
    lines.append(f"  9\n$EXTMIN\n 10\n0.0\n 20\n0.0\n 30\n0.0")
    lines.append(f"  9\n$EXTMAX\n 10\n{float(width)}\n 20\n{float(height)}\n 30\n0.0")
    lines.append("  0\nENDSEC")

    # --- TABLES section (minimal) ---
    lines.append("  0\nSECTION\n  2\nTABLES")
    # LTYPE table with CONTINUOUS
    lines.append("  0\nTABLE\n  2\nLTYPE\n 70\n1")
    lines.append("  0\nLTYPE\n  2\nCONTINUOUS\n 70\n0\n  3\nSolid line\n 72\n65\n 73\n0\n 40\n0.0")
    lines.append("  0\nENDTAB")
    # LAYER table with layer 0
    lines.append("  0\nTABLE\n  2\nLAYER\n 70\n1")
    lines.append("  0\nLAYER\n  2\n0\n 70\n0\n 62\n7\n  6\nCONTINUOUS")
    lines.append("  0\nENDTAB")
    lines.append("  0\nENDSEC")

    # --- ENTITIES section ---
    lines.append("  0\nSECTION\n  2\nENTITIES")

    for poly in polylines:
        pts = poly
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]  # wrap around to close the polyline
            lines.append(
                f"  0\nLINE\n  8\n0\n"
                f" 10\n{x1:.4f}\n 20\n{y1:.4f}\n 30\n0.0\n"
                f" 11\n{x2:.4f}\n 21\n{y2:.4f}\n 31\n0.0"
            )

    lines.append("  0\nENDSEC")

    # --- EOF ---
    lines.append("  0\nEOF")

    with open(output_path, "w", encoding="ascii", newline="\r\n") as f:
        f.write("\n".join(lines))


def convert_image_to_dxf(
    input_path: str,
    output_path: str = None,
    threshold_val: int = 127,
    simplify_tolerance: float = 0.5,
    invert: bool = True,
    scale_mm: float = 1.0,
    use_edges: bool = True
) -> str:
    """
    Extract contours from image and export as DXF R12 LINE entities for Fusion 360.

    Args:
        input_path: Path to the source raster image.
        output_path: Path for output DXF file (default: same name as input with .dxf).
        threshold_val: Binarization threshold (0-255).
        simplify_tolerance: Contour simplification % (0 = no simplification).
        invert: If True, treats dark areas as foreground.
        scale_mm: Scale factor (pixels to mm). Default 1.0 means 1 pixel = 1 mm.
        use_edges: If True, uses Canny edge detection instead of threshold (better for photos).
    """
    input_path = os.path.abspath(input_path)
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    if not output_path:
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}.dxf"
    else:
        output_path = os.path.abspath(output_path)

    print(f"[*] Reading image: {input_path}")
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Could not open image file: {input_path}")

    height, width = img.shape
    print(f"[*] Image size: {width}x{height} px")

    # Bilateral filter to smooth noise while keeping edges sharp
    smooth = cv2.bilateralFilter(img, 7, 50, 50)

    if use_edges:
        # Canny edge detection - much better for photographs
        binary = cv2.Canny(smooth, 40, 120)
        # Dilate slightly to close small gaps in edges
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.dilate(binary, kernel, iterations=1)
    else:
        # Simple threshold - good for logos / line art
        thresh_type = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
        _, binary = cv2.threshold(smooth, threshold_val, 255, thresh_type)

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    polylines = []
    for cnt in contours:
        if len(cnt) < 3:
            continue

        # Simplify contour
        if simplify_tolerance > 0:
            perimeter = cv2.arcLength(cnt, True)
            epsilon = simplify_tolerance * perimeter / 100.0
            approx = cv2.approxPolyDP(cnt, epsilon, True)
        else:
            approx = cnt

        if len(approx) < 3:
            continue

        # Convert to (x, y) with Y-axis flipped and scaled to mm
        pts = [
            (float(pt[0][0]) * scale_mm, float(height - pt[0][1]) * scale_mm)
            for pt in approx
        ]
        polylines.append(pts)

    dxf_width = float(width) * scale_mm
    dxf_height = float(height) * scale_mm

    print(f"[*] Writing DXF R12 with {len(polylines)} contours...")
    _write_dxf_r12(output_path, polylines, dxf_width, dxf_height)

    file_size_kb = os.path.getsize(output_path) / 1024
    print(f"[SUCCESS] DXF saved to {output_path} ({file_size_kb:.1f} KB)")
    print(f"[*] Drawing size: {dxf_width:.1f} x {dxf_height:.1f} mm")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert Image to Fusion 360 compatible DXF R12 file"
    )
    parser.add_argument("input", help="Path to input image (PNG, JPG, BMP, WEBP)")
    parser.add_argument("-o", "--output", help="Path to output DXF file (optional)")
    parser.add_argument(
        "-t", "--threshold", type=int, default=127,
        help="Threshold value 0-255 (default: 127)"
    )
    parser.add_argument(
        "-s", "--simplify", type=float, default=0.5,
        help="Contour simplification tolerance %% (default: 0.5)"
    )
    parser.add_argument(
        "--scale", type=float, default=1.0,
        help="Scale factor: pixels to mm (default: 1.0 = 1px is 1mm)"
    )
    parser.add_argument(
        "--no-edges", action="store_true",
        help="Use threshold instead of Canny edge detection (better for logos)"
    )

    args = parser.parse_args()
    try:
        convert_image_to_dxf(
            input_path=args.input,
            output_path=args.output,
            threshold_val=args.threshold,
            simplify_tolerance=args.simplify,
            scale_mm=args.scale,
            use_edges=not args.no_edges
        )
    except Exception as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
