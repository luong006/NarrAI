import os
import sys
import json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

stories_data = [
    # ==================== TRUYỆN CỔ TÍCH ====================
    {
        "id": "so-dua",
        "title": "Sọ Dừa",
        "slug": "so-dua",
        "topic": "Truyện cổ tích kỳ ảo & Đạo đức dân gian",
        "category": "Truyện Cổ Tích",
        "genre": ["Cổ tích", "Dân gian", "Kỳ ảo", "Đạo đức", "Tình yêu"],
        "summary": "Truyện cổ tích ca ngợi vẻ đẹp tâm hồn và tài năng tiềm ẩn của chàng Sọ Dừa dị hình dị dạng, cùng lòng nhân hậu thủy chung của cô út phú ông vượt qua muôn vàn thử thách hiểm nghèo.",
        "content": """Ngày xưa ở một làng nọ, có hai vợ chồng nghèo đi ở cho phú ông. Đã ngoài năm mươi mà họ vẫn chưa có mụn con nào. Một hôm người vợ vào rừng đốn củi, khát nước quá, thấy cái sọ dừa bên gốc cây đựng đầy nước mưa liền bưng lên uống. Về nhà bà thụ thai, ít lâu sau sinh ra một đứa bé tròn lông lốc như quả dừa, không chân không tay nhưng biết nói cười. Người mẹ toan vứt đi, đứa bé khóc van xin: \"Mẹ ơi, con là người đấy, mẹ đừng vứt con!\". Bà thương tình giữ lại nuôi và đặt tên là Sọ Dừa.

Lớn lên, Sọ Dừa xin mẹ đến chăn bò cho phú ông. Phú ông ngần ngại nhưng thấy cậu bé chẳng tốn cơm gạo lại không đòi công xá cao nên đồng ý. Kỳ lạ thay, ngày ngày Sọ Dừa lăn đàn bò ra đồng, con nào con nấy béo mẫm, no tròn, chiều đến lại lăn về chuồng đủ số. Phú ông rất hài lòng.

Đến mùa gặt, ba cô con gái của phú ông thay phiên nhau đem cơm ra đồng cho Sọ Dừa. Hai cô chị kiêu kỳ, khinh bỉ cậu bé dị hình; chỉ có cô út hiền thục, nết na luôn đối xử nhân hậu với chàng. Một trưa hè oi ả, cô út mang cơm đến, bỗng nghe tiếng sáo véo von, êm ái vọng lại từ rặng tre. Nàng rón rén bước tới nhìn thì kinh ngạc thấy một chàng thanh niên tuấn tú, khôi ngô đang ngồi trên võng đào thổi sáo cho đàn bò gặm cỏ. Vừa thấy bóng người, chàng thanh niên lại biến thành Sọ Dừa tròn lông lốc. Từ đó, cô út đem lòng thầm thương trộm nhớ chàng.

Cuối năm, Sọ Dừa về bảo mẹ sang hỏi con gái phú ông làm vợ. Mẹ chàng ái ngại nhưng thương con đành sang ướm lời. Phú ông cười khẩy thách cưới: một chĩnh vàng cốm, mười tấm lụa đào, mười con lợn béo và mười vò rượu tăm. Cứ ngỡ Sọ Dừa sẽ bỏ cuộc, nhưng đúng ngày hẹn, Sọ Dừa mang đủ sính lễ lộng lẫy cùng đoàn gia nhân khiêng kiệu hoa sang rước dâu. Phú ông hỏi ba người con gái, hai cô chị bĩu môi từ chối, chỉ có cô út e thẹn gật đầu bằng lòng.

Đêm tân hôn, Sọ Dừa hiện nguyên hình là một chàng trai khôi ngô tuấn tú, hào hoa phong nhã khiến cô út vô cùng sung sướng. Sọ Dừa ngày đêm miệt mài đèn sách. Năm ấy triều đình mở khoa thi, chàng đỗ Trạng nguyên vinh hiển. Trước khi lên đường đi sứ, chàng trao cho vợ một con dao pha, hai hòn đá lửa và hai quả trứng gà, dặn nàng luôn mang theo bên mình phòng khi nguy cấp.

Hai cô chị ghen ghét em út lấy được chồng hiển đạt, liền rủ cô út chèo thuyền ra biển ngắm cảnh rồi xô nàng xuống dòng nước xiết. Cô út bị một con cá kình khổng lồ nuốt vào bụng. Nhớ lời chồng dặn, nàng rút dao đâm chết cá kình. Xác cá trôi dạt vào một hoang đảo. Nàng mổ bụng cá chui ra, dùng đá lửa nhóm lửa nướng thịt cá ăn qua ngày. Hai quả trứng gà nở thành hai chú gà con, chẳng mấy chốc thành gà trống gáy vang.

Một hôm, thấy thuyền lớn đi ngang qua đảo, chú gà trống bay lên mỏm đá cất tiếng gáy: \"Ò… ó… o… Phải thuyền quan Trạng rước cô tôi về!\". Quan Trạng Sọ Dừa cho thuyền ghé vào đảo, hai vợ chồng mừng rỡ hội ngộ. Chàng đưa vợ về nhà mở tiệc ăn mừng, hai cô chị xấu hổ lẻn trốn đi biệt tích. Từ đó, vợ chồng Quan Trạng sống hạnh phúc, đức độ trọn đời.""",
        "characters": [
            {
                "name": "Sọ Dừa",
                "role": "lead",
                "gender": "male",
                "dna": "handsome young Vietnamese scholar, noble refined face, piercing wise eyes, wearing majestic crimson Mandarin court robe with embroidered dragon badge and scholar gauze cap"
            },
            {
                "name": "Cô Út",
                "role": "lead",
                "gender": "female",
                "dna": "gentle 18yo Vietnamese rural maiden, serene kind face, warm compassionate eyes, jet-black hair tied in silk headband, wearing traditional pastel green ao tu than"
            },
            {
                "name": "Phú Ông",
                "role": "supporting",
                "gender": "male",
                "dna": "elderly wealthy Vietnamese landlord, greedy calculating gaze, mustache, wearing rich dark silk gown holding traditional folding fan"
            }
        ],
        "world_setting": "Làng quê đồng bằng Bắc Bộ trù phú, rặng tre xanh ngắt, bờ biển hoang sơ và cảnh đón rước Trạng nguyên rực rỡ cờ hoa.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Dưới bóng tre trưa hè mát rượi, cô út sững sờ ngắm nhìn chàng thanh niên khôi ngô đang thổi sáo êm đềm.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, handsome Vietnamese youth playing bamboo flute sitting under lush bamboo grove, gentle maiden peeking with shy admiration behind tree, delicate screentone",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Trước sự ngỡ ngàng của phú ông, đoàn gia nhân rước sính lễ vàng ngọc lộng lẫy tiến vào sân nhà.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, lavish traditional Vietnamese wedding betrothal procession, bearers carrying ornate lacquer trays of gold and silk, astonished wealthy landlord looking on, high contrast manga style",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Bị dạt vào hoang đảo, cô út kiên cường dùng đá lửa nhóm lửa sưởi ấm bên chú gà trống nhỏ.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, resilient gentle young Vietnamese woman striking flint sparks by stone campfire on rocky desolate island shore, cute rooster chick nearby, dynamic lighting manga screentone",
                "layout_type": "square"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Thuyền quan Trạng cập bờ, vợ chồng Sọ Dừa ôm nhau mừng mừng tủi tủi sau bao thử thách gian truân.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, emotional reunion of handsome noble Mandarin official and his beloved resilient wife on shoreline, grand royal vessel in background, warm emotional climax 2D manga lineart",
                "layout_type": "wide"
            }
        ]
    },
    {
        "id": "su-tich-trau-cau",
        "title": "Sự tích Trầu Cau",
        "slug": "su-tich-trau-cau",
        "topic": "Truyền thuyết đạo nghĩa & Tình cảm gia đình",
        "category": "Truyện Cổ Tích",
        "genre": ["Cổ tích", "Truyền thuyết", "Gia đình", "Nghĩa vợ chồng", "Tình anh em"],
        "summary": "Câu chuyện cảm động ngàn đời về tình anh em ruột thịt keo sơn và nghĩa vợ chồng thủy chung son sắt hóa thân thành cây cau, tảng đá vôi và dây trầu quấn quýt, khởi nguồn cho phong tục ăn trầu thắm đượm văn hóa Việt.",
        "content": """Vào đời vua Hùng thứ tư, có hai anh em sinh đôi tên là Cao Tân và Cao Lang, giống nhau như hai giọt nước, người ngoài khó lòng phân biệt được. Cha mẹ mất sớm, hai anh em cùng theo học cụ đồ họ Lưu. Thầy Lưu có một cô con gái xinh đẹp, dịu dàng đem lòng mến mộ đức độ của hai chàng trai. Nàng muốn kén người anh làm chồng nhưng không biết ai là anh ai là em. Một hôm nàng dọn một bát cháo cùng một đôi đũa mời hai người. Thấy Cao Lang kính cẩn nhường đũa cho Cao Tân ăn trước, nàng liền nhận ra và xin cha gả cho người anh.

Sau ngày cưới, hai vợ chồng chung sống êm ấm. Nhưng Cao Tân vì mải chăm lo hạnh phúc riêng nên tình cảm đối với em có phần lạt lẽo hơn trước. Cao Lang cảm thấy tủi thân nhưng không dám hé răng than thở. Một hôm hai anh em cùng đi làm đồng về muộn, Cao Lang vào nhà trước. Người vợ trong bóng hoàng hôn nhập nhoạng tưởng là chồng liền chạy ra ôm chầm lấy. Vừa lúc đó Cao Tân bước vào cửa, thấy cảnh tượng ấy liền sinh lòng ngờ vực, giận dỗi em.

Cao Lang vô cùng đau xót và uất ức. Chàng không muốn gia đình chia rẽ, liền lặng lẽ ra đi trong đêm tối. Chàng đi mãi, đi mãi về phương Nam cho đến khi gặp một con sông lớn nước chảy cuồn cuộn không sao qua được. Kiệt sức vì đói và thương tâm, chàng ngồi bên bờ sông ôm mặt khóc cho đến chết, hóa thành một tảng đá vôi trắng muốt.

Ở nhà không thấy em đâu, Cao Tân hối hận khôn xiết. Chàng từ biệt vợ rồi lần theo dấu vết em đi tìm. Đi mãi đến bờ sông, thấy tảng đá vôi lạ lùng, chàng ngồi tựa vào đó khóc than rồi kiệt sức qua đời, hóa thành một thân cây thẳng đứng vút lên trời, trên ngọn có chùm quả hình trứng, đó là cây cau.

Người vợ ở nhà chờ đợi mỏi mòn, lòng dạ như thiêu như đốt, cũng quyết định khăn gói đi tìm chồng. Nàng đến bờ sông, thấy cây cau mọc cạnh tảng đá vôi liền ngồi dưới gốc cây than khóc. Nàng chết đi và biến thành một dây leo xanh biếc quấn chặt lấy thân cây cau, lá có vị cay nồng, đó là cây trầu không.

Ít lâu sau, vua Hùng vi hành qua vùng ấy, nghe dân chúng kể lại câu chuyện tình cảm éo le và thủy chung son sắt của ba người, vua vô cùng xúc động. Vua sai hái một quả cau cùng một lá trầu nhai thử, rồi nhổ nước xuống tảng đá vôi thì thấy một dòng nước đỏ tươi thắm đượm và mùi thơm ngát tỏa ra. Vua phán: \"Thật là thứ gắn kết tình nghĩa keo sơn của anh em, vợ chồng!\". Từ đó, vua truyền cho muôn dân trồng trầu cau và dùng trong mọi dịp cưới hỏi, giỗ chạp, mở đầu cho tục ăn trầu thắm đượm tình nghĩa của dân tộc Việt Nam.""",
        "characters": [
            {
                "name": "Cao Tân",
                "role": "lead",
                "gender": "male",
                "dna": "traditional young Vietnamese husband, honest handsome countenance, wearing brown linen peasant robe with woven headband"
            },
            {
                "name": "Cao Lang",
                "role": "lead",
                "gender": "male",
                "dna": "twin brother of Cao Tan, delicate compassionate eyes, loyal sensitive expression, wearing traditional rustic farmer attire"
            },
            {
                "name": "Nàng Lưu Thị",
                "role": "lead",
                "gender": "female",
                "dna": "virtuous beautiful Vietnamese wife, tearful expressive eyes, traditional rustic purple ao tu than and silk kerchief"
            }
        ],
        "world_setting": "Bờ sông hoang sơ thời các vua Hùng, tảng đá vôi trắng muốt, hàng cau cao vút và giàn trầu xanh biếc ngát hương.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Cao Lang ôm mặt nghẹn ngào bên bờ sông vắng, trút hơi thở cuối cùng hóa thành tảng đá vôi ngàn năm.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, sorrowful young Vietnamese man weeping by surging riverbank in twilight, collapsing beside waters, emotional dramatic composition manga style",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Tìm được dấu vết em, Cao Tân gục đầu bên tảng đá, hóa thành cây cau vươn thẳng hiên ngang giữa đất trời.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, remorseful brother embracing ancient white limestone rock, supernatural mist rising transforming into tall slender areca palm tree, dramatic screentone",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Người vợ tìm đến bờ sông, hóa thành dây trầu xanh biếc quấn chặt lấy thân cau trong tình nghĩa thủy chung son sắt.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, devoted Vietnamese maiden leaning against tall palm tree, betel vine entwining tenderly around trunk, spiritual emotional aura manga screentone",
                "layout_type": "square"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Vua Hùng nâng lá trầu quả cau, xúc động ngợi ca biểu tượng tình nghĩa thiêng liêng lưu truyền muôn đời.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, ancient revered Vietnamese Hung King in ornate tribal bronze headdress inspecting betel leaf and areca nut, admiring crimson stain, regal historical manga lineart",
                "layout_type": "wide"
            }
        ]
    },
    {
        "id": "son-tinh-thuy-tinh",
        "title": "Sơn Tinh Thủy Tinh",
        "slug": "son-tinh-thuy-tinh",
        "topic": "Truyền thuyết thời Hùng Vương & Thiên nhiên",
        "category": "Truyện Cổ Tích",
        "genre": ["Cổ tích", "Truyền thuyết", "Thần thoại", "Hùng Vương", "Kỳ ảo"],
        "summary": "Truyền thuyết hùng tráng giải thích hiện tượng bão lũ hàng năm qua trận chiến kinh thiên động địa giữa thần núi Tản Viên Sơn Tinh và chúa tể sông biển Thủy Tinh để rước công chúa Mỵ Nương.",
        "content": """Hùng Vương thứ mười tám có một người con gái tên là Mỵ Nương, nhan sắc tuyệt trần, tính nết đoan trang hiền dịu. Vua cha yêu thương nàng hết mực, muốn kén cho nàng một người chồng thật xứng đáng.

Một hôm, có hai chàng trai cùng đến cầu hôn. Một người tự xưng là Sơn Tinh, chúa miền non cao Tản Viên, có tài vẫy tay về phía đông, phía đông nổi cồn bãi; vẫy tay về phía tây, phía tây mọc lên từng dãy núi non trùng điệp. Người kia tự xưng là Thủy Tinh, chúa vùng nước thẳm biển sâu, có tài gọi gió gió đến, hô mưa mưa về, dâng nước ngập tràn đồng bãi. Cả hai đều có phép thần thông biến hóa, ngang tài ngang sức khiến vua Hùng băn khoăn không biết chọn ai.

Sau khi bàn bạc cùng các lạc hầu, vua Hùng phán: \"Hai người đều tài ba phi thường, nhưng ta chỉ có một con gái. Ngày mai, ai đem sính lễ đến trước sẽ được rước Mỵ Nương về làm vợ. Sính lễ gồm: một trăm ván cơm nếp, một trăm tiệp bánh chưng, voi chín ngà, gà chín cựa, ngựa chín hồng mao, mỗi thứ một đôi\".

Hôm sau, từ tinh mơ gà gáy, Sơn Tinh đã đem đầy đủ sính lễ quý giá đến trước sân rồng. Vua Hùng mừng rỡ gả công chúa Mỵ Nương cho Sơn Tinh. Sơn Tinh rước nàng về núi cao Tản Viên trong tiếng kèn trống rộn rã.

Thủy Tinh đến sau, không lấy được vợ liền đùng đùng nổi giận, tập hợp quân binh đuổi theo hòng cướp lại Mỵ Nương. Thủy Tinh hô mưa, gọi gió, làm rung chuyển đất trời, dâng nước sông lên cuồn cuộn ngập tràn đồng ruộng, nhà cửa, thành Phong Châu nổi lềnh bềnh trên biển nước đỏ ngầu.

Sơn Tinh không hề nao núng. Thần dùng phép màu dời từng quả đồi, dựng từng dãy núi chặn đứng dòng nước xiết. Nước dâng cao bao nhiêu, đồi núi của Sơn Tinh lại cao lên bấy nhiêu. Dân chúng trên núi cùng nhau giã gạo, bắn nỏ, lăn đá đánh trả quân thủy quái. Hai bên giao tranh kịch liệt suốt nhiều ngày đêm. Cuối cùng, Thủy Tinh đuối sức, phép cạn, đành phải rút quân về biển sâu.

Từ đó oán thù khắc sâu, năm nào cũng vậy, cứ vào khoảng tháng bảy tháng tám, Thủy Tinh lại dâng nước làm mưa bão ngập lụt đánh Sơn Tinh. Nhưng lần nào cũng vậy, Thủy Tinh đều chuốc lấy thất bại trước sự kiên cường của thần núi Tản Viên.""",
        "characters": [
            {
                "name": "Sơn Tinh",
                "role": "lead",
                "gender": "male",
                "dna": "majestic mountain deity Tan Vien, powerful muscular physique, resolute heroic eyes, wearing traditional bronze battle chestplate and tribal feathered headband wielding earth magic staff"
            },
            {
                "name": "Thủy Tinh",
                "role": "antagonist",
                "gender": "male",
                "dna": "fierce oceanic water lord, wild aquatic flowing dark hair, sharp ruthless gaze, dark scaled armor holding trident spear summoning tidal waves"
            },
            {
                "name": "Mỵ Nương",
                "role": "supporting",
                "gender": "female",
                "dna": "radiant royal princess, graceful innocent beauty, ornate bronze era silk gown adorned with jade and golden ornaments"
            }
        ],
        "world_setting": "Vùng đất Phong Châu cổ kính thời Hùng Vương, đỉnh núi Tản Viên mây phủ hùng vĩ đối đầu với những đợt sóng cuồng phong bão táp.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Sơn Tinh và Thủy Tinh cùng thi triển thần thông kinh thiên trước điện rồng vua Hùng.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, epic confrontation between Mountain God raising stone peaks and Water God summoning swirling water dragons before King Hung court, dynamic perspective manga style",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Đúng sáng sớm hôm sau, Sơn Tinh rước đầy đủ sính lễ thần thoại voi chín ngà, ngựa chín hồng mao đến đón Mỵ Nương.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, divine Mountain God presenting mythical nine-tusked elephant and crimson-maned steed to delighted ancient Vietnamese royal court, intricate lineart",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Thủy Tinh nổi giận dâng nước ngập tràn đất trời, triệu hồi thủy quái tấn công thành trì.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, enraged Water God summoning massive tsunami engulfing ancient ancient river valleys, lightning crackling in storm clouds, high contrast manga screentone",
                "layout_type": "tall"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Sơn Tinh hiên ngang dời non lấp biển, đánh tan dòng nước xiết bảo vệ bình yên cho muôn dân.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, heroic Mountain God raising colossal stone barriers against raging torrents, victorious epic stance atop mountain peak, masterpiece 2D manga lineart",
                "layout_type": "wide"
            }
        ]
    },

    # ==================== TRUYỆN LỊCH SỬ ====================
    {
        "id": "ngo-quyen",
        "title": "Ngô Quyền & Đại Thắng Bạch Đằng Giang (938)",
        "slug": "ngo-quyen",
        "topic": "Đại thắng lịch sử chấm dứt ngàn năm Bắc thuộc",
        "category": "Truyện Lịch Sử",
        "genre": ["Lịch sử", "Chiến trận", "Bạch Đằng", "Chấm dứt Bắc thuộc", "Anh hùng dân tộc"],
        "summary": "Chiến công hiển hách của Tiền Ngô Vương Ngô Quyền với trận địa cọc gỗ ngầm huyền thoại trên sông Bạch Đằng năm 938, chôn vùi thủy quân Nam Hán, mở ra kỷ nguyên độc lập tự chủ lâu dài cho dân tộc Việt Nam.",
        "content": """Năm 937, hào trưởng Dương Đình Nghệ bị phản tướng Kiều Công Tiễn sát hại để cướp quyền bính. Kiều Công Tiễn hoảng sợ trước sự phẫn nộ của quân dân, liền sai sứ sang cầu cứu vua Nam Hán. Nhận được cơ hội xâm lược, vua Nam Hán phong con trai là Vạn Vương Hoằng Tháo làm Giao Chỉ quận vương, thống lĩnh đại thủy quân ồ ạt tiến sang xâm lược nước ta.

Lúc bấy giờ, Ngô Quyền - vị tướng tài ba xuất thân đất Đường Lâm, rể của Dương Đình Nghệ - đang cai quản Ái Châu (Thanh Hóa). Nghe tin giặc phản trắc, ông lập tức khởi binh tiến ra Đại La, tiêu diệt Kiều Công Tiễn trừ mối họa bên trong, rồi gấp rút chuẩn bị kháng chiến chống ngoại xâm.

Biết thủy quân Nam Hán sẽ tiến vào theo cửa sông Bạch Đằng, Ngô Quyền đã đưa ra một kế sách quân sự thiên tài: lợi dụng quy luật thủy triều lên xuống mạnh mẽ của vùng cửa biển. Ông hạ lệnh cho quân dân đẵn gỗ lim, gỗ táu từ rừng rậm vạt nhọn đầu, bịt sắt rồi cắm ngầm xuống lòng sông Bạch Đằng ở những khúc hiểm yếu.

Cuối năm 938, đoàn thuyền chiến khổng lồ do Hoằng Tháo chỉ huy hùng hổ vượt biển tiến vào cửa ngõ Bạch Đằng. Khi thủy triều đang lên cao ngập kín bãi cọc nhọn, Ngô Quyền cử các thuyền nhẹ ra khiêu chiến rồi giả vờ thua chạy. Tướng giặc Hoằng Tháo kiêu ngạo đốc thúc đại quân thúc thuyền đuổi riết theo sau.

Đợi khi thuyền giặc lọt hẳn vào khúc sông hiểm yếu và thủy triều bắt đầu rút xuống cực nhanh, Ngô Quyền phất cờ hiệu lệnh phản công dữ dội. Từ hai bên bờ lau sậy, chiến thuyền Đại Việt lao ra đánh tạt sườn quân địch, nỏ cứng và tên lửa bắn xối xả. Thủy quân Nam Hán hoảng loạn quay đầu bỏ chạy, nhưng lúc này thủy triều đã cạn, những mũi cọc nhọn bọc sắt nhô lên đâm thủng đáy hàng loạt chiến thuyền giặc. Thuyền giặc vỡ toang, va vào nhau đắm chìm vô số, binh lính chết đuối nghẽn cả khúc sông. Tướng giặc Hoằng Tháo trúng tên tử trận tại chỗ.

Đại thắng Bạch Đằng năm 938 đã đè bẹp hoàn toàn mộng xâm lăng của phong kiến phương Bắc, chính thức chấm dứt hơn 1.000 năm Bắc thuộc đen tối, mở ra kỷ nguyên độc lập, tự chủ huy hoàng cho non sông đất nước Việt Nam. Mùa xuân năm 939, Ngô Quyền lên ngôi vua, đóng đô ở Cổ Loa, lập nên nhà Ngô vẻ vang.""",
        "characters": [
            {
                "name": "Ngô Quyền",
                "role": "lead",
                "gender": "male",
                "dna": "legendary Vietnamese King, imposing heroic stature, brilliant piercing eyes, majestic bronze helmet and battle armor, holding command sword overlooking river"
            },
            {
                "name": "Hoằng Tháo",
                "role": "antagonist",
                "gender": "male",
                "dna": "arrogant young Southern Han prince general, ornate heavy Chinese armor, frantic terrified face as his war fleet crashes"
            },
            {
                "name": "Tướng lĩnh Đại Việt",
                "role": "supporting",
                "gender": "male",
                "dna": "rugged courageous Vietnamese naval warrior, shirtless muscular torso with martial tattoos and red headband firing fire arrows"
            }
        ],
        "world_setting": "Cửa sông Bạch Đằng mùa đông năm 938 cuồn cuộn sóng nước, bãi cọc gỗ bịt sắt ngầm và khói lửa chiến trận rực trời.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Dưới sự chỉ huy của Ngô Quyền, quân dân ngày đêm đẵn gỗ lim, cắm trận địa cọc ngầm bịt sắt xuống lòng sông Bạch Đằng.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, ancient Vietnamese warriors erecting massive iron-tipped wooden stakes into riverbed at low tide, disciplined historical military preparations, dynamic angle manga lineart",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Thuyền chiến Đại Việt dũng cảm khiêu chiến rồi giả rút lui dụ đoàn chiến hạm Nam Hán lọt sâu vào bẫy hiểm.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, agile Vietnamese war canoes luring massive enemy armadas into treacherous estuary at high tide, dramatic oceanic perspective",
                "layout_type": "wide"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Thủy triều rút nhanh, cọc nhọn đâm thủng hàng loạt tàu giặc, Ngô Quyền phất cờ tổng phản công như sấm sét.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, catastrophic scene of enemy war galleys impaled and splintered on sharp iron stakes as tide recedes, smoke and fire raging, high contrast manga screentone",
                "layout_type": "tall"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Chiến thắng Bạch Đằng vang dội, Tiền Ngô Vương Ngô Quyền đặt dấu chấm hết cho ngàn năm Bắc thuộc, mở kỷ nguyên độc lập dân tộc.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, victorious Vietnamese King Ngo Quyen standing proud atop commanding flagship banner waving in wind over pacified Bach Dang river, majestic historic conclusion 2D manga lineart",
                "layout_type": "wide"
            }
        ]
    },
    {
        "id": "ly-thuong-kiet",
        "title": "Lý Thường Kiệt & Bản Tuyên Ngôn Nam Quốc Sơn Hà (1077)",
        "slug": "ly-thuong-kiet",
        "topic": "Kháng chiến chống Tống & Bản tuyên ngôn độc lập đầu tiên",
        "category": "Truyện Lịch Sử",
        "genre": ["Lịch sử", "Quân sự", "Chiến lược", "Nam Quốc Sơn Hà", "Đại Việt"],
        "summary": "Thiên tài quân sự Lý Thường Kiệt với tư tưởng tiên phát chế nhân độc đáo và chiến công trên phòng tuyến sông Như Nguyệt, nơi bài thơ thần 'Nam quốc sơn hà' vang lên khẳng định chủ quyền bất khả xâm phạm của non sông đất Việt.",
        "content": """Vào thời vua Lý Nhân Tông, nhà Tống ở phương Bắc đang lâm vào khủng hoảng nặng nề, tể tướng Vương An Thạch toan tính xua quân đánh chiếm Đại Việt để giải tỏa mâu thuẫn nội bộ. Đoán trước dã tâm của giặc, Thái úy Lý Thường Kiệt chủ trương: \"Ngồi yên đợi giặc không bằng đem quân đánh trước để chặn mũi nhọn của giặc\".

Năm 1075, Lý Thường Kiệt táo bạo dẫn 10 vạn quân bất ngờ vượt biên giới tập kích các căn cứ hậu cần Ung Châu, Khâm Châu, Liêm Châu của nhà Tống, phá tan mọi chuẩn bị lương thảo của địch rồi rút êm về nước lập phòng tuyến chặn giặc. Đây là một đòn chiến lược phủ đầu xuất sắc chưa từng có trong lịch sử.

Trở về nước, Lý Thường Kiệt chọn bờ nam sông Như Nguyệt (sông Cầu) làm phòng tuyến chiến lược quyết định. Ông cho đắp lũy đất cao, cắm cọc tre dày đặc nhiều tầng nhiều lớp dọc suốt trăm dặm chiến tuyến để ngăn chặn kỵ binh và bộ binh giặc tràn xuống kinh thành Thăng Long.

Năm 1077, 30 vạn quân Tống do Quách Quỳ chỉ huy hùng hổ kéo sang, nhưng bị chặn đứng hoàn toàn trước phòng tuyến sông Như Nguyệt kiên cố. Nhiều lần quân Tống đóng bè vượt sông hòng chọc thủng lũy tre nhưng đều bị quân dân Đại Việt đánh tan tác, xác giặc trôi đầy mặt sông.

Trong lúc thế trận giằng co căng thẳng, nhằm cổ vũ sĩ khí quân sĩ và bẻ gãy ý chí giặc, Lý Thường Kiệt đã cho người vào đền thờ thần Trương Hống, Trương Hát bên bờ sông, đêm khuya cất giọng ngâm vang bài thơ thần rền vang khắp sông nước:

\"Nam quốc sơn hà Nam đế cư,
Tiệt nhiên định phận tại thiên thư.
Như hà nghịch lỗ lai xâm phạm,
Nhữ đẳng hành khan thủ bại hư!\"

(Sông núi nước Nam vua Nam ở,
Vành vạnh định phận tại sách trời.
Cớ sao lũ giặc sang xâm phạm,
Chúng bay sẽ bị đánh tơi bời!)

Tiếng thơ hào sảng rung chuyển màn đêm khiến quân giặc rụng rời kinh hãi, ngỡ rằng trời đất Đại Việt đều nổi giận; trong khi quân ta nức lòng phấn khởi, sĩ khí ngút trời.

Nắm chắc thời cơ, Lý Thường Kiệt mở cuộc tổng phản công bất ngờ trong đêm tối, đánh tan các doanh trại quân Tống. Quách Quỳ đại bại thảm hại, chết hơn nửa số quân, tiến thoái lưỡng nan. Với tinh thần nhân đạo và tầm nhìn bang giao sâu rộng, Lý Thường Kiệt chủ động đề nghị giảng hòa để mở đường cho giặc rút lui giữ thể diện, bảo toàn xương máu cho nhân dân hai nước.

Chiến thắng sông Như Nguyệt và bài thơ thần \"Nam quốc sơn hà\" đã trở thành bản Tuyên ngôn Độc lập đầu tiên của dân tộc Việt Nam, khẳng định muôn đời chủ quyền thiêng liêng của giang sơn bờ cõi.""",
        "characters": [
            {
                "name": "Lý Thường Kiệt",
                "role": "lead",
                "gender": "male",
                "dna": "esteemed Vietnamese Grand Marshall, commanding wise countenance, silver-streaked hair, wearing intricate royal Ly Dynasty bronze lamellar armor with dragon insignia and crimson cape"
            },
            {
                "name": "Quách Quỳ",
                "role": "antagonist",
                "gender": "male",
                "dna": "Song dynasty commanding general, grim despondent gaze, heavy northern imperial armor holding military command banner"
            },
            {
                "name": "Chiến binh Đại Việt",
                "role": "supporting",
                "gender": "male",
                "dna": "disciplined Ly dynasty soldier, leather armor, gripping long bronze spear defending bamboo ramparts"
            }
        ],
        "world_setting": "Phòng tuyến sông Như Nguyệt năm 1077 mây mù khói lửa, chiến lũy tre bạt ngàn và đền thiêng vang vọng tiếng thơ thần trong đêm.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Thái úy Lý Thường Kiệt trực tiếp thị sát, chỉ huy xây dựng phòng tuyến lũy tre kiên cố bên bờ nam sông Như Nguyệt.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, wise Grand Marshall Ly Thuong Kiet overlooking fortification works of dense bamboo ramparts along misty river Nhu Nguyet, epic military panorama",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Quân Tống đóng bè vượt sông tấn công điên cuồng nhưng bị chiến binh Đại Việt kiên cường đánh lui.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, dramatic river battle, Song dynasty invaders on rafts repelled by fierce volley of arrows and spears from bamboo fortress, intense combat manga lineart",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Trong đêm tối tĩnh mịch, bài thơ thần Nam Quốc Sơn Hà vang lên từ đền thiêng chấn động trời đất, làm bạt vía quân giặc.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, mystical riverside shrine glowing with divine lightning as celestial voice echoes patriotic poem Nam Quoc Son Ha, terrified enemy sentries trembling in darkness, striking manga screentone",
                "layout_type": "square"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Đại Việt tổng phản công thắng lợi rực rỡ, Lý Thường Kiệt mở lượng khoan hồng cho giặc rút quân, giữ vững nền thái bình muôn thuở.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, triumphant Vietnamese army celebrating sovereignty, Grand Marshall gesturing with nobility, historic masterpiece 2D manga lineart",
                "layout_type": "wide"
            }
        ]
    },
    {
        "id": "quang-trung",
        "title": "Quang Trung - Nguyễn Huệ & Đại Thắng Kỷ Dậu (1789)",
        "slug": "quang-trung",
        "topic": "Hành quân thần tốc & Đại phá 29 vạn quân Thanh",
        "category": "Truyện Lịch Sử",
        "genre": ["Lịch sử", "Quang Trung", "Tây Sơn", "Ngọc Hồi Đống Đa", "Thần tốc"],
        "summary": "Chiến dịch hành quân thần tốc vô tiền khoáng hậu và nghệ thuật quân sự đỉnh cao của Hoàng đế Quang Trung Nguyễn Huệ, đánh tan 29 vạn quân xâm lược Mãn Thanh vào mùa xuân Kỷ Dậu 1789, giải phóng hoàn toàn kinh thành Thăng Long.",
        "content": """Cuối năm 1788, vua tôi Lê Chiêu Thống hèn nhát rước 29 vạn quân Mãn Thanh do Tổng đốc Lưỡng Quảng Tôn Sĩ Nghị chỉ huy tràn vào xâm lược nước ta, chiếm đóng kinh thành Thăng Long. Quân Tây Sơn dưới sự chỉ huy mưu trí của Ngô Thì Nhậm và Ngô Văn Sở đã chủ động rút lui về phòng tuyến Tam Điệp - Biện Sơn để bảo toàn lực lượng và cấp báo vào Phú Xuân.

Nhận được tin khẩn, ngày 22 tháng 12 năm 1788, tại núi Bân (Huế), Bắc Bình Vương Nguyễn Huệ làm lễ tế trời đất, lên ngôi Hoàng đế lấy niên hiệu là Quang Trung, rồi lập tức hạ lệnh xuất quân thần tốc ra Bắc.

Để di chuyển hàng vạn dặm mà quân sĩ không mệt mỏi, vua Quang Trung sáng tạo phương thức hành quân độc đáo: cứ ba người thành một tốp, hai người cáng một người nằm nghỉ thay phiên nhau ngày đêm không ngừng nghỉ. Vừa hành quân, ông vừa tuyển thêm hàng vạn tân binh ở Nghệ An, Thanh Hóa, duyệt binh và truyền bài hịch rực lửa yêu nước:

\"Đánh cho để dài tóc,
Đánh cho để đen răng,
Đánh cho nó chích luân bất phản,
Đánh cho nó phiến giáp bất hoàn,
Đánh cho sử tri nam quốc anh hùng chi hữu chủ!\"

Đến Tam Điệp vào ngày 30 Tết Kỷ Dậu, vua Quang Trung khao quân ăn Tết trước và tuyên bố đanh thép trước ba quân tướng sĩ: \"Hẹn ngày mồng 7 Tết sẽ vào thành Thăng Long mở tiệc ăn mừng!\".

Đúng đêm Giao thừa Tết Kỷ Dậu, quân Tây Sơn bí mật vượt sông Gián Khẩu, bắt gọn toàn bộ lính do thám của giặc khiến Tôn Sĩ Nghị hoàn toàn mù tịt. Đêm mùng 3 Tết, quân ta vây kín đồn Hà Hồi, dùng loa bắc gọi hàng khiến hàng vạn quân giặc rụng rời đầu hàng không mất một mũi tên.

Mờ sáng mùng 5 Tết, trận quyết chiến lịch sử nổ ra tại pháo đài kiên cố Ngọc Hồi. Vua Quang Trung đích thân cưỡi voi chiến đầu lĩnh trận tiền, cho quân dùng những tấm ván quấn rơm ướt che đạn súng thần công xông thẳng vào lũy giặc. Quân Tây Sơn dũng mãnh phá toang cửa đồn, chém đầu hàng ngàn tên giặc. Cùng lúc đó, đạo quân của Đô đốc Đặng Tiến Đông bất ngờ tập kích đồn Khương Thượng (Đống Đa), tướng giặc Sầm Nghi Đống khiếp sợ thắt cổ tự tử.

Nghe tin hai đồn trọng yếu sụp đổ, Tôn Sĩ Nghị hoảng loạn không kịp mặc giáp, không kịp thắng yên ngựa, cùng đám tàn quân liều chết vượt cầu phao sông Hồng tháo chạy. Cầu phao đứt tung, xác giặc rơi xuống sông Hồng làm nghẽn cả dòng chảy.

Trưa mùng 5 Tết Kỷ Dậu - sớm hơn hai ngày so với lời hẹn ước - Hoàng đế Quang Trung trên chiếc áo bào sạm đen khói súng dẫn đầu đại quân khải hoàn tiến vào Thăng Long trong tiếng reo hò rền vang của muôn dân trăm họ, viết nên trang sử chói lọi muôn đời của dân tộc.""",
        "characters": [
            {
                "name": "Hoàng đế Quang Trung",
                "role": "lead",
                "gender": "male",
                "dna": "heroic Vietnamese Emperor Nguyen Hue, fiery charismatic eyes, dynamic commanding presence, wearing battle-scarred dark brocade royal armor atop war elephant holding commander sabre"
            },
            {
                "name": "Tôn Sĩ Nghị",
                "role": "antagonist",
                "gender": "male",
                "dna": "haughty Qing dynasty Viceroy, arrogant face turned pale in terror, disheveled imperial robe fleeing across broken pontoon bridge"
            },
            {
                "name": "Dũng sĩ Tây Sơn",
                "role": "supporting",
                "gender": "male",
                "dna": "fierce Tay Son shock infantry warrior, red headband, carrying wet thatch wooden storm shield advancing fearlessly"
            }
        ],
        "world_setting": "Mùa xuân Kỷ Dậu 1789, đại bản doanh hành quân thần tốc, khói lửa chiến trường Ngọc Hồi Đống Đa và thành Thăng Long rực rỡ hoa đào mùa xuân.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Tại núi Bân, Nguyễn Huệ tế cáo trời đất lên ngôi Hoàng đế Quang Trung, phát lệnh hành quân thần tốc ra Bắc.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, coronation ceremony of Emperor Quang Trung on Mount Ban, raising sacred sword before thousands of cheering troops under fluttering Tay Son banners, dramatic composition",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Ba quân Tây Sơn hành quân ngày đêm không nghỉ, luân phiên nằm võng cáng thần tốc tiến ra phòng tuyến Tam Điệp.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, ingenious Vietnamese rapid march technique through rugged mountain passes at night, torches lighting relentless march, dynamic manga panel",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Mờ sáng mùng 5 Tết, Hoàng đế Quang Trung cưỡi voi chiến xung phong đập tan pháo đài Ngọc Hồi kiên cố.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, Emperor Quang Trung atop armored war elephant leading heroic charge against enemy fortress, soldiers with wet straw shields charging through cannon smoke, high contrast manga style",
                "layout_type": "tall"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Trưa mùng 5 Tết, Quang Trung áo bào sạm khói súng dẫn đoàn quân chiến thắng tiến vào kinh thành Thăng Long rực rỡ sắc đào.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, victorious Emperor Quang Trung in battle-darkened royal tunic entering ancient Thang Long citadel surrounded by joyful cheering populace and blooming peach blossoms, epic historical conclusion 2D manga lineart",
                "layout_type": "wide"
            }
        ]
    },
    {
        "id": "dinh-bo-linh",
        "title": "Đinh Bộ Lĩnh & Cờ Lau Tập Trận Dẹp Loạn 12 Sứ Quân",
        "slug": "dinh-bo-linh",
        "topic": "Tuổi thơ cờ lau tập trận & Thống nhất đất nước",
        "category": "Truyện Lịch Sử",
        "genre": ["Lịch sử", "Đinh Bộ Lĩnh", "Cờ lau tập trận", "Đại Cồ Việt", "Thống nhất"],
        "summary": "Từ trò chơi cờ lau tập trận của cậu bé chăn trâu đất Hoa Lư đến chiến công dẹp yên loạn 12 sứ quân, thống nhất giang sơn, xưng Hoàng đế và lập nên nước Đại Cồ Việt độc lập tự chủ.",
        "content": """Sau khi Ngô Quyền qua đời năm 944, triều đình Cổ Loa rơi vào cảnh tranh quyền đoạt vị hỗn loạn. Các thế lực hào trưởng nổi dậy khắp nơi, chia cắt giang sơn thành 12 vùng cát cứ, sử gọi là Loạn 12 Sứ quân. Đất nước lâm vào cảnh chiến tranh liên miên, ruộng đồng bỏ hoang, nhân dân lầm than cơ cực.

Lúc bấy giờ ở động Hoa Lư (Ninh Bình), có cậu bé Đinh Bộ Lĩnh, mồ côi cha từ nhỏ, ngày ngày cùng lũ trẻ trong làng đi chăn trâu. Ngay từ thuở nhỏ, Đinh Bộ Lĩnh đã bộc lộ tư chất thủ lĩnh thông minh, can đảm và có tài thao lược xuất chúng.

Cậu thường bẻ bông lau làm cờ hiệu, chia lũ trẻ chăn trâu thành hai đạo quân tập trận đánh nhau. Đạo quân do Đinh Bộ Lĩnh chỉ huy luôn giành chiến thắng nhờ mưu mẹo tài tình. Mỗi lần thắng trận, lũ trẻ lại khoanh tay làm kiệu công kênh Đinh Bộ Lĩnh trên vai, rước đi như rước vua. Nhận thấy tài năng và lòng nhân ái của cậu, thanh niên và hào kiệt trong khắp vùng lũ lượt tìm về dưới trướng.

Lớn lên, khi đất nước chìm trong loạn lạc, Đinh Bộ Lĩnh cùng các bạn thiếu thời như Đinh Điền, Nguyễn Bặc, Lưu Cơ, Trịnh Tú quyết chí dựng cờ khởi nghĩa tại căn cứ hiểm trở Thung Lau - Hoa Lư.

Nhờ địa hình đầm lầy, hang động hiểm trở của vùng non nước Tràng An cùng tài dụng binh khéo léo, kết hợp giữa thu phục nhân tâm và tấn công thần tốc, Đinh Bộ Lĩnh lần lượt đánh bại và quy phục từng sứ quân một. Đi đến đâu, quân của ông cũng được nhân dân ủng hộ, tiếp tế lương thảo nồng nhiệt. Ông đánh đâu thắng đó, được quân dân tôn xưng là Vạn Thắng Vương.

Chỉ trong một thời gian ngắn, Đinh Bộ Lĩnh đã dẹp yên hoàn toàn 12 sứ quân, thu non sông về một mối, chấm dứt thời kỳ loạn lạc đẫm máu.

Năm 968, Vạn Thắng Vương lên ngôi Hoàng đế, lấy hiệu là Đinh Tiên Hoàng, đặt tên nước là Đại Cồ Việt, đóng đô tại Hoa Lư non nước hùng vĩ. Việc xưng Hoàng đế (ngang hàng với thiên tử phương Bắc) và đặt quốc hiệu riêng đã khẳng định ý chí tự cường, độc lập vững chắc của dân tộc Việt Nam.""",
        "characters": [
            {
                "name": "Đinh Bộ Lĩnh",
                "role": "lead",
                "gender": "male",
                "dna": "young resolute Vietnamese hero, charismatic piercing eyes, athletic build, holding reed banner atop stone boulder surrounded by admiring childhood followers"
            },
            {
                "name": "Đinh Điền",
                "role": "supporting",
                "gender": "male",
                "dna": "loyal warrior brother of Dinh Bo Linh, strong muscular build, traditional ancient Vietnamese leather battle vest"
            },
            {
                "name": "Quân sĩ Hoa Lư",
                "role": "supporting",
                "gender": "male",
                "dna": "fierce loyal warrior of the limestone mountain redoubt, wielding iron sword and wooden shield"
            }
        ],
        "world_setting": "Vùng thung lũng đá vôi Hoa Lư huyền thoại, rừng lau trắng bạt ngàn và kinh đô Hoa Lư đắp bằng vách núi tự nhiên kỳ vĩ.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Cậu bé Đinh Bộ Lĩnh cưỡi trâu, tay phất cờ lau chỉ huy lũ trẻ tập trận giữa cánh đồng thung lũng Hoa Lư.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, spirited young Vietnamese boy riding water buffalo waving white reed plume flag, childhood comrades playing war games among limestone karsts, charming historical manga style",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Lũ trẻ chăn trâu khoanh tay làm kiệu công kênh Đinh Bộ Lĩnh trong tiếng reo hò rộn rã non sông.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, village children carrying future emperor on their interlocked arms like a regal palanquin, majestic karst mountains backdrop, high contrast lineart",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Vạn Thắng Vương Đinh Bộ Lĩnh xuất trận dũng mãnh, đánh tan và quy phục các sứ quân chia cắt giang sơn.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, mature heroic commander Dinh Bo Linh in iron scale armor charging across battlefield leading disciplined army, uniting fractured lands, dynamic battle manga screentone",
                "layout_type": "square"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Đinh Tiên Hoàng lên ngôi Hoàng đế, định đô Hoa Lư, lập nên nước Đại Cồ Việt thái bình thịnh trị.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, grand coronation of Emperor Dinh Tien Hoang in ancient stone mountain citadel of Hoa Lu, proudly proclaiming independence and Great Dai Co Viet empire, historic climax 2D manga lineart",
                "layout_type": "wide"
            }
        ]
    },
    {
        "id": "le-loi",
        "title": "Lê Lợi & Khởi Nghĩa Lam Sơn - Sự Tích Hồ Gươm",
        "slug": "le-loi",
        "topic": "Khởi nghĩa Lam Sơn & Thanh gươm Thuận Thiên",
        "category": "Truyện Lịch Sử",
        "genre": ["Lịch sử", "Lê Lợi", "Lam Sơn", "Hồ Gươm", "Thuận Thiên"],
        "summary": "Mười năm nếm mật nằm gai của nghĩa quân Lam Sơn dưới sự lãnh đạo của Bình Định Vương Lê Lợi và quân sư Nguyễn Trãi, cùng huyền tích thanh gươm thần Thuận Thiên trao trả cho Rùa Vàng tại hồ Tả Vọng.",
        "content": """Đầu thế kỷ 15, nhà Minh mượn cớ phù Trần diệt Hồ xua quân sang xâm lược nước ta. Dưới ách đô hộ tàn bạo của giặc Minh, nhân dân lầm than cơ cực: \"Nướng dân đen trên ngọn lửa hung tàn, vùi con đỏ xuống dưới hầm tai vạ\".

Trước cảnh nước mất nhà tan, hào trưởng đất Lam Sơn (Thanh Hóa) là Lê Lợi đã nuôi chí lớn cứu nước. Năm 1416, ông cùng 18 nghĩa sĩ thân tín tổ chức Hội thề Lũng Nhai nguyện một lòng sống chết chống giặc cứu nước. Năm 1418, Lê Lợi chính thức dựng cờ khởi nghĩa, tự xưng là Bình Định Vương.

Những năm đầu, nghĩa quân Lam Sơn gặp vô vàn gian truân, nhiều lần bị giặc vây hãm trên núi Chí Linh hiểm trở, phải ăn rau rừng măng le, giết cả voi chiến ngựa chiến để sống sót qua ngày. Lê Lợi luôn chia ngọt sẻ bùi cùng ba quân tướng sĩ: \"Tướng sĩ một lòng phụ tử, hòa nước sông chén rượu ngọt ngào\".

Cảm phục ý chí kiên cường ấy, thần linh đã phó thác cho nghĩa quân thanh gươm báu mang tên Thuận Thiên (Thuận theo ý trời). Người đánh cá Lê Thận kéo lưới ba lần đều vớt được một lưỡi gươm sáng loáng; sau đó Lê Lợi đi qua gốc đa bắt được chiếc chuôi gươm nạm ngọc vừa như in. Khi tra gươm vào chuôi, thanh bảo kiếm phát ra ánh hào quang rực rỡ mang hai chữ \"Thuận Thiên\". Từ khi có gươm thần và sự phò tá đắc lực của quân sư tài ba Nguyễn Trãi, nghĩa quân đánh đâu thắng đó, uy thế lẫy lừng.

Năm 1426, nghĩa quân tiến quân ra Bắc, lập chiến công vang dội tại Tốt Động - Chúc Động. Năm 1427, tại ải Chi Lăng hiểm trở, nghĩa quân chém đầu Liễu Thăng, tiêu diệt và bắt sống hơn 10 vạn quân tiếp viện của giặc Minh. Vương Thông trong thành Đông Quan khiếp sợ cùng đường, xin mở hội thề Đông Quan để rút quân về nước. Lê Lợi không những tha chết mà còn cấp cho giặc hàng ngàn chiến thuyền, ngựa xe và lương thảo để về nước an toàn, thể hiện tinh thần nhân nghĩa cao cả của dân tộc Đại Việt.

Năm 1428, Lê Lợi lên ngôi Hoàng đế (Lê Thái Tổ), mở ra triều đại Hậu Lê rực rỡ, sai Nguyễn Trãi viết bài Bình Ngô Đại Cáo thiên cổ hùng văn.

Một năm sau ngày đại thắng, khi vua Lê Thái Tổ du thuyền trên hồ Tả Vọng (Hà Nội), bỗng một con Rùa Vàng khổng lồ nhô lên mặt nước cất tiếng: \"Xin Bệ hạ hoàn lại gươm báu cho Long Quân!\". Nhà vua rút gươm trao trả, Rùa Vàng ngậm lấy thanh kiếm rồi lặn sâu xuống đáy nước biếc. Từ đó, hồ Tả Vọng được đổi tên thành Hồ Hoàn Kiếm (Hồ Gươm), biểu tượng ngàn đời của khát vọng hòa bình và độc lập tự do của dân tộc Việt Nam.""",
        "characters": [
            {
                "name": "Lê Lợi",
                "role": "lead",
                "gender": "male",
                "dna": "heroic Vietnamese King Le Loi, noble resolute face, dignified beard, holding luminous sacred sword Thuan Thien, wearing royal dragon robes of Later Le Dynasty"
            },
            {
                "name": "Nguyễn Trãi",
                "role": "supporting",
                "gender": "male",
                "dna": "brilliant scholar strategist, wise contemplative eyes, scholar cap and robes holding strategic scroll"
            },
            {
                "name": "Thần Kim Quy",
                "role": "supporting",
                "gender": "unknown",
                "dna": "colossal mystical golden turtle deity emerging amidst shimmering celestial green mist on Hoan Kiem lake"
            }
        ],
        "world_setting": "Rừng núi Lam Sơn - Chí Linh hiểm trở và mặt nước hồ Tả Vọng (Hồ Gươm) bảng lảng sương mai giữa kinh thành Thăng Long thanh bình.",
        "panels": [
            {
                "panel_index": 1,
                "dialogue_text": "Lê Lợi cùng các nghĩa sĩ cắt máu ăn thề tại Hội thề Lũng Nhai, nguyện một lòng diệt giặc cứu non sông.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, historic blood oath of Lung Nhai, Le Loi and loyal brothers sworn under ancient mountain trees, dramatic lighting manga screentone",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "dialogue_text": "Lưỡi gươm vớt từ lòng nước khớp kỳ diệu với chuôi gươm nạm ngọc, phát ra ánh hào quang Thuận Thiên huyền diệu.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, Le Loi assembling the mystical divine sword Thuan Thien, radiant celestial beam illuminating camp in mountain redoubt, spiritual manga lineart",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "dialogue_text": "Trận phục kích Chi Lăng đại thắng, nghĩa quân Lam Sơn đập tan 10 vạn viện binh giặc Minh, quét sạch bóng quân thù.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, dramatic ambush battle in mountain pass of Chi Lang, victorious Vietnamese guerrilla archers repelling armored invaders, dynamic action manga style",
                "layout_type": "tall"
            },
            {
                "panel_index": 4,
                "dialogue_text": "Trên hồ Tả Vọng bảng lảng sương khói, nhà vua trang trọng trao trả gươm báu cho Rùa Vàng trong niềm ước vọng hòa bình muôn thuở.",
                "image_prompt": "masterpiece 2D Japanese anime manga illustration, clean monochrome black ink lineart, majestic Emperor Le Loi on royal dragon barge offering glowing sacred sword to giant mystical Golden Turtle emerging on calm waters of Hoan Kiem lake, timeless historic masterpiece 2D manga lineart",
                "layout_type": "wide"
            }
        ]
    }
]

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dirs = [
        os.path.join(base_dir, "data", "stories"),
        os.path.join(os.path.dirname(base_dir), "data", "stories"),
        os.path.join(os.path.dirname(base_dir), "final", "data", "stories"),
        os.path.join(os.path.dirname(base_dir), "final", "backend", "data", "stories"),
    ]

    for d in target_dirs:
        os.makedirs(d, exist_ok=True)
        for s in stories_data:
            fpath = os.path.join(d, f"{s['id']}.json")
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(s, f, ensure_ascii=False, indent=2)
            print(f"Saved {s['id']}.json to {d}")

    # Also update queue.json to include these new stories as merged / published
    queue_files = [
        os.path.join(base_dir, "data", "queue.json"),
        os.path.join(os.path.dirname(base_dir), "data", "queue.json"),
        os.path.join(os.path.dirname(base_dir), "final", "data", "queue.json"),
        os.path.join(os.path.dirname(base_dir), "final", "backend", "data", "queue.json"),
    ]

    for qfile in queue_files:
        if not os.path.exists(qfile):
            continue
        try:
            with open(qfile, "r", encoding="utf-8") as f:
                qdata = json.load(f)
            
            existing_ids = {item["id"] for item in qdata.get("stories", [])}
            
            for s in stories_data:
                if s["id"] not in existing_ids:
                    qdata.setdefault("stories", []).append({
                        "id": s["id"],
                        "title": s["title"],
                        "topic": s["topic"],
                        "category": s["category"],
                        "genre": s["genre"],
                        "language": "vi",
                        "sourceLanguages": ["vi", "en"],
                        "status": "merged",
                        "createdAt": "2026-10-11T00:00:00Z",
                        "updatedAt": "2026-10-11T00:00:00Z",
                        "prUrl": None,
                        "prNumber": None,
                        "branchName": f"ai-stories/{s['id']}",
                        "error": None
                    })
            
            with open(qfile, "w", encoding="utf-8") as f:
                json.dump(qdata, f, ensure_ascii=False, indent=2)
            print(f"Updated queue in {qfile}")
        except Exception as e:
            print(f"Error updating {qfile}: {e}")

if __name__ == "__main__":
    main()
