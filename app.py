import io
import os
import re
from typing import List, Tuple, Optional
from datetime import datetime
import shutil

import cv2
import easyocr
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
import mysql.connector

# Cấu hình trang web
st.set_page_config(page_title="Demo Nhận Dạng Biển Số Xe - EasyOCR", layout="wide", initial_sidebar_state="expanded")

# CSS tùy chỉnh để styling đẹp
st.markdown("""
<style>
    /* Toàn cục */
    :root {
        --primary-color: #2E86AB;
        --secondary-color: #A23B72;
        --success-color: #06A77D;
        --warning-color: #F18F01;
        --danger-color: #D62828;
        --light-bg: #F7F7F7;
        --dark-text: #1C1C1C;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
    }
    
    /* Main content area */
    .main {
        background: #FFFFFF;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #2E86AB;
        font-weight: 600;
    }
    
    h1 {
        border-bottom: 3px solid #2E86AB;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #2E86AB 0%, #1a4d6d 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(46, 134, 171, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(46, 134, 171, 0.4);
    }
    
    /* Info/Success/Warning/Error boxes */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid;
        padding: 16px;
        background-color: rgba(0,0,0,0.02);
    }
    
    /* Cards style for info sections */
    .info-card {
        background: linear-gradient(135deg, #f5f9fc 0%, #eff4f8 100%);
        border-left: 4px solid #2E86AB;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        background-color: #E8E8E8;
        border: none;
        color: #1C1C1C;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #2E86AB;
        color: white;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #E0E0E0;
        padding: 10px;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #2E86AB;
        box-shadow: 0 0 0 3px rgba(46, 134, 171, 0.1);
    }
    
    /* Selectbox and other inputs */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        border-radius: 8px;
        border: 2px solid #E0E0E0;
    }
    
    /* Metric cards */
    .stMetric {
        background: linear-gradient(135deg, #ffffff 0%, #f5f9fc 100%);
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Radio button styling */
    .stRadio > label {
        padding: 8px 12px;
        border-radius: 6px;
        transition: all 0.3s ease;
    }
    
    .stRadio > label:hover {
        background-color: #f0f0f0;
    }
    
    /* Table styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #2E86AB, transparent);
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_reader() -> easyocr.Reader:
    """Tải model EasyOCR một lần, dùng lại cho các lần nhận dạng sau."""
    return easyocr.Reader(["en"], gpu=False)


def get_auth_config() -> Tuple[str, str]:
    """Lấy tài khoản đăng nhập từ secrets hoặc biến môi trường."""
    username = None
    password = None

    try:
        username = st.secrets.get("admin_user", None)
        password = st.secrets.get("admin_pass", None)
    except StreamlitSecretNotFoundError:
        pass

    if not username:
        username = os.environ.get("ADMIN_USER", "admin")
    if not password:
        password = os.environ.get("ADMIN_PASS", "admin123")

    return username, password


def get_db_config() -> dict:
    """Lấy cấu hình kết nối CSDL từ secrets hoặc biến môi trường."""
    try:
        if "db" in st.secrets:
            return {
                "host": st.secrets["db"].get("host", "127.0.0.1"),
                "user": st.secrets["db"].get("user", "root"),
                "password": st.secrets["db"].get("password", ""),
                "database": st.secrets["db"].get("database", "baixe_db"),
                "port": int(st.secrets["db"].get("port", 3306)),
            }
    except StreamlitSecretNotFoundError:
        pass

    return {
        "host": os.environ.get("DB_HOST", "127.0.0.1"),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "baixe_db"),
        "port": int(os.environ.get("DB_PORT", "3306")),
    }


def get_db_connection() -> Optional[mysql.connector.MySQLConnection]:
    """Tạo kết nối MySQL, trả về None nếu lỗi."""
    try:
        config = get_db_config()
        return mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        st.error(f"Lỗi kết nối CSDL: {err}")
        return None


def save_plate_image(image_pil: Image.Image, so_bien: str, loai_su_kien: str = "VAO") -> str:
    """Lưu ảnh biển số vào thư mục uploads và trả về đường dẫn."""
    try:
        # Tạo thư mục nếu chưa tồn tại
        uploads_dir = "uploads"
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
        
        # Tạo tên file với timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{so_bien.replace('/', '_').replace(' ', '_')}_{loai_su_kien}_{timestamp}.jpg"
        filepath = os.path.join(uploads_dir, filename)
        
        # Lưu ảnh
        image_pil.save(filepath, "JPEG")
        
        return filepath
    except Exception as e:
        st.error(f"Lỗi lưu ảnh: {e}")
        return ""

def read_text_and_boxes(
    image_bgr: np.ndarray,
) -> Tuple[List[Tuple[str, float]], List[np.ndarray]]:
    """Chạy OCR trên ảnh và trả về text, confidence cùng các bounding box."""
    reader = load_reader()
    results = reader.readtext(image_bgr)

    texts_with_conf: List[Tuple[str, float]] = []
    boxes: List[np.ndarray] = []
    
    for (bbox, text, conf) in results:
        # --- BẮT ĐẦU BỘ LỌC (FILTER) ---
        
        # 1. Lọc độ tin cậy: Chỉ lấy khi máy chắc chắn trên 25% (giảm từ 30% để bắt nhiều hơn)
        if conf < 0.25:
            continue
            
        # 2. Lọc ký tự rác: Ngày tháng thường có "/" hoặc giờ có ":"
        if "/" in text or ":" in text:
            continue

        cleaned = re.sub(r"[^A-Z0-9]", "", text.upper())

        # 3. Lọc độ dài: Chữ quá ngắn (dưới 2 ký tự) thường là nhiễu
        if len(cleaned) < 2:
            continue

        # 4. Lọc chuỗi hex 8 ký tự (thường là timestamp/counter trên camera)
        if re.fullmatch(r"[0-9A-F]{8}", cleaned):
            continue
            
        # --- KẾT THÚC BỘ LỌC ---
        
        # Nếu vượt qua hết các bài kiểm tra trên thì mới thêm vào danh sách
        texts_with_conf.append((cleaned, conf))  # Lưu cả confidence
        boxes.append(np.array(bbox, dtype=np.int32))

    return texts_with_conf, boxes


def preprocess_image(image_bgr: np.ndarray) -> np.ndarray:
    """Tiền xử lý ảnh để cải thiện OCR: tăng độ tương phản, khử nhiễu."""
    # Chuyển sang grayscale
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    
    # Áp dụng CLAHE (Contrast Limited Adaptive Histogram Equalization) để tăng độ tương phản
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Khử nhiễu
    denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
    
    # Chuyển lại BGR
    return cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)

def draw_boxes(image_bgr: np.ndarray, boxes: List[np.ndarray], texts_with_conf: List[Tuple[str, float]]) -> np.ndarray:
    """Vẽ khung chữ nhật và hiển thị text + confidence trên ảnh."""
    output = image_bgr.copy()
    for i, box in enumerate(boxes):
        x_min = int(np.min(box[:, 0]))
        y_min = int(np.min(box[:, 1]))
        x_max = int(np.max(box[:, 0]))
        y_max = int(np.max(box[:, 1]))
        
        # Vẽ khung
        cv2.rectangle(output, (x_min, y_min), (x_max, y_max), (0, 255, 0), 3)
        
        # Vẽ text và confidence
        if i < len(texts_with_conf):
            text, conf = texts_with_conf[i]
            label = f"{text} ({conf*100:.1f}%)"
            
            # Vẽ nền cho text
            (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(output, (x_min, y_min - text_height - 10), 
                         (x_min + text_width, y_min), (0, 255, 0), -1)
            
            # Vẽ text
            cv2.putText(output, label, (x_min, y_min - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    return output

def pil_to_bgr(pil_image: Image.Image) -> np.ndarray:
    """Chuyển ảnh PIL sang định dạng BGR để dùng với OpenCV."""
    image_rgb = np.array(pil_image.convert("RGB"))
    return cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

def bgr_to_pil(image_bgr: np.ndarray) -> Image.Image:
    """Chuyển ảnh BGR (OpenCV) về PIL để hiển thị trong Streamlit."""
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(image_rgb)


def render_ocr_page() -> None:
    """Trang demo OCR biển số."""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0;'>🎯 Nhận Dạng Biển Số Xe</h1>
        <p style='color: #E0E0E0; margin: 10px 0 0 0;'>Sử dụng EasyOCR - Công nghệ AI nhận dạng ký tự quang học</p>
    </div>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    if not conn:
        st.stop()

    # Cấu hình
    st.markdown("### ⚙️ Cấu hình sự kiện")
    col_cfg_left, col_cfg_mid, col_cfg_right = st.columns(3)
    with col_cfg_left:
        loai_su_kien = st.selectbox("📌 Loại sự kiện", ["VAO", "RA"], index=0)
    with col_cfg_mid:
        chu_xe = st.text_input("👤 Chủ xe (tùy chọn)")
    with col_cfg_right:
        sdt = st.text_input("📱 SĐT (tùy chọn)")

    trang_thai = st.selectbox("✓ Trạng thái xe", [1, 0], format_func=lambda v: "✅ Hoạt động" if v == 1 else "❌ Ngưng")

    if "last_plate_text" not in st.session_state:
        st.session_state.last_plate_text = ""

    st.divider()

    # Tabs: Tải ảnh hoặc Camera
    st.markdown("### 📸 Tải ảnh hoặc quét camera")
    tab1, tab2 = st.tabs(["📁 Tải ảnh", "📷 Camera"])
    
    with tab1:
        uploaded = st.file_uploader("Tải ảnh biển số (jpg, png)", type=["jpg", "jpeg", "png"])
        
        # Tùy chọn tiền xử lý
        use_preprocessing = st.checkbox("🔧 Tiền xử lý ảnh (tăng độ tương phản, khử nhiễu)", value=True)
        
        if uploaded is not None:
            image_bytes = uploaded.read()
            pil_image = Image.open(io.BytesIO(image_bytes))
            image_bgr = pil_to_bgr(pil_image)

            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown("#### 📸 Ảnh gốc")
                st.image(pil_image, use_container_width=True)

            with col_right:
                st.markdown("#### ✨ Ảnh kết quả")
                if st.button("🔍 Nhận dạng ngay", key="ocr_upload", use_container_width=True):
                    with st.spinner("🔄 Đang xử lý và đọc biển số..."):
                        # Tiền xử lý nếu được bật
                        processed_bgr = preprocess_image(image_bgr) if use_preprocessing else image_bgr
                        
                        texts_with_conf, boxes = read_text_and_boxes(processed_bgr)
                        output_bgr = draw_boxes(processed_bgr, boxes, texts_with_conf)
                        output_pil = bgr_to_pil(output_bgr)

                        st.image(output_pil, use_container_width=True)

                        # Hiển thị kết quả với confidence
                        if texts_with_conf:
                            texts = [t[0] for t in texts_with_conf]
                            plate_text = " - ".join(texts).strip()
                            st.session_state.last_plate_text = plate_text
                            
                            # Hiển thị từng phần với confidence
                            st.success(f"✅ **Biển số: {plate_text}**")
                            
                            with st.expander("📊 Chi tiết nhận dạng"):
                                for text, conf in texts_with_conf:
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.write(f"**{text}**")
                                    with col2:
                                        st.metric("Độ tin cậy", f"{conf*100:.1f}%")
                        else:
                            st.warning("⚠️ Không tìm thấy biển số nào hợp lệ!")

                if st.session_state.last_plate_text:
                    st.divider()
                    if st.button("💾 Lưu vào CSDL", key="save_upload", use_container_width=True):
                        try:
                            # Lưu ảnh
                            image_path = save_plate_image(pil_image, st.session_state.last_plate_text, loai_su_kien)
                            
                            with conn.cursor() as cursor:
                                cursor.execute(
                                    """
                                    INSERT INTO bienso (so_bien, chu_xe, sdt, trang_thai)
                                    VALUES (%s, %s, %s, %s)
                                    ON DUPLICATE KEY UPDATE
                                        chu_xe = VALUES(chu_xe),
                                        sdt = VALUES(sdt),
                                        trang_thai = VALUES(trang_thai)
                                    """,
                                    (
                                        st.session_state.last_plate_text,
                                        chu_xe.strip(),
                                        sdt.strip() or None,
                                        trang_thai,
                                    ),
                                )
                                cursor.execute(
                                    """
                                    INSERT INTO lichsu (so_bien, loai_su_kien, duong_dan_anh)
                                    VALUES (%s, %s, %s)
                                    """,
                                    (st.session_state.last_plate_text, loai_su_kien, image_path),
                                )
                                conn.commit()
                            st.success(f"✅ Đã lưu biển số vào bảng bienso và ghi lịch sử!")
                            st.info(f"📁 Ảnh: {image_path}")
                        except mysql.connector.Error as err:
                            st.error(f"❌ Lỗi lưu CSDL: {err}")
        else:
            st.info("👋 Vui lòng tải ảnh để bắt đầu nhận dạng.")
    
    with tab2:
        st.markdown("#### 📷 Chụp ảnh từ camera")
        
        # Tùy chọn tiền xử lý cho camera
        use_preprocessing_cam = st.checkbox("🔧 Tiền xử lý ảnh camera", value=True, key="preprocess_cam")
        
        camera_photo = st.camera_input("Chụp ảnh biển số")
        
        if camera_photo is not None:
            image_bytes = camera_photo.read()
            pil_image = Image.open(io.BytesIO(image_bytes))
            image_bgr = pil_to_bgr(pil_image)

            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown("#### 📸 Ảnh chụp")
                st.image(pil_image, use_container_width=True)

            with col_right:
                st.markdown("#### ✨ Ảnh kết quả")
                if st.button("🔍 Nhận dạng ngay", key="ocr_camera", use_container_width=True):
                    with st.spinner("🔄 Đang xử lý và đọc biển số..."):
                        # Tiền xử lý nếu được bật
                        processed_bgr = preprocess_image(image_bgr) if use_preprocessing_cam else image_bgr
                        
                        texts_with_conf, boxes = read_text_and_boxes(processed_bgr)
                        output_bgr = draw_boxes(processed_bgr, boxes, texts_with_conf)
                        output_pil = bgr_to_pil(output_bgr)

                        st.image(output_pil, use_container_width=True)

                        # Hiển thị kết quả với confidence
                        if texts_with_conf:
                            texts = [t[0] for t in texts_with_conf]
                            plate_text = " - ".join(texts).strip()
                            st.session_state.last_plate_text = plate_text
                            
                            # Hiển thị từng phần với confidence
                            st.success(f"✅ **Biển số: {plate_text}**")
                            
                            with st.expander("📊 Chi tiết nhận dạng"):
                                for text, conf in texts_with_conf:
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.write(f"**{text}**")
                                    with col2:
                                        st.metric("Độ tin cậy", f"{conf*100:.1f}%")
                        else:
                            st.warning("⚠️ Không tìm thấy biển số nào hợp lệ!")

                if st.session_state.last_plate_text:
                    st.divider()
                    if st.button("💾 Lưu vào CSDL", key="save_camera", use_container_width=True):
                        try:
                            # Lưu ảnh
                            image_path = save_plate_image(pil_image, st.session_state.last_plate_text, loai_su_kien)
                            
                            with conn.cursor() as cursor:
                                cursor.execute(
                                    """
                                    INSERT INTO bienso (so_bien, chu_xe, sdt, trang_thai)
                                    VALUES (%s, %s, %s, %s)
                                    ON DUPLICATE KEY UPDATE
                                        chu_xe = VALUES(chu_xe),
                                        sdt = VALUES(sdt),
                                        trang_thai = VALUES(trang_thai)
                                    """,
                                    (
                                        st.session_state.last_plate_text,
                                        chu_xe.strip(),
                                        sdt.strip() or None,
                                        trang_thai,
                                    ),
                                )
                                cursor.execute(
                                    """
                                    INSERT INTO lichsu (so_bien, loai_su_kien, duong_dan_anh)
                                    VALUES (%s, %s, %s)
                                    """,
                                    (st.session_state.last_plate_text, loai_su_kien, image_path),
                                )
                                conn.commit()
                            st.success(f"✅ Đã lưu biển số vào bảng bienso và ghi lịch sử!")
                            st.info(f"📁 Ảnh: {image_path}")
                        except mysql.connector.Error as err:
                            st.error(f"❌ Lỗi lưu CSDL: {err}")

    conn.close()


def fetch_all_bienso(conn: mysql.connector.MySQLConnection, province_prefix: Optional[str]) -> List[tuple]:
    """Lấy danh sách biển số (có thể lọc theo 2 số đầu tỉnh)."""
    with conn.cursor() as cursor:
        if province_prefix:
            cursor.execute(
                """
                SELECT id, so_bien, chu_xe, sdt, ngay_dang_ky, trang_thai
                FROM bienso
                WHERE so_bien LIKE %s
                ORDER BY id DESC
                """,
                (f"{province_prefix}%",),
            )
        else:
            cursor.execute(
                "SELECT id, so_bien, chu_xe, sdt, ngay_dang_ky, trang_thai FROM bienso ORDER BY id DESC"
            )
        return cursor.fetchall()


def fetch_province_codes(conn: mysql.connector.MySQLConnection) -> List[str]:
    """Lấy danh sách mã tỉnh (2 số đầu) từ dữ liệu hiện có."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT DISTINCT LEFT(so_bien, 2) AS ma_tinh
            FROM bienso
            WHERE so_bien REGEXP '^[0-9]{2}'
            ORDER BY ma_tinh
            """
        )
        return [row[0] for row in cursor.fetchall() if row[0]]


def search_bienso(conn: mysql.connector.MySQLConnection, keyword: str) -> List[tuple]:
    """Tìm kiếm biển số theo từ khóa."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, so_bien, chu_xe, sdt, ngay_dang_ky, trang_thai
            FROM bienso
            WHERE so_bien LIKE %s OR chu_xe LIKE %s OR sdt LIKE %s
            ORDER BY id DESC
            """,
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"),
        )
        return cursor.fetchall()


def fetch_all_lichsu(conn: mysql.connector.MySQLConnection, so_bien: Optional[str]) -> List[tuple]:
    """Lấy lịch sử ra/vào theo biển số (nếu có)."""
    with conn.cursor() as cursor:
        if so_bien:
            cursor.execute(
                """
                SELECT id, so_bien, thoi_gian, loai_su_kien, duong_dan_anh, ghi_chu
                FROM lichsu
                WHERE so_bien = %s
                ORDER BY id DESC
                """,
                (so_bien,),
            )
        else:
            cursor.execute(
                """
                SELECT id, so_bien, thoi_gian, loai_su_kien, duong_dan_anh, ghi_chu
                FROM lichsu
                ORDER BY id DESC
                """
            )
        return cursor.fetchall()


# ===== HÀM CHI TIẾT XE =====
def fetch_chi_tiet_xe(conn: mysql.connector.MySQLConnection, so_bien: str) -> Optional[tuple]:
    """Lấy chi tiết xe theo biển số."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, so_bien, loai_xe, hang_xe, mau_xe, nam_san_xuat, ma_khung, ma_may
            FROM chi_tiet_xe
            WHERE so_bien = %s
            """,
            (so_bien,),
        )
        return cursor.fetchone()


def save_chi_tiet_xe(conn: mysql.connector.MySQLConnection, so_bien: str, loai_xe: str, 
                      hang_xe: str, mau_xe: str, nam_sx: int, ma_khung: str, ma_may: str) -> bool:
    """Lưu hoặc cập nhật chi tiết xe."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO chi_tiet_xe (so_bien, loai_xe, hang_xe, mau_xe, nam_san_xuat, ma_khung, ma_may)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    loai_xe = VALUES(loai_xe),
                    hang_xe = VALUES(hang_xe),
                    mau_xe = VALUES(mau_xe),
                    nam_san_xuat = VALUES(nam_san_xuat),
                    ma_khung = VALUES(ma_khung),
                    ma_may = VALUES(ma_may)
                """,
                (so_bien, loai_xe, hang_xe, mau_xe, nam_sx, ma_khung, ma_may),
            )
            conn.commit()
        return True
    except mysql.connector.Error:
        return False


# ===== HÀM DANH SÁCH ĐEN & CẢNH BÁO =====
def fetch_danh_sach_den(conn: mysql.connector.MySQLConnection) -> List[tuple]:
    """Lấy danh sách xe cấm/theo dõi."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT id, so_bien, ly_do, muc_do_canh_bao, ngay_tao, ngay_het_hieu_luc, trang_thai
            FROM danh_sach_den
            ORDER BY trang_thai DESC, ngay_tao DESC
            """
        )
        return cursor.fetchall()


def add_danh_sach_den(conn: mysql.connector.MySQLConnection, so_bien: str, ly_do: str, 
                       muc_do: str, ngay_het_hieu_luc: Optional[str]) -> bool:
    """Thêm xe vào danh sách đen."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO danh_sach_den (so_bien, ly_do, muc_do_canh_bao, ngay_het_hieu_luc)
                VALUES (%s, %s, %s, %s)
                """,
                (so_bien, ly_do, muc_do, ngay_het_hieu_luc or None),
            )
            conn.commit()
        return True
    except mysql.connector.Error:
        return False


def xoa_danh_sach_den(conn: mysql.connector.MySQLConnection, id_danh_sach: int) -> bool:
    """Xóa xe khỏi danh sách đen."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM danh_sach_den WHERE id = %s", (id_danh_sach,))
            conn.commit()
        return True
    except mysql.connector.Error:
        return False


