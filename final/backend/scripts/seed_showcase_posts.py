"""
NarrAI Literary Showcase Seed Script.
Seeds 6 high-quality, genre-diverse stories into the NarrAI social network:
1. Lịch sử & Dã sử: Nam Quốc Sơn Hà (Phòng tuyến sông Như Nguyệt)
2. Tiên hiệp & Kỳ ảo: Hạo Thiên Kiếm Khí (Thượng cổ di vật)
3. Khoa học viễn tưởng: Sài Gòn 2099: Bản Giao Hưởng Neon
4. Trinh thám & Giật gân: Án Mạng Trong Biệt Thự Cổ Hà Nội
5. Kinh dị & Linh dị: Chuyện Kỳ Dị Bên Bến Sông Đáy
6. Đô thị & Chữa lành: Tiệm Trà Hoa Đêm Phố Cổ

Can run locally against SQLite / PostgreSQL or remotely via API.
"""

import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import json
import urllib.request
import urllib.parse

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

SHOWCASE_POSTS = [
    {
        "title": "Nam Quốc Sơn Hà: Tiếng Thơ Bên Phòng Tuyến Như Nguyệt",
        "genre": "Lịch sử",
        "tags": ["Lịch sử", "Lý Thường Kiệt", "Dã sử", "Hào khí Đông A"],
        "snippet": "Đêm sương lạnh buốt trên sông Như Nguyệt, tiếng trống trận trầm hùng xé tan màn đêm tĩnh mịch. Tướng quân Lý Thường Kiệt đứng sừng sững bên bờ chiến lũy, ánh mắt nhìn thẳng vào hàng vạn chiến thuyền quân Tống đang rình rập...",
        "story_text": """## Chương 1: Đêm Trăng Sông Như Nguyệt

Gió mùa đông bắc rít từng cơn lạnh buốt qua rặng tre ngà ven sông Như Nguyệt. Dòng nước đen thẫm cuộn sóng như một dải lụa khổng lồ ngăn cách hai bên chiến tuyến.

Tôi đứng tựa vào cột tiêu của vọng gác, hai bàn tay buốt cóng siết chặt cán mác đồng. Đằng xa, bờ bắc sáng rực ánh đuốc của trại quân Quách Quỳ. Tiếng tù và của giặc từng chặp rúc lên, nặng nề và ghê rợn như tiếng thở của loài dã thú khổng lồ đang chực nuốt chửng giang sơn Đại Việt.

“Lâm, chớ có nhìn lâu vào đốm lửa của địch,” tiếng một người cất lên sau lưng. 

Tôi quay lại, giật mình cúi đầu: “Bẩm Thái úy!”

Lý Thường Kiệt khoác áo chiến bào màu lam sẫm, không mang giáp trụ nặng nề, chỉ cầm ngang một thanh đoản kiếm. Đôi mắt ngài sâu thẳm, phản chiếu ánh trăng hạ tuần lạnh như băng tuyết. 

“Trời sắp nổi gió lớn,” Thái úy nhìn về hướng đền Trương Hống, Trương Hát. “Đêm nay, lòng dạ quân giặc sẽ tan vỡ trước lời thề của non sông.”

Lời ngài vừa dứt, từ sâu trong bóng tối của ngôi đền cổ, một giọng đọc sang sảng như sấm rền bắt đầu vang vọng khắp mặt sông:

*Nam quốc sơn hà Nam đế cư,*
*Tiệt nhiên định phận tại thiên thư...*

Cả khúc sông bỗng chốc lặng phắc. Rồi hàng vạn binh sĩ Đại Việt đồng loạt gõ khiên, tiếng gươm đao va chạm hòa cùng tiếng thét vang trời, rung chuyển cả bờ cõi!""",
    },
    {
        "title": "Sài Gòn 2099: Bản Giao Hưởng Neon & Ký Ức Số",
        "genre": "Khoa học viễn tưởng",
        "tags": ["Cyberpunk", "Sài Gòn 2099", "AI", "Neon"],
        "snippet": "Những biển quảng cáo Hologram ba chiều rực rỡ chiếu rọi xuống dòng kênh Nhiêu Lộc phủ đầy ánh sáng quang học. Minh – một hacker tự do – vô tình giải mã được một đoạn ký ức bị cấm của tập đoàn điều hành thành phố...",
        "story_text": """## Chương 1: Cơn Mưa Acid Trên Đại Lộ Nguyễn Huệ 2099

Cơn mưa mang nồng độ acid nhẹ xối xả đập vào tấm kính cường lực của phi thuyền tuần tra. Dưới kia, đại lộ Nguyễn Huệ rực rỡ dưới hàng triệu bóng đèn neon đa sắc, những bảng quảng cáo hologram khổng lồ chiếu rọi hình ảnh các người mẫu nhân tạo mỉm cười hoàn hảo.

Minh kéo chiếc mũ trùm đầu của chiếc áo khoác sợi carbon, ngón tay thoăn thoắt gõ trên bàn phím ảo chiếu từ thiết bị thần kinh gắn sau gáy.

“Phát hiện tín hiệu bất thường ở tầng 88 của tháp Bitexco-Neurolink,” giọng trợ lý AI Lạc Hồng vang lên trong ốc tai.

“Bao nhiêu dung lượng?” Minh thì thầm.

“1024 Exabyte. Dữ liệu nén dạng ý thức sống. Minh, đây không phải mã nguồn bình thường... Đây là ký ức nguyên bản của một con người đã bị xóa sổ 50 năm trước.”

Minh khựng lại nửa nhịp thở. Anh nhìn xuống dòng người tấp nập dưới phố với những cánh tay máy và đôi mắt điện tử lấp lánh. Nếu bí mật này bị phơi bày, toàn bộ trật tự của Sài Gòn Cyberpunk sẽ sụp đổ hoàn toàn.""",
    },
    {
        "title": "Hạo Thiên Kiếm Khí: Cổ Vật Trên Đỉnh Mù Căng Chải",
        "genre": "Tiên hiệp",
        "tags": ["Tiên hiệp", "Tu chân", "Kiếm hiệp", "Kỳ ảo"],
        "snippet": "Giữa những tầng mây trắng bồng bềnh phủ kín ruộng bậc thang non cao, truyền thuyết về thanh kiếm cổ chứa tàn hồn của một vị kiếm tiên Đại Việt thức tỉnh sau ngàn năm phong ấn...",
        "story_text": """## Chương 1: Kiếm Khí Rạch Trời

Đỉnh Mù Căng Chải mây mù vần vũ. Từng thửa ruộng bậc thang uốn lượn dưới sương sớm như những vảy rồng khổng lồ đang nằm ngủ say giữa núi rừng Tây Bắc.

Diệp Phong quỳ gối trước hang đá cổ, hơi thở dồn dập. Đan điền của hắn đang bỏng rát như có một ngọn lửa địa ngục thiêu đốt. Trước mặt hắn, cắm sâu vào tảng đá hoa cương nghìn năm tuổi, là một thanh kiếm rỉ sét nhưng tỏa ra từng đợt kiếm áp kinh hoàng.

“Kẻ phàm trần nào dám kinh động đến giấc ngủ của lão phu?” Một giọng nói cổ xưa, trầm ấm vang vọng thẳng vào thức hải của Diệp Phong.

Diệp Phong cắn răng, máu rỉ ra từ khóe môi: “Vãn bối không có ý mạo phạm. Nhưng môn phái nghịch đạo đang tàn sát cả bản làng. Nếu tiền bối không cho mượn kiếm, hôm nay ta thà chết chứ không lùi!”

Khoảnh khắc bàn tay hắn chạm vào chuôi kiếm đồng cổ, bầu trời Tây Bắc bỗng xé toạc ra một luồng sáng vàng kim chói lọi!""",
    },
    {
        "title": "Bóng Ma Biệt Thự Cổ Phố Chân Cầm",
        "genre": "Trinh thám",
        "tags": ["Trinh thám", "Hà Nội", "Suy luận", "Bí ẩn"],
        "snippet": "Một vụ án mạng kỳ lạ trong căn biệt thự kiến trúc Pháp cổ giữa lòng phố cổ Hà Nội. Manh mối duy nhất là một quân cờ tướng bằng ngọc bích nằm cạnh tách trà sen còn bốc khói...",
        "story_text": """## Chương 1: Tách Trà Còn Hơi Ấm

Mưa phùn rây rây trên những mái ngói rêu phong của phố Chân Cầm. Đồng hồ điểm 11 giờ đêm khi thám tử Trần Bảo bước chân vào sảnh căn biệt thự thời Pháp thuộc.

Nạn nhân là ông Nguyễn Khắc Lương, một nhà sưu tầm cổ vật nổi tiếng. Ông ngồi ngay ngắn trên chiếc ghế bành bọc da cũ kỹ, đầu ngả ra sau, đôi mắt mở to nhìn trân trân lên trần nhà như vừa chứng kiến điều gì không thể tin nổi.

“Hiện trường không có dấu hiệu giằng co, cửa sổ và cửa ra vào đều khóa trong,” đại úy Thành bước lại gần, thì thầm.

Bảo cúi người quan sát chiếc bàn trà bằng gỗ mun. Một quân cờ Tướng chữ “Tướng” bằng ngọc bích màu xanh thẫm nằm nghiêng cạnh tách trà sen. Nước trà vẫn còn bốc lên làn khói mỏng.

“Kẻ thủ ác không phải người lạ,” Bảo khẽ nhếch khóe môi. “Và hắn vừa mới rời khỏi căn phòng này chưa đầy năm phút trước.”""",
    },
    {
        "title": "Chuyện Kỳ Dị Bên Bến Sông Đáy",
        "genre": "Kinh dị",
        "tags": ["Kinh dị", "Dân gian", "Linh dị", "Truyền thuyết"],
        "snippet": "Cứ vào đêm rằm tháng Bảy, người dân làng Chài lại nghe thấy tiếng hò reo huyền bí phát ra từ cồn cát giữa sông Đáy, nơi từng chôn giấu kho báu của một đội thuyền buôn mất tích bí ẩn...",
        "story_text": """## Chương 1: Tiếng Gọi Giữa Đêm Rằm

Đêm rằm tháng Bảy, trăng tròn vành vạnh nhưng ánh sáng mờ đục như nhuốm màu nước sông đục ngầu. Dọc đôi bờ sông Đáy, lau sậy xào xạc theo từng cơn gió lạnh thổi ngược từ phía cửa biển.

Ông lão Vạn Chèo cắm chiếc sào tre xuống lòng bùn, quay sang dặn thằng cháu nội bằng giọng run run: “Nhớ kỹ lời ông, sau canh ba, nghe thấy ai gọi tên cũng tuyệt đối không được ngoảnh đầu lại.”

Thằng bé gật đầu, kéo chiếc chăn chiên chùm kín cổ. Nhưng rồi, từ giữa bãi bồi hoang vắng, tiếng hát ru con bỗng cất lên não nề:

*Gió đưa cây cải về trời...*
*Rau râm ở lại chịu lời đắng cay...*

Tiếng hát rõ mồn một như người hát đang đứng ngay mũi thuyền nan. Thằng bé không nén nổi tò mò, từ từ he hé hé mắt nhìn qua khe nan tre...""",
    },
    {
        "title": "Tiệm Trà Hoa Đêm Phố Cổ",
        "genre": "Đô thị",
        "tags": ["Đô thị", "Chữa lành", "Hà Nội", "Tình cảm"],
        "snippet": "Ẩn sâu trong một con ngõ nhỏ của Hà Nội có một tiệm trà hoa chỉ mở cửa từ nửa đêm đến rạng sáng. Nơi đó, mỗi tách trà là một câu chuyện lắng đọng giúp xoa dịu những vết thương lòng của người trẻ...",
        "story_text": """## Chương 1: Vị Ngọt Của Hoa Cúc Tiến Vua

Phố phường Hà Nội chìm vào giấc ngủ muộn. 1 giờ sáng, tiếng còi xe tắt lịm, nhường chỗ cho tiếng xào xạc của chiếc chổi đót của cô lao công quét lá rụng.

Trong ngõ Yên Thái, ánh đèn vàng ấm áp hắt ra từ cánh cửa gỗ mộc mạc của Tiệm Trà Hoa Đêm. An đẩy cửa bước vào, tiếng chuông gió bằng đồng khẽ reo lên một chuỗi âm thanh trong trẻo.

“Chào em, hôm nay uống gì?” Người chủ quán trạc ba mươi tuổi mỉm cười nhẹ nhàng, tay đang chậm rãi rót nước sôi vào chiếc ấm đất nung.

An ngồi xuống chiếc ghế đẩu, đôi mắt mệt mỏi sau mười bốn tiếng làm việc liên tục: “Cho em một tách gì đó... để cảm thấy bớt cô đơn được không anh?”

Người chủ quán khẽ gật đầu, với tay lấy chiếc hũ gốm đựng hoa cúc vàng sấy lạnh: “Một ấm Cúc Tiến Vua ướp mật ong rừng. Vị đắng nhẹ đầu lưỡi, nhưng hậu ngọt sẽ giữ ấm trái tim em đến tận sáng.”""",
    }
]

