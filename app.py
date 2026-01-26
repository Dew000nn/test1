import os
import re
import fitz  # PyMuPDF
import google.generativeai as genai
import streamlit as st
from prompt import PROMPT_WORKAW
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import dotenv

# โหลด Config
dotenv.load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# --- Config (Temperature 0 = แม่นยำที่สุด) ---
generation_config = {
    "temperature": 0.0,
    "top_p": 1.0, 
    "top_k": 32,
    "max_output_tokens": 2048,
    "response_mime_type": "text/plain",
}

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
}

# --- CSS ธีมพระจันทร์คืนเหงา (Midnight Moon Theme) ---
page_bg_img = """
<style>
/* พื้นหลังไล่เฉดสีท้องฟ้ายามค่ำคืน */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #1A1A2E 0%, #16213E 50%, #0F3460 100%);
    color: #E0E0E0;
}
/* ปรับแต่ง Header */
[data-testid="stHeader"] {
    background-color: rgba(0, 0, 0, 0);
}
/* ปรับแต่ง Sidebar */
[data-testid="stSidebar"] {
    background-color: #16213E;
    border-right: 1px solid #4E4E4E;
}
/* ปรับแต่งตัวหนังสือใน Sidebar */
[data-testid="stSidebar"] section[data-testid="stSidebarNav"] span {
    color: #E0E0E0;
}
/* ปรับแต่ง Chat Input */
.stChatInputContainer {
    padding-bottom: 20px;
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# --- ระบบอ่านไฟล์แบบ Hybrid ---
@st.cache_resource
def load_pdf_data_hybrid(file_path):
    text_content = ""
    page_images_map = {} 
    
    if os.path.exists(file_path):
        try:
            doc = fitz.open(file_path)
            for i, page in enumerate(doc):
                page_num = i + 1
                text = page.get_text()
                text_content += f"\n[--- Page {page_num} START ---]\n{text}\n[--- Page {page_num} END ---]\n"
                
                # Extract Images
                image_blocks = [b for b in page.get_text("blocks") if b[6] == 1]
                saved_images = []
                
                if image_blocks:
                    for img_block in image_blocks:
                        rect = fitz.Rect(img_block[:4])
                        if rect.width > 50 and rect.height > 50: 
                            try:
                                pix_crop = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=rect)
                                saved_images.append(pix_crop.tobytes("png"))
                            except: pass
                
                if not saved_images:
                    pix_full = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    saved_images.append(pix_full.tobytes("png"))

                if saved_images:
                    page_images_map[page_num] = saved_images
            return text_content, page_images_map
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return "", {}
    else:
        st.error(f"ไม่พบไฟล์ {file_path}")
        return "", {}

# --- เรียกใช้งาน ---
pdf_filename = "Graphic.pdf"
pdf_text, pdf_hybrid_images = load_pdf_data_hybrid(pdf_filename)

# --- Prompt (Strict Mode) ---
FULL_SYSTEM_PROMPT = f"""
{PROMPT_WORKAW}
... (คงเดิมไว้เพื่อความแม่นยำ) ...
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", 
    safety_settings=SAFETY_SETTINGS,
    generation_config=generation_config,
    system_instruction=FULL_SYSTEM_PROMPT
)

# --- UI Streamlit ---
def clear_history():
    st.session_state["messages"] = [
        {"role": "model", "content": "คืนนี้พระจันทร์สวยจังนะคะ... มีอะไรให้ 'Moonlight Bot' ช่วยหาคำตอบในเอกสารไหมคะ? 🌙👤"}
    ]
    st.rerun()

with st.sidebar:
    st.title("🌕 Moonlight Settings")
    if st.button("🗑️ ลบความทรงจำ"):
        clear_history()

st.title("🌙 Moonlight Bot")
st.caption("คุยกับบอทใต้แสงจันทร์ ค้นหาทุกอย่างจากเอกสารของคุณ")

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "model", "content": "คืนนี้พระจันทร์สวยจังนะคะ... มีอะไรให้ 'Moonlight Bot' ช่วยหาคำตอบในเอกสารไหมคะ? 🌙👤"}
    ]

# แสดงผลประวัติ
for msg in st.session_state["messages"]:
    avatar_icon = "👤" if msg["role"] == "user" else "🌙"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.write(msg["content"])
        if "image_list" in msg and msg["image_list"]:
            for img_data in msg["image_list"]:
                st.image(img_data, caption=f"🌘 บันทึกจากหน้า {msg.get('page_num_ref')}", use_container_width=True)

# รับข้อความ
if prompt := st.chat_input("พิมพ์คำถามของคุณที่นี่..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    # Logic การสร้าง Response (เหมือนเดิมแต่เปลี่ยน Emoji)
    # ... (ส่วน generate_response เดิม) ...