# ===== HÀM VI PHẠM =====
def fetch_vi_pham(conn: mysql.connector.MySQLConnection, so_bien: Optional[str] = None) -> List[tuple]:
    """Lấy danh sách vi phạm."""
    with conn.cursor() as cursor:
        if so_bien:
            cursor.execute(
                """
                SELECT id, so_bien, loai_vi_pham, muc_phat, trang_thai, ngay_phat_hien, ngay_xu_ly
                FROM vi_pham
                WHERE so_bien = %s
                ORDER BY ngay_phat_hien DESC
                """,
                (so_bien,),
            )
        else:
            cursor.execute(
                """
                SELECT id, so_bien, loai_vi_pham, muc_phat, trang_thai, ngay_phat_hien, ngay_xu_ly
                FROM vi_pham
                ORDER BY ngay_phat_hien DESC
                """
            )
        return cursor.fetchall()


def add_vi_pham(conn: mysql.connector.MySQLConnection, so_bien: str, loai_vi_pham: str, muc_phat: float) -> bool:
    """Thêm vi phạm mới."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vi_pham (so_bien, loai_vi_pham, muc_phat)
                VALUES (%s, %s, %s)
                """,
                (so_bien, loai_vi_pham, muc_phat),
            )
            conn.commit()
        return True
    except mysql.connector.Error:
        return False


