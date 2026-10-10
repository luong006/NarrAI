import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Tình huống mẫu: Phân cảnh kịch tính cao độ giữa 2 nhân vật có quan hệ phức tạp
# - Quan hệ thấy được: 2 thám tử/cộng sự đang cùng ngồi trong xe ô tô dưới mưa quan sát đối tượng.
# - Quan hệ không thấy được (Underlying Subtext): 
#   + Nhân vật A (Huy) vừa phát hiện Nhân vật B (Hà) chính là nội gián của tổ chức tội phạm (Epistemic: A knows, B doesn't know A knows).
#   + Vector cảm xúc: Trust của A đối với B tụt từ 90 xuống 0, Fear/Vigilance tăng lên 85.
#   + Khẩu súng của Huy đang mở khóa an toàn giấu dưới vạt áo khoác.

SAMPLE_SCENE = """
Trời mưa như trút nước đập vào kính chắn gió của chiếc xe cũ. Huy và Hà ngồi im lặng trong khoang xe mờ tối, bên ngoài là ánh đèn neon nhấp nháy từ cổng kho hàng số 4.
Hà đưa cho Huy một điếu thuốc, mỉm cười: "Còn mười phút nữa là xe hàng xuất hiện. Anh căng thẳng quá đấy, anh Huy."
Huy nhìn điếu thuốc, rồi nhìn vào đôi mắt của Hà - người đồng đội 5 năm vào sinh ra tử. Tay phải của Huy đặt trong túi áo khoác, ngón tay khẽ chạm vào lẫy khóa an toàn của khẩu súng ngắn.
"Hà này, chiếc đồng hồ dây da em đeo... là quà của ai tặng?" Huy hỏi, giọng trầm và lạnh đến kỳ lạ.
Nụ cười trên môi Hà khẽ sượng lại trong một tích tắc.
"""

# ==============================================================================
# PHƯƠNG PHÁP 1: KHÔNG CÓ ONTOLOGY (BASELINE - NAIVE PROMPTS)
# ==============================================================================
baseline_panels = [
    {
        "panel": 1,
        "raw_prompt": "A car in the rain with two people inside, manga style",
        "analysis": {
            "nhan_vat": "Vô định hình (không rõ tuổi, mặt, tóc, quần áo). Khung sau sẽ biến thành người khác.",
            "boi_canh": "Chỉ là xe trong mưa chung chung, không rõ xe gì, góc nhìn nào.",
            "quan_he_thay_duoc": "Hai người chỉ ngồi trong xe, không có sự tương tác cụ thể.",
            "quan_he_khong_thay_duoc": "HOÀN TOÀN BIẾN MẤT. Không có sự căng thẳng, không có cảm giác nghi ngờ hay chết chóc."
        }
    },
    {
        "panel": 2,
        "raw_prompt": "A girl smiling and offering a cigarette to a man inside car, manga style",
        "analysis": {
            "nhan_vat": "Hà bị vẽ thành 'a generic anime girl' cười tươi vui vẻ, Huy bị vẽ thành đàn ông bất kỳ.",
            "boi_canh": "Góc nhìn ngẫu nhiên, ánh sáng không đồng nhất với panel 1.",
            "quan_he_thay_duoc": "Chỉ thấy hành động đưa điếu thuốc bình thường như đôi bạn thân.",
            "quan_he_khong_thay_duoc": "KHÔNG THẤY ĐƯỢC. Mất hoàn toàn nét giả tạo trong nụ cười và sự thăm dò ngầm."
        }
    },
    {
        "panel": 3,
        "raw_prompt": "Close-up of a man looking at a cigarette and touching a gun in pocket, manga style",
        "analysis": {
            "nhan_vat": "Mặt người đàn ông có thể lệch hoàn toàn so với panel 1 & 2.",
            "boi_canh": "Mất liên kết với không gian trong xe ô tô.",
            "quan_he_thay_duoc": "Chỉ thấy một người cầm súng một mình.",
            "quan_he_khong_thay_duoc": "Mất cảm giác phản bội, đau đớn và cảnh giác tột độ của 5 năm đồng đội."
        }
    },
    {
        "panel": 4,
        "raw_prompt": "Two people looking at each other inside car, girl surprised, manga style",
        "analysis": {
            "nhan_vat": "Cô gái ngạc nhiên kiểu truyện hài (surprised face anime), phá hỏng hoàn toàn không khí gián điệp/ly kỳ.",
            "boi_canh": "Xe ô tô có thể biến thành xe hiện đại khác hẳn panel 1.",
            "quan_he_thay_duoc": "Hai người nhìn nhau.",
            "quan_he_khong_thay_duoc": "Không thể hiện được sự sụp đổ của chiếc mặt nạ ngụy trang."
        }
    }
]

