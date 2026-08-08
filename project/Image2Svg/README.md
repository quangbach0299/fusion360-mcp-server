# Image2Svg Converter Utility

Chuyển đổi hình ảnh (PNG, JPG, BMP, WEBP, v.v.) thành định dạng định dạng vectơ **SVG**.
Hỗ trợ cả chế độ ảnh màu (high-fidelity color vectorization) và chế độ bản vẽ đen trắng (black & white sketch / CAD contour).

---

## 🛠️ Cài đặt thư viện

Dự án đã sử dụng `vtracer` (Rust-backed vectorizer) và `opencv-python` cho độ chính xác cao.

```bash
uv pip install pillow opencv-python vtracer numpy
```

---

## 🚀 Cách sử dụng

### 1. Dùng lệnh CLI đơn giản:

```bash
# Chuyển đổi ảnh bất kỳ thành SVG (tự động lưu thành <tên_ảnh>.svg)
python project/Image2Svg/image_to_svg.py logo.png

# Chỉ định đường dẫn đầu ra custom:
python project/Image2Svg/image_to_svg.py logo.png -o output/logo_vector.svg

# Chuyển bản vẽ sketch đen trắng (Binary mode):
python project/Image2Svg/image_to_svg.py sketch.jpg -c binary
```

---

## 🐍 Dùng trong Python script:

```python
from project.Image2Svg.image_to_svg import convert_image_to_svg

svg_file = convert_image_to_svg(
    input_path="my_sketch.png",
    output_path="my_sketch.svg",
    color_mode="binary"  # hoặc "color"
)
print("SVG saved at:", svg_file)
```