# ===== HÀM THANH TOÁN =====
def fetch_thanh_toan(conn: mysql.connector.MySQLConnection, so_bien: Optional[str] = None) -> List[tuple]:
    """Lấy danh sách thanh toán."""
    with conn.cursor() as cursor:
        if so_bien:
            cursor.execute(
                """
                SELECT id, so_bien, so_tien, loai_thanh_toan, phuong_thuc, trang_thai, ngay_tao, ngay_thanh_toan
                FROM thanh_toan
                WHERE so_bien = %s
                ORDER BY ngay_tao DESC
                """,
                (so_bien,),
            )
        else:
            cursor.execute(
                """
                SELECT id, so_bien, so_tien, loai_thanh_toan, phuong_thuc, trang_thai, ngay_tao, ngay_thanh_toan
                FROM thanh_toan
                ORDER BY ngay_tao DESC
                """
            )
        return cursor.fetchall()


def add_thanh_toan(conn: mysql.connector.MySQLConnection, so_bien: str, so_tien: float, 
                    loai: str, phuong_thuc: str) -> bool:
    """Thêm hóa đơn thanh toán."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO thanh_toan (so_bien, so_tien, loai_thanh_toan, phuong_thuc)
                VALUES (%s, %s, %s, %s)
                """,
                (so_bien, so_tien, loai, phuong_thuc),
            )
            conn.commit()
        return True
    except mysql.connector.Error:
        return False


def cap_nhat_thanh_toan(conn: mysql.connector.MySQLConnection, id_thanh_toan: int, 
                         trang_thai: str, ngay_thanh_toan: Optional[str] = None) -> bool:
    """Cập nhật trạng thái thanh toán."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE thanh_toan
                SET trang_thai = %s, ngay_thanh_toan = %s
                WHERE id = %s
                """,
                (trang_thai, ngay_thanh_toan, id_thanh_toan),
            )
            conn.commit()
        return True
    except mysql.connector.Error:
        return False


# ===== HÀM THỐNG KÊ =====

def get_su_kien_gan_nhat(conn: mysql.connector.MySQLConnection, so_bien: str) -> Optional[str]:
    """Lấy sự kiện gần nhất của xe (VAO hoặc RA)."""
    so_bien = so_bien.strip().upper()
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT loai_su_kien FROM lichsu
            WHERE so_bien = %s
            ORDER BY thoi_gian DESC
            LIMIT 1
            """,
            (so_bien,)
        )
        result = cursor.fetchone()
        return result[0] if result else None


def validate_su_kien_xen_ke(conn: mysql.connector.MySQLConnection, so_bien: str, loai_su_kien_moi: str) -> tuple:
    """
    Kiểm tra xem sự kiện mới có hợp lệ không (phải xen kẽ VAO/RA).
    Returns: (is_valid, message)
    """
    so_bien = so_bien.strip().upper()
    su_kien_cuoi = get_su_kien_gan_nhat(conn, so_bien)
    
    # Nếu chưa có lịch sử, cho phép bất kỳ sự kiện nào
    if su_kien_cuoi is None:
        return True, "✅ Sự kiện đầu tiên cho xe này."
    
    # Nếu sự kiện cuối cùng giống sự kiện mới, không hợp lệ
    if su_kien_cuoi == loai_su_kien_moi:
        if loai_su_kien_moi == "VAO":
            return False, "❌ Xe này vừa VAO, không thể VAO lại. Vui lòng ghi RA trước."
        else:
            return False, "❌ Xe này vừa RA, không thể RA lại. Vui lòng ghi VAO trước."
    
    # Nếu xen kẽ đúng
    if loai_su_kien_moi == "VAO":
        return True, "✅ Sự kiện hợp lệ: Ghi nhận VAO."
    else:
        return True, "✅ Sự kiện hợp lệ: Ghi nhận RA."


def get_thong_ke_tong_quat(conn: mysql.connector.MySQLConnection) -> dict:
    """Lấy thống kê tổng quát."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM bienso WHERE trang_thai = 1")
        so_xe_active = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM danh_sach_den WHERE trang_thai = 1")
        so_xe_canh_bao = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vi_pham WHERE trang_thai = 'chua_xu_ly'")
        so_vi_pham_chua_xu_ly = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(so_tien) FROM thanh_toan WHERE trang_thai = 'da_thanh_toan'")
        doanh_thu = cursor.fetchone()[0] or 0
        
        return {
            "so_xe_active": so_xe_active,
            "so_xe_canh_bao": so_xe_canh_bao,
            "so_vi_pham": so_vi_pham_chua_xu_ly,
            "doanh_thu": float(doanh_thu),
        }