# ==============================================================================
# PHƯƠNG PHÁP 2: CÓ NARRATIVE ONTOLOGY MASTER V2.0 (NOKG 4 CHIỀU)
# ==============================================================================
# Ontology Context được trích xuất và tiêm vào:
# 1. Visual DNA:
#    - Huy: "weary 32yo Vietnamese detective, short rugged dark hair, stubble, wearing faded brown trench coat over rumpled collar shirt, sharp vigilant eyes, scar across left eyebrow"
#    - Hà: "27yo female undercover agent, sleek shoulder-length bob hair, wearing dark turtleneck beneath leather jacket, vintage gold wristwatch on left wrist, subtle calculated smile"
# 2. Spatial Anchor:
#    - Setting: "cramped dark interior of a battered sedan, heavy rain cascading down windshield, flickering amber streetlamp and neon reflections, claustrophobic atmosphere"
# 3. Visible Proxemics (Quan hệ thấy được):
#    - Sitting shoulder-to-shoulder in tight passenger/driver seats, close proximity forced by car cabin.
# 4. Invisible Subtext (Quan hệ không thấy được):
#    - Trust = 0, Suspicion = 95, Hidden Threat = Hand gripping concealed pistol under trench coat.
#    - Chiaroscuro lighting (Half-shadow on faces to signify duality and betrayal).

