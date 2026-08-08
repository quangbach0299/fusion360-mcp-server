#!/usr/bin/env python3
"""
Image to DXF Vectorizer Utility for Autodesk Fusion 360
Converts raster images / sketches into native AutoCAD DXF format with clean LWPOLYLINE elements.
"""

import os
import sys
import argparse
import cv2
import numpy as np
import ezdxf

def convert_image_to_dxf(
    input_path: str,
    output_path: str = None,
    threshold_val: int = 127,
    simplify_tolerance: float = 0.5,
    invert: bool = True
) -> str:
    """
    Extract contours from image and export as native DXF LWPOLYLINE objects for Fusion 360.
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

    # Apply bilateral filter to smooth noise
    smooth = cv2.bilateralFilter(img, 7, 50, 50)

    # Apply thresholding or edge detection
    thresh_type = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
    _, binary = cv2.threshold(smooth, threshold_val, 255, thresh_type)

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Create new DXF document (R2010 version compatible with Fusion 360)
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    contour_count = 0
    for cnt in contours:
        if len(cnt) < 3:
            continue

        # Simplify contour
        if simplify_tolerance > 0:
            epsilon = simplify_tolerance * cv2.arcLength(cnt, True) / 100.0
            approx = cv2.approxPolyDP(cnt, epsilon, True)
        else:
            approx = cnt

        if len(approx) < 3:
            continue

        # Convert coordinates (invert Y axis for DXF CAD coordinate system)
        pts = [(float(pt[0][0]), float(height - pt[0][1])) for pt in approx]

        # Add Polyline to DXF
        msp.add_lwpolyline(pts, close=True)
        contour_count += 1

    doc.saveas(output_path)
    print(f"[SUCCESS] Exported {contour_count} DXF polylines to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Convert Image to Fusion 360 compatible DXF file")
    parser.add_argument("input", help="Path to input image")
    parser.add_argument("-o", "--output", help="Path to output DXF file (optional)")
    parser.add_argument("-t", "--threshold", type=int, default=127, help="Threshold value (0-255)")
    parser.add_argument("-s", "--simplify", type=float, default=0.5, help="Contour simplification tolerance % (default: 0.5)")

    args = parser.parse_args()
    try:
        convert_image_to_dxf(
            input_path=args.input,
            output_path=args.output,
            threshold_val=args.threshold,
            simplify_tolerance=args.simplify
        )
    except Exception as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