def get_thong_ke_ra_vao_theo_ngay(conn: mysql.connector.MySQLConnection, 
                                   ngay: Optional[str] = None) -> pd.DataFrame:
    """Lấy thống kê lần vào/ra theo ngày."""
    with conn.cursor() as cursor:
        if ngay:
            cursor.execute(
                """
                SELECT DATE(thoi_gian) as ngay, loai_su_kien, COUNT(*) as so_lan
                FROM lichsu
                WHERE DATE(thoi_gian) = %s
                GROUP BY ngay, loai_su_kien
                ORDER BY ngay, loai_su_kien
                """,
                (ngay,),
            )
        else:
            cursor.execute(
                """
                SELECT DATE(thoi_gian) as ngay, loai_su_kien, COUNT(*) as so_lan
                FROM lichsu
                GROUP BY ngay, loai_su_kien
                ORDER BY ngay DESC, loai_su_kien
                LIMIT 30
                """
            )
        result = cursor.fetchall()
        return pd.DataFrame(result, columns=["Ngày", "Loại sự kiện", "Số lần"]) if result else pd.DataFrame()


# ===== HÀM TRA CỨU BIỂN SỐ =====
def get_info_xe_toan_bo(conn: mysql.connector.MySQLConnection, so_bien: str) -> dict:
    """Lấy toàn bộ thông tin xe theo biển số."""
    info = {
        "bienso": None,
        "chi_tiet": None,
        "danh_sach_den": None,
        "vi_pham": [],
        "thanh_toan": [],
        "lichsu_gan_nhat": [],
        "tong_lan_vao": 0,
        "tong_lan_ra": 0,
    }
    
    so_bien = so_bien.strip().upper()
    
    with conn.cursor() as cursor:
        # Lấy thông tin biển số
        cursor.execute(
            "SELECT id, so_bien, chu_xe, sdt, email_chu_xe, ngay_dang_ky, trang_thai FROM bienso WHERE so_bien = %s",
            (so_bien,)
        )
        result = cursor.fetchone()
        if result:
            info["bienso"] = {
                "id": result[0],
                "so_bien": result[1],
                "chu_xe": result[2],
                "sdt": result[3],
                "email": result[4],
                "ngay_dang_ky": result[5],
                "trang_thai": result[6],
            }
        
        # Lấy chi tiết xe
        cursor.execute(
            "SELECT id, loai_xe, hang_xe, mau_xe, nam_san_xuat, ma_khung, ma_may FROM chi_tiet_xe WHERE so_bien = %s",
            (so_bien,)
        )
        result = cursor.fetchone()
        if result:
            info["chi_tiet"] = {
                "id": result[0],
                "loai_xe": result[1],
                "hang_xe": result[2],
                "mau_xe": result[3],
                "nam_sx": result[4],
                "ma_khung": result[5],
                "ma_may": result[6],
            }
        
        # Lấy danh sách đen
        cursor.execute(
            "SELECT id, ly_do, muc_do_canh_bao, ngay_tao, trang_thai FROM danh_sach_den WHERE so_bien = %s AND trang_thai = 1",
            (so_bien,)
        )
        result = cursor.fetchone()
        if result:
            info["danh_sach_den"] = {
                "id": result[0],
                "ly_do": result[1],
                "muc_do": result[2],
                "ngay_tao": result[3],
                "trang_thai": result[4],
            }
        
        # Lấy vi phạm chưa xử lý
        cursor.execute(
            "SELECT id, loai_vi_pham, muc_phat, trang_thai, ngay_phat_hien FROM vi_pham WHERE so_bien = %s ORDER BY ngay_phat_hien DESC LIMIT 10",
            (so_bien,)
        )
        info["vi_pham"] = [
            {"id": row[0], "loai": row[1], "muc_phat": float(row[2]), "trang_thai": row[3], "ngay": row[4]}
            for row in cursor.fetchall()
        ]
        
        # Lấy thanh toán chưa thanh toán
        cursor.execute(
            "SELECT id, so_tien, loai_thanh_toan, phuong_thuc, trang_thai, ngay_tao FROM thanh_toan WHERE so_bien = %s ORDER BY ngay_tao DESC LIMIT 10",
            (so_bien,)
        )
        info["thanh_toan"] = [
            {"id": row[0], "so_tien": float(row[1]), "loai": row[2], "phuong_thuc": row[3], "trang_thai": row[4], "ngay": row[5]}
            for row in cursor.fetchall()
        ]
        
        # Lấy lịch sử gần nhất
        cursor.execute(
            "SELECT id, thoi_gian, loai_su_kien FROM lichsu WHERE so_bien = %s ORDER BY thoi_gian DESC LIMIT 20",
            (so_bien,)
        )
        info["lichsu_gan_nhat"] = [
            {"id": row[0], "thoi_gian": row[1], "loai": row[2]}
            for row in cursor.fetchall()
        ]
        
        # Tính tổng lần vào/ra
        cursor.execute(
            "SELECT SUM(CASE WHEN loai_su_kien = 'VAO' THEN 1 ELSE 0 END), SUM(CASE WHEN loai_su_kien = 'RA' THEN 1 ELSE 0 END) FROM lichsu WHERE so_bien = %s",
            (so_bien,)
        )
        result = cursor.fetchone()
        if result:
            info["tong_lan_vao"] = result[0] or 0
            info["tong_lan_ra"] = result[1] or 0
    
    return info


