# Hệ Thống Nhận Dạng Biển Số Xe

Ứng dụng Streamlit nhận dạng và tra cứu biển số xe bằng OCR (EasyOCR), lưu lịch sử ra/vào, quản lý vi phạm, thanh toán, danh sách đen và thống kê.

## 📚 Lý Thuyết Nền Tảng

### 1. OCR (Optical Character Recognition)
OCR là công nghệ cho phép máy tính nhận dạng và chuyển đổi văn bản từ hình ảnh thành dữ liệu có thể chỉnh sửa. Quy trình OCR bao gồm:

**Các bước cơ bản:**
- **Tiền xử lý ảnh**: Chuyển đổi sang grayscale, điều chỉnh độ sáng/tương phản, khử nhiễu
- **Phân đoạn**: Tách vùng chứa text từ background
- **Nhận dạng ký tự**: Sử dụng mô hình Deep Learning (CNN/RNN) để nhận dạng từng ký tự
- **Hậu xử lý**: Sửa lỗi, định dạng kết quả

**Deep Learning trong OCR:**
- **CNN (Convolutional Neural Networks)**: Trích xuất đặc trưng từ ảnh (cạnh, góc, hình dạng ký tự)
- **RNN/LSTM**: Xử lý chuỗi ký tự, học ngữ cảnh giữa các ký tự
- **Attention Mechanism**: Tập trung vào vùng quan trọng của ảnh

### 2. Nhận Dạng Biển Số Xe
Nhận dạng biển số xe là bài toán OCR đặc thù với những thách thức riêng:

**Thách thức:**
- Điều kiện ánh sáng thay đổi (ban ngày/đêm, có/không đèn flash)
- Góc chụp nghiêng, xa, gần
- Biển số bẩn, mờ, bị che khuất
- Font chữ đặc biệt của biển số Việt Nam

**Giải pháp:**
- **Image Enhancement**: Điều chỉnh độ sáng, tương phản tự động
- **Preprocessing**: Khử nhiễu, chuẩn hóa kích thước
- **Multi-language OCR**: Hỗ trợ cả chữ và số tiếng Việt
- **Post-processing**: Validate format biển số (XX-YYY.ZZ hoặc XX-YYYYYY)

**Format biển số Việt Nam:**
- Mã tỉnh (2 số) + Mã loại xe (1 chữ cái) + Số thứ tự
- Ví dụ: `29A-123.45`, `51F-734.20`, `30H-12345`
- 63 tỉnh/thành phố với mã riêng biệt

### 3. Xử Lý Ảnh (Image Processing)
Các kỹ thuật xử lý ảnh được sử dụng trong hệ thống:

**Brightness Adjustment (Điều chỉnh độ sáng):**
```
new_pixel = old_pixel + brightness_value
```
- Giúp làm sáng ảnh quá tối hoặc tối ảnh quá sáng
- Range: -50 đến +50

**Contrast Enhancement (Tăng độ tương phản):**
```
new_pixel = (old_pixel - 128) * contrast_factor + 128
```
- Làm rõ sự khác biệt giữa vùng sáng và tối
- Range: 0.5 đến 2.0

**Grayscale Conversion:**
- Giảm độ phức tạp từ 3 channels (RGB) xuống 1 channel
- Tăng tốc độ xử lý, giảm nhiễu màu

## 🛠️ Công Cụ & Thư Viện Sử Dụng

### 1. **Streamlit** - Framework Web
**Vai trò**: Xây dựng giao diện web tương tác

**Ưu điểm:**
- Tạo web app nhanh chóng chỉ bằng Python
- Hỗ trợ session state để quản lý trạng thái
- Tích hợp file uploader, camera input, charts
- Hot reload tự động khi code thay đổi

**Sử dụng trong dự án:**
- `st.file_uploader()`: Upload ảnh biển số
- `st.camera_input()`: Chụp ảnh trực tiếp
- `st.session_state`: Lưu kết quả OCR, login state
- `st.sidebar`: Menu điều hướng
- `st.plotly_chart()`: Hiển thị biểu đồ thống kê

### 2. **EasyOCR** - OCR Engine
**Vai trò**: Nhận dạng ký tự từ ảnh biển số

**Tại sao chọn EasyOCR:**
- Hỗ trợ 80+ ngôn ngữ, bao gồm tiếng Việt
- Pre-trained models chính xác cao
- API đơn giản, dễ tích hợp
- Tự động detect vùng text

**Mô hình sử dụng:**
- CRAFT (Character Region Awareness for Text Detection): Phát hiện vùng text
- CRNN (Convolutional Recurrent Neural Network): Nhận dạng ký tự
- Language models: Tiếng Việt (`vi`) + Tiếng Anh (`en`)

**Cấu hình:**
```python
reader = easyocr.Reader(['vi', 'en'], gpu=False)
result = reader.readtext(image)
```

### 3. **OpenCV** - Computer Vision
**Vai trò**: Xử lý và tiền xử lý ảnh

