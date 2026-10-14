import os
import sys
import json
import uuid
import re
from datetime import datetime, timezone

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from db.models import Story, User, Comic, ComicPanel, SocialPost, engine
from sqlalchemy.orm import sessionmaker
from auth import get_password_hash

ROOT_DIR = os.path.dirname(backend_dir)
ROOT_QUEUE_PATH = os.path.join(ROOT_DIR, "data", "queue.json")
BACKEND_QUEUE_PATH = os.path.join(backend_dir, "data", "queue.json")
ROOT_STORIES_DIR = os.path.join(ROOT_DIR, "data", "stories")
BACKEND_STORIES_DIR = os.path.join(backend_dir, "data", "stories")

os.makedirs(os.path.dirname(ROOT_QUEUE_PATH), exist_ok=True)
os.makedirs(os.path.dirname(BACKEND_QUEUE_PATH), exist_ok=True)
os.makedirs(ROOT_STORIES_DIR, exist_ok=True)
os.makedirs(BACKEND_STORIES_DIR, exist_ok=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

STORIES_CATALOG = [
    {
        "id": "tam-cam",
        "title": "Tấm Cám",
        "topic": "Truyện cổ tích Việt Nam",
        "category": "Truyện cổ tích & Thần thoại",
        "genre": ["Cổ tích", "Dân gian Việt Nam", "Nhân quả", "Phép màu"],
        "summary": "Truyện cổ tích kinh điển về lòng nhân hậu, kiên cường của cô Tấm trải qua bao kiếp nạn hóa thân từ chim vàng anh, cây xoan đào, khung cửi đến quả thị để trở lại đoàn tụ cùng nhà vua.",
        "content": """Ngày xưa, có cô Tấm hiền lành, mồ côi mẹ từ nhỏ, phải sống cùng người cha, mụ dì ghẻ cay nghiệt và người em gái cùng cha khác mẹ tên Cám. Tấm quanh năm làm lụng vất vả, từ sáng sớm đến đêm khuya, trong khi Cám được nuông chiều, chỉ biết rong chơi.

Một hôm, dì ghẻ bảo hai chị em đi bắt tép, ai được nhiều giỏ sẽ thưởng cho một chiếc yếm đỏ. Tấm chăm chỉ mò được đầy giỏ tép tươi, còn Cám mải đuổi bướm hái hoa nên giỏ trống không. Cám lừa Tấm: "Chị Tấm ơi chị Tấm, đầu chị lấm, chị hụp cho sâu kẻo về mẹ mắng". Tấm tin lời lặn xuống ao gội đầu, Cám liền trút hết giỏ tép của Tấm vào giỏ mình rồi chạy về trước lĩnh thưởng.

Khi Tấm bước lên bờ, thấy giỏ trống trơn, tủi thân òa khóc nức nở. Bụt hiện lên trong ánh hào quang dịu mát, an ủi Tấm và bảo Tấm nhìn vào giỏ. Trong giỏ chỉ còn một con cá bống nhỏ xíu. Bụt dặn Tấm đem bống về thả xuống giếng nuôi, mỗi bữa bớt lại một bát cơm cho bống ăn và dặn câu gọi: "Bống bống bang bang, lên ăn cơm vàng cơm bạc nhà ta, chớ ăn cơm hẩm cháo hoa nhà người".

Cá bống lớn nhanh như thổi, trở thành người bạn tri kỷ duy nhất của Tấm. Mụ dì ghẻ sinh lòng ngờ vực, rình rập biết được liền bày mưu lừa Tấm đi chăn trâu xa, ở nhà bắt bống làm thịt. Tấm về không thấy bống đâu, chỉ thấy mặt nước lặng ngắt, lại ôm mặt khóc than. Bụt lại hiện lên dặn Tấm tìm nhặt xương bống bỏ vào bốn chiếc lọ sành rồi chôn dưới bốn chân giường.

Ít lâu sau, nhà vua mở hội trẩy lớn. Dì ghẻ trộn một thúng thóc với một thúng gạo bắt Tấm nhặt xong mới được đi hội. Bụt sai đàn chim sẻ sà xuống nhặt giúp Tấm trong chớp mắt, rồi bảo Tấm đào bốn chiếc lọ sành lên. Kỳ diệu thay, trong lọ hóa ra quần áo lụa là rực rỡ, chiếc yếm đào tinh xảo và một đôi hài thêu lấp lánh cùng một con ngựa ô phi như gió.

Trên đường đến hội, ngựa nhảy qua con suối nhỏ làm rơi một chiếc hài xuống nước. Đoàn voi của nhà vua đi qua, voi nhất quyết không chịu đi tiếp. Vua truyền lệnh lặn xuống vớt lên được chiếc hài gấm nhỏ nhắn, tinh xảo phi thường. Vua ban chiếu: bất cứ cô gái nào ướm vừa chiếc hài sẽ được lập làm Hoàng hậu. Hàng ngàn cô gái kinh kỳ, kể cả mẹ con Cám đều thử nhưng không ai vừa. Đến lượt Tấm bước vào, nàng ướm chân vào chiếc hài vừa như in, lại rút chiếc hài thứ hai trong dải áo ra. Nhà vua mừng rỡ khôn xiết, lập tức rước Tấm về cung làm Hoàng hậu trong sự ghen tức tột cùng của mẹ con Cám.

Vào ngày giỗ cha, Tấm về thăm nhà. Mụ dì ghẻ bảo Tấm trèo lên cây cau hái buồng cau cúng cha. Khi Tấm lên đến ngọn, mụ ở dưới cầm dao đốn gốc. Tấm ngã xuống ao thiệt mạng. Mẹ con Cám vào cung thay Tấm làm hoàng hậu. Nhưng linh hồn Tấm thanh sạch không tan biến: Tấm hóa thành chim Vàng Anh bay về ngự hoa viên hót khúc ca tha thiết. Cám bắt chim giết thịt, lông chim hóa thành hai cây Xoan Đào tỏa bóng mát che cho nhà vua. Cám lại sai đốn cây làm khung cửi, tiếng khung cửi rít lên: "Cót ca cót két, lấy tranh chồng chị, chị khoét mắt ra!".

Sợ hãi, Cám đem đốt khung cửi rồi đổ tro thật xa hoàng cung. Từ đống tro tàn mọc lên một cây thị tươi tốt, trên cành chỉ có duy nhất một quả thị vàng óng, thơm ngát lạ thường. Một bà lão nghèo bán nước đi qua ngửa vạt áo khấn: "Thị ơi thị rụng bị bà, bà để bà ngửi chứ bà không ăn". Quả thị rụng đúng vào vạt áo bà lão. Hằng ngày khi bà đi vắng, Tấm từ quả thị bước ra quét dọn nhà cửa sạch sẽ, thổi cơm nóng hổi, têm trầu cánh phượng tuyệt đẹp.

Một ngày nọ, nhà vua vi hành ghé qua quán nước của bà cụ. Thấy miếng trầu têm cánh phượng khéo léo giống hệt trầu Tấm têm năm xưa, vua gặng hỏi bà cụ. Bà lão đành kể thật ngọn ngành. Vua xin được gặp người trong nhà, vừa lúc Tấm từ buồng bước ra. Hai vợ chồng nhận ra nhau, ôm nhau mừng mừng tủi tủi. Nhà vua rước Hoàng hậu Tấm trở lại cung điện nguy nga, còn mẹ con Cám phải chịu hình phạt thích đáng cho những tội ác của mình. Từ đó, Tấm và nhà vua sống trọn đời hạnh phúc, thương yêu muôn dân trăm họ.""",
        "characters": [
            {
                "name": "Cô Tấm",
                "role": "lead",
                "gender": "female",
                "dna": "beautiful 18yo traditional Vietnamese maiden, gentle almond eyes, radiant kind smile, long jet-black hair tied in silk scarf, wearing traditional rustic brown ao tu than with vibrant lotus-pink inner robe and delicate embroidered silk slippers"
            },
            {
                "name": "Cám",
                "role": "antagonist",
                "gender": "female",
                "dna": "17yo haughty Vietnamese girl, sharp envious eyes, styled hair with flashy accessories, wearing bright embroidered silk ao tu than"
            },
            {
                "name": "Hoàng đế",
                "role": "supporting",
                "gender": "male",
                "dna": "noble young Vietnamese king, handsome resolute face, regal gold embroidered royal dragon robe with jade belt"
            }
        ],
        "world_setting": "Làng quê Bắc Bộ thanh bình với giếng nước cổ, rặng tre xanh mát và Hoàng cung Đại Việt nguy nga cổ kính.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Tấm ngồi bên bờ giếng cổ, tay nâng niu bát cơm nhỏ gọi cá bống trong ánh hoàng hôn thanh bình.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, beautiful 18yo traditional Vietnamese maiden gentle almond eyes long jet-black hair tied in silk scarf wearing traditional rustic ao tu than, kneeling by ancient mossy stone well holding small rice bowl, serene rural Vietnamese village background with bamboo grove, 2D manga screentone",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Bụt hiện lên giữa vầng hào quang rực rỡ, hiền từ an ủi nàng Tấm đang rơi lệ.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, mystical benevolent ancient spirit glowing with celestial mist, comforting young Vietnamese maiden in tears, magical dust particles, dramatic high contrast manga screentone",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Trước cung đình hoa lệ, Tấm nhẹ nhàng ướm vừa chiếc hài thêu lấp lánh trong sự ngỡ ngàng của quần thần.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, beautiful Vietnamese maiden trying on tiny ornate embroidered silk slipper fitting perfectly, noble young King watching with radiant admiration, grand ancient Vietnamese palace courtyard, medium shot",
                "layout_type": "tall"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Tấm bước ra từ quả thị thơm ngát, mỉm cười tái ngộ cùng nhà vua sau bao kiếp nạn kiên trung.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, beautiful graceful Vietnamese Queen emerging beside golden persimmon tree, reuniting with emotional young King, romantic dramatic reunion, warm emotional climax 2D manga lineart",
                "layout_type": "square"
            }
        ]
    },
    {
        "id": "thach-sanh",
        "title": "Thạch Sanh",
        "topic": "Truyện cổ tích dũng sĩ Việt Nam",
        "category": "Truyện cổ tích & Thần thoại",
        "genre": ["Cổ tích", "Dũng sĩ", "Diệt ác trừ tà", "Công lý"],
        "summary": "Truyện cổ tích về chàng dũng sĩ mồ côi Thạch Sanh dũng cảm diệt Chằn tinh, bắn Đại bàng cứu công chúa và dùng tiếng đàn thần cùng niêu cơm kỳ diệu đẩy lùi liên quân 18 nước chư hầu.",
        "content": """Ngày xưa, ở quận Cao Bình có hai vợ chồng già nghèo khó nhưng ăn ở vô cùng nhân đức. Ngọc Hoàng cảm động bèn sai Thái tử đầu thai làm con. Người mẹ mang thai nhiều năm mới sinh ra một cậu bé khôi ngô tuấn tú, đặt tên là Thạch Sanh. Chưa được bao lâu thì cha mẹ lần lượt qua đời, Thạch Sanh sống cô độc dưới một túp lều tranh bên gốc đa già, gia tài chỉ có một chiếc khố rách và một cây búa sắc cha để lại. Đến năm chàng khôn lớn, Ngọc Hoàng sai thiên thần xuống dạy cho chàng đủ các môn võ nghệ và trăm thứ phép thần thông biến hóa.

Trong vùng có tên Lý Thông làm nghề nấu rượu. Thấy Thạch Sanh khỏe mạnh phi thường, hắn bèn kết nghĩa anh em nhằm lợi dụng sức lực của chàng gánh vác việc nặng cho nhà mình.

Bấy giờ trong vùng có con Chằn tinh hung dữ, mỗi năm dân làng phải nộp một mạng người cho nó ăn thịt. Năm ấy đến lượt nhà Lý Thông phải nộp mạng. Mẹ con Lý Thông mưu mô lừa Thạch Sanh đến miếu canh thay mình trong đêm. Nửa đêm, Chằn tinh nhe nanh giương vuốt lao vào miếu định ăn thịt chàng. Thạch Sanh không hề nao núng, vung búa thần giao chiến quyết liệt. Sau hồi giằng co, chàng giáng búa chém đứt đầu yêu quái, thu về bộ cung tên vàng rực rỡ rồi mang đầu Chằn tinh về nhà. Mẹ con Lý Thông khiếp vía, nhưng liền lừa Thạch Sanh rằng đó là trăn thần của vua nuôi, xúi chàng trốn ngay về gốc đa, còn Lý Thông cướp công đem đầu quái vật vào cung lĩnh thưởng, được vua phong làm quan Đô đốc.

Ít lâu sau, nhà vua mở hội kén rể cho công chúa Quỳnh Nga. Giữa lúc công chúa đang dạo chơi trong vườn hoa, một con Đại bàng tinh khổng lồ từ trên trời sà xuống quắp nàng bay đi. Bay qua gốc đa, Đại bàng bị Thạch Sanh dùng cung vàng bắn trọng thương trúng cánh. Thạch Sanh lần theo vết máu tìm đến tận cửa hang đá bí mật dưới vực sâu.

Nhà vua đau đớn, sai Lý Thông đi tìm công chúa. Lý Thông hoang mang tìm đến Thạch Sanh nhờ giúp đỡ. Thạch Sanh thật thà dẫn đường và tự mình buộc dây thừng xuống hang sâu đánh nhau dữ dội với Đại bàng tinh, chém chết yêu quái và buộc công chúa vào dây cho quân kéo lên. Khi công chúa vừa lên khỏi miệng hang, Lý Thông liền cho quân lăn đá tảng lấp kín cửa hang nhằm chôn sống Thạch Sanh để độc chiếm công cứu nàng.

Bị giam dưới hang sâu, Thạch Sanh tìm đường thoát và tình cờ cứu được Thái tử con vua Thủy Tề đang bị giam cầm. Vua Thủy Tề mở tiệc tạ ơn, tặng chàng muôn vàn vàng bạc ngọc ngà nhưng chàng chỉ xin một cây đàn thần bằng gỗ rồi trở về gốc đa sinh sống.

Hồn Chằn tinh và Đại bàng tinh không siêu thoát, lẻn vào kho vua ăn trộm của cải rồi giấu vào gốc đa để vu oan cho Thạch Sanh. Chàng bị bắt giam vào ngục tối. Ở trong ngục, Thạch Sanh lấy đàn thần ra gảy. Tiếng đàn kỳ diệu nức nở vang lên khắp hoàng cung:
"Đàn kêu tích tịch tình tang,
Ai mang công chúa dưới hang trở về?
Đàn kêu ai chém Chằn tinh,
Cho chàng áo gấm hiển vinh một mình..."

Công chúa Quỳnh Nga từ ngày thoát nạn bị câm, nghe tiếng đàn bỗng bật cười và nói được. Nàng xin vua cha cho triệu người gảy đàn vào yết kiến. Trước triều đình, Thạch Sanh kể rõ mọi sự tình. Nhà vua phẫn nộ, hạ lệnh bắt giam mẹ con Lý Thông và giao cho Thạch Sanh xét xử. Chàng rộng lượng tha mạng cho chúng, nhưng trên đường về quê, mẹ con Lý Thông bị sét đánh chết và hóa thành bọ hung.

Vua gả công chúa Quỳnh Nga cho Thạch Sanh. Hoàng tử 18 nước chư hầu trước kia cầu hôn không được, nay tức giận đem quân sang vây hãm kinh thành. Thạch Sanh một mình bước lên mặt thành gảy đàn thần. Tiếng đàn khi êm ái như gió thoảng, khi rộn rã như tiếng mẹ ru khiến binh lính đối phương buông vũ khí, nhớ quê nhà khóc lóc xin hàng. Thạch Sanh lại bày một niêu cơm nhỏ thiết đãi quân giặc. Quân lính cười chê niêu cơm bé tẹo, nhưng ăn mãi cơm vẫn đầy ắp không bao giờ vơi. Quân tướng 18 nước chư hầu bái phục sát đất, cúi đầu tạ ơn rồi rút lui trong hòa bình. Về sau, vua truyền ngôi báu cho Thạch Sanh, đất nước thái bình thịnh trị muôn đời.""",
        "characters": [
            {
                "name": "Thạch Sanh",
                "role": "lead",
                "gender": "male",
                "dna": "mighty 20yo Vietnamese warrior hero, muscular build, resolute heroic gaze, wearing rustic loincloth and battle sash, holding magic glowing bronze battle-axe and celestial wooden zither"
            },
            {
                "name": "Công chúa Quỳnh Nga",
                "role": "supporting",
                "gender": "female",
                "dna": "graceful 18yo Vietnamese royal princess, delicate serene face, wearing royal embroidered silk robe with gold phoenix embroidery"
            },
            {
                "name": "Lý Thông",
                "role": "antagonist",
                "gender": "male",
                "dna": "crafty 35yo merchant turned corrupt mandarin, scheming narrow eyes, wearing ostentatious silk mandarin robes"
            }
        ],
        "world_setting": "Túp lều tranh dưới gốc đa cổ thụ đại ngàn, miếu hoang rùng rợn và Kinh đô Đại Việt uy nghiêm.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Dưới gốc đa già cổ thụ, Thạch Sanh vung búa sắc luyện võ với ý chí kiên cường và sức mạnh phi thường.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, mighty 20yo Vietnamese warrior hero muscular build wielding heavy bronze axe, standing beneath massive ancient banyan tree, dynamic training stance, screentone shading",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Trong miếu hoang tăm tối, Thạch Sanh dũng cảm giao chiến một mất một còn với Chằn tinh hung ác.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, intense battle scene, Vietnamese warrior swinging glowing axe at giant ferocious monster beast in dark ruined shrine, high contrast action anime manga",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Từ chốn ngục tối oan khuất, tiếng đàn thần của Thạch Sanh cất lên ai oán vang vọng khắp kinh thành.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, heroic warrior sitting in stone dungeon cell playing wooden magical zither, mystical melodic energy radiating through iron bars, emotional dramatic lighting",
                "layout_type": "tall"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Thạch Sanh ung dung đãi tiệc niêu cơm thần vô tận, cảm hóa muôn vạn binh tướng 18 nước chư hầu.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, noble warrior standing on fortress wall with endless magical tiny clay rice pot, thousands of surrendered soldiers bowing in awe, grand cinematic manga composition",
                "layout_type": "wide"
            }
        ]
    },
    {
        "id": "cay-tre-tram-dot",
        "title": "Cây Tre Trăm Đốt",
        "topic": "Truyện cổ tích dân gian Việt Nam",
        "category": "Truyện cổ tích & Thần thoại",
        "genre": ["Cổ tích", "Dân gian", "Công lý", "Hài hước dân gian"],
        "summary": "Truyện cổ tích về anh Khoai hiền lành, chịu thương chịu khó tìm được cây tre trăm đốt nhờ câu thần chú 'Khắc nhập, khắc xuất' nhiệm màu của ông Bụt, trừng trị phú ông gian xảo.",
        "content": """Ngày xưa có một phú ông giàu nứt đố đổ vách nhưng tính tình vô cùng keo kiệt và tráo trở. Trong nhà có anh đầy tớ tên Khoai, khỏe mạnh, thật thà và chịu thương chịu khó.

Để bóc lột sức lao động của anh Khoai, phú ông hứa gả cô con gái út xinh đẹp cho anh sau ba năm làm lụng không công. Anh Khoai tin lời, ngày đêm cày sâu cuốc bẫm, đắp đập be bờ, giúp phú ông gặt hái lúa thóc đầy bồ, gia sản ngày càng hưng thịnh.

Hết hạn ba năm, phú ông lật lọng, ngấm ngầm nhận lời gả con gái cho con trai một phú hộ giàu có khác trong làng. Để tống khứ anh Khoai đi xa, phú ông bảo: "Con muốn cưới con gái ta thì phải lên rừng tìm cho được cây tre trăm đốt đem về làm đũa ăn cưới, lúc đó ta mới cử hành hôn lễ".

Anh Khoai thật thà vác dao lên rừng sâu tìm kiếm. Anh trèo đèo lội suối, chặt hết bụi tre này đến bụi tre khác nhưng chỉ thấy những cây tre có vài chục đốt, chẳng có cây nào đủ một trăm đốt cả. Bất lực và tủi thân, anh Khoai ngồi bệt bên bìa rừng ôm mặt khóc nức nở.

Bụt hiện lên trong làn khói xanh thơm ngát, râu tóc bạc phơ, cất tiếng hỏi: "Vì sao con khóc?". Anh Khoai đem hết chuyện kể lại. Bụt cười hiền hậu bảo: "Con hãy đi chặt cho đủ một trăm đốt tre rời xếp lại một chỗ, rồi đọc câu thần chú: 'Khắc nhập, khắc xuất!'".

Anh Khoai làm y lời. Khi anh hô "Khắc nhập, khắc nhập!", một trăm đốt tre lập tức dính chặt lại với nhau thành một cây tre dài sừng sững đúng một trăm đốt. Anh mừng rỡ muốn vác về nhưng cây tre quá dài không luồn qua rừng được. Anh liền đọc "Khắc xuất, khắc xuất!", cây tre lập tức rời ra thành một trăm đốt nhỏ như cũ. Anh hớn hở bó lại gánh về làng.

Về đến nhà phú ông, anh thấy cỗ bàn linh đình, gia đình nhà gái đang chuẩn bị rước dâu gả cho tên nhà giàu. Phú ông thấy anh về liền cười nhạo: "Ta bảo tìm cây tre trăm đốt chứ ai bảo mang một đống que củi về!".

Anh Khoai bình tĩnh đặt một trăm đốt tre xuống giữa sân rồi hô lớn: "Khắc nhập, khắc nhập!". Các đốt tre liền dính liền lại thành cây tre dài thẳng tắp. Phú ông kinh ngạc chạy lại sờ tay vào cây tre, anh Khoai liền hô tiếp: "Khắc nhập, khắc nhập!", phú ông bị dính chặt cứng vào thân tre không sao gỡ ra được. Tên thông gia và chú rể chạy lại kéo cũng bị dính luôn thành một chuỗi người quằn quại kêu van xin tha mạng.

Trước sự chứng kiến của dân làng, phú ông phải van lạy anh Khoai và hứa lập tức gả con gái út cho anh. Anh Khoai mới thong thả đọc: "Khắc xuất, khắc xuất!". Cây tre rời ra và mọi người được thả tự do. Lễ cưới ấm cúng của anh Khoai và cô con gái út diễn ra trong tiếng chúc tụng hân hoan của khắp xóm làng.""",
        "characters": [
            {
                "name": "Anh Khoai",
                "role": "lead",
                "gender": "male",
                "dna": "honest 22yo Vietnamese farmer youth, robust sun-tanned build, bright sincere eyes, wearing rustic dark brown peasant tunic and rolled pants, holding bamboo machete"
            },
            {
                "name": "Phú ông",
                "role": "antagonist",
                "gender": "male",
                "dna": "greedy 50yo wealthy landlord, plump physique, cunning eyes, wearing embroidered silk brown robe and traditional turban"
            },
            {
                "name": "Ông Bụt",
                "role": "supporting",
                "gender": "male",
                "dna": "mystical benevolent ancient Vietnamese fairy deity, long flowing snow-white beard and hair, gentle compassionate eyes, glowing celestial robes"
            }
        ],
        "world_setting": "Làng quê đồng bằng Bắc Bộ, rừng tre xanh ngút ngàn và sân đình nhà phú ông.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Anh Khoai ngồi khóc bên bìa rừng rậm rạp khi không thể tìm thấy cây tre đủ một trăm đốt.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, honest 22yo Vietnamese farmer youth weeping beside dense bamboo forest, deep mystical mountain atmosphere, emotional screentone shading",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Bụt hiện lên nhân từ, truyền dạy câu thần chú kỳ diệu 'Khắc nhập, khắc xuất' cho chàng nông dân.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, glowing ancient deity with flowing white beard appearing in mystical mist to teach humble farmer, magical light particles 2D manga",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Tại sân nhà phú ông, anh Khoai hô vang 'Khắc nhập!', một trăm đốt tre liền dính chặt phú ông gian ngoa.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, dramatic comedic scene, bamboo joints joining together magic energy sticking greedy rich landlord to giant tall bamboo pole, villagers laughing, dynamic angle",
                "layout_type": "tall"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Đám cưới hạnh phúc của anh Khoai và người con gái hiền thục diễn ra trong niềm hân hoan của xóm làng.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, traditional joyful Vietnamese countryside wedding, smiling honest farmer and gentle bride in wedding robes, warm festive atmosphere",
                "layout_type": "wide"
            }
        ]
    },
    {
        "id": "an-khe-tra-vang",
        "title": "Ăn Khế Trả Vàng (Cây Khế)",
        "topic": "Truyện cổ tích đạo đức & Nhân quả",
        "category": "Truyện cổ tích & Thần thoại",
        "genre": ["Cổ tích", "Đạo đức", "Nhân quả", "Bài học cuộc sống"],
        "summary": "Truyện cổ tích về hai anh em chia gia tài, người em nhân hậu được chim thần chở đi lấy vàng nhờ cây khế, còn người anh tham lam phải nhận kết cục bi đát.",
        "content": """Ngày xưa, có hai anh em mồ côi cha mẹ. Khi trưởng thành, người anh tham lam chiếm hết ruộng vườn nhà cửa trâu bò, chỉ chia cho người em một túp lều rách nát và một cây khế ngọt cằn cỗi ở góc vườn.

Vợ chồng người em không một lời oán thán, hằng ngày chăm chỉ cày thuê cuốc mướn và dốc lòng chăm sóc, tưới tắm cho cây khế. Đến mùa, cây khế trĩu trịt những chùm quả vàng óng, mọng nước ngọt lịm.

Bỗng một ngày, có một con chim phượng hoàng khổng lồ tuyệt đẹp bay đến đậu trên cành ăn khế. Thấy chim ăn nhiều quả chín, người em than thở: "Chim ơi, gia tài tôi chỉ có mỗi cây khế này để bán kiếm gạo, chim ăn hết thì chúng tôi lấy gì sinh sống?".

Chim phượng hoàng bỗng cất tiếng người êm ái:
"Ăn một quả, trả một cục vàng,
May túi ba gang, mang đi mà đựng."

Người em nghe lời chim, bảo vợ may chiếc túi vải đúng ba gang tay. Sáng hôm sau, chim phượng hoàng bay đến, cõng người em trên lưng rồi vỗ cánh bay qua muôn trùng biển cả đến một hòn đảo hoang ngập tràn vàng bạc châu báu lấp lánh. Người em chỉ nhặt đúng đầy chiếc túi ba gang rồi theo chim bay về. Từ đó, người em trở nên giàu có, mang của cải giúp đỡ bà con nghèo khó trong vùng.

Người anh thấy em giàu lên nhanh chóng bèn sang gặng hỏi. Người em thật thà kể hết mọi chuyện. Người anh liền nằng nặc đòi đổi toàn bộ gia sản đồ sộ của mình để lấy cây khế cằn cỗi.

Đến mùa khế chín, chim phượng hoàng lại bay về ăn. Người anh giả vờ khóc lóc than thở, chim cũng đáp lại câu dặn may túi ba gang. Nhưng với lòng tham vô đáy, người anh đã may một chiếc túi to mười hai gang và dắt thêm bao tải quanh người.

Khi chim cõng người anh đến đảo vàng, hắn điên cuồng vơ vét vàng bạc ngọc ngà nhét đầy túi mười hai gang, lại còn nhét thêm vào túi áo túi quần. Trên đường bay trở về qua biển lớn, gió to sóng dữ nổi lên, chim phượng hoàng quá nặng nhọc kiệt sức nghiêng cánh. Chiếc túi vàng nặng trĩu kéo người anh rơi tũm xuống đáy biển sâu, còn chim phượng hoàng bay vút lên bầu trời cao rộng.""",
        "characters": [
            {
                "name": "Người em",
                "role": "lead",
                "gender": "male",
                "dna": "kind 20yo Vietnamese farmer, gentle sincere eyes, warm smile, wearing modest dark indigo traditional peasant clothing"
            },
            {
                "name": "Người anh",
                "role": "antagonist",
                "gender": "male",
                "dna": "greedy 30yo wealthy man, gluttonous heavy build, covetous sharp eyes, wearing opulent silk brocade robe"
            },
            {
                "name": "Chim Phượng Hoàng Thần",
                "role": "supporting",
                "gender": "unknown",
                "dna": "majestic giant mythical celestial bird, iridescent luminous feathers glowing with golden divine aura, majestic wingspan"
            }
        ],
        "world_setting": "Mảnh vườn nghèo bên cây khế trĩu quả và hòn đảo vàng bí ẩn giữa đại dương bao la.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Dưới bóng cây khế sai trĩu quả vàng mọng, người em hiền hậu ngước nhìn chim phượng hoàng khổng lồ đáp xuống.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, kind humble Vietnamese farmer standing under lush starfruit tree heavy with ripe fruits looking up at giant mythical phoenix bird, peaceful village setting",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Chim phượng hoàng dang rộng đôi cánh rực rỡ, cõng người em bay qua biển lớn hướng về đảo vàng kỳ bí.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, majestic giant divine bird flying above vast ocean carrying humble youth on its back, clouds and waves screentone, epic fantasy composition",
                "layout_type": "tall"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Trên đảo vàng hoang sơ, người em chỉ lấy vừa vặn chiếc túi ba gang đúng như lời chim thần dặn dò.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, honest youth picking moderate gold gems into a small modest three-span cloth bag on rocky treasure island, ethical restraint, medium close-up",
                "layout_type": "square"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Giữa biển sâu sóng cuộn, người anh tham lam ôm bọc vàng quá nặng rơi xuống biển trong sự hối hận muộn màng.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, dramatic stormy ocean climax, greedy man falling into raging sea waves weighed down by enormous heavy bags of gold, divine bird soaring away into sky",
                "layout_type": "wide"
            }
        ]
    },
    {
        "id": "su-tich-banh-chung-banh-giay",
        "title": "Sự tích Bánh Chưng Bánh Giầy",
        "topic": "Truyền thuyết thời đại Hùng Vương",
        "category": "Truyền thuyết & Thần thoại",
        "genre": ["Truyền thuyết", "Vua Hùng", "Văn hóa ẩm thực", "Đạo hiếu"],
        "summary": "Truyền thuyết thời Vua Hùng thứ 6 về chàng hoàng tử Lang Liêu hiếu thảo, dùng hạt gạo nếp quê hương làm nên bánh Chưng vuông tượng trưng cho Đất và bánh Giầy tròn tượng trưng cho Trời.",
        "content": """Đời Hùng Vương thứ sáu, sau khi đánh tan giặc Ân, đất nước thái bình, nhà vua muốn truyền ngôi cho con. Vua có hai mươi người con trai, ai cũng tài giỏi. Vua bèn mở hội truyền rằng: "Ta muốn truyền ngôi cho người biết nối chí ta, không nhất thiết là con trưởng. Đến ngày đầu xuân, ai dâng được lễ vật cúng Tiên vương vừa ý ta nhất, thể hiện được lòng hiếu thảo và ý nghĩa sâu xa, ta sẽ truyền ngôi báu cho".

Các hoàng tử đua nhau sai người lên rừng săn muông thú quý hiếm, lặn lội xuống biển sâu mò ngọc trai ngà voi, đồi mồi, sơn hào hải vị với hy vọng đoạt được ngai vàng.

Duy chỉ có người con trai thứ mười tám tên là Lang Liêu, mồ côi mẹ từ nhỏ, tính tình khiêm nhường, gần gũi với nhân dân đồng ruộng là vô cùng lo lắng. Chàng nghĩ mình chỉ quen với việc cấy cày trồng trọt, lấy đâu ra của ngon vật lạ như các anh em.

Một đêm nọ, Lang Liêu nằm mộng thấy một vị Thần nhân râu tóc bạc phơ hiện ra bảo chàng: "Trong trời đất, không có gì quý bằng hạt gạo, vì hạt gạo nuôi sống con người. Ngươi hãy lấy gạo nếp thơm làm chiếc bánh hình tròn tượng trưng cho Trời, và chiếc bánh hình vuông tượng trưng cho Đất, ở trong bọc nhân ngon, đặt lá xanh bên ngoài bọc kín. Đó chính là lễ vật quý giá nhất dâng lên Tiên vương".

Tỉnh dậy, Lang Liêu vô cùng mừng rỡ. Chàng chọn những hạt nếp cái hoa vàng mẩy tròn nhất, đỗ xanh đãi sạch vỏ, thịt lợn ba chỉ ướp tiêu thơm nồng. Chàng dùng lá dong xanh mướt gói thành chiếc bánh vuông vắn, đem luộc chín kỹ suốt một ngày một đêm, gọi là Bánh Chưng tượng trưng cho Đất mẹ sinh sôi muôn loài. Chàng lại lấy nếp thơm đồ xôi, giã nhuyễn rồi nặn thành hình tròn trắng muốt, mịn màng, gọi là Bánh Giầy tượng trưng cho Bầu Trời che chở.

Đến ngày hẹn, các hoàng tử dâng lên mâm cao cỗ đầy gấm vóc, sơn hào hải vị. Đến lượt Lang Liêu chỉ dâng lên hai mâm bánh mộc mạc làm từ hạt gạo quê hương. Vua Hùng nếm thử, tấm tắc khen hương vị thơm ngon đậm đà, bèn hỏi ý nghĩa.

Lang Liêu đem lời dạy của Thần kể lại rành mạch. Vua Hùng xúc động rơi lệ phán trước quần thần: "Bánh của Lang Liêu không chỉ ngon miệng mà còn chứa đựng đạo lý bao la của Đất Trời, công ơn sinh thành dưỡng dục của cha mẹ và tôn vinh hạt ngọc của người nông dân cày cấy".

Vua Hùng quyết định truyền ngôi báu cho Lang Liêu. Từ đó, cứ mỗi dịp Tết Nguyên Đán cổ truyền, người Việt Nam luôn gói bánh Chưng bánh Giầy dâng cúng tổ tiên để ghi nhớ cội nguồn dân tộc.""",
        "characters": [
            {
                "name": "Lang Liêu",
                "role": "lead",
                "gender": "male",
                "dna": "noble 20yo Vietnamese prince of Hung Kings era, humble sincere expression, athletic graceful posture, wearing ancient bronze-age patterned sash and dark indigo woven tunic"
            },
            {
                "name": "Hùng Vương thứ 6",
                "role": "supporting",
                "gender": "male",
                "dna": "venerable 60yo King of Van Lang, majestic benevolent beard, wearing royal bronze feather headdress and red embroidered ancient robe"
            }
        ],
        "world_setting": "Kinh đô Phong Châu thời Hùng Vương, bếp lửa bập bùng nấu bánh đêm đông và núi non Văn Lang hùng vĩ.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Lang Liêu ngồi trầm ngâm bên hiên nhà sàn, trăn trở tìm lễ vật ý nghĩa dâng lên vua cha.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, thoughtful young Vietnamese prince in ancient Van Lang tunic sitting on rustic wooden veranda looking at rice fields, night moonlight screentone",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Trong giấc mộng thanh khiết, vị Thần nhân chỉ dẫn chàng bí quyết tạo nên bánh Chưng và bánh Giầy từ hạt gạo nếp.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, mystical celestial deity in dream realm imparting divine wisdom to sleeping prince, ethereal light rays and rice grain aura",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Bên bếp lửa hồng bập bùng suốt đêm đông, Lang Liêu cẩn trọng canh nồi bánh Chưng thơm ngát mùi lá dong nếp mới.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, dedicated young prince tending large boiling pot over glowing campfire at night, warm flickering shadows, atmospheric cozy manga style",
                "layout_type": "square"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Vua Hùng nâng mâm bánh Chưng bánh Giầy khen ngợi trước triều đình và truyền lại ngôi báu cho Lang Liêu.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, ancient Vietnamese King on carved wooden throne tasting square and round rice cakes, proclaiming humble prince as new king before cheering courtiers",
                "layout_type": "tall"
            }
        ]
    },
    {
        "id": "thanh-giong",
        "title": "Thánh Gióng (Phù Đổng Thiên Vương)",
        "topic": "Truyền thuyết anh hùng dân tộc",
        "category": "Truyền thuyết & Thần thoại",
        "genre": ["Truyền thuyết", "Tứ bất tử", "Chống giặc ngoại xâm", "Anh hùng"],
        "summary": "Truyền thuyết về cậu bé làng Gióng lên ba chưa biết nói cười, khi giặc Ân tràn vào bờ cõi bỗng vươn vai thành tráng sĩ cưỡi ngựa sắt, nhổ tre ngà quét sạch quân xâm lược rồi bay về trời.",
        "content": """Đời Hùng Vương thứ sáu, ở làng Phù Đổng có hai vợ chồng già hiền lành chăm chỉ nhưng mãi chưa có con. Một hôm người vợ ra đồng thấy một vết chân khổng lồ, bèn đặt chân vào ướm thử. Về nhà bà thụ thai, mười hai tháng sau sinh ra một cậu bé khôi ngô, đặt tên là Gióng. Kỳ lạ thay, lên ba tuổi cậu bé vẫn không biết nói, không biết cười, đặt đâu nằm đấy.

Bấy giờ giặc Ân hung tàn kéo sang xâm lược nước ta, thế giặc rất mạnh. Vua Hùng lo lắng sai sứ giả đi khắp nơi tìm người tài giỏi cứu nước.

Khi sứ giả đi ngang qua làng Phù Đổng gióng trống loan truyền lệnh vua, cậu bé Gióng bỗng nhiên cất tiếng nói đầu tiên bảo mẹ: "Mẹ ra mời sứ giả vào đây cho con!".

Trước mặt sứ giả, cậu bé dõng dạc phán: "Ông về tâu với đức vua đúc cho ta một con ngựa sắt, một thanh gươm sắt, một bộ áo giáp sắt và một chiếc nón sắt, ta sẽ phá tan lũ giặc này!".

Sứ giả kinh ngạc vội về tâu vua. Vua Hùng mừng rỡ lập tức tập hợp thợ rèn ngày đêm đúc ngựa sắt và binh giáp.

Từ ngày đó, Gióng lớn nhanh như thổi. Cơm ăn bao nhiêu cũng không no, áo vừa may xong đã chật ních. Dân làng Phù Đổng nô nức gom góp từng nồi cơm, cà pháo, mo cơm nuôi Gióng lớn khôn vì nghĩa lớn.

Khi giặc Ân đã tiến sát chân núi Trâu Sơn, sứ giả đem ngựa sắt và giáp sắt tới. Gióng vươn vai một cái bỗng biến thành một tráng sĩ khổng lồ, mình cao hơn trượng, oai phong lẫm liệt. Tráng sĩ mặc giáp sắt, cầm gươm sắt, nhảy lên lưng ngựa. Con ngựa sắt hí vang một tiếng dài, phun lửa đỏ rực rồi phi như bay ra trận.

Tráng sĩ xông thẳng vào đồn giặc, vung gươm chém giặc như chém chuối, giặc Ân ngã rạ la liệt. Gươm sắt gãy, tráng sĩ không hề nao núng, liền nhổ từng bụi tre ngà bên đường quật túi bụi vào quân thù khiến giặc tan tác tháo chạy.

Quét sạch bóng giặc Ân, tráng sĩ một mình một ngựa phi thẳng lên đỉnh núi Sóc Sơn. Tại đây, người cởi giáp sắt để lại rồi cùng ngựa sắt từ từ bay thẳng lên trời cao.

Để tưởng nhớ công ơn cứu nước, vua Hùng phong chàng là Phù Đổng Thiên Vương và lập đền thờ tại quê nhà làng Gióng, phong làm một trong Tứ bất tử của dân tộc Việt Nam.""",
        "characters": [
            {
                "name": "Thánh Gióng",
                "role": "lead",
                "gender": "male",
                "dna": "legendary giant Vietnamese warrior deity, towering heroic build, resolute divine piercing eyes, wearing heavy ancient iron armor plates and holding iron sword and bamboo stalk"
            }
        ],
        "world_setting": "Làng Phù Đổng thanh bình, chiến trường rực lửa Trâu Sơn và đỉnh non cao Sóc Sơn linh thiêng.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Cậu bé Gióng lên ba bỗng cất tiếng nói thiêng liêng đầu tiên, nhờ mẹ mời sứ giả cứu nước vào nhà.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, miraculous young 3yo boy speaking clearly to amazed mother and royal envoy inside rustic ancient straw house, mystical atmosphere",
                "layout_type": "square"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Dân làng Phù Đổng nô nức chung tay gom từng bát gạo, quả cà nuôi chàng tráng sĩ lớn nhanh như thổi.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, united ancient Vietnamese villagers offering large bowls of rice to rapidly growing giant heroic youth, heartwarming community spirit",
                "layout_type": "wide"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Tráng sĩ Gióng cưỡi ngựa sắt phun lửa rực trời, nhổ từng bụi tre ngà quét sạch bóng quân xâm lược.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, epic battle scene, giant warrior hero riding armored horse breathing flames, swinging large bamboo cluster defeating enemy hordes, dynamic perspective",
                "layout_type": "tall"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Trên đỉnh núi Sóc Sơn lộng gió, Thánh Gióng cởi giáp sắt rồi cùng ngựa thiêng từ từ bay về cõi trời bất tử.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, majestic hero riding celestial iron horse ascending into glowing cloud sky from windy mountain peak, divine transcendent departure",
                "layout_type": "wide"
            }
        ]
    }
]