def render_manage_page() -> None:
    """Trang quản lý xe (CRUD cơ bản) và lịch sử ra/vào."""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0; display: flex; align-items: center;'>
            🚗 Quản lý xe
        </h1>
    </div>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    if not conn:
        st.stop()

    # Thêm biển số mới
    with st.container():
        st.markdown("### ➕ Thêm biển số mới")
        with st.form("add_bienso_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                so_bien = st.text_input("📍 Số biển")
            with col2:
                chu_xe = st.text_input("👤 Chủ xe")
            with col3:
                sdt = st.text_input("📱 Số điện thoại")
            
            col_status, col_submit = st.columns([2, 1])
            with col_status:
                trang_thai = st.selectbox("✓ Trạng thái", [1, 0], format_func=lambda v: "✅ Hoạt động" if v == 1 else "❌ Ngưng")
            with col_submit:
                submitted = st.form_submit_button("➕ Thêm mới", use_container_width=True)

            if submitted:
                if not so_bien:
                    st.warning("⚠️ Vui lòng nhập số biển.")
                else:
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute(
                                """
                                INSERT INTO bienso (so_bien, chu_xe, sdt, trang_thai)
                                VALUES (%s, %s, %s, %s)
                                """,
                                (so_bien.upper(), chu_xe, sdt or None, trang_thai),
                            )
                            conn.commit()
                        st.success("✅ Đã thêm biển số mới.")
                    except mysql.connector.Error as err:
                        st.error(f"❌ Lỗi thêm dữ liệu: {err}")

    st.divider()

    # Danh sách biển số
    st.markdown("### 📋 Danh sách biển số")
    col_search_left, col_search_mid, col_search_right = st.columns([3, 2, 1])
    with col_search_left:
        keyword = st.text_input("🔎 Tìm kiếm biển số / chủ xe / SĐT")
    with col_search_mid:
        province_codes = fetch_province_codes(conn)
        province_options = ["Tất cả"] + province_codes
        province_filter = st.selectbox("📌 Lọc theo mã tỉnh", province_options)
    with col_search_right:
        search_btn = st.button("🔍 Tìm kiếm", use_container_width=True)

    if keyword and search_btn:
        data = search_bienso(conn, keyword.strip())
        st.caption(f"📌 Kết quả tìm kiếm cho: **{keyword}**")
    else:
        prefix = None if province_filter == "Tất cả" else province_filter
        data = fetch_all_bienso(conn, prefix)

    if data:
        df_bienso = pd.DataFrame(
            data,
            columns=["ID", "Số biển", "Chủ xe", "SĐT", "Ngày đăng ký", "Trạng thái"],
        )
        st.dataframe(df_bienso, use_container_width=True)

        ids = [row[0] for row in data]
        selected_id = st.selectbox("Chọn ID để cập nhật/xóa", ids)

        selected_row = next((row for row in data if row[0] == selected_id), None)
        if selected_row:
            with st.form("update_bienso_form"):
                so_bien_u = st.text_input("Số biển", value=selected_row[1])
                chu_xe_u = st.text_input("Chủ xe", value=selected_row[2])
                sdt_u = st.text_input("Số điện thoại", value=selected_row[3] or "")
                trang_thai_u = st.selectbox(
                    "Trạng thái",
                    [1, 0],
                    index=0 if selected_row[5] == 1 else 1,
                    format_func=lambda v: "Hoạt động" if v == 1 else "Ngưng",
                )

                col_a, col_b = st.columns(2)
                with col_a:
                    update_btn = st.form_submit_button("Cập nhật")
                with col_b:
                    delete_btn = st.form_submit_button("Xóa")

                if update_btn:
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute(
                                """
                                UPDATE bienso
                                SET so_bien = %s, chu_xe = %s, sdt = %s, trang_thai = %s
                                WHERE id = %s
                                """,
                                (so_bien_u.upper(), chu_xe_u, sdt_u or None, trang_thai_u, selected_id),
                            )
                            conn.commit()
                        st.success("Đã cập nhật thông tin.")
                    except mysql.connector.Error as err:
                        st.error(f"Lỗi cập nhật: {err}")

                if delete_btn:
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute("DELETE FROM bienso WHERE id = %s", (selected_id,))
                            conn.commit()
                        st.success("Đã xóa biển số.")
                    except mysql.connector.Error as err:
                        st.error(f"Lỗi xóa: {err}")
    else:
        st.info("Chưa có dữ liệu biển số.")

    st.subheader("Lịch sử ra/vào")
    so_bien_filter = st.text_input("Lọc theo số biển (tùy chọn)")
    lich_su = fetch_all_lichsu(conn, so_bien_filter.strip() or None)

    if lich_su:
        df_lichsu = pd.DataFrame(
            lich_su,
            columns=["ID", "Số biển", "Thời gian", "Loại sự kiện", "Đường dẫn ảnh", "Ghi chú"],
        )
        st.dataframe(df_lichsu, use_container_width=True)
    else:
        st.info("Chưa có lịch sử ra/vào.")

    conn.close()


# ===== TRANG CHI TIẾT XE =====
def render_chi_tiet_xe_page() -> None:
    """Trang quản lý chi tiết xe."""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0;'>📋 Chi tiết xe</h1>
        <p style='color: #E0E0E0; margin: 10px 0 0 0;'>Quản lý thông tin chi tiết về xe</p>
    </div>
    """, unsafe_allow_html=True)
    
    conn = get_db_connection()
    if not conn:
        st.stop()
    
    st.markdown("### 🔎 Tìm kiếm xe")
    so_bien_input = st.text_input("📍 Nhập số biển để xem/cập nhật chi tiết")
    
    if so_bien_input:
        chi_tiet = fetch_chi_tiet_xe(conn, so_bien_input.strip().upper())
        
        if chi_tiet:
            st.success(f"Tìm thấy: {so_bien_input}")
            id_ct, so_bien, loai_xe, hang_xe, mau_xe, nam_sx, ma_khung, ma_may = chi_tiet
            
            with st.form("form_chi_tiet"):
                col1, col2 = st.columns(2)
                with col1:
                    loai_xe_select = st.selectbox("Loại xe", 
                        ["4cho", "7cho", "giaothong", "moto", "khac"], 
                        index=["4cho", "7cho", "giaothong", "moto", "khac"].index(loai_xe) if loai_xe else 0)
                    hang_xe_input = st.text_input("Hãng xe", value=hang_xe or "")
                    mau_xe_input = st.text_input("Màu xe", value=mau_xe or "")
                
                with col2:
                    nam_sx_input = st.number_input("Năm sản xuất", value=nam_sx or 2020, min_value=1990, max_value=2030)
                    ma_khung_input = st.text_input("Mã khung", value=ma_khung or "")
                    ma_may_input = st.text_input("Mã máy", value=ma_may or "")
                
                if st.form_submit_button("Cập nhật"):
                    if save_chi_tiet_xe(conn, so_bien, loai_xe_select, hang_xe_input, mau_xe_input, 
                                       nam_sx_input, ma_khung_input, ma_may_input):
                        st.success("Đã cập nhật chi tiết xe.")
                    else:
                        st.error("Lỗi cập nhật chi tiết xe.")
        else:
            st.warning(f"Không tìm thấy biển số: {so_bien_input}")
            
            with st.form("form_them_chi_tiet"):
                st.write("**Thêm chi tiết xe mới**")
                col1, col2 = st.columns(2)
                with col1:
                    loai_xe = st.selectbox("Loại xe", ["4cho", "7cho", "giaothong", "moto", "khac"])
                    hang_xe = st.text_input("Hãng xe")
                    mau_xe = st.text_input("Màu xe")
                
                with col2:
                    nam_sx = st.number_input("Năm sản xuất", value=2020, min_value=1990, max_value=2030)
                    ma_khung = st.text_input("Mã khung")
                    ma_may = st.text_input("Mã máy")
                
                if st.form_submit_button("Thêm mới"):
                    if save_chi_tiet_xe(conn, so_bien_input.strip().upper(), loai_xe, hang_xe, 
                                       mau_xe, nam_sx, ma_khung, ma_may):
                        st.success("Đã thêm chi tiết xe.")
                    else:
                        st.error("Lỗi thêm chi tiết xe.")
    
    conn.close()


# ===== TRANG DANH SÁCH ĐEN & CẢNH BÁO =====
def render_danh_sach_den_page() -> None:
    """Trang quản lý danh sách đen."""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #D62828 0%, #A23B72 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0;'>🚫 Danh sách đen & cảnh báo</h1>
        <p style='color: #E0E0E0; margin: 10px 0 0 0;'>Quản lý xe nguy hiểm hoặc bị cảnh báo</p>
    </div>
    """, unsafe_allow_html=True)
    
    conn = get_db_connection()
    if not conn:
        st.stop()
    
    st.markdown("### ➕ Thêm xe vào danh sách đen")
    with st.form("form_them_danh_sach_den"):
        col1, col2 = st.columns(2)
        with col1:
            so_bien = st.text_input("Số biển")
            ly_do = st.text_area("Lý do")
        
        with col2:
            muc_do = st.selectbox("Mức độ cảnh báo", ["cao", "trung", "thap"])
            ngay_het = st.date_input("Ngày hết hiệu lực (tùy chọn)", value=None)
        
        if st.form_submit_button("Thêm vào danh sách"):
            if so_bien:
                if add_danh_sach_den(conn, so_bien.upper(), ly_do, muc_do, ngay_het):
                    st.success("Đã thêm vào danh sách đen.")
                else:
                    st.error("Lỗi thêm vào danh sách.")
            else:
                st.warning("Vui lòng nhập số biển.")
    
    st.subheader("Danh sách xe cấm/theo dõi")
    data = fetch_danh_sach_den(conn)
    
    if data:
        df = pd.DataFrame(data, columns=["ID", "Số biển", "Lý do", "Mức độ", "Ngày tạo", "Ngày hết hiệu lực", "Trạng thái"])
        st.dataframe(df, use_container_width=True)
        
        id_xoa = st.selectbox("Chọn ID để xóa", [row[0] for row in data])
        if st.button("Xóa khỏi danh sách"):
            if xoa_danh_sach_den(conn, id_xoa):
                st.success("Đã xóa khỏi danh sách.")
                st.rerun()
    else:
        st.info("Danh sách trống.")
    
    conn.close()