nokg_panels = [
    {
        "panel": 1,
        "layout": "wide",
        "prompt": "black and white manga, wide establishing interior two-shot inside cramped battered sedan, heavy rain cascading down windshield, faint flickering amber neon reflection through rain-streaked glass. Left seat: weary 32yo detective Huy in faded brown trench coat, right seat: 27yo female partner Hà in leather jacket. Oppressive claustrophobic silence, high contrast noir screentone",
        "dimensions": {
            "nhan_vat": "✅ CỐ ĐỊNH 100%: Đúng phục trang (trench coat nâu, áo da), đúng tuổi và phom người.",
            "boi_canh": "✅ KHÔNG GIAN BẤT BIẾN: Nội thất xe cũ, mưa đập kính chắn gió, ánh sáng neon mờ nhạt nhất quán.",
            "quan_he_thay_duoc": "✅ KHÔNG GIAN HẸP: Hai người ngồi kề vai trong không gian kín ngột ngạt.",
            "quan_he_khong_thay_duoc": "✅ BẦU KHÔNG KHÍ NGẸT THỞ: Ánh sáng noir phản chiếu qua màn mưa thể hiện khoảng cách tâm lý vô hình giữa hai người."
        }
    },
    {
        "panel": 2,
        "layout": "square",
        "prompt": "black and white manga, medium over-the-shoulder shot from Huy's perspective. 27yo female agent Hà with sleek bob hair in dark turtleneck and leather jacket, extending a lit cigarette across the console. She offers a pleasant yet calculated smile, left wrist clearly showing vintage gold wristwatch with leather strap. Rain streaks blurred in background, delicate ink shading",
        "dimensions": {
            "nhan_vat": "✅ CỐ ĐỊNH 100%: Tóc bob, áo cổ lọ đen dưới áo da, ĐẶC BIỆT CÓ CHIẾC ĐỒNG HỒ VÀNG TRÊN CỔ TAY TRÁI (Manh mối mấu chốt).",
            "boi_canh": "✅ GÓC MÁY CHUẨN: Góc qua vai của Huy, nền mờ kính xe đẫm mưa.",
            "quan_he_thay_duoc": "✅ HÀNH VI TƯƠNG TÁC: Tay đưa điếu thuốc qua bệ tỳ tay giữa hai ghế.",
            "quan_he_khong_thay_duoc": "✅ NỤ CƯỜI TÍNH TOÁN: Prompt chỉ định 'pleasant yet calculated smile' - nụ cười ngụy tạo của kẻ nội gián che đậy dã tâm."
        }
    },
    {
        "panel": 3,
        "layout": "tall",
        "prompt": "black and white manga, split dramatic panel. Top half: close-up of 32yo detective Huy's face, cold piercing gaze, scar on left eyebrow, face half-draped in deep shadow. Bottom half: extreme close-up of his right hand inside faded trench coat pocket, thumb resting tensely on the safety latch of a concealed snub-nosed revolver. Heavy cross-hatching, intense psychological dread",
        "dimensions": {
            "nhan_vat": "✅ CỐ ĐỊNH 100%: Vết sẹo lông mày trái, ánh mắt buốt giá, áo khoác trench coat.",
            "boi_canh": "✅ TẬP TRUNG CHI TIẾT: Khung chia đôi (split panel) tập trung vào khuôn mặt và bàn tay trong túi áo.",
            "quan_he_thay_duoc": "✅ ÁNH MẮT & HÀNH ĐỘNG ẨN: Mắt nhìn đối phương nhưng tay đặt vào vũ khí.",
            "quan_he_khong_thay_duoc": "✅ SỰ PHẢN BỘI & NGUY CƠ BẠO LỰC NGẦM: Bàn tay đặt trên lẫy khóa an toàn của súng thể hiện sự cảnh giác sinh tử, biến cố chuẩn bị bùng nổ mà nhân vật kia chưa hay biết."
        }
    },
    {
        "panel": 4,
        "layout": "square",
        "prompt": "black and white manga, intense tight close-up on 27yo agent Hà's face. Her polite smile instantly freezing, pupils slightly dilated in sudden chilling realization, cold sweat drop at temple. In foreground, detective Huy's cold silhouette asking the question. Dramatic Japanese manga screentone speedlines, psychological breakdown moment",
        "dimensions": {
            "nhan_vat": "✅ CỐ ĐỊNH 100%: Đúng khuôn mặt Hà từ các panel trước nhưng biểu cảm vi mô đột biến.",
            "boi_canh": "✅ KHÔNG GIAN TÂM LÝ: Nền đen tối giản với đường nét tốc độ (screentone) thể hiện đòn tâm lý giáng xuống.",
            "quan_he_thay_duoc": "✅ ĐỐI MẶT TRỰC DIỆN: Bóng đen của Huy lấn át tiền cảnh, áp đảo Hà ở hậu cảnh.",
            "quan_he_khong_thay_duoc": "✅ SỤP ĐỔ MẶT NẠ DỐI TRÁ: Đồng tử co lại, nụ cười đóng băng, giọt mồ hôi lạnh - phản ánh khoảnh khắc 'Bí mật đã bị lộ'."
        }
    }
]

print("="*80)
print("🔍 BẢNG SO SÁNH ĐỐI CHỨNG: HIỆU QUẢ THỂ HIỆN TRANH TRUYỆN TRƯỚC & SAU KHI CÓ ONTOLOGY")
print("="*80)

for p_base, p_nokg in zip(baseline_panels, nokg_panels):
    idx = p_base["panel"]
    print(f"\n--- KHUNG TRANH #{idx} ---")
    print(f"❌ [CHƯA CÓ ONTOLOGY]: {p_base['raw_prompt']}")
    print(f"   • Nhân vật:   {p_base['analysis']['nhan_vat']}")
    print(f"   • Bối cảnh:   {p_base['analysis']['boi_canh']}")
    print(f"   • Thấy được:  {p_base['analysis']['quan_he_thay_duoc']}")
    print(f"   • Ngầm/Ẩn:    {p_base['analysis']['quan_he_khong_thay_duoc']}")
    
    print(f"\n✅ [CÓ NARRATIVE ONTOLOGY NOKG v2.0]: (Layout: {p_nokg['layout']})")
    print(f"   Prompt: \"{p_nokg['prompt'][:110]}...\"")
    print(f"   • Nhân vật:   {p_nokg['dimensions']['nhan_vat']}")
    print(f"   • Bối cảnh:   {p_nokg['dimensions']['boi_canh']}")
    print(f"   • Thấy được:  {p_nokg['dimensions']['quan_he_thay_duoc']}")
    print(f"   • Ngầm/Ẩn:    {p_nokg['dimensions']['quan_he_khong_thay_duoc']}")
    print("-" * 80)
