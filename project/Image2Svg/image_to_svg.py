#!/usr/bin/env python3
"""
Image2Svg Converter Utility
Converts raster images (PNG, JPG, BMP, WEBP, etc.) to SVG vector graphics.
Supports high-fidelity color vectorization, line-art sketch extraction from photos, and contour tracing.
"""

import os
import sys
import argparse
from pathlib import Path


def extract_sketch_lineart(input_path: str, output_temp_png: str, low_thresh: int = 40, high_thresh: int = 120):
    """
    Extract clean line-art / outline from a photo using Bilateral Filtering + Canny Edge Detection.
    Prepares photo for SVG vector line tracing.
    """
    import cv2
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"Cannot load image: {input_path}")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Bilateral filter preserves sharp edges while smoothing background noise
    smooth = cv2.bilateralFilter(gray, 7, 50, 50)
    
    # Canny edge detection for clean outlines
    edges = cv2.Canny(smooth, low_thresh, high_thresh)
    
    # Invert (black lines on white background)
    inv_edges = cv2.bitwise_not(edges)
    cv2.imwrite(output_temp_png, inv_edges)
    return output_temp_png


def convert_with_vtracer(
    input_path: str,
    output_path: str,
    color_mode: str = "color",
    hierarchical: str = "stacked",
    filter_speckle: int = 4,
    color_precision: int = 6,
    layer_difference: int = 16,
    corner_threshold: int = 60,
    length_threshold: float = 4.0,
    max_iterations: int = 10,
    splice_threshold: int = 45,
    path_precision: int = 3
) -> bool:
    """Convert raster image to SVG using VTracer engine."""
    try:
        import vtracer
        vtracer.convert_image_to_svg_py(
            image_path=input_path,
            out_path=output_path,
            colormode=color_mode,
            hierarchical=hierarchical,
            filter_speckle=filter_speckle,
            color_precision=color_precision,
            layer_difference=layer_difference,
            corner_threshold=corner_threshold,
            length_threshold=length_threshold,
            max_iterations=max_iterations,
            splice_threshold=splice_threshold,
            path_precision=path_precision
        )
        return True
    except ImportError:
        print("[WARNING] vtracer not installed. Falling back to OpenCV contour method.")
        return False
    except Exception as e:
        print(f"[ERROR] VTracer conversion failed: {e}")
        return False


def convert_with_opencv(
    input_path: str,
    output_path: str,
    threshold_val: int = 127,
    invert: bool = True,
    simplify_tolerance: float = 1.0
) -> bool:
    """Convert black & white sketch / image to SVG path using OpenCV contours."""
    try:
        import cv2
        import numpy as np

        img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise FileNotFoundError(f"Could not load image at {input_path}")

        height, width = img.shape

        # Apply thresholding
        thresh_type = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
        _, binary = cv2.threshold(img, threshold_val, 255, thresh_type)

        # Find contours
        contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        svg_paths = []
        for cnt in contours:
            if len(cnt) < 3:
                continue
            
            # Optionally simplify contour
            if simplify_tolerance > 0:
                epsilon = simplify_tolerance * cv2.arcLength(cnt, True) / 100.0
                approx = cv2.approxPolyDP(cnt, epsilon, True)
            else:
                approx = cnt

            if len(approx) < 3:
                continue

            pts = approx.reshape(-1, 2)
            path_d = f"M {pts[0][0]} {pts[0][1]}"
            for pt in pts[1:]:
                path_d += f" L {pt[0]} {pt[1]}"
            path_d += " Z"
            svg_paths.append(f'  <path d="{path_d}" fill="black" stroke="none" />')

        svg_content = [
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
            '  <g>',
            '\n'.join(svg_paths),
            '  </g>',
            '</svg>'
        ]

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(svg_content))

        return True
    except Exception as e:
        print(f"[ERROR] OpenCV contour conversion failed: {e}")
        return False


def convert_image_to_svg(
    input_path: str,
    output_path: str = None,
    mode: str = "auto",
    preset: str = "color",
    color_mode: str = "color",
    filter_speckle: int = 4,
    threshold: int = 127
) -> str:
    """
    Main conversion entry point.
    Presets:
      - 'color': High fidelity color vectorization.
      - 'sketch': Converts photo to clean line-art outlines (ideal for CAD/Fusion360 sketch).
      - 'binary': Direct black & white thresholding (ideal for logos/graphics).
    """
    input_path = os.path.abspath(input_path)
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input image file not found: {input_path}")

    if not output_path:
        base_name = Path(input_path).stem
        suffix = f"_{preset}" if preset != "color" else ""
        output_path = os.path.join(os.path.dirname(input_path), f"{base_name}{suffix}.svg")
    else:
        output_path = os.path.abspath(output_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"[*] Converting: {input_path}")
    print(f"[*] Mode: {preset.upper()} -> Output: {output_path}")

    temp_png = None
    source_image_for_vtracer = input_path

    if preset == "sketch":
        temp_png = os.path.join(os.path.dirname(output_path), "_temp_lineart.png")
        source_image_for_vtracer = extract_sketch_lineart(input_path, temp_png)
        color_mode = "binary"
        filter_speckle = 2

    elif preset == "binary":
        color_mode = "binary"

    success = False
    if mode in ("auto", "vtracer"):
        success = convert_with_vtracer(
            input_path=source_image_for_vtracer,
            output_path=output_path,
            color_mode=color_mode,
            filter_speckle=filter_speckle,
            corner_threshold=30 if preset == "sketch" else 60,
            length_threshold=2.0 if preset == "sketch" else 4.0
        )

    if not success and mode in ("auto", "opencv", "contour"):
        print("[*] Trying OpenCV contour conversion mode...")
        success = convert_with_opencv(
            input_path=source_image_for_vtracer,
            output_path=output_path,
            threshold_val=threshold
        )

    # Clean up temp lineart PNG if created
    if temp_png and os.path.exists(temp_png):
        try:
            os.remove(temp_png)
        except Exception:
            pass

    if success:
        print(f"[SUCCESS] SVG saved to {output_path}")
        return output_path
    else:
        raise RuntimeError("Failed to convert image to SVG.")


def main():
    parser = argparse.ArgumentParser(description="Image to SVG Vectorizer Utility")
    parser.add_argument("input", help="Path to input raster image (PNG, JPG, BMP, WEBP)")
    parser.add_argument("-o", "--output", help="Path to output SVG file (optional)")
    parser.add_argument(
        "-p", "--preset",
        choices=["color", "sketch", "binary"],
        default="color",
        help="Conversion preset: 'color' (full color), 'sketch' (photo to CAD line-art outline), 'binary' (black & white logo)"
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["auto", "vtracer", "opencv"],
        default="auto",
        help="Conversion engine (default: auto)"
    )
    parser.add_argument(
        "-s", "--speckle",
        type=int,
        default=4,
        help="Filter noise speckles size in pixels (default: 4)"
    )

    args = parser.parse_args()
    try:
        convert_image_to_svg(
            input_path=args.input,
            output_path=args.output,
            mode=args.mode,
            preset=args.preset,
            filter_speckle=args.speckle
        )
    except Exception as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