# ===== TRANG VI PHẠM =====
def render_vi_pham_page() -> None:
    """Trang quản lý vi phạm."""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #F18F01 0%, #D62828 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0;'>⚠️ Quản lý vi phạm</h1>
        <p style='color: #E0E0E0; margin: 10px 0 0 0;'>Ghi nhận và xử lý vi phạm</p>
    </div>
    """, unsafe_allow_html=True)
    
    conn = get_db_connection()
    if not conn:
        st.stop()
    
    st.markdown("### ➕ Ghi nhận vi phạm")
    with st.form("form_them_vi_pham"):
        col1, col2 = st.columns(2)
        with col1:
            so_bien = st.text_input("📍 Số biển")
            loai_vi_pham = st.selectbox("Loại vi phạm", 
                ["nợ phí gửi xe", "vượt quá giới hạn lần vào/ra", "biển số không hợp lệ", 
                 "tài xế vi phạm giao thông", "khác"])
        
        with col2:
            muc_phat = st.number_input("Mức phạt (VNĐ)", value=0.0, min_value=0.0)
        
        if st.form_submit_button("Thêm vi phạm"):
            if so_bien:
                if add_vi_pham(conn, so_bien.upper(), loai_vi_pham, muc_phat):
                    st.success("Đã thêm vi phạm.")
                else:
                    st.error("Lỗi thêm vi phạm.")
            else:
                st.warning("Vui lòng nhập số biển.")
    
    st.subheader("Danh sách vi phạm")
    so_bien_filter = st.text_input("Lọc theo biển số (tùy chọn)")
    data = fetch_vi_pham(conn, so_bien_filter.strip().upper() if so_bien_filter else None)
    
    if data:
        df = pd.DataFrame(data, columns=["ID", "Số biển", "Loại", "Mức phạt", "Trạng thái", "Ngày phát hiện", "Ngày xử lý"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Chưa có vi phạm nào.")
    
    conn.close()


# ===== TRANG THANH TOÁN =====
def render_thanh_toan_page() -> None:
    """Trang quản lý thanh toán."""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #06A77D 0%, #2E86AB 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0;'>💳 Quản lý thanh toán</h1>
        <p style='color: #E0E0E0; margin: 10px 0 0 0;'>Xử lý các khoản thanh toán</p>
    </div>
    """, unsafe_allow_html=True)
    
    conn = get_db_connection()
    if not conn:
        st.stop()
    
    st.markdown("### ➕ Tạo hóa đơn thanh toán")
    with st.form("form_them_thanh_toan"):
        col1, col2 = st.columns(2)
        with col1:
            so_bien = st.text_input("📍 Số biển")
            so_tien = st.number_input("💰 Số tiền (VNĐ)", value=0.0, min_value=0.0)
        
        with col2:
            loai = st.selectbox("Loại thanh toán", ["giu_xe", "vi_pham", "khac"])
            phuong_thuc = st.selectbox("Phương thức", ["tien_mat", "the_tin_dung", "ck_ngan_hang", "khac"])
        
        if st.form_submit_button("Tạo hóa đơn"):
            if so_bien and so_tien > 0:
                if add_thanh_toan(conn, so_bien.upper(), so_tien, loai, phuong_thuc):
                    st.success("Đã tạo hóa đơn.")
                else:
                    st.error("Lỗi tạo hóa đơn.")
            else:
                st.warning("Vui lòng nhập đầy đủ thông tin.")
    
    st.subheader("Danh sách thanh toán")
    so_bien_filter = st.text_input("Lọc theo biển số (tùy chọn)")
    data = fetch_thanh_toan(conn, so_bien_filter.strip().upper() if so_bien_filter else None)
    
    if data:
        df = pd.DataFrame(data, columns=["ID", "Số biển", "Số tiền", "Loại", "Phương thức", "Trạng thái", "Ngày tạo", "Ngày thanh toán"])
        st.dataframe(df, use_container_width=True)
        
        # Cập nhật thanh toán
        st.subheader("Cập nhật trạng thái thanh toán")
        id_thanh_toan = st.selectbox("Chọn hóa đơn", [row[0] for row in data])
        trang_thai_moi = st.selectbox("Trạng thái mới", ["chua_thanh_toan", "da_thanh_toan", "huy"])
        
        if st.button("Cập nhật"):
            if cap_nhat_thanh_toan(conn, id_thanh_toan, trang_thai_moi, "NOW()"):
                st.success("Đã cập nhật trạng thái.")
                st.rerun()
    else:
        st.info("Chưa có hóa đơn nào.")
    
    conn.close()


