import streamlit as st
import os
import pandas as pd
from PIL import Image
import math
import requests

# Tự động nạp cấu hình từ tệp .env (nếu có)
def load_env():
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

load_env()

# ==============================================================================
# 1. PAGE CONFIGURATION & CUSTOM STYLING
# ==============================================================================
st.set_page_config(
    page_title="Solar 24h - Giải pháp Điện Năng Lượng Mặt Trời & Tài Chính",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium UI Styling: Navy Blue (#0A2540), Leaf Green (#2ECC71), Accent Gold (#F1C40F)
st.markdown("""
<style>
    /* Import modern Outfit font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Core containers styling */
    .custom-card {
        background-color: #ffffff;
        padding: 22px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(10, 37, 64, 0.05);
        border: 1px solid #E2E8F0;
        border-left: 5px solid #2ECC71;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .custom-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(46, 204, 113, 0.12);
    }
    
    .hero-container {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        padding: 35px;
        border-radius: 20px;
        border: 1px solid #A5D6A7;
        margin-bottom: 25px;
    }
    
    .section-header {
        color: #0A2540;
        border-left: 5px solid #2ECC71;
        padding-left: 12px;
        margin-top: 30px;
        margin-bottom: 20px;
        font-weight: 700;
        font-size: 1.6rem;
    }
    
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(10, 37, 64, 0.04);
        border-bottom: 4px solid #2ECC71;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0A2540;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #718096;
        margin-top: 5px;
        font-weight: 500;
    }
    
    /* Submit button styling */
    div.stButton > button:first-child {
        background-color: #2ECC71;
        color: white;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        border: none;
        transition: background-color 0.3s;
    }
    /* Phong cách hóa st.tabs thành dạng nút bấm lớn nổi bật */
    div[data-testid="stTabs"] {
        border-bottom: 3px solid #2ECC71;
        margin-bottom: 25px;
    }
    div[data-testid="stTabs"] button {
        padding: 14px 28px !important;
        border-radius: 12px 12px 0 0 !important;
        transition: all 0.2s ease-in-out !important;
        background-color: #F8F9FA !important;
        margin-right: 8px !important;
        border: 1px solid #E2E8F0 !important;
        border-bottom: none !important;
    }
    /* Ghi đè trực tiếp kích thước chữ của thẻ p/span bên trong nút bấm của Streamlit */
    div[data-testid="stTabs"] button p, 
    div[data-testid="stTabs"] button span,
    div[data-testid="stTabs"] button div,
    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] span {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        color: #0A2540 !important;
        transition: color 0.2s ease-in-out !important;
    }
    /* Hiệu ứng khi di chuột qua */
    div[data-testid="stTabs"] button:hover {
        background-color: #27AE60 !important;
        border-color: #27AE60 !important;
    }
    div[data-testid="stTabs"] button:hover p,
    div[data-testid="stTabs"] button:hover span {
        color: #FFFFFF !important;
    }
    /* Khi tab được chọn */
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background-color: #2ECC71 !important;
        border-color: #2ECC71 !important;
        box-shadow: 0 4px 15px rgba(46, 204, 113, 0.25) !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] p,
    div[data-testid="stTabs"] button[aria-selected="true"] span {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. OFFICIAL DATABASE & HELPER MATHEMATICS
# ==============================================================================

# EVN Retail Electricity Tariff 2026 (Progressive Brackets)
EVN_BRACKETS = [
    {"name": "Bậc 1", "min": 0, "max": 50, "price": 1984},
    {"name": "Bậc 2", "min": 51, "max": 100, "price": 2050},
    {"name": "Bậc 3", "min": 101, "max": 200, "price": 2380},
    {"name": "Bậc 4", "min": 201, "max": 300, "price": 2998},
    {"name": "Bậc 5", "min": 301, "max": 400, "price": 3350},
    {"name": "Bậc 6", "min": 401, "max": float('inf'), "price": 3460}
]
VAT_RATE = 0.08  # 8% VAT

# Official Solar 24h Pricing Database (Gói SOLAR F1 - F10)
SOLAR_PACKAGES = {
    "SOLAR F1": {
        "kwp": 2.3,
        "panels": 4,
        "battery": "2.5 kWh (BSB)",
        "inverter": "Luxpower SNA 5000W (Bảo hành 3 năm)",
        "price": 47800000,
        "desc": "Phù hợp hộ gia đình nhỏ có hóa đơn điện dưới 500.000đ/tháng.",
        "range_min": 0,
        "range_max": 500000,
        "checklist": [
            "4 Tấm pin năng lượng mặt trời AE SOLAR 2 Mặt Kính (Đức) 580W",
            "1 Biến tần Inverter LUXPOWER SNA 5000W",
            "1 Pin LITHIUM lưu trữ BSB 51.2V/50Ah (2.5 kWh)",
            "1 Tủ điện Hybrid chuyên dụng",
            "Trọn bộ vật tư phụ lắp đặt giàn pin",
            "Trọn bộ dây dẫn điện DC/AC và dây tiếp địa",
            "Chi phí vận chuyển & nhân công lắp đặt hoàn thiện"
        ],
        "gen_min": 6,
        "gen_max": 10
    },
    "SOLAR F2": {
        "kwp": 4.6,
        "panels": 8,
        "battery": "5 kWh (BSB)",
        "inverter": "Luxpower SNA 5000W (Bảo hành 3 năm)",
        "price": 68500000,
        "desc": "Phù hợp hộ gia đình có hóa đơn điện từ 500.000đ đến 1.000.000đ/tháng.",
        "range_min": 500000,
        "range_max": 1000000,
        "checklist": [
            "8 Tấm pin năng lượng mặt trời AE SOLAR 2 Mặt Kính (Đức) 580W",
            "1 Biến tần Inverter LUXPOWER SNA 5000W",
            "1 Pin LITHIUM lưu trữ BSB 51.2V/100Ah (5 kWh)",
            "1 Tủ điện Hybrid chuyên dụng",
            "Trọn bộ vật tư phụ lắp đặt giàn pin",
            "Trọn bộ dây dẫn điện DC/AC và dây tiếp địa",
            "Chi phí vận chuyển & nhân công lắp đặt hoàn thiện"
        ],
        "gen_min": 10,
        "gen_max": 18
    },
    "SOLAR F3": {
        "kwp": 5.8,
        "panels": 10,
        "battery": "10 kWh (LS Battery)",
        "inverter": "SVE 6kW (Bảo hành 5 năm)",
        "price": 88000000,
        "desc": "Phù hợp hộ gia đình có hóa đơn điện từ 1.000.000đ đến 1.500.000đ/tháng.",
        "range_min": 1000000,
        "range_max": 1500000,
        "checklist": [
            "10 Tấm pin năng lượng mặt trời AE SOLAR 2 Mặt Kính (Đức) 580W",
            "1 Biến tần Inverter SVE 6kW",
            "1 Pin LITHIUM lưu trữ LS BATTERY 51.2V/200Ah (10 kWh)",
            "1 Tủ điện Hybrid chuyên dụng",
            "Trọn bộ vật tư phụ lắp đặt giàn pin",
            "Trọn bộ dây dẫn điện DC/AC và dây tiếp địa",
            "Chi phí vận chuyển & nhân công lắp đặt hoàn thiện"
        ],
        "gen_min": 15,
        "gen_max": 28
    },
    "SOLAR F4": {
        "kwp": 6.9,
        "panels": 12,
        "battery": "16 kWh (EJOR)",
        "inverter": "SVE 6kW (Bảo hành 5 năm)",
        "price": 104700000,
        "desc": "Phù hợp hộ kinh doanh/gia đình có hóa đơn điện từ 1.500.000đ đến 2.000.000đ/tháng.",
        "range_min": 1500000,
        "range_max": 2000000,
        "checklist": [
            "12 Tấm pin năng lượng mặt trời AE SOLAR 2 Mặt Kính (Đức) 580W",
            "1 Biến tần Inverter SVE 6kW",
            "1 Pin LITHIUM lưu trữ EJOR 51.2V/314Ah (16 kWh)",
            "1 Tủ điện Hybrid chuyên dụng (nâng cấp)",
            "Trọn bộ vật tư phụ lắp đặt giàn pin",
            "Trọn bộ dây dẫn điện DC/AC và dây tiếp địa",
            "Chi phí vận chuyển & nhân công lắp đặt hoàn thiện"
        ],
        "gen_min": 20,
        "gen_max": 30
    },
    "SOLAR F5": {
        "kwp": 8.1,
        "panels": 14,
        "battery": "16 kWh (EJOR hoặc LS)",
        "inverter": "LUXPOWER 6.5 PRO (Bảo hành 6 năm)",
        "price": 114900000,
        "desc": "Phù hợp gia đình lớn, biệt thự có hóa đơn điện từ 2.000.000đ đến 2.500.000đ/tháng.",
        "range_min": 2000000,
        "range_max": 2500000,
        "checklist": [
            "14 Tấm pin năng lượng mặt trời AE SOLAR 2 Mặt Kính (Đức) 580W",
            "1 Biến tần Inverter HYBRID LUXPOWER 6.5PRO",
            "1 Pin LITHIUM lưu trữ EJOR hoặc LS 51.2V/314Ah (16 kWh)",
            "1 Tủ điện Hybrid chuyên dụng",
            "Trọn bộ vật tư phụ lắp đặt giàn pin",
            "Trọn bộ dây dẫn điện DC/AC và dây tiếp địa",
            "Chi phí vận chuyển & nhân công lắp đặt hoàn thiện"
        ],
        "gen_min": 20,
        "gen_max": 34
    },
    "SOLAR F6": {
        "kwp": 9.3,
        "panels": 16,
        "battery": "16 kWh (EJOR hoặc LS)",
        "inverter": "LUXPOWER 6.5 PRO (Bảo hành 6 năm)",
        "price": 123600000,
        "desc": "Phù hợp hộ gia đình/biệt thự có hóa đơn điện từ 2.500.000đ đến 3.000.000đ/tháng.",
        "range_min": 2500000,
        "range_max": 3000000,
        "checklist": [
            "16 Tấm pin năng lượng mặt trời AE SOLAR 2 Mặt Kính (Đức) 580W",
            "1 Biến tần Inverter HYBRID LUXPOWER 6.5PRO",
            "1 Pin LITHIUM lưu trữ EJOR hoặc LS 51.2V/314Ah (16 kWh)",
            "1 Tủ điện Hybrid chuyên dụng (công suất lớn)",
            "Trọn bộ vật tư phụ lắp đặt giàn pin",
            "Trọn bộ dây dẫn điện DC/AC và dây tiếp địa",
            "Chi phí vận chuyển & nhân công lắp đặt hoàn thiện"
        ],
        "gen_min": 25,
        "gen_max": 40
    },
    "SOLAR F7": {
        "kwp": 11.6,
        "panels": 20,
        "battery": "32 kWh (EJOR hoặc LS)",
        "inverter": "2 x LUXPOWER 6.5 PRO (Chạy song song)",
        "price": 203000000,
        "desc": "Phù hợp cơ sở kinh doanh, kho lạnh có hóa đơn điện từ 3.000.000đ đến 4.000.000đ/tháng.",
        "range_min": 3000000,
        "range_max": 4000000,
        "checklist": [
            "20 Tấm pin năng lượng mặt trời AE SOLAR 2 Mặt Kính (Đức) 580W",
            "2 Biến tần Inverter HYBRID LUXPOWER 6.5PRO chạy song song",
            "2 Pin LITHIUM lưu trữ EJOR hoặc LS 16 kWh (Tổng cộng 32 kWh)",
            "1 Tủ điện Hybrid phân phối chuyên dụng",
            "Trọn bộ vật tư phụ lắp đặt giàn pin cơ cấu chịu bão",
            "Trọn bộ dây dẫn điện DC/AC và dây tiếp địa chuyên dụng",
            "Chi phí vận chuyển & nhân công lắp đặt hoàn thiện"
        ],
        "gen_min": 35,
        "gen_max": 50
    },
    "SOLAR F8": {
        "kwp": 13.9,
        "panels": 24,
        "battery": "32 kWh (EJOR hoặc LS)",
        "inverter": "2 x LUXPOWER 6.5 PRO (Chạy song song)",
        "price": 217900000,
        "desc": "Phù hợp cơ sở sản xuất, kho lạnh lớn có hóa đơn điện từ 4.000.000đ đến 5.000.000đ/tháng.",
        "range_min": 4000000,
        "range_max": 5000000,
        "checklist": [
            "24 Tấm pin năng lượng mặt trời AE SOLAR 2 Mặt Kính (Đức) 580W",
            "2 Biến tần Inverter HYBRID LUXPOWER 6.5PRO chạy song song",
            "2 Pin LITHIUM lưu trữ EJOR hoặc LS 16 kWh (Tổng cộng 32 kWh)",
            "1 Tủ điện Hybrid phân phối chuyên dụng",
            "Trọn bộ vật tư phụ lắp đặt giàn pin cơ cấu chịu bão",
            "Trọn bộ dây dẫn điện DC/AC và dây tiếp địa chuyên dụng",
            "Chi phí vận chuyển & nhân công lắp đặt hoàn thiện"
        ],
        "gen_min": 40,
        "gen_max": 60
    },
    "SOLAR F9": {
        "kwp": 17.4,
        "panels": 30,
        "battery": "32 kWh (EJOR hoặc LS)",
        "inverter": "2 x LUXPOWER 6.5 PRO (Chạy song song)",
        "price": 239000000,
        "desc": "Phù hợp doanh nghiệp vừa, kho lạnh có hóa đơn điện từ 5.000.000đ đến 7.000.000đ/tháng.",
        "range_min": 5000000,
        "range_max": 7000000,
        "checklist": [
            "30 Tấm pin năng lượng mặt trời AE SOLAR 2 Mặt Kính (Đức) 580W",
            "2 Biến tần Inverter HYBRID LUXPOWER 6.5PRO chạy song song",
            "2 Pin LITHIUM lưu trữ EJOR hoặc LS 16 kWh (Tổng cộng 32 kWh)",
            "1 Tủ điện Hybrid phân phối chuyên dụng (3 pha)",
            "Trọn bộ vật tư phụ lắp đặt giàn pin cơ cấu chịu bão",
            "Trọn bộ dây dẫn điện DC/AC và dây tiếp địa chuyên dụng",
            "Chi phí vận chuyển & nhân công lắp đặt hoàn thiện"
        ],
        "gen_min": 50,
        "gen_max": 70
    },
    "SOLAR F10": {
        "kwp": 22.0,
        "panels": 38,
        "battery": "48 kWh (EJOR hoặc LS)",
        "inverter": "3 x LUXPOWER 6.5 PRO (Chạy song song)",
        "price": 329300000,
        "desc": "Hệ thống siêu công suất cho biệt phủ, nhà xưởng lớn có hóa đơn điện trên 7.000.000đ/tháng.",
        "range_min": 7000000,
        "range_max": float('inf'),
        "checklist": [
            "38 Tấm pin năng lượng mặt trời AE SOLAR 2 Mặt Kính (Đức) 580W",
            "3 Biến tần Inverter HYBRID LUXPOWER 6.5PRO chạy song song",
            "3 Pin LITHIUM lưu trữ EJOR hoặc LS 16 kWh (Tổng cộng 48 kWh)",
            "1 Tủ điện Hybrid phân phối công suất lớn",
            "Trọn bộ vật tư phụ lắp đặt giàn pin cơ cấu chịu bão",
            "Trọn bộ dây dẫn điện DC/AC và dây tiếp địa chuyên dụng",
            "Chi phí vận chuyển & nhân công lắp đặt hoàn thiện"
        ],
        "gen_min": 60,
        "gen_max": 90
    }
}

def load_and_show_image(img_path, caption="", width=None):
    """Loads and displays local image safely without crashing."""
    if os.path.exists(img_path):
        try:
            img = Image.open(img_path)
            st.image(img, caption=caption, use_container_width=True if width is None else False, width=width)
            return True
        except Exception:
            st.warning(f"Không thể đọc file ảnh: {os.path.basename(img_path)}")
    return False

def calculate_monthly_electricity_cost(kwh):
    """Calculates progressive tariff retail cost from kWh consumption (EVN 2026)."""
    remaining = kwh
    total_cost = 0
    for bracket in EVN_BRACKETS:
        limit = bracket["max"] - bracket["min"] if bracket["max"] != float('inf') else float('inf')
        if remaining <= 0:
            break
        consumed = min(remaining, limit)
        total_cost += consumed * bracket["price"]
        remaining -= consumed
    # Add 8% VAT
    return total_cost * (1 + VAT_RATE)

def back_calculate_kwh_from_cost(post_tax_cost):
    """Back-calculates kWh consumption from the post-tax electricity bill amount."""
    pre_tax_cost = post_tax_cost / (1 + VAT_RATE)
    kwh = 0
    remaining_cost = pre_tax_cost
    
    for bracket in EVN_BRACKETS:
        limit = bracket["max"] - bracket["min"] if bracket["max"] != float('inf') else float('inf')
        max_bracket_cost = limit * bracket["price"]
        
        if remaining_cost <= max_bracket_cost:
            kwh += remaining_cost / bracket["price"]
            break
        else:
            kwh += limit
            remaining_cost -= max_bracket_cost
            
    return round(kwh, 2)

def calculate_shinhan_installment(loan_amount, term_months):
    """Calculates Shinhan Bank monthly installment using Flat Interest Rate of 0.59% per month."""
    if loan_amount <= 0:
        return 0, 0, 0
    flat_rate = 0.0059  # 0.59% per month
    monthly_interest = loan_amount * flat_rate
    monthly_principal = loan_amount / term_months
    total_monthly = monthly_principal + monthly_interest
    return round(total_monthly), round(monthly_principal), round(monthly_interest)

# ==============================================================================
# 3. HEADER (LOGO & BRANDING)
# ==============================================================================
col_logo, col_title = st.columns([1, 4])

with col_logo:
    logo_path = "Logo Solar 24h.png"
    if os.path.exists(logo_path):
        try:
            logo_img = Image.open(logo_path)
            st.image(logo_img, width=150)
        except Exception:
            st.markdown("<h2 style='color:#2ECC71; margin:0;'>Solar 24h</h2>", unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='color:#2ECC71; margin:0;'>Solar 24h</h2>", unsafe_allow_html=True)

with col_title:
    st.markdown("""
        <div style='padding-top: 15px;'>
            <h1 style='color: #0A2540; margin: 0; font-size: 2.5rem; font-weight: 800;'>SOLAR 24H</h1>
            <p style='color: #2ECC71; font-size: 1.2rem; font-weight: 600; margin: 0; text-transform: uppercase; letter-spacing: 1px;'>
                Giải Pháp Điện Năng Lượng Mặt Trời Trọn Gói
            </p>
        </div>
    """, unsafe_allow_html=True)

st.write("---")

# ==============================================================================
# 4. HERO SECTION
# ==============================================================================
st.markdown("""
<div class='hero-container'>
    <h2 style='color: #0A2540; margin-top: 0; font-weight: 700; font-size: 1.8rem;'>🌿 Kiến Tạo Tương Lai Xanh - Tiết Kiệm Tối Đa Chi Phí</h2>
    <p style='color: #1E5631; font-size: 1.1rem; line-height: 1.6; margin-bottom: 0;'>
        Chào mừng quý khách đến với <b>Solar 24h</b>. Chúng tôi là đơn vị chuyên nghiệp hàng đầu tại miền Tây và toàn quốc, 
        cung cấp các giải pháp điện mặt trời trọn gói chất lượng cao. Với việc ứng dụng tấm pin công nghệ Đức <b>AE Solar</b>, 
        kết hợp pin lưu trữ lithium bền bỉ, chúng tôi giúp các hộ gia đình và doanh nghiệp cắt giảm trực tiếp bậc thang giá điện 
        và tự chủ nguồn năng lượng xanh thân thiện với môi trường.
    </p>
</div>
""", unsafe_allow_html=True)

# 3 Pillars
h_col1, h_col2, h_col3 = st.columns(3)
with h_col1:
    st.markdown("""
    <div class="custom-card">
        <h3 style="color:#0A2540; margin-top:0; font-size:1.2rem;">💰 Hiệu Quả Tài Chính</h3>
        <p style="font-size:0.95rem; line-height:1.5; color:#4A5568; margin-bottom:0;">
            Cắt giảm ngay tới 90% hóa đơn tiền điện. Hoàn vốn cực nhanh từ 3.5 - 5 năm. Hệ thống vận hành bền bỉ trên 25 năm.
        </p>
    </div>
    """, unsafe_allow_html=True)

with h_col2:
    st.markdown("""
    <div class="custom-card">
        <h3 style="color:#0A2540; margin-top:0; font-size:1.2rem;">🌳 Bảo Vệ Hệ Sinh Thái</h3>
        <p style="font-size:0.95rem; line-height:1.5; color:#4A5568; margin-bottom:0;">
            Sử dụng 100% nguồn bức xạ tự nhiên vô tận. Giảm phát thải CO2 tương đương trồng hàng trăm cây xanh mỗi năm.
        </p>
    </div>
    """, unsafe_allow_html=True)

with h_col3:
    st.markdown("""
    <div class="custom-card">
        <h3 style="color:#0A2540; margin-top:0; font-size:1.2rem;">🛠️ Chất Lượng Đỉnh Cao</h3>
        <p style="font-size:0.95rem; line-height:1.5; color:#4A5568; margin-bottom:0;">
            Sản phẩm chính hãng AE Solar (Đức), Inverter Deye, Luxpower, Solis. Bảo hành thiết bị dài hạn lên tới 5 - 10 năm.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.write("---")

# ==============================================================================
# 5. DANH MỤC GÓI LẮP ĐẶT (TABS)
# ==============================================================================
st.header("📋 Danh Mục Gói Lắp Đặt Tiêu Chuẩn")
st.markdown("Chọn nhóm gói phù hợp để xem cấu hình chi tiết từ cơ sở dữ liệu chính thức của **Solar 24h**:")

tab1, tab2, tab3 = st.tabs([
    "🏡 Gói Hộ Gia Đình (Dưới 10 kWp)", 
    "🏭 Gói Doanh Nghiệp (Trên 10 kWp)", 
    "⚙️ Gói Tùy Chỉnh & Lưu Trữ (Hybrid)"
])

# ------------------------------------------------------------------------------
# TAB 1: GÓI HỘ GIA ĐÌNH
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("🏡 Điện Mặt Trời Áp Mái Cho Hộ Gia Đình (< 10 kWp)")
    col_t1_left, col_t1_right = st.columns([3, 2])
    
    with col_t1_left:
        st.markdown("""
        Các gói gia đình từ **SOLAR F1 đến SOLAR F6** được thiết kế đặc thù để cắt giảm tiền điện sinh hoạt ở các bậc cao lũy tiến. 
        Đồng thời, hệ thống tích hợp pin lưu trữ giúp cấp điện liên tục khi có sự cố mất điện lưới.
        """)
        
        # Filter packages below 10 kWp
        fam_pkgs = {k: v for k, v in SOLAR_PACKAGES.items() if v["kwp"] < 10.0}
        
        # Selection box to view details interactively
        selected_fam = st.selectbox("Chọn gói hộ gia đình để xem chi tiết cấu hình:", list(fam_pkgs.keys()))
        fam_data = fam_pkgs[selected_fam]
        
        st.markdown(f"""
        <div style='background-color: #F8F9FA; border: 1px solid #E2E8F0; padding: 20px; border-radius: 12px;'>
            <h4 style='color: #0A2540; margin-top:0;'>📦 Chi tiết gói: {selected_fam} ({fam_data["kwp"]} kWp)</h4>
            <p style='color: #555;'>{fam_data["desc"]}</p>
            <table style='width:100%; border-collapse: collapse; font-size:0.95rem; margin-bottom: 15px;'>
                <tr>
                    <td style='padding:5px; font-weight:600;'>Giá trọn gói:</td>
                    <td style='padding:5px; text-align:right; font-weight:700; color:#2ECC71;'>{fam_data["price"]:,.0f} VND</td>
                </tr>
                <tr>
                    <td style='padding:5px; font-weight:600;'>Số tấm pin:</td>
                    <td style='padding:5px; text-align:right;'>{fam_data["panels"]} Tấm pin AE Solar 2 Mặt Kính (Đức) 580W</td>
                </tr>
                <tr>
                    <td style='padding:5px; font-weight:600;'>Biến tần Inverter:</td>
                    <td style='padding:5px; text-align:right;'>{fam_data["inverter"]}</td>
                </tr>
                <tr>
                    <td style='padding:5px; font-weight:600;'>Bộ lưu trữ Lithium:</td>
                    <td style='padding:5px; text-align:right;'>{fam_data["battery"]}</td>
                </tr>
            </table>
            <b>📋 Danh mục vật tư & hạng mục đi kèm:</b>
            <ul style='margin-top: 5px; margin-bottom:0; font-size: 0.9rem;'>
                {"".join([f"<li>{item}</li>" for item in fam_data["checklist"]])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col_t1_right:
        st.markdown("**Thiết Bị Tiêu Chuẩn & Dự Án Thực Tế**")
        img_col1, img_col2 = st.columns(2)
        with img_col1:
            load_and_show_image("Thiết Bị Điện Mặt Trời/AE SOLAR 2 Mặt Kính.png", caption="Tấm pin AE Solar 2 Mặt Kính")
        with img_col2:
            load_and_show_image("Thiết Bị Điện Mặt Trời/Inverter Deye.png", caption="Inverter Deye")
            
        load_and_show_image("Công trình thực tế/Hộ gia đình.png", caption="Hệ thống áp mái hộ gia đình thực tế bởi Solar 24h")

# ------------------------------------------------------------------------------
# TAB 2: GÓI DOANH NGHIỆP
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("🏭 Điện Mặt Trời Cho Doanh Nghiệp & Nhà Xưởng (≥ 10 kWp)")
    col_t2_left, col_t2_right = st.columns([3, 2])
    
    with col_t2_left:
        st.markdown("""
        Các gói từ **SOLAR F7 đến SOLAR F10** được tối ưu hóa cho doanh nghiệp, siêu thị, khách sạn và nhà kho sản xuất. 
        Hệ thống không chỉ tiết kiệm chi phí giờ cao điểm sản xuất đắt đỏ, làm mát mái tôn từ 3 - 5°C mà còn giúp doanh nghiệp đạt tiêu chuẩn xanh phục vụ xuất khẩu.
        """)
        
        # Filter packages above 10 kWp
        biz_pkgs = {k: v for k, v in SOLAR_PACKAGES.items() if v["kwp"] >= 10.0}
        
        selected_biz = st.selectbox("Chọn gói doanh nghiệp để xem chi tiết cấu hình:", list(biz_pkgs.keys()))
        biz_data = biz_pkgs[selected_biz]
        
        st.markdown(f"""
        <div style='background-color: #F8F9FA; border: 1px solid #E2E8F0; padding: 20px; border-radius: 12px;'>
            <h4 style='color: #0A2540; margin-top:0;'>📦 Chi tiết gói: {selected_biz} ({biz_data["kwp"]} kWp)</h4>
            <p style='color: #555;'>{biz_data["desc"]}</p>
            <table style='width:100%; border-collapse: collapse; font-size:0.95rem; margin-bottom: 15px;'>
                <tr>
                    <td style='padding:5px; font-weight:600;'>Giá trọn gói:</td>
                    <td style='padding:5px; text-align:right; font-weight:700; color:#2ECC71;'>{biz_data["price"]:,.0f} VND</td>
                </tr>
                <tr>
                    <td style='padding:5px; font-weight:600;'>Số tấm pin:</td>
                    <td style='padding:5px; text-align:right;'>{biz_data["panels"]} Tấm pin AE Solar 2 Mặt Kính (Đức) 580W</td>
                </tr>
                <tr>
                    <td style='padding:5px; font-weight:600;'>Biến tần Inverter:</td>
                    <td style='padding:5px; text-align:right;'>{biz_data["inverter"]}</td>
                </tr>
                <tr>
                    <td style='padding:5px; font-weight:600;'>Bộ lưu trữ Lithium:</td>
                    <td style='padding:5px; text-align:right;'>{biz_data["battery"]}</td>
                </tr>
            </table>
            <b>📋 Danh mục vật tư & hạng mục đi kèm:</b>
            <ul style='margin-top: 5px; margin-bottom:0; font-size: 0.9rem;'>
                {"".join([f"<li>{item}</li>" for item in biz_data["checklist"]])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col_t2_right:
        st.markdown("**Thiết Bị Công Nghiệp & Công Trình Nhà Xưởng**")
        img_col1, img_col2 = st.columns(2)
        with img_col1:
            load_and_show_image("Thiết Bị Điện Mặt Trời/AE SOLAR 2 Mặt Kính.png", caption="Tấm pin AE Solar 2 Mặt Kính")
        with img_col2:
            load_and_show_image("Thiết Bị Điện Mặt Trời/Inverter Solis.png", caption="Inverter Solis công nghiệp")
            
        load_and_show_image("Công trình thực tế/Nhà xưởng.png", caption="Hệ thống áp mái nhà xưởng thi công bởi Solar 24h")

# ------------------------------------------------------------------------------
# TAB 3: GÓI TÙY CHỈNH (HYBRID & THỦY SẢN)
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("⚙️ Hệ Thống Hybrid Tùy Chỉnh & Ứng Dụng Đặc Thù")
    col_t3_left, col_t3_right = st.columns([3, 2])
    
    with col_t3_left:
        st.markdown("""
        Hệ thống Hybrid kết hợp lưu trữ cho phép tự chủ năng lượng hoàn toàn:
        *   **Hòa lưới có lưu trữ**: Ban ngày sạc đầy pin dự phòng, ban đêm giải phóng sử dụng. Khi mất điện lưới, hệ thống tự động ngắt khỏi lưới và cấp điện dự phòng trong 10ms để thiết bị trong nhà (camera, tủ lạnh, máy tính) hoạt động liên tục.
        *   **Giải pháp cho Sà lang - Ghe tàu**: Lắp đặt hệ khung giàn pin chắc chắn chịu lực rung lắc lớn, Inverter chống ẩm mặn, cấp điện sinh hoạt thoải mái khi tàu bè di chuyển dài ngày trên sông nước, giúp giảm thời gian chạy máy phát điện diesel ồn ào và tốn kém.
        *   **Thiết kế biệt thự cao cấp**: Tối ưu hóa mỹ thuật mái ngói, giấu dây dẫn thẩm mỹ, hệ tủ điện Hybrid gọn gàng sang trọng.
        """)
        
        st.info("💡 **Gợi ý**: Quý khách có thể tự do tùy chỉnh dung lượng pin lithium lưu trữ (Gigabox, BSB, SVE, Seplos) hoặc nâng cấp dòng Inverter theo nhu cầu sử dụng thực tế. Đội ngũ kỹ sư Solar 24h luôn sẵn sàng hỗ trợ thiết kế riêng.")
        
    with col_t3_right:
        st.markdown("**Thiết Bị Hybrid & Ứng Dụng Đặc Thù**")
        img_col1, img_col2 = st.columns(2)
        with img_col1:
            load_and_show_image("Thiết Bị Điện Mặt Trời/Inverter LuxPower.png", caption="Inverter LuxPower Hybrid")
        with img_col2:
            load_and_show_image("Thiết Bị Điện Mặt Trời/Pin Gigabox.png", caption="Pin lưu trữ Gigabox Lithium")
            
        load_and_show_image("Công trình thực tế/Sà lang - ghe - tàu.png", caption="Hệ thống Hybrid độc lập lắp trên sà lang sông nước")

st.write("---")

# ==============================================================================
# 6. QUICK CALCULATOR & FINANCIAL ENGINE
# ==============================================================================
st.header("⚡ Bộ Công Cụ Tính Toán Thiết Kế & Hoàn Vốn Tự Động")
st.markdown("Nhập số tiền điện hoặc lượng điện tiêu thụ để hệ thống tự động phân tích kỹ thuật và kinh tế:")

calc_col1, calc_col2 = st.columns([1, 2])

with calc_col1:
    st.markdown("#### 📥 Nhập thông số sử dụng")
    
    with st.container(border=True):
        input_type = st.radio(
            "Chọn phương thức nhập liệu:",
            ["Hóa đơn tiền điện (VNĐ/Tháng)", "Lượng điện tiêu thụ (kWh/Tháng)"]
        )
        
        if input_type == "Hóa đơn tiền điện (VNĐ/Tháng)":
            user_bill = st.slider(
                "Nhập số tiền điện bình quân mỗi tháng (gồm VAT):",
                min_value=500000, max_value=30000000, value=2500000, step=100000,
                format="%,d"
            )
            estimated_kwh = back_calculate_kwh_from_cost(user_bill)
        else:
            estimated_kwh = st.number_input(
                "Nhập lượng điện tiêu thụ hàng tháng (kWh):",
                min_value=20, max_value=10000, value=750, step=20
            )
            user_bill = calculate_monthly_electricity_cost(estimated_kwh)
            
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        st.write(f"📊 **Hóa đơn hàng tháng:** {user_bill:,.0f} VNĐ")
        st.write(f"🔌 **Lượng điện tiêu thụ:** {estimated_kwh:,.1f} kWh/tháng")
        st.write(f"🌞 **Tiêu thụ trung bình:** {estimated_kwh/30:.2f} kWh/ngày")

    st.markdown("#### ⚙️ Tham số vận hành & kỹ thuật")
    with st.container(border=True):
        sun_hours = st.slider(
            "Số giờ nắng đỉnh trung bình (Peak Sun Hours/ngày):",
            min_value=3.5, max_value=5.5, value=4.3, step=0.1,
            help="Khu vực Đồng Tháp - Tiền Giang - miền Tây dao động từ 4.2 đến 4.5 giờ/ngày."
        )
        sys_efficiency = st.slider(
            "Hiệu suất chuyển đổi thực tế hệ thống (%):",
            min_value=70, max_value=90, value=82, step=1,
            help="Bao gồm tổn hao dây dẫn, bụi bẩn bám dính, nhiệt độ môi trường. Mặc định là 82%."
        ) / 100

# ------------------------------------------------------------------------------
# CALCULATION ALGORITHM (PRODUCING RECOMMENDED PACKAGE)
# ------------------------------------------------------------------------------
rec_pkg_name = "SOLAR F1"
for name, data in SOLAR_PACKAGES.items():
    if data["range_min"] <= user_bill < data["range_max"]:
        rec_pkg_name = name
        break
    if user_bill >= 7000000:
        rec_pkg_name = "SOLAR F10"

rec_pkg = SOLAR_PACKAGES[rec_pkg_name]

# Production math
monthly_generation = rec_pkg["kwp"] * sun_hours * 30 * sys_efficiency
daily_generation = rec_pkg["kwp"] * sun_hours * sys_efficiency

# Calculate post-solar cost (using progressive EVN scale)
remaining_kwh = max(0.0, estimated_kwh - monthly_generation)
post_solar_bill = calculate_monthly_electricity_cost(remaining_kwh)
monthly_savings = user_bill - post_solar_bill

# Payback period
payback_years = rec_pkg["price"] / (monthly_savings * 12) if monthly_savings > 0 else 0.0

with calc_col2:
    st.markdown("#### 📊 Đề xuất cấu hình từ Solar 24h")
    
    # Showcase primary recommended package card
    st.markdown(f"""
    <div style='background-color: #EBF8FF; border: 2px solid #2ECC71; border-radius: 12px; padding: 20px; margin-bottom: 20px;'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <h3 style='color: #0A2540; margin: 0; font-size:1.35rem;'>Gói phù hợp nhất: {rec_pkg_name} ({rec_pkg["kwp"]} kWp)</h3>
            <span style='background-color: #F1C40F; color: #0A2540; font-weight: 700; padding: 6px 14px; border-radius: 20px; font-size: 1rem;'>
                {rec_pkg["price"]:,.0f} VNĐ (Trọn gói)
            </span>
        </div>
        <p style='color: #4A5568; margin-top: 8px; font-size: 0.95rem; line-height: 1.5;'>{rec_pkg["desc"]}</p>
        <div style='margin-top: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 0.9rem;'>
            <div>🛠️ <b>Cấu hình chính:</b><br>
                • {rec_pkg["panels"]} Tấm pin AE Solar 2 Mặt Kính (Đức) 580W<br>
                • Biến tần: {rec_pkg["inverter"].split(" (")[0]}<br>
                • Lưu trữ: {rec_pkg["battery"]}
            </div>
            <div>⚡ <b>Khả năng vận hành:</b><br>
                • Sản lượng: <b>{daily_generation:.1f} kWh / ngày</b> (trung bình)<br>
                • Cắt giảm hóa đơn điện lên tới: <b>{min(90.0, (monthly_savings/user_bill)*100):.1f}%</b>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Metric cards row
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{monthly_generation:,.0f} kWh</div>
            <div class='metric-label'>Lượng điện sinh ra / Tháng</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col2:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{monthly_savings:,.0f} đ</div>
            <div class='metric-label'>Tiền điện tiết kiệm / Tháng</div>
        </div>
        """, unsafe_allow_html=True)
    with m_col3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{payback_years:.1f} năm</div>
            <div class='metric-label'>Thời gian hoàn vốn (ROI)</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Carbon offset
    # 1 kWh grid electricity reduces approx 0.7224 kg CO2 in Vietnam
    co2_saved_yearly = rec_pkg["kwp"] * 4 * 365 * 0.7224
    trees_equivalent = co2_saved_yearly / 20.0
    
    st.markdown(f"""
    <div style='background-color: #E0F2F1; padding: 15px; border-radius: 12px; border-left: 5px solid #004D40; margin-top: 15px; font-size: 0.95rem; color: #004D40;'>
        🌳 <b>Đóng góp cho bảo vệ môi trường:</b> Hệ thống này giúp cắt giảm <b>~{co2_saved_yearly:,.0f} kg CO2/năm</b> phát thải, tương đương trồng mới <b>~{trees_equivalent:.0f} cây xanh</b> mỗi năm.
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SHINHAN BANK CREDIT CALCULATOR (Tích hợp sâu dưới calculator)
# ------------------------------------------------------------------------------
st.markdown("<h4 style='color: #0A2540; margin-top: 25px;'>💳 Đòn Bẩy Tài Chính - Chương Trình Trả Góp Shinhan Bank</h4>", unsafe_allow_html=True)
st.markdown("Solar 24h hỗ trợ kết nối vay tín dụng xanh từ Shinhan Bank với lãi suất ưu đãi cố định phẳng **0.59%/tháng**:")

f_col1, f_col2 = st.columns([1, 1.2])

with f_col1:
    pkg_price = rec_pkg["price"]
    max_loan_allowed = min(100000000, pkg_price)
    
    loan_amount = st.slider(
        "Số tiền đề xuất vay từ Shinhan Bank (VND):",
        min_value=10000000,
        max_value=int(max_loan_allowed),
        value=int(max_loan_allowed),
        step=5000000,
        format="%,d"
    )
    
    prepayment = pkg_price - loan_amount
    
    term_months = st.selectbox(
        "Thời hạn trả góp (Tháng):",
        [12, 24, 36, 48],
        index=3
    )
    
    # Calculate installment values
    total_monthly_pay, p_part, i_part = calculate_shinhan_installment(loan_amount, term_months)

with f_col2:
    net_monthly_flow = monthly_savings - total_monthly_pay
    
    st.markdown(f"""
    <div style='background-color: #FFFDE7; border: 1px solid #FFF59D; padding: 20px; border-radius: 12px; font-size: 0.95rem; color: #333;'>
        <h5 style='color: #0A2540; margin-top:0; font-weight:600;'>📊 Phân tích dòng tiền hàng tháng:</h5>
        • Tổng tiền đầu tư hệ thống: <b>{pkg_price:,.0f} VNĐ</b><br>
        • Khách hàng trả trước: <b style='color: #2ECC71;'>{prepayment:,.0f} VNĐ</b><br>
        • Ngân hàng giải ngân: <b style='color: #0A2540;'>{loan_amount:,.0f} VNĐ</b><br>
        • Số tiền gốc + lãi trả góp: <b style='color: #E53E3E; font-weight:700;'>{total_monthly_pay:,.0f} VNĐ / Tháng</b><br>
          <span style='font-size:0.85rem; color:#666;'><i>(Gốc: {p_part:,.0f} đ | Lãi: {i_part:,.0f} đ)</i></span>
        <hr style='margin: 10px 0; border-top:1px solid #FFF59D;'>
        • Tiền điện tiết kiệm được: <b style='color: #2ECC71; font-weight:700;'>+{monthly_savings:,.0f} VNĐ / Tháng</b><br>
    </div>
    """, unsafe_allow_html=True)
    
    if net_monthly_flow >= 0:
        st.success(f"📈 **Dòng tiền thặng dư:** +{net_monthly_flow:,.0f} VNĐ/Tháng. Tiền điện tiết kiệm nhiều hơn tiền trả góp! Lấy tiền điện tự trả tiền đầu tư hệ thống.")
    else:
        st.warning(f"📉 **Chênh lệch dòng tiền:** {net_monthly_flow:,.0f} VNĐ/Tháng. Bạn chỉ cần bù thêm một phần nhỏ mỗi tháng để sở hữu vĩnh viễn hệ thống.")

# ==============================================================================
# 7. COMPARE MATRIX TAB (SOLAR F1 - F10)
# ==============================================================================
with st.expander("📊 Bảng So Sánh Cấu Hình Toàn Bộ 10 Gói SOLAR F1 - F10"):
    st.markdown("Dưới đây là bảng tổng hợp thông số gốc được đồng bộ chính xác với cơ sở dữ liệu báo giá tự động của công ty:")
    
    matrix_data = []
    for name, data in SOLAR_PACKAGES.items():
        m_gen = data["kwp"] * sun_hours * 30 * sys_efficiency
        
        # Tính toán tiết kiệm dựa trên hóa đơn tối đa khuyến nghị của từng gói (hoặc tối thiểu + 3 triệu nếu vô hạn)
        if data["range_max"] == float('inf'):
            base_bill = data["range_min"] + 3000000
        else:
            base_bill = data["range_max"]
            
        base_kwh = back_calculate_kwh_from_cost(base_bill)
        rem_kwh = max(0.0, base_kwh - m_gen)
        post_bill = calculate_monthly_electricity_cost(rem_kwh)
        sav = base_bill - post_bill
        
        matrix_data.append({
            "Mã Gói": name,
            "Công suất (kWp)": f"{data['kwp']} kWp",
            "Số Tấm Pin (580W)": f"{data['panels']} Tấm",
            "Dung lượng Pin": data["battery"],
            "Biến tần Inverter": data["inverter"].split(" (")[0],
            "Sản lượng (kWh/Tháng)": f"{m_gen:,.0f} kWh",
            "Tiết kiệm / Tháng": f"{sav:,.0f} đ",
            "Đơn Giá Trọn Gói (VNĐ)": f"{data['price']:,.0f}"
        })
        
    df_matrix = pd.DataFrame(matrix_data)
    st.dataframe(df_matrix, use_container_width=True, hide_index=True)

st.write("---")

# ==============================================================================
# 8. CONTACT FORM (FORM LIÊN HỆ & BÁO GIÁ)
# ==============================================================================
st.header("📞 Nhận Báo Giá & Khảo Sát Mái Nhà Miễn Phí")
st.markdown("Hãy cung cấp thông tin liên hệ của bạn, đội ngũ kỹ sư Solar 24h sẽ gọi điện tư vấn phương án tối ưu nhất:")

with st.form("solar_contact_form", clear_on_submit=True):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        customer_name = st.text_input("Họ và tên khách hàng *", placeholder="Nhập đầy đủ họ và tên")
    with col_f2:
        customer_phone = st.text_input("Số điện thoại di động *", placeholder="Ví dụ: 0901234567")
        
    col_f3, col_f4 = st.columns(2)
    with col_f3:
        roof_area_input = st.number_input("Diện tích mái nhà sẵn có (m²)", min_value=10, max_value=5000, value=50, step=5)
    with col_f4:
        package_interest = st.selectbox(
            "Gói sản phẩm quan tâm",
            [
                f"Chưa quyết định (Cần tư vấn thêm dựa trên đề xuất {rec_pkg_name})",
                "Gói Hộ Gia Đình (Dưới 10 kWp)",
                "Gói Doanh Nghiệp (Trên 10 kWp)",
                "Hệ thống Hybrid hòa lưới có lưu trữ",
                "Hệ thống Sà lang, ghe tàu sông nước"
            ]
        )
        
    customer_notes = st.text_area("Ghi chú bổ sung (Loại mái nhà, hướng mái, địa điểm cụ thể, thời gian tiện nghe máy...)", placeholder="Ví dụ: Mái tôn tại Mỹ Tho, hướng Đông Nam. Muốn tư vấn thêm về pin lưu trữ...")
    
    submitted = st.form_submit_button("Gửi Yêu Cầu Tư Vấn")
    
    if submitted:
        if not customer_name.strip() or not customer_phone.strip():
            st.error("⚠️ Vui lòng điền đầy đủ thông tin Họ tên và Số điện thoại liên hệ!")
        else:
            contact_file = "contacts.csv"
            new_contact = pd.DataFrame([{
                "ThoiGian": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "HoTen": customer_name.strip(),
                "SoDienThoai": customer_phone.strip(),
                "DienTichMai": roof_area_input,
                "GoiQuanTam": package_interest,
                "GhiChu": customer_notes.strip()
            }])
            
            # Save using utf-8-sig encoding for perfect Vietnamese parsing in Excel
            if os.path.exists(contact_file):
                try:
                    df = pd.read_csv(contact_file)
                    df = pd.concat([df, new_contact], ignore_index=True)
                    df.to_csv(contact_file, index=False, encoding="utf-8-sig")
                except Exception:
                    new_contact.to_csv(contact_file, index=False, encoding="utf-8-sig")
            else:
                new_contact.to_csv(contact_file, index=False, encoding="utf-8-sig")
                
            st.success(f"🎉 Gửi thông tin thành công! Cảm ơn anh/chị {customer_name}. Kỹ sư của Solar 24h sẽ gọi điện hỗ trợ anh/chị sớm nhất.")
            
            # Đồng bộ Google Sheets qua Webhook (nếu được cấu hình trong .env)
            webhook_url = os.environ.get("GOOGLE_SHEET_WEBHOOK_URL", "").strip()
            if webhook_url:
                try:
                    payload = {
                        "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "name": customer_name.strip(),
                        "phone": customer_phone.strip(),
                        "area": int(roof_area_input),
                        "package": package_interest,
                        "notes": customer_notes.strip()
                    }
                    response = requests.post(webhook_url, json=payload, timeout=8)
                    # In nhật ký kiểm tra lỗi vào Terminal nền
                    print(f"DEBUG Google Sheets: status={response.status_code}, response={response.text[:150]}")
                    
                    if response.status_code == 200 and "Success" in response.text:
                        st.toast("📊 Đã tự động đồng bộ dữ liệu lên Google Sheets!", icon="⚡")
                    else:
                        st.error(f"⚠️ Đồng bộ Google Sheets thất bại (Đầu ra: {response.text[:120]}...)")
                except Exception as e:
                    st.error(f"⚠️ Không thể kết nối đồng bộ Google Sheets: {str(e)}")

st.write("---")

# ==============================================================================
# 9. REAL WORK PROJECTS GALLERY
# ==============================================================================
st.header("📸 Dự Án Thực Tế Lắp Đặt Bởi Solar 24h")
st.markdown("Hình ảnh ghi nhận từ một số dự án tiêu biểu đã bàn giao kỹ thuật:")

gallery_items = [
    {"path": "Công trình thực tế/Hộ gia đình.png", "title": "Hệ thống áp mái hộ gia đình - TP. HCM"},
    {"path": "Công trình thực tế/Nhà xưởng.png", "title": "Hệ thống áp mái nhà xưởng sản xuất - Long An"},
    {"path": "Công trình thực tế/Sà lang - ghe - tàu.png", "title": "Hệ thống Hybrid trên Sà lang sông nước"},
    {"path": "Công trình thực tế/Gò Công .png", "title": "Dự án điện mặt trời hòa lưới - Gò Công"},
    {"path": "Công trình thực tế/Mỹ Tho 1.png", "title": "Thi công lắp đặt áp mái biệt thự - Mỹ Tho"},
    {"path": "Công trình thực tế/TP HCM 2.png", "title": "Lắp đặt áp mái tôn bền bỉ - TP. HCM"}
]

cols_gallery = st.columns(3)
for idx, item in enumerate(gallery_items):
    col = cols_gallery[idx % 3]
    with col:
        load_and_show_image(item["path"], caption=item["title"])

# ==============================================================================
# 10. TECHNICAL GUIDELINES
# ==============================================================================
with st.expander("🛠️ Quy Chuẩn Khảo Sát & Lắp Đặt Cơ Bản"):
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown("""
        **1. Khảo sát hướng đón nắng và diện tích mặt bằng:**
        *   **Hướng đón nắng**: Hướng tốt nhất ở Việt Nam là **hướng Nam** hoặc **Đông Nam**. Pin sẽ nhận bức xạ ổn định và đồng đều nhất suốt cả năm.
        *   **Không gian cần thiết**: Khoảng **5 - 6 m²** diện tích mái thoáng cho mỗi **1 kWp** công suất lắp đặt.
        *   **Đổ bóng**: Hạn chế tuyệt đối tình trạng đổ bóng từ bồn nước, nhà cao tầng kế bên hay tán cây. Một vùng bị đổ bóng nhỏ cũng làm giảm sản lượng điện của cả dãy pin do hiệu ứng nghẽn cổ chai.
        """)
    with t_col2:
        st.markdown("""
        **2. Kỹ thuật lắp đặt & Bảo dưỡng:**
        *   **Giải pháp trên mái tôn**: Sử dụng bát chữ L chịu lực cố định chặt vào xà gồ tôn, gioăng cao su chất lượng cao chịu nhiệt và keo dán chuyên dụng chống dột tuyệt đối.
        *   **Giải pháp trên mái ngói**: Sử dụng thanh treo móc ngói luồn vào dưới ngói để bắt đường ray nhôm nâng giàn pin mà không cần đục hay nứt ngói.
        *   **Tần suất vệ sinh**: Nên lau chùi bụi bẩn bám dính định kỳ từ **3 - 6 tháng một lần** để bảo vệ hiệu năng hấp thụ quang điện (bụi quá dày có thể sụt giảm tới 15% công suất).
        *   **Lưu ý**: Chỉ xịt nước lau pin vào lúc sáng sớm hoặc chiều mát. Tuyệt đối không rửa kính pin lúc giữa trưa nắng gắt để tránh sốc nhiệt làm rạn nứt kính cường lực.
        """)

# ==============================================================================
# 11. FOOTER BRANDING
# ==============================================================================
st.write("---")
st.markdown("""
<div style='text-align: center; color: #718096; font-size: 0.9rem; padding: 10px 0 20px 0;'>
    <b>CÔNG TY TNHH TMDV SOLAR 24H</b><br>
    📍 Địa chỉ văn phòng: Khu Phố Long Hòa A, Phường Đạo Thạnh, Tỉnh Đồng Tháp. (Kế bên khu hành chính công Đồng Tháp)<br>
    ☎️ Hotline: 0909.363.579 - 0896.488.299 | MST: 1201633082<br>
    © 2026 Solar 24h. Đã đăng ký bảo hộ thương hiệu toàn quốc.
</div>
""", unsafe_allow_html=True)