def seed_database_and_pipeline():
    print("==================================================")
    print("🌱 SEEDING RICH VIETNAMESE STORIES & FOLKTALES 🌱")
    print("==================================================")

    # 1. Update queue.json
    queue_data = {"version": 1, "stories": []}
    if os.path.exists(ROOT_QUEUE_PATH):
        try:
            with open(ROOT_QUEUE_PATH, "r", encoding="utf-8") as f:
                queue_data = json.load(f)
        except Exception:
            queue_data = {"version": 1, "stories": []}

    existing_ids = {s["id"] for s in queue_data.get("stories", []) if isinstance(s, dict) and "id" in s}

    for item in STORIES_CATALOG:
        if item["id"] not in existing_ids:
            queue_data["stories"].append({
                "id": item["id"],
                "title": item["title"],
                "topic": item["topic"],
                "category": item["category"],
                "genre": item["genre"],
                "language": "vi",
                "sourceLanguages": ["vi", "en"],
                "status": "merged",
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "updatedAt": datetime.now(timezone.utc).isoformat(),
                "prUrl": f"https://github.com/anhdinh0701/final/pull/{len(queue_data['stories'])+1}",
                "prNumber": len(queue_data["stories"]) + 1,
                "branchName": f"ai-stories/{item['id']}",
                "error": None
            })

    for q_path in [ROOT_QUEUE_PATH, BACKEND_QUEUE_PATH]:
        with open(q_path, "w", encoding="utf-8") as f:
            json.dump(queue_data, f, ensure_ascii=False, indent=2)
    print(f"✅ Updated {ROOT_QUEUE_PATH} and {BACKEND_QUEUE_PATH} with {len(queue_data['stories'])} stories.")

    # 2. Save JSON Story Files
    for item in STORIES_CATALOG:
        story_file_data = {
            "id": item["id"],
            "title": item["title"],
            "slug": item["id"],
            "topic": item["topic"],
            "category": item["category"],
            "genre": item["genre"],
            "summary": item["summary"],
            "content": item["content"],
            "characters": item["characters"],
            "world_setting": item["world_setting"],
            "panels": item["panels"],
            "metadata": {
                "language": "vi",
                "wordCount": len(re.findall(r'\S+', item["content"])),
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "aiModel": "NarrAI-Engine-Pro",
                "status": "published"
            }
        }
        for target_dir in [ROOT_STORIES_DIR, BACKEND_STORIES_DIR]:
            fpath = os.path.join(target_dir, f"{item['id']}.json")
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(story_file_data, f, ensure_ascii=False, indent=2)
    print(f"✅ Generated {len(STORIES_CATALOG)} story files in data/stories/ & backend/data/stories/.")

    # 3. Seed Database (Stories, Users, Comics, Social Posts)
    db = SessionLocal()
    try:
        # Ensure default author user exists
        author = db.query(User).filter(User.username == "admin").first()
        if not author:
            author = db.query(User).filter(User.username == "admin_pipeline").first()
        if not author:
            author = User(
                username="admin_pipeline",
                full_name="Trạm Biên Soạn NarrAI",
                password_hash=get_password_hash("Admin123!"),
                coins=100000
            )
            db.add(author)
            db.commit()
            db.refresh(author)

        for item in STORIES_CATALOG:
            session_id = f"pipeline_{item['id']}"
            existing_story = db.query(Story).filter(Story.session_id == session_id).first()
            if not existing_story:
                new_story = Story(
                    session_id=session_id,
                    user_id=author.id,
                    initial_prompt=item["title"],
                    refined_prompt=item["summary"],
                    genre=", ".join(item["genre"]),
                    tone="Hào hùng, nhân văn và thấm đẫm bản sắc văn hóa Việt Nam",
                    story_content=item["content"],
                    word_count=len(re.findall(r'\S+', item["content"])),
                    bible_data=json.dumps({
                        "title": item["title"],
                        "characters": item["characters"],
                        "world_setting": item["world_setting"],
                        "cultural_tier": 1
                    }, ensure_ascii=False),
                    memory_data=json.dumps({
                        "story_beats": [p["dialogue_text"] for p in item["panels"]]
                    }, ensure_ascii=False)
                )
                db.add(new_story)
                db.commit()
                db.refresh(new_story)
                existing_story = new_story

            # Ensure Comic & ComicPanels
            comic = db.query(Comic).filter(Comic.story_id == existing_story.id).first()
            if not comic:
                comic = Comic(
                    user_id=author.id,
                    story_id=existing_story.id,
                    title=item["title"],
                    adapted_offset=len(item["content"])
                )
                db.add(comic)
                db.commit()
                db.refresh(comic)

                for p in item["panels"]:
                    panel = ComicPanel(
                        comic_id=comic.id,
                        panel_index=p["panel_index"],
                        image_prompt=p["image_prompt"],
                        dialogue_text=p["dialogue_text"],
                        layout_type=p.get("layout_type", "square"),
                        image_url=""
                    )
                    db.add(panel)
                    db.commit()
                    db.refresh(panel)
                    panel.image_url = f"/api/comic/image/{panel.id}"
                db.commit()

            # Ensure SocialPost for Community Feed / Discovery
            existing_post = db.query(SocialPost).filter(SocialPost.story_id == existing_story.id).first()
            if not existing_post:
                social_post = SocialPost(
                    user_id=author.id,
                    story_id=existing_story.id,
                    title=item["title"],
                    content_snippet=item["summary"],
                    genre=item["genre"][0] if item["genre"] else "Cổ tích",
                    tags=json.dumps(item["genre"], ensure_ascii=False),
                    likes_count=128,
                    comments_count=24,
                    views_count=1560,
                    completion_count=89
                )
                db.add(social_post)
                db.commit()

        print(f"✅ Successfully seeded {len(STORIES_CATALOG)} complete stories, comic panels, and social posts to Database!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database_and_pipeline()