# ===== TRANG THỐNG KÊ & BÁO CÁO =====
def render_thong_ke_page() -> None:
    """Trang thống kê và báo cáo."""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #2E86AB 0%, #06A77D 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0;'>📊 Thống kê & báo cáo</h1>
        <p style='color: #E0E0E0; margin: 10px 0 0 0;'>Phân tích dữ liệu hệ thống</p>
    </div>
    """, unsafe_allow_html=True)
    
    conn = get_db_connection()
    if not conn:
        st.stop()
    
    # Thống kê tổng quát
    st.markdown("### 📊 Thống kê tổng quát")
    thong_ke = get_thong_ke_tong_quat(conn)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🚗 Xe đang hoạt động", thong_ke["so_xe_active"])
    with col2:
        st.metric("⚠️ Xe cảnh báo", thong_ke["so_xe_canh_bao"])
    with col3:
        st.metric("⚠️ Vi phạm chưa xử lý", thong_ke["so_vi_pham"])
    with col4:
        st.metric("💰 Doanh thu", f"{thong_ke['doanh_thu']:,.0f} ₫")
    
    st.divider()
    
    # Thống kê ra/vào theo ngày
    st.markdown("### 📈 Lưu lượng xe ra/vào")
    df_ra_vao = get_thong_ke_ra_vao_theo_ngay(conn)
    
    if not df_ra_vao.empty:
        # Vẽ biểu đồ
        st.bar_chart(df_ra_vao.set_index("Ngày"))
        st.dataframe(df_ra_vao, use_container_width=True)
    else:
        st.info("Chưa có dữ liệu.")
    
    conn.close()


# ===== TRANG TRA CỨU BIỂN SỐ =====
def render_tra_cuu_bienso_page() -> None:
    """Trang tra cứu thông tin xe theo biển số."""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0;'>🔍 Tra cứu thông tin xe</h1>
        <p style='color: #E0E0E0; margin: 10px 0 0 0;'>Tìm kiếm bằng biển số, ảnh hoặc camera</p>
    </div>
    """, unsafe_allow_html=True)
    
    conn = get_db_connection()
    if not conn:
        st.stop()
    
    # Cấu hình sự kiện
    st.markdown("### ⚙️ Cấu hình sự kiện")
    loai_su_kien = st.selectbox("📌 Loại sự kiện", ["VAO", "RA"], index=0)
    
    st.divider()
    
    # Hai cách nhập: Tìm kiếm trực tiếp hoặc quét ảnh/camera
    st.markdown("### 🔎 Chọn phương thức tra cứu")
    tab1, tab2, tab3 = st.tabs(["🔤 Nhập biển số", "📁 Tải ảnh", "📷 Camera"])
    
    with tab1:
        st.markdown("#### Tìm kiếm trực tiếp")
        so_bien = st.text_input("📍 Nhập số biển", placeholder="Ví dụ: 51A-123.45")
        
        if st.button("🔍 Tra cứu", key="btn_tracuu_direct", use_container_width=True):
            if so_bien:
                info = get_info_xe_toan_bo(conn, so_bien)
                
                if not info["bienso"]:
                    st.error(f"❌ Không tìm thấy biển số: {so_bien}")
                else:
                    # Hiển thị thông tin cơ bản
                    st.success(f"✅ Tìm thấy biển số: {so_bien}")
                    
                    # Kiểm tra sự kiện xen kẽ VAO/RA
                    # Lấy loại sự kiện được chọn (từ cấu hình ở đầu trang)
                    # Kiểm tra từ loại sự kiện được chọn trong cấu hình
                    is_valid, msg_validation = validate_su_kien_xen_ke(conn, so_bien, loai_su_kien)
                    
                    if is_valid:
                        st.info(msg_validation)
                    else:
                        st.warning(msg_validation)
                        st.stop()
                    
                    # Kiểm tra cảnh báo
                    if info["danh_sach_den"]:
                        st.warning(f"⚠️ **XE CÓ TRONG DANH SÁCH ĐEN** - Lý do: {info['danh_sach_den']['ly_do']}")
                    
                    # Thông tin chủ xe
                    st.subheader("📋 Thông tin chủ xe")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Chủ xe:** {info['bienso']['chu_xe']}")
                    with col2:
                        st.write(f"**SĐT:** {info['bienso']['sdt'] or 'N/A'}")
                    with col3:
                        st.write(f"**Ngày đăng ký:** {info['bienso']['ngay_dang_ky']}")
                    
                    # Thông tin xe
                    if info["chi_tiet"]:
                        st.subheader("🚗 Thông tin chi tiết xe")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Loại xe:** {info['chi_tiet']['loai_xe']}")
                        with col2:
                            st.write(f"**Hãng xe:** {info['chi_tiet']['hang_xe'] or 'N/A'}")
                        with col3:
                            st.write(f"**Màu:** {info['chi_tiet']['mau_xe'] or 'N/A'}")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Năm SX:** {info['chi_tiet']['nam_sx'] or 'N/A'}")
                        with col2:
                            st.write(f"**Mã khung:** {info['chi_tiet']['ma_khung'] or 'N/A'}")
                        with col3:
                            st.write(f"**Mã máy:** {info['chi_tiet']['ma_may'] or 'N/A'}")
                    
                    # Thống kê ra/vào
                    st.subheader("📊 Thống kê ra/vào")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Tổng lần vào", info["tong_lan_vao"])
                    with col2:
                        st.metric("Tổng lần ra", info["tong_lan_ra"])
                    
                    # Vi phạm
                    if info["vi_pham"]:
                        st.subheader("⚠️ Vi phạm")
                        for vp in info["vi_pham"]:
                            status_color = "🔴" if vp["trang_thai"] == "chua_xu_ly" else "🟢"
                            st.write(f"{status_color} **{vp['loai']}** - Phạt: {vp['muc_phat']:,.0f} ₫ - {vp['trang_thai']}")
                    
                    # Thanh toán chưa thanh toán
                    if info["thanh_toan"]:
                        thua_toan = [t for t in info["thanh_toan"] if t["trang_thai"] == "chua_thanh_toan"]
                        if thua_toan:
                            st.subheader("💰 Hóa đơn chưa thanh toán")
                            tong_no = sum(t["so_tien"] for t in thua_toan)
                            st.metric("Tổng nợ", f"{tong_no:,.0f} ₫")
                            for tt in thua_toan:
                                st.write(f"- {tt['loai']}: {tt['so_tien']:,.0f} ₫ ({tt['ngay']})")
                    
                    # Lịch sử gần nhất
                    if info["lichsu_gan_nhat"]:
                        st.subheader("📅 Lịch sử 20 lần gần nhất")
                        lichsu_df = pd.DataFrame([
                            {"Thời gian": lsu["thoi_gian"], "Loại sự kiện": lsu["loai"]}
                            for lsu in info["lichsu_gan_nhat"]
                        ])
                        st.dataframe(lichsu_df, use_container_width=True)
            else:
                st.warning("Vui lòng nhập số biển.")
    
    with tab2:
        st.markdown("#### 📁 Quét từ ảnh biển số")
        
        # Tùy chọn tiền xử lý
        use_preprocessing_tracuu = st.checkbox("🔧 Tiền xử lý ảnh", value=True, key="preprocess_tracuu")
        
        uploaded_file = st.file_uploader("Tải ảnh biển số (jpg, png)", type=["jpg", "jpeg", "png"], key="upload_tracuu")
        
        # Initialize session state
        if "tracuu_result_tab2" not in st.session_state:
            st.session_state.tracuu_result_tab2 = None
        
        if uploaded_file is not None:
            image_bytes = uploaded_file.read()
            pil_image = Image.open(io.BytesIO(image_bytes))
            image_bgr = pil_to_bgr(pil_image)
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("#### 📸 Ảnh gốc")
                st.image(pil_image, use_container_width=True)
            
            with col_right:
                st.markdown("#### ✨ Nhận dạng")
                if st.button("🔍 Quét biển số", key="btn_scan_image", use_container_width=True):
                    with st.spinner("🔄 Đang xử lý và quét biển số..."):
                        # Tiền xử lý nếu được bật
                        processed_bgr = preprocess_image(image_bgr) if use_preprocessing_tracuu else image_bgr
                        
                        texts_with_conf, boxes = read_text_and_boxes(processed_bgr)
                        output_bgr = draw_boxes(processed_bgr, boxes, texts_with_conf)
                        output_pil = bgr_to_pil(output_bgr)
                        
                        st.image(output_pil, use_container_width=True)
                        
                        if texts_with_conf:
                            texts = [t[0] for t in texts_with_conf]
                            plate_text = " - ".join(texts).strip()
                            st.success(f"✅ Phát hiện: **{plate_text}**")
                            
                            # Lưu vào session state
                            st.session_state.detected_plate_tab2 = plate_text
                            st.session_state.texts_with_conf_tab2 = texts_with_conf
                            st.session_state.pil_image_tab2 = pil_image
                        else:
                            st.warning("⚠️ Không phát hiện được biển số nào. Thử ảnh khác.")
                            st.session_state.detected_plate_tab2 = None
            
            # Hiển thị phần chỉnh sửa nếu đã có kết quả
            if hasattr(st.session_state, 'detected_plate_tab2') and st.session_state.detected_plate_tab2:
                st.divider()
                
                # Hiển thị confidence
                with st.expander("📊 Chi tiết nhận dạng"):
                    for text, conf in st.session_state.texts_with_conf_tab2:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{text}**")
                        with col2:
                            st.metric("Độ tin cậy", f"{conf*100:.1f}%")
                
                # Cho phép chỉnh sửa biển số
                st.markdown("#### ✏️ Chỉnh sửa biển số (nếu cần)")
                plate_corrected = st.text_input(
                    "Biển số (nếu quét sai, hãy chỉnh lại):", 
                    value=st.session_state.detected_plate_tab2,
                    key="correct_plate_tab2"
                )
                
                if st.button("✅ Xác nhận và tra cứu", key="confirm_tab2", use_container_width=True):
                    with st.spinner("🔍 Đang tra cứu..."):
                        # Tra cứu ngay
                        info = get_info_xe_toan_bo(conn, plate_corrected)
                        
                        # Kiểm tra sự kiện xen kẽ VAO/RA
                        is_valid, msg_validation = validate_su_kien_xen_ke(conn, plate_corrected, loai_su_kien)
                        
                        if not is_valid:
                            st.warning(msg_validation)
                            st.stop()
                        
                        # Lưu ảnh vào database
                        image_path = save_plate_image(st.session_state.pil_image_tab2, plate_corrected, loai_su_kien)
                        
                        # Lưu kết quả vào session state
                        st.session_state.tracuu_result_tab2 = {
                            'info': info,
                            'plate': plate_corrected,
                            'image_path': image_path,
                            'validation_msg': msg_validation
                        }
                        
                        # Ghi lịch sử
                        if not info["bienso"]:
                            try:
                                with conn.cursor() as cursor:
                                    cursor.execute(
                                        """
                                        INSERT INTO lichsu (so_bien, loai_su_kien, duong_dan_anh, ghi_chu)
                                        VALUES (%s, %s, %s, %s)
                                        """,
                                        (plate_corrected, "VAO", image_path, "Biển số chưa đăng ký"),
                                    )
                                    conn.commit()
                            except mysql.connector.Error as err:
                                st.error(f"Lỗi ghi lịch sử: {err}")
                        else:
                            try:
                                with conn.cursor() as cursor:
                                    cursor.execute(
                                        """
                                        INSERT INTO lichsu (so_bien, loai_su_kien, duong_dan_anh)
                                        VALUES (%s, %s, %s)
                                        """,
                                        (plate_corrected, "VAO", image_path),
                                    )
                                    conn.commit()
                            except mysql.connector.Error as err:
                                st.error(f"Lỗi ghi lịch sử: {err}")
                
                # Hiển thị kết quả tra cứu
                if st.session_state.tracuu_result_tab2:
                    st.divider()
                    result = st.session_state.tracuu_result_tab2
                    info = result['info']
                    plate_corrected = result['plate']
                    
                    # Hiển thị thông báo validation
                    if 'validation_msg' in result:
                        st.info(result['validation_msg'])
                    
                    if not info["bienso"]:
                        st.error(f"❌ Không tìm thấy biển số: {plate_corrected}")
                        st.info("ℹ️ Đã ghi lịch sử xe lạ vào hệ thống.")
                    else:
                        st.success(f"✅ Phát hiện: **{plate_corrected}**")
                        
                        # Kiểm tra cảnh báo
                        if info["danh_sach_den"]:
                            st.warning(f"⚠️ **XE CÓ TRONG DANH SÁCH ĐEN** - {info['danh_sach_den']['ly_do']}")
                        
                        # Thông tin chủ xe
                        st.markdown("### 📋 Thông tin chủ xe")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.info(f"**Chủ xe:** {info['bienso']['chu_xe']}")
                        with col2:
                            st.info(f"**SĐT:** {info['bienso']['sdt'] or 'N/A'}")
                        with col3:
                            st.info(f"**Trạng thái:** {'✅ Hoạt động' if info['bienso']['trang_thai'] == 1 else '❌ Ngưng'}")
                        
                        # Thống kê ra vào
                        st.markdown("### 📊 Thống kê ra/vào")
                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            st.metric("🚗 Tổng lần vào", info["tong_lan_vao"])
                        with col_m2:
                            st.metric("🚪 Tổng lần ra", info["tong_lan_ra"])
                        
                        # Vi phạm
                        if info["vi_pham"]:
                            st.markdown("### ⚠️ Vi phạm")
                            st.warning(f"**Có {len(info['vi_pham'])} vi phạm chưa xử lý**")
                            for vp in info["vi_pham"][:3]:
                                st.write(f"- {vp['loai']}: {vp['muc_phat']:,.0f} ₫ ({vp['trang_thai']})")
                        
                        # Nợ tiền
                        if info["thanh_toan"]:
                            chua_tt = [t for t in info["thanh_toan"] if t["trang_thai"] == "chua_thanh_toan"]
                            if chua_tt:
                                st.markdown("### 💰 Công nợ")
                                tong_no = sum(t["so_tien"] for t in chua_tt)
                                st.error(f"**Tổng nợ: {tong_no:,.0f} ₫**")
    
    with tab3:
        st.markdown("#### 📷 Chụp ảnh từ camera")
        
        # Tùy chọn tiền xử lý
        use_preprocessing_cam_tracuu = st.checkbox("🔧 Tiền xử lý ảnh camera", value=True, key="preprocess_cam_tracuu")
        
        camera_photo = st.camera_input("Chụp ảnh biển số")
        
        # Initialize session state
        if "tracuu_result_tab3" not in st.session_state:
            st.session_state.tracuu_result_tab3 = None
        
        if camera_photo is not None:
            image_bytes = camera_photo.read()
            pil_image = Image.open(io.BytesIO(image_bytes))
            image_bgr = pil_to_bgr(pil_image)
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("#### 📸 Ảnh chụp")
                st.image(pil_image, use_container_width=True)
            
            with col_right:
                st.markdown("#### ✨ Nhận dạng")
                if st.button("🔍 Quét biển số", key="btn_scan_camera", use_container_width=True):
                    with st.spinner("🔄 Đang xử lý và quét biển số..."):
                        # Tiền xử lý nếu được bật
                        processed_bgr = preprocess_image(image_bgr) if use_preprocessing_cam_tracuu else image_bgr
                        
                        texts_with_conf, boxes = read_text_and_boxes(processed_bgr)
                        output_bgr = draw_boxes(processed_bgr, boxes, texts_with_conf)
                        output_pil = bgr_to_pil(output_bgr)
                        
                        st.image(output_pil, use_container_width=True)
                        
                        if texts_with_conf:
                            texts = [t[0] for t in texts_with_conf]
                            plate_text = " - ".join(texts).strip()
                            st.success(f"✅ Phát hiện: **{plate_text}**")
                            
                            # Lưu vào session state
                            st.session_state.detected_plate_tab3 = plate_text
                            st.session_state.texts_with_conf_tab3 = texts_with_conf
                            st.session_state.pil_image_tab3 = pil_image
                        else:
                            st.warning("⚠️ Không phát hiện được biển số nào. Thử chụp lại.")
                            st.session_state.detected_plate_tab3 = None
            
            # Hiển thị phần chỉnh sửa nếu đã có kết quả
            if hasattr(st.session_state, 'detected_plate_tab3') and st.session_state.detected_plate_tab3:
                st.divider()
                
                # Hiển thị confidence
                with st.expander("📊 Chi tiết nhận dạng"):
                    for text, conf in st.session_state.texts_with_conf_tab3:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{text}**")
                        with col2:
                            st.metric("Độ tin cậy", f"{conf*100:.1f}%")
                
                # Cho phép chỉnh sửa biển số
                st.markdown("#### ✏️ Chỉnh sửa biển số (nếu cần)")
                plate_corrected = st.text_input(
                    "Biển số (nếu quét sai, hãy chỉnh lại):", 
                    value=st.session_state.detected_plate_tab3,
                    key="correct_plate_tab3"
                )
                
                if st.button("✅ Xác nhận và tra cứu", key="confirm_tab3", use_container_width=True):
                    with st.spinner("🔍 Đang tra cứu..."):
                        # Tra cứu ngay
                        info = get_info_xe_toan_bo(conn, plate_corrected)
                        
                        # Kiểm tra sự kiện xen kẽ VAO/RA
                        is_valid, msg_validation = validate_su_kien_xen_ke(conn, plate_corrected, loai_su_kien)
                        
                        if not is_valid:
                            st.warning(msg_validation)
                            st.stop()
                        
                        # Lưu ảnh vào database
                        image_path = save_plate_image(st.session_state.pil_image_tab3, plate_corrected, loai_su_kien)
                        
                        # Lưu kết quả vào session state
                        st.session_state.tracuu_result_tab3 = {
                            'info': info,
                            'plate': plate_corrected,
                            'image_path': image_path,
                            'validation_msg': msg_validation
                        }
                        
                        # Ghi lịch sử
                        if not info["bienso"]:
                            try:
                                with conn.cursor() as cursor:
                                    cursor.execute(
                                        """
                                        INSERT INTO lichsu (so_bien, loai_su_kien, duong_dan_anh, ghi_chu)
                                        VALUES (%s, %s, %s, %s)
                                        """,
                                        (plate_corrected, "VAO", image_path, "Biển số chưa đăng ký"),
                                    )
                                    conn.commit()
                            except mysql.connector.Error as err:
                                st.error(f"Lỗi ghi lịch sử: {err}")
                        else:
                            try:
                                with conn.cursor() as cursor:
                                    cursor.execute(
                                        """
                                        INSERT INTO lichsu (so_bien, loai_su_kien, duong_dan_anh)
                                        VALUES (%s, %s, %s)
                                        """,
                                        (plate_corrected, "VAO", image_path),
                                    )
                                    conn.commit()
                            except mysql.connector.Error as err:
                                st.error(f"Lỗi ghi lịch sử: {err}")
                
                # Hiển thị kết quả tra cứu
                if st.session_state.tracuu_result_tab3:
                    st.divider()
                    result = st.session_state.tracuu_result_tab3
                    info = result['info']
                    plate_corrected = result['plate']
                    
                    # Hiển thị thông báo validation
                    if 'validation_msg' in result:
                        st.info(result['validation_msg'])
                    
                    if not info["bienso"]:
                        st.error(f"❌ Không tìm thấy biển số: {plate_corrected}")
                        st.info("ℹ️ Đã ghi lịch sử xe lạ vào hệ thống.")
                    else:
                        st.success(f"✅ Phát hiện: **{plate_corrected}**")
                        
                        # Kiểm tra cảnh báo
                        if info["danh_sach_den"]:
                            st.warning(f"⚠️ **XE CÓ TRONG DANH SÁCH ĐEN** - {info['danh_sach_den']['ly_do']}")
                        
                        # Thông tin chủ xe
                        st.markdown("### 📋 Thông tin chủ xe")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.info(f"**Chủ xe:** {info['bienso']['chu_xe']}")
                        with col2:
                            st.info(f"**SĐT:** {info['bienso']['sdt'] or 'N/A'}")
                        with col3:
                            st.info(f"**Trạng thái:** {'✅ Hoạt động' if info['bienso']['trang_thai'] == 1 else '❌ Ngưng'}")
                        
                        # Thống kê ra vào
                        st.markdown("### 📊 Thống kê ra/vào")
                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            st.metric("🚗 Tổng lần vào", info["tong_lan_vao"])
                        with col_m2:
                            st.metric("🚪 Tổng lần ra", info["tong_lan_ra"])
                        
                        # Vi phạm
                        if info["vi_pham"]:
                            st.markdown("### ⚠️ Vi phạm")
                            st.warning(f"**Có {len(info['vi_pham'])} vi phạm chưa xử lý**")
                            for vp in info["vi_pham"][:3]:
                                st.write(f"- {vp['loai']}: {vp['muc_phat']:,.0f} ₫ ({vp['trang_thai']})")
                        
                        # Nợ tiền
                        if info["thanh_toan"]:
                            chua_tt = [t for t in info["thanh_toan"] if t["trang_thai"] == "chua_thanh_toan"]
                            if chua_tt:
                                st.markdown("### 💰 Công nợ")
                                tong_no = sum(t["so_tien"] for t in chua_tt)
                                st.error(f"**Tổng nợ: {tong_no:,.0f} ₫**")
    
    conn.close()