def seed_locally():
    from db.models import SessionLocal, User, SocialPost
    from services.recommender_service import publish_post
    from auth import get_password_hash

    db = SessionLocal()
    try:
        # 1. Ensure author user exists
        author = db.query(User).filter(User.username == "narrai_author").first()
        if not author:
            author = User(
                username="narrai_author",
                full_name="Biên Tập Viên NarrAI",
                password_hash=get_password_hash("AuthorPass123!"),
                coins=1000
            )
            db.add(author)
            db.commit()
            db.refresh(author)
            print(f"Created author user: {author.username} (ID: {author.id})")

        # 2. Check existing posts
        existing_count = db.query(SocialPost).count()
        print(f"Current posts in database: {existing_count}")

        # 3. Publish showcase posts
        added = 0
        for item in SHOWCASE_POSTS:
            existing = db.query(SocialPost).filter(SocialPost.title == item["title"]).first()
            if not existing:
                post = publish_post(
                    db=db,
                    user_id=author.id,
                    title=item["title"],
                    content_snippet=item["snippet"],
                    story_text=item["story_text"],
                    genre=item["genre"],
                    tags=item["tags"],
                )
                print(f"Seeded: '{post.title}' (ID: {post.id}, Genre: {post.genre})")
                added += 1
            else:
                print(f"Already exists: '{item['title']}'")

        print(f"\nSeeding complete! Successfully added {added} showcase posts.")
    finally:
        db.close()

if __name__ == "__main__":
    print("--- Seeding NarrAI Showcase Posts ---")
    seed_locally()
