# Image2Svg Converter Utility

Chuyển đổi hình ảnh (PNG, JPG, BMP, WEBP, v.v.) thành định dạng **SVG Vector**.
Hỗ trợ 3 chế độ (presets):
- **`color`**: Vectorize ảnh màu đầy đủ (hỗ trợ ảnh chụp, logo nhiều màu).
- **`sketch`**: Trích xuất đường nét phác thảo (Line-Art Outline) từ ảnh chụp để làm Sketch cho Fusion 360 / Laser / CNC.
- **`binary`**: Chuyển đổi đồ họa đen trắng (Binary Threshold) cho logo / đồ họa đơn sắc.

---

## 🛠️ Cài đặt thư viện

```bash
uv pip install pillow opencv-python vtracer numpy
```

---

## 🚀 Cách sử dụng

### 1. Dùng lệnh CLI:

```bash
# Trích xuất đường nét phác thảo (Sketch / Line-Art) từ bức ảnh chụp (Ví dụ: Ronaldo Siu)
python project/Image2Svg/image_to_svg.py ronaldoSiu.png -p sketch -o ronaldoSiu_sketch.svg

# Vectorize toàn bộ mảng màu của ảnh (Color mode):
python project/Image2Svg/image_to_svg.py image.png -p color -o image_color.svg

# Chuyển đồ họa đen trắng đơn sắc (Binary mode):
python project/Image2Svg/image_to_svg.py logo.png -p binary
```

---

## 🐍 Dùng trong Python:

```python
from project.Image2Svg.image_to_svg import convert_image_to_svg

# Tạo đường nét phác thảo cho Fusion 360
svg_file = convert_image_to_svg(
    input_path="ronaldoSiu.png",
    output_path="ronaldoSiu_sketch.svg",
    preset="sketch"
)
```