# --- GIAO DIỆN CHÍNH ---

# Header
st.markdown("""
<div style='text-align: center; padding: 20px 0; background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%); border-radius: 10px; margin-bottom: 20px;'>
    <h1 style='color: white; margin: 0; font-size: 2.5em;'>🚗 Hệ Thống Nhận Dạng Biển Số Xe</h1>
    <p style='color: #E0E0E0; margin: 10px 0 0 0; font-size: 1.1em;'>Sử dụng AI OCR - EasyOCR</p>
</div>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "login_error" not in st.session_state:
    st.session_state.login_error = ""

if not st.session_state.logged_in:
    # Login page styling
    st.markdown("""
    <div style='max-width: 400px; margin: 50px auto; padding: 40px; background: linear-gradient(135deg, #f5f9fc 0%, #eff4f8 100%); border-radius: 10px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); border: 2px solid #2E86AB;'>
    <h2 style='color: #2E86AB; text-align: center; margin-bottom: 30px;'>🔐 Đăng Nhập</h2>
    """, unsafe_allow_html=True)
    
    username = st.text_input("👤 Tài khoản", key="username_input")
    password = st.text_input("🔑 Mật khẩu", type="password", key="password_input")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Đăng Nhập", use_container_width=True):
            admin_user, admin_pass = get_auth_config()
            if username == admin_user and password == admin_pass:
                st.session_state.logged_in = True
                st.session_state.login_error = ""
                st.success("✅ Đăng nhập thành công!")
                st.rerun()
            else:
                st.session_state.login_error = "❌ Sai tài khoản hoặc mật khẩu."

    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.session_state.login_error:
        st.error(st.session_state.login_error)

    st.info("ℹ️ Bạn có thể cấu hình tài khoản trong secrets hoặc biến môi trường ADMIN_USER/ADMIN_PASS.")
else:
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 20px 0; border-bottom: 2px solid white;'>
            <h2 style='color: white; margin: 0;'>🎯 Menu Chính</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='padding: 10px 0;'></div>", unsafe_allow_html=True)
        
        menu = st.radio("", [
            "🚗 Quản lý xe", 
            "🎯 Nhận dạng biển số",
            "🔍 Tra cứu biển số",
            "📋 Chi tiết xe",
            "🚫 Danh sách đen",
            "⚠️ Vi phạm",
            "💳 Thanh toán",
            "📊 Thống kê & báo cáo"
        ], index=0)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("ℹ️ Thông tin", use_container_width=True):
                st.info("Hệ thống quản lý nhận dạng biển số xe v1.0")
        with col2:
            if st.button("🚪 Đăng xuất", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()

    if menu == "🚗 Quản lý xe":
        render_manage_page()
    elif menu == "🎯 Nhận dạng biển số":
        render_ocr_page()
    elif menu == "🔍 Tra cứu biển số":
        render_tra_cuu_bienso_page()
    elif menu == "📋 Chi tiết xe":
        render_chi_tiet_xe_page()
    elif menu == "🚫 Danh sách đen":
        render_danh_sach_den_page()
    elif menu == "⚠️ Vi phạm":
        render_vi_pham_page()
    elif menu == "💳 Thanh toán":
        render_thanh_toan_page()
    else:
        render_thong_ke_page()