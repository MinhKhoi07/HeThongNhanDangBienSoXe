# Hệ Thống Nhận Dạng Biển Số Xe

Ứng dụng Streamlit nhận dạng và tra cứu biển số xe bằng OCR (EasyOCR), lưu lịch sử ra/vào, quản lý vi phạm, thanh toán, danh sách đen và thống kê.

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