**Chức năng sử dụng:**
- `cv2.imread()`: Đọc file ảnh
- `cv2.cvtColor()`: Chuyển đổi không gian màu (RGB, Grayscale)
- `cv2.resize()`: Thay đổi kích thước ảnh
- Preprocessing: Khử nhiễu, làm mịn, edge detection

### 4. **PIL (Pillow)** - Image Processing
**Vai trò**: Xử lý ảnh cấp cao

**Chức năng sử dụng:**
- `Image.open()`: Mở file ảnh
- `ImageEnhance.Brightness()`: Điều chỉnh độ sáng
- `ImageEnhance.Contrast()`: Điều chỉnh độ tương phản
- `ImageFilter`: Làm mịn, sharpen ảnh

### 5. **MySQL/MariaDB** - Database
**Vai trò**: Lưu trữ dữ liệu hệ thống

**Cấu trúc cơ sở dữ liệu:**
- `bienso`: Thông tin xe (biển số, loại xe, chủ xe, màu xe)
- `lichsu`: Lịch sử ra/vào (thời gian, ảnh, trạng thái)
- `vi_pham`: Danh sách vi phạm và phí phạt
- `thanh_toan`: Lịch sử thanh toán
- `danh_sach_den`: Xe trong danh sách đen

**Ưu điểm MySQL:**
- Hiệu suất cao với large dataset
- ACID compliance (đảm bảo tính toàn vẹn)
- Hỗ trợ transactions, indexes
- Dễ backup và restore

### 6. **Pandas** - Data Analysis
**Vai trò**: Xử lý và phân tích dữ liệu

**Sử dụng:**
- Đọc dữ liệu từ MySQL thành DataFrame
- Thống kê: `groupby()`, `count()`, `sum()`
- Tính toán phần trăm, top N
- Xuất báo cáo Excel/CSV

### 7. **Plotly** - Data Visualization
**Vai trò**: Tạo biểu đồ tương tác

**Loại biểu đồ:**
- Bar chart: Top 10 biển số xuất hiện nhiều
- Pie chart: Phân bố xe theo tỉnh
- Line chart: xu hướng ra/vào theo thời gian
- Table: Bảng thống kê chi tiết

## 🔄 Quy Trình Hoạt Động Hệ Thống

### 1. Luồng Nhận Dạng Biển Số
```
Input (Ảnh) 
    ↓
Tiền xử lý (Brightness/Contrast)
    ↓
EasyOCR Recognition
    ↓
Post-processing (Format validation)
    ↓
Hiển thị kết quả + Cho phép chỉnh sửa
    ↓
Lưu vào Database
```

### 2. Luồng Quản Lý Ra/Vào
```
Nhận dạng biển số
    ↓
Kiểm tra trong Database
    ↓
├─ Có: Lấy thông tin xe
└─ Không: Thêm xe mới
    ↓
Xác định trạng thái (VAO/RA)
    ↓
Kiểm tra danh sách đen
    ↓
├─ Trong DS đen: Cảnh báo
└─ Bình thường: Ghi log
    ↓
Lưu lịch sử + Ảnh
```

### 3. Luồng Thống Kê
```
Query Database
    ↓
Pandas DataFrame Processing
    ↓
Tính toán metrics (count, percentage, trends)
    ↓
Plotly Visualization
    ↓
Streamlit Display
```

## Yêu cầu hệ thống
- Python 3.10+ (khuyến nghị 3.11)
- MySQL/MariaDB
- Windows/Mac/Linux

## Cài đặt
1. Tạo môi trường ảo

Windows:
- python -m venv .venv
- .venv\Scripts\activate

2. Cài thư viện
- pip install -r requirements.txt

Nếu chưa có requirements.txt, cài tối thiểu:
- pip install streamlit easyocr opencv-python-headless numpy pandas pillow mysql-connector-python

## Cấu hình CSDL
1. Import file SQL vào MySQL/MariaDB:
- database/baixe_db.sql (hoặc baixe_db_new.sql nếu bạn đã tạo schema mới)

2. Cấu hình kết nối trong Streamlit:

Cách 1: dùng biến môi trường
- DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT

Cách 2: dùng secrets
Tạo file .streamlit/secrets.toml:

[db]
host = "127.0.0.1"
user = "root"
password = ""
database = "baixe_db"
port = 3306

## Tài khoản đăng nhập
Mặc định:
- admin / admin123

Bạn có thể đổi trong secrets:
admin_user, admin_pass

## Chạy ứng dụng
- streamlit run app.py

## Chức năng chính
- Nhận dạng biển số từ ảnh hoặc camera
- Tra cứu biển số
- Quản lý xe, chi tiết xe
- Danh sách đen & cảnh báo
- Vi phạm & thanh toán
- Thống kê & báo cáo

## Lưu ảnh
Ảnh được lưu vào thư mục uploads/ và đường dẫn được ghi vào bảng lichsu.

## Ghi chú
- Hệ thống có cơ chế chỉnh sửa biển số sau khi OCR nhận dạng.
- Logic vào/ra yêu cầu xen kẽ VAO/RA để tránh ghi sai.
