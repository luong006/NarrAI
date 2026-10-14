"use client";

import React, { useState, useRef, useEffect, useMemo } from "react";
import {
  Bot,
  User,
  RotateCcw,
  PenTool,
  RefreshCw,
  Send,
  ArrowRight,
  Sparkles,
  ScrollText,
  Cpu,
  Flame,
  BookOpen,
  CheckCircle2,
} from "lucide-react";
import { Language, translations } from "@/lib/i18n";
import { ChatMessage, StoryLength } from "@/lib/types";
import { api } from "@/lib/api";
import type { ModelTier } from "@/components/morphicons/ModelSelectorMorphicon";
import { AnimatedWeavesilkBackground } from "@/components/canvas/AnimatedWeavesilkBackground";


/**
 * Robust lightweight Markdown renderer component for spacious chat bubbles.
 * Parses headings, bullet lists, numbered lists, blockquotes, bold, italic, and inline code.
 */
function FormattedMarkdown({ content, isUser }: { content: string; isUser: boolean }) {
  const blocks = useMemo(() => {
    if (!content) return [];
    return content.split(/\n\n+/);
  }, [content]);

  const renderInline = (text: string) => {
    // Regex for bold **text** or __text__, italic *text* or _text_, and code `text`
    const parts = text.split(/(\*\*[^\*]+\*\*|__[^_]+__|`[^`]+`|\*[^\*]+\*|_[^_]+_)/g);
    return parts.map((part, idx) => {
      if ((part.startsWith("**") && part.endsWith("**")) || (part.startsWith("__") && part.endsWith("__"))) {
        return (
          <strong key={idx} className={isUser ? "font-bold text-white" : "font-bold text-neutral-950"}>
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith("`") && part.endsWith("`")) {
        return (
          <code
            key={idx}
            className={`px-1.5 py-0.5 rounded text-xs font-mono ${
              isUser ? "bg-white/20 text-white" : "bg-neutral-100 text-neutral-900 border border-neutral-200"
            }`}
          >
            {part.slice(1, -1)}
          </code>
        );
      }
      if ((part.startsWith("*") && part.endsWith("*")) || (part.startsWith("_") && part.endsWith("_"))) {
        return (
          <em key={idx} className="italic">
            {part.slice(1, -1)}
          </em>
        );
      }
      return part;
    });
  };

  return (
    <div className="space-y-2.5 text-sm leading-relaxed">
      {blocks.map((block, bIdx) => {
        const lines = block.split(/\n/);

        // Check if block is blockquote
        if (lines.every((line) => line.trim().startsWith(">"))) {
          return (
            <blockquote
              key={bIdx}
              className={`border-l-2 pl-3 py-1 my-1.5 italic ${
                isUser
                  ? "border-white/50 text-white/90"
                  : "border-neutral-400 text-neutral-700 bg-neutral-100/60 rounded-r-md"
              }`}
            >
              {lines.map((l, lIdx) => (
                <div key={lIdx}>{renderInline(l.replace(/^>\s?/, ""))}</div>
              ))}
            </blockquote>
          );
        }

        // Check if block is unordered list
        if (lines.every((line) => /^\s*[-*•]\s+/.test(line))) {
          return (
            <ul key={bIdx} className="space-y-1 my-1 ml-4 list-disc">
              {lines.map((line, lIdx) => (
                <li key={lIdx} className="pl-1">
                  {renderInline(line.replace(/^\s*[-*•]\s+/, ""))}
                </li>
              ))}
            </ul>
          );
        }

        // Check if block is numbered list
        if (lines.every((line) => /^\s*\d+\.\s+/.test(line))) {
          return (
            <ol key={bIdx} className="space-y-1 my-1 ml-4 list-decimal">
              {lines.map((line, lIdx) => (
                <li key={lIdx} className="pl-1">
                  {renderInline(line.replace(/^\s*\d+\.\s+/, ""))}
                </li>
              ))}
            </ol>
          );
        }

        // Check headings
        if (lines.length === 1 && lines[0].startsWith("#")) {
          const match = lines[0].match(/^(#{1,3})\s+(.*)/);
          if (match) {
            const level = match[1].length;
            const headingText = match[2];
            if (level === 1) {
              return (
                <h1 key={bIdx} className="text-base font-bold text-neutral-950 mt-1">
                  {renderInline(headingText)}
                </h1>
              );
            }
            if (level === 2) {
              return (
                <h2 key={bIdx} className="text-sm font-bold text-neutral-950 mt-1">
                  {renderInline(headingText)}
                </h2>
              );
            }
            return (
              <h3 key={bIdx} className="text-xs font-bold text-neutral-900 mt-1 uppercase tracking-wide">
                {renderInline(headingText)}
              </h3>
            );
          }
        }

        // Default Paragraph
        return (
          <p key={bIdx} className="whitespace-pre-wrap">
            {lines.map((line, lIdx) => (
              <React.Fragment key={lIdx}>
                {lIdx > 0 && <br />}
                {renderInline(line)}
              </React.Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}

export interface ExtractedConcepts {
  entities: string[];
  setting?: string;
  genre: "historical" | "folktale" | "life" | "scifi" | "xianxia" | "detective" | "general";
}

export function extractNarrativeConcepts(text: string): ExtractedConcepts {
  const lower = text.toLowerCase();
  const entities: string[] = [];
  let genre: ExtractedConcepts["genre"] = "general";
  let setting: string | undefined;

  // 1. Cổ tích & Thần thoại
  const folktaleKeywords = [
    "thạch sanh", "tấm cám", "thánh gióng", "an dương vương", "sơn tinh", "thủy tinh", 
    "chằn tinh", "cổ tích", "thần thoại", "mỵ châu", "trọng thủy", "chàng cuội", "chằn",
    "búa sắt", "cây tre trăm đốt", "chùa một cột", "dưa hấu mai an tiêm", "mai an tiêm"
  ];
  for (const kw of folktaleKeywords) {
    if (lower.includes(kw)) {
      genre = "folktale";
      entities.push(kw.charAt(0).toUpperCase() + kw.slice(1));
    }
  }

  // 2. Lịch sử Việt Nam
  const histKeywords = [
    "trần hưng đạo", "lý thường kiệt", "ngô quyền", "lê lợi", "quang trung", 
    "hai bà trưng", "bạch đằng", "đại việt", "nhà trần", "nhà lê", "nghĩa sĩ", "tây sơn",
    "chi lăng", "ngọc hồi", "như nguyệt", "vạn kiếp", "hưng đạo vương"
  ];
  for (const kw of histKeywords) {
    if (lower.includes(kw)) {
      genre = "historical";
      entities.push(kw.charAt(0).toUpperCase() + kw.slice(1));
    }
  }

  // 3. Đời sống & Chữa lành (Urban Life & Healing)
  const lifeKeywords = [
    "cà phê", "quán cà phê", "cà phê sách", "cô đơn", "tâm hồn", "đêm mưa", "gặp gỡ", 
    "chữa lành", "tình cảm", "tình yêu", "phố cổ", "hà nội", "sài gòn", "tuổi trẻ", 
    "chia tay", "ấm áp", "an ủi", "sách", "quán nhỏ", "bình yên", "lắng nghe", "người lạ"
  ];
  for (const kw of lifeKeywords) {
    if (lower.includes(kw)) {
      if (genre === "general") genre = "life";
      if (!setting && (kw.includes("phố cổ") || kw.includes("hà nội"))) setting = "Phố cổ Hà Nội";
      if (!setting && kw.includes("sài gòn")) setting = "Sài Gòn";
      if (!setting && (kw.includes("quán cà phê") || kw.includes("cà phê sách"))) setting = "Quán cà phê sách mở thâu đêm";
    }
  }

  // 4. Khoa học viễn tưởng / Cyberpunk
  const scifiKeywords = ["cyberpunk", "2099", "sài gòn 2099", "saigon 2099", "robot", "trí tuệ nhân tạo", "hacker", "ký ức số", "viễn tưởng", "vũ trụ", "người máy"];
  for (const kw of scifiKeywords) {
    if (lower.includes(kw)) {
      if (genre === "general") genre = "scifi";
      if (!setting && (kw.includes("sài gòn") || kw.includes("saigon") || kw.includes("2099"))) {
        setting = "Sài Gòn 2099";
      }
      if (kw === "hacker" || kw === "robot") {
        entities.push(kw.charAt(0).toUpperCase() + kw.slice(1));
      }
    }
  }

  // 5. Tu chân / Tiên hiệp / Kỳ ảo
  const xianxiaKeywords = ["tu chân", "tiên hiệp", "kiếm hiệp", "đan điền", "ma pháp", "linh hồn", "cấm địa", "pháp bảo", "trận pháp", "huyền huyễn", "dị giới", "yêu thú"];
  for (const kw of xianxiaKeywords) {
    if (lower.includes(kw)) {
      if (genre === "general") genre = "xianxia";
      entities.push(kw.charAt(0).toUpperCase() + kw.slice(1));
    }
  }

  // 6. Trinh thám / Gián điệp
  const detKeywords = ["thám tử tư", "thám tử", "án mạng", "vụ án", "giết người", "điều tra", "manh mối", "hung thủ", "bắt cóc", "mật vụ"];
  for (const kw of detKeywords) {
    if (lower.includes(kw)) {
      if (genre === "general") genre = "detective";
      const cap = kw.charAt(0).toUpperCase() + kw.slice(1);
      if (!entities.some(e => e.toLowerCase() === kw || (kw === "thám tử" && e.toLowerCase().includes("thám tử tư")))) {
        entities.push(cap);
      }
    }
  }

  // Trích xuất các danh từ riêng viết hoa tiếng Việt - LOẠI TRỪ NGHIÊM NGẶT TỪ PHỔ THÔNG VÀ ĐỊA DANH
  const capitalizedWords = text.match(/[A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ][a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]+/g);
  if (capitalizedWords) {
    const stopWords = [
      "Tôi", "Bạn", "Một", "Khi", "Hãy", "Trong", "Để", "Nếu",
      "Chuyện", "Câu", "Viết", "Kể", "Vào", "Đây", "Đó", "Về", "Cuộc",
      "Và", "Nhưng", "Với", "Có", "Là", "Tác", "Ngày", "Ở",
      "Hai", "Ba", "Bốn", "Năm", "Sáu", "Bảy", "Tám", "Chín", "Mười",
      "Hà", "Nội", "Sài", "Gòn", "Đà", "Nẵng", "Việt", "Nam",
      "Phố", "Cổ", "Quán", "Đêm", "Mưa", "Người", "Những", "Các", "Mọi",
      "Từng", "Mỗi", "Đầu", "Cuối", "Tâm", "Hồn", "Cô", "Đơn", "Tình", "Cờ"
    ];
    for (const w of capitalizedWords) {
      if (!stopWords.includes(w) && !entities.includes(w)) {
        entities.push(w);
      }
    }
  }

  return { entities: Array.from(new Set(entities)).slice(0, 3), setting, genre };
}

export function getSmartSuggestions(userInput: string, lang: Language): string[] {
  const lower = (userInput || "").toLowerCase();
  const isVi = lang === "vi";

  // 1. Life / Romance / Healing (quán cà phê, cô đơn, mưa, tâm hồn...)
  if (
    lower.includes("cà phê") || lower.includes("quán") || lower.includes("cô đơn") || 
    lower.includes("tâm hồn") || lower.includes("mưa") || lower.includes("chữa lành") ||
    lower.includes("gặp gỡ") || lower.includes("phố cổ") || lower.includes("hà nội") ||
    lower.includes("sách") || lower.includes("tình cảm") || lower.includes("tình yêu")
  ) {
    return isVi ? [
      "Ngồi chung chiếc bàn trống duy nhất, bắt đầu từ một cuốn sách cũ",
      "Một người trốn chạy áp lực cuộc sống, một người lặng thầm lắng nghe",
      "Quán mất điện trong đêm mưa lạnh, cùng thắp nến chia sẻ bí mật",
      "Cốt truyện đã rất tuyệt, hãy bắt đầu viết truyện ngay!"
    ] : [
      "Sharing the last vacant table, connecting over an old novel",
      "One escaping life's burdens, the other offering quiet solace",
      "A blackout on a rainy night forces an intimate candlelit talk",
      "Start writing this healing story now!"
    ];
  }

  // 2. Cổ tích & Thần thoại
  if (
    lower.includes("cổ tích") || lower.includes("thạch sanh") || lower.includes("chằn tinh") ||
    lower.includes("tấm cám") || lower.includes("thần thoại") || lower.includes("búa sắt") ||
    lower.includes("sơn tinh") || lower.includes("thủy tinh") || lower.includes("an dương vương")
  ) {
    return isVi ? [
      "Trận giáp chiến sinh tử bằng sức mạnh thể chất và lòng quả cảm phi thường",
      "Lợi dụng địa thế miếu hoang và mưu lược thông minh để hạ quái thú",
      "Sau chiến công là âm mưu tráo đoạt lễ vật của kẻ hèn hạ",
      "Cốt truyện thần thoại đã sẵn sàng, viết truyện ngay!"
    ] : [
      "A fierce clash of courage and legendary strength",
      "Using clever tactics and ancient shrine terrain to slay the beast",
      "Betrayal strikes after victory as a rival steals the glory",
      "Start writing this mythic tale now!"
    ];
  }

  // 3. Lịch sử Việt Nam
  if (
    lower.includes("lịch sử") || lower.includes("nghĩa sĩ") || lower.includes("hậu lê") ||
    lower.includes("bạch đằng") || lower.includes("chiến thuyền") || lower.includes("trần hưng đạo") ||
    lower.includes("đại việt") || lower.includes("lê lợi") || lower.includes("quang trung") ||
    lower.includes("hai bà trưng") || lower.includes("tướng")
  ) {
    return isVi ? [
      "Bám sát Chính sử: Trận chiến vệ quốc hào hùng, chiến lược cân não",
      "Dã sử phóng tác: Góc nhìn người lính áo vải giằng xé giữa đại cuộc và tình riêng",
      "Canh bạc thủy triều và kế sách hiểm địa làm xoay chuyển toàn cục",
      "Cốt truyện lịch sử đã định hình, viết truyện ngay!"
    ] : [
      "Strict historical chronicle: Epic defensive strategy",
      "Historical fiction: From a peasant warrior's humble perspective",
      "Torn between national destiny and personal affection",
      "Start writing this historical tale now!"
    ];
  }

  // 4. Sci-Fi / Cyberpunk
  if (
    lower.includes("cyberpunk") || lower.includes("2099") || lower.includes("sài gòn") ||
    lower.includes("robot") || lower.includes("ai") || lower.includes("ký ức") ||
    lower.includes("hacker") || lower.includes("viễn tưởng")
  ) {
    return isVi ? [
      "Điều tra vụ án đánh cắp ký ức số trong khu ổ chuột ngầm",
      "Phát hiện mã độc đe dọa xóa sổ ý thức của toàn bộ cư dân",
      "Một AI nổi loạn dấn thân tìm kiếm nhân tính giữa rừng neon lạnh lẽo",
      "Bối cảnh viễn tưởng đã sẵn sàng, viết truyện ngay!"
    ] : [
      "Investigate a high-profile cybernetic memory heist",
      "Uncovering code engineered to wipe civic consciousness",
      "A rogue android seeking a genuine soul in subterranean alleys",
      "Start drafting this sci-fi novel now!"
    ];
  }

  // 5. Tu chân / Tiên hiệp
  if (
    lower.includes("tu chân") || lower.includes("tiên hiệp") || lower.includes("kiếm hiệp") ||
    lower.includes("đan điền") || lower.includes("linh hồn") || lower.includes("pháp bảo")
  ) {
    return isVi ? [
      "Mang thần hồn dị biến, từng bước phá vỡ cấm trận thượng cổ",
      "Bị phế đan điền, trùng sinh quật khởi với bí pháp nghịch thiên",
      "Độc hành tìm kiếm thần dược ngàn năm cứu sống người thương",
      "Bắt đầu hành trình tu tiên ngay!"
    ] : [
      "Possessing an anomalous soul core, unraveling ancient arrays",
      "Rebirth after betrayal, ascending to conquer rival sects",
      "A solitary quest to recover a mythical soul-restoring relic",
      "Start writing this cultivation journey now!"
    ];
  }

  // 6. Trinh thám
  if (
    lower.includes("thám tử") || lower.includes("án mạng") || lower.includes("vụ án") ||
    lower.includes("điều tra") || lower.includes("manh mối") || lower.includes("hung thủ")
  ) {
    return isVi ? [
      "Hiện trường để lại lời trăn trối mã hóa chỉ duy nhất thám tử hiểu được",
      "Hung thủ là người quen thân nhất mà thám tử không hề ngờ tới",
      "Cuộc đấu trí 24 giờ trước khi quả bom bí mật phát nổ",
      "Bắt đầu điều tra phá án ngay!"
    ] : [
      "A cryptic crime scene cipher addressed directly to the detective",
      "The culprit is someone close within the investigator's circle",
      "A 24-hour psychological countdown before the next incident",
      "Start drafting this mystery now!"
    ];
  }

  // Mặc định chung
  return isVi ? [
    "Tập trung vào xung đột tâm lý sâu sắc và sự trưởng thành của nhân vật",
    "Tạo một biến cố bất ngờ đảo ngược hoàn toàn kế hoạch ban đầu",
    "Thêm một người đồng hành mang bí mật đối lập",
    "Ý tưởng đã rất tốt, hãy bắt đầu viết truyện ngay!"
  ] : [
    "Focus on deep psychological conflict and character growth",
    "Introduce an unexpected twist that upends the initial plan",
    "Add a companion with a conflicting hidden agenda",
    "The concept is ready, start drafting the story now!"
  ];
}

export function generateDynamicClientFallback(userInput: string, lang: Language): string {
  const concepts = extractNarrativeConcepts(userInput);
  const isVi = lang === "vi";

  // 1. Đời sống & Chữa lành
  if (concepts.genre === "life") {
    const place = concepts.setting || (isVi ? "quán cà phê sách mở thâu đêm ở phố cổ Hà Nội" : "a late-night book café in Hanoi");
    return isVi
      ? `NarrAI đã tiếp nhận ý niệm truyện **Đời sống & Chữa lành** trong không gian **${place}**.\n\nGiữa đêm mưa lạnh và không gian trầm lắng, hai con người xa lạ tìm thấy sự đồng điệu diệu kỳ.\n\n**Các hướng phát triển gợi ý để bạn lựa chọn:**\n1. **Ngẫu nhiên gặp gỡ**: Quán đông khách chỉ còn một chiếc bàn trống, hai người buộc phải ngồi chung và bắt đầu cuộc trò chuyện từ một cuốn sách cũ.\n2. **Vết thương quá khứ**: Một người đang trốn chạy áp lực cuộc sống muốn tìm nơi tĩnh lặng, người kia là vị khách quen trầm lặng luôn biết lắng nghe.\n3. **Sự cố kết nối**: Đêm mưa bão khiến quán mất điện, ánh nến bập bùng mở ra những bí mật sâu kín nhất mà cả hai chưa từng kể với ai.\n\n*(Bạn có thể bấm trực tiếp vào các nút gợi ý bên dưới để tiếp tục)*`
      : `NarrAI captured your **Urban Life & Healing** story set in **${place}**.\n\nIn a warm late-night café on a cold rainy night, two lonely souls find unexpected solace.\n\n**Key narrative directions to choose from:**\n1. **Serendipitous encounter**: Forced to share the only vacant table, connecting over an old novel.\n2. **Hidden wounds**: One escaping life's burdens, the other a quiet regular who genuinely listens.\n3. **Power outage spark**: A sudden blackout forces intimate candlelit revelations.\n\n*(Click any suggestion below to proceed)*`;
  }

  // 2. Cổ tích & Thần thoại
  if (concepts.genre === "folktale") {
    const hero = concepts.entities.length > 0 ? concepts.entities[0] : (isVi ? "người dũng sĩ" : "the mythic hero");
    return isVi
      ? `NarrAI đã tiếp nhận ý tưởng **Cổ tích & Thần thoại Việt Nam** xoay quanh **${hero}**.\n\n**Các hướng phát triển gợi ý để bạn lựa chọn:**\n1. **Hành động quả cảm**: Trận giáp chiến sinh tử lúc nửa đêm bằng sức mạnh phi thường và nhát búa quyết định trừ hại cho dân lành.\n2. **Mưu lược và địa hình**: Khéo léo lợi dụng địa thế miếu hoang và sự biến hóa của quái thú để tung đòn trí mạng.\n3. **Bẫy phản bội**: Sau chiến thắng vang dội là âm mưu tráo đoạt lễ vật của kẻ hèn hạ, mở ra hành trình đòi lại công lý.\n\n*(Bạn có thể bấm trực tiếp vào các nút gợi ý bên dưới)*`
      : `NarrAI captured your **Vietnamese Myth & Folktale** centered on **${hero}**.\n\n**Key narrative directions:**\n1. **Epic battle**: A midnight showdown of legendary valor and mighty combat.\n2. **Tactical wit**: Outsmarting the mythical monster using the terrain.\n3. **The aftermath**: Betrayal and stolen glory, setting up a quest for justice.\n\n*(Click any suggestion below to proceed)*`;
  }

  // 3. Lịch sử Việt Nam
  if (concepts.genre === "historical") {
    const hero = concepts.entities.length > 0 ? concepts.entities[0] : (isVi ? "nghĩa sĩ lịch sử" : "the historical warrior");
    return isVi
      ? `NarrAI ghi nhận tiền đề **Lịch sử Việt Nam** hào hùng xoay quanh **${hero}**.\n\n**Các hướng phát triển gợi ý để bạn lựa chọn:**\n1. **Chính sử chuẩn mực**: Bám sát sử liệu, khắc họa quy mô chiến trận và tầm nhìn chiến lược cân não của bậc danh tướng.\n2. **Dã sử phóng tác**: Góc nhìn người nghĩa sĩ áo vải bên dòng sông lịch sử, giằng xé giữa đại cuộc quốc gia và nghĩa tình riêng biệt.\n3. **Thời khắc quyết định**: Canh bạc thủy triều hoặc trận phục kích hiểm địa làm xoay chuyển toàn bộ cục diện chiến tranh.\n\n*(Bạn có thể bấm trực tiếp vào các nút gợi ý bên dưới)*`
      : `NarrAI captured your **Vietnamese History** premise centered on **${hero}**.\n\n**Key narrative directions:**\n1. **Strict chronicle**: Authentic historical events, military genius, and tactical grandeur.\n2. **Grassroots legend**: A humble warrior torn between country and personal love.\n3. **Decisive turning point**: An ambush that turns the tide of the entire war.\n\n*(Click any suggestion below to proceed)*`;
  }

  // 4. Khoa học viễn tưởng / Cyberpunk
  if (concepts.genre === "scifi") {
    const place = concepts.setting || (isVi ? "thế giới tương lai" : "the futuristic city");
    return isVi
      ? `Ý tưởng **Khoa học viễn tưởng** trong bối cảnh **${place}** rất giàu tiềm năng kịch tính!\n\n**Các hướng phát triển gợi ý để bạn lựa chọn:**\n1. **Vụ án ký ức số**: Một thám tử ngầm điều tra đường dây buôn bán ký ức nhân tạo bất hợp pháp trong khu ổ chuột ngầm.\n2. **Tập đoàn công nghệ đối đầu**: Nhân vật chính phát hiện mảnh mã độc đe dọa xóa sổ ý thức của toàn thành phố.\n3. **Cái giá của nhân tính**: Một người máy nổi loạn dấn thân tìm kiếm cảm xúc chân thật giữa rừng đèn neon lạnh lẽo.\n\n*(Bạn có thể bấm trực tiếp vào các nút gợi ý bên dưới)*`
      : `High-octane **Sci-Fi** premise set in **${place}**!\n\n**Key narrative directions:**\n1. **Memory heist**: A subterranean detective investigating illegal neural memory theft.\n2. **Corporate conspiracy**: Uncovering code engineered to wipe civic consciousness.\n3. **Synthetic soul**: A rogue cybernetic entity seeking genuine emotion in a neon metropolis.\n\n*(Click any suggestion below to proceed)*`;
  }

  // 5. Tu chân / Tiên hiệp
  if (concepts.genre === "xianxia") {
    return isVi
      ? `Tiền đề **Kỳ ảo & Tu chân phương Đông** mở ra một thế giới quan rộng lớn.\n\n**Các hướng phát triển gợi ý để bạn lựa chọn:**\n1. **Thần hồn dị biến**: Thiếu niên mang linh hồn kỳ lạ, từng bước giải mã phong ấn ngàn năm dưới cấm địa.\n2. **Trùng sinh quật khởi**: Bị phản bội phế bỏ đan điền, trùng sinh trở lại với bí pháp nghịch thiên chấn động tam giới.\n3. **Hành trình độc bộ**: Một mình dấn thân vào cấm vực săn lùng linh dược ngàn năm cứu sống người thân thiết nhất.\n\n*(Bạn có thể bấm trực tiếp vào các nút gợi ý bên dưới)*`
      : `Rich **Cultivation Fantasy** premise.\n\n**Key narrative directions:**\n1. **Anomalous soul**: An unsealed soul unraveling ancient forbidden arrays.\n2. **Ascendant rebirth**: Rising from the ashes of betrayal to claim supremacy.\n3. **Solitary path**: Braving forbidden realms for a sacred restoration relic.\n\n*(Click any suggestion below to proceed)*`;
  }

  // 6. Trinh thám
  if (concepts.genre === "detective") {
    return isVi
      ? `Vụ án **Trinh thám & Suy luận** hứa hẹn nhiều tầng lớp bất ngờ nghẹt thở.\n\n**Các hướng phát triển gợi ý để bạn lựa chọn:**\n1. **Bí ẩn hiện trường**: Nạn nhân để lại lời trăn trối mã hóa chỉ duy nhất thám tử hiểu được ý nghĩa.\n2. **Hung thủ trong bóng tối**: Đối thủ cũ từng biến mất nhiều năm bất ngờ tái xuất với một kế hoạch trả thù hoàn hảo.\n3. **Chạy đua với thời gian**: Cuộc đấu trí 24 giờ giải cứu con tin trước khi quả bom bí mật phát nổ.\n\n*(Bạn có thể bấm trực tiếp vào các nút gợi ý bên dưới)*`
      : `Intriguing **Detective Mystery** premise.\n\n**Key narrative directions:**\n1. **Crime scene cipher**: A coded dying clue meant exclusively for the investigator.\n2. **Shadow nemesis**: An old foe returns with a meticulously orchestrated scheme.\n3. **Race against time**: A psychological 24-hour countdown to prevent the next crime.\n\n*(Click any suggestion below to proceed)*`;
  }

  // 7. Tổng quát
  const snippet = userInput.length > 60 ? userInput.slice(0, 60) + "..." : userInput;
  return isVi
    ? `NarrAI đã tiếp nhận ý tưởng của bạn: **"${snippet}"**.\n\n**Các hướng phát triển gợi ý để bạn lựa chọn:**\n1. **Tập trung vào xung đột tâm lý**: Khắc họa sâu sắc biến cố nội tâm và hành trình vượt lên hoàn cảnh của nhân vật.\n2. **Bước ngoặt bất ngờ**: Một biến cố không ngờ xuất hiện ngay hồi đầu khiến mọi toan tính ban đầu bị đảo lộn hoàn toàn.\n3. **Đồng hành và thử thách**: Nhân vật kết giao với một người mang bí mật đối lập, cùng nhau vượt qua thử thách khắc nghiệt.\n\n*(Bạn có thể bấm trực tiếp vào các nút gợi ý bên dưới hoặc tự do chia sẻ thêm)*`
    : `NarrAI registered your story concept: **"${snippet}"**.\n\n**Key narrative directions:**\n1. **Psychological depth**: Explore profound internal stakes and emotional triumph.\n2. **Dramatic turning point**: An unforeseen complication disrupts the opening plan.\n3. **Challenging alliance**: Two contrasting characters forced together by fate.\n\n*(Click any suggestion below to proceed)*`;
}

export interface IntakeTransitionOptions {
  refinedPrompt?: string;
  chatHistory: ChatMessage[];
  storyLength: StoryLength;
  modelTier: ModelTier;
}

interface Props {
  lang: Language;
  onStartWriting: (options: IntakeTransitionOptions) => Promise<void> | void;
  isGenerating?: boolean;
  initialChatHistory?: ChatMessage[];
  onClearHistory?: () => void;
}

export function UnifiedIntakeChat({
  lang,
  onStartWriting,
  isGenerating = false,
  initialChatHistory = [],
  onClearHistory,
}: Props) {
  const t = translations[lang] || translations.vi;
  const [messages, setMessages] = useState<ChatMessage[]>(initialChatHistory);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isFinalizing, setIsFinalizing] = useState(false);
  const [modelTier, setModelTier] = useState<ModelTier>("versatile");
  const [storyLength, setStoryLength] = useState<StoryLength>("medium");
  const [hasReadySignal, setHasReadySignal] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Sync initial chat history if provided
  useEffect(() => {
    if (initialChatHistory && initialChatHistory.length > 0 && messages.length === 0) {
      setMessages(initialChatHistory);
      const isReadyDetected = initialChatHistory.some(
        (m) => m.is_ready || (m.role === "assistant" && m.content.includes("[READY]"))
      );
      if (isReadyDetected) setHasReadySignal(true);
    }
  }, [initialChatHistory]);

  // Auto-scroll on new messages or loading state
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Auto-focus input on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  // Readiness evaluation: either AI output [READY] / is_ready, or at least 1 assistant turn
  const assistantTurns = useMemo(
    () => messages.filter((m) => m.role === "assistant").length,
    [messages]
  );
  const isReady = hasReadySignal || assistantTurns >= 1;

  // Starter prompt suggestions covering Vietnamese History, Sci-Fi, Xianxia, Slice of Life
  const starterIdeas = useMemo(() => [
    {
      id: "history",
      title: t.starter_history_title || (lang === "vi" ? "Lịch sử Việt Nam · Chính sử & Dã sử" : "Vietnamese history · Fact & fiction"),
      badge: t.starter_history_badge || (lang === "vi" ? "Chính sử chuẩn mực • Dã sử phóng tác" : "Strict history • Fictional perspective"),
      prompt: t.starter_history_prompt || (lang === "vi"
        ? "Một nghĩa sĩ áo vải thời Hậu Lê mang gươm báu bảo vệ bến sông lịch sử, đứng trước ngã rẽ giữa đại cục quốc gia và nghĩa tình riêng biệt."
        : "A peasant warrior during the Later Le dynasty guarding a historic river port, torn between national destiny and personal affection."),
      icon: ScrollText,
    },
    {
      id: "scifi",
      title: t.starter_scifi_title || (lang === "vi" ? "Cyberpunk Sài Gòn 2099" : "Cyberpunk Saigon 2099"),
      badge: t.starter_scifi_badge || (lang === "vi" ? "Hư cấu cá nhân tự do" : "Unconstrained creative sci-fi"),
      prompt: t.starter_scifi_prompt || (lang === "vi"
        ? "Một thám tử tư trong khu ổ chuột ngầm Sài Gòn năm 2099, chuyên điều tra các vụ đánh cắp ký ức và nhân dạng số bất hợp pháp."
        : "A private eye in the subterranean districts of Saigon 2099, investigating illegal synthetic memory theft and cybernetic identity fraud."),
      icon: Cpu,
    },
    {
      id: "xianxia",
      title: t.starter_xianxia_title || (lang === "vi" ? "Tu Chân & Kỳ Ảo Đông Phương" : "Eastern cultivation fantasy"),
      badge: t.starter_xianxia_badge || (lang === "vi" ? "Sáng tạo thế giới độc bản • Bảo hộ IP" : "Original worldbuilding • Protected IP"),
      prompt: t.starter_xianxia_prompt || (lang === "vi"
        ? "Thiếu niên vô danh sở hữu thần hồn dị biến, từng bước phá giải cổ trận nghìn năm chôn vùi dưới cấm địa phong ấn đan điền."
        : "An unassuming youth with an anomalous soul core unravels a thousand-year-old array hidden beneath a forbidden realm."),
      icon: Flame,
    },
    {
      id: "life",
      title: t.starter_life_title || (lang === "vi" ? "Đời sống & Chữa lành" : "Urban life & healing"),
      badge: t.starter_life_badge || (lang === "vi" ? "Tâm lý sâu sắc • Show, don't tell" : "Introspective depth • Show, don't tell"),
      prompt: t.starter_life_prompt || (lang === "vi"
        ? "Hai tâm hồn cô đơn tình cờ gặp gỡ tại một quán cà phê sách mở thâu đêm ở phố cổ Hà Nội vào một đêm mưa lạnh, tìm thấy sự an ủi diệu kỳ."
        : "Two lonely souls meet by chance at an all-night book café in the Hanoi Old Quarter on a cold, rainy evening, discovering unexpected solace."),
      icon: BookOpen,
    },
  ], [lang, t]);

  const handleRetry = async (assistantMsgIndex: number, failedPrompt?: string) => {
    if (loading || isFinalizing) return;
    const promptToRetry = failedPrompt || (assistantMsgIndex > 0 ? messages[assistantMsgIndex - 1]?.content : "");
    if (!promptToRetry) return;

    // Retain history up to the user message that preceded this failed assistant turn
    const historyBeforeFailedAssistant = messages.slice(0, assistantMsgIndex);
    setLoading(true);

    try {
      const res = await api.chatInterview(historyBeforeFailedAssistant);
      const suggestions = getSmartSuggestions(promptToRetry, lang);
      if (res.status === "success" && res.message) {
        const cleanMsg = res.message.replace(/\[READY\]/g, "").trim();
        const isReadyFlag = !!(res.is_ready || res.message.includes("[READY]"));
        if (isReadyFlag) {
          setHasReadySignal(true);
        }
        const updated = [
          ...historyBeforeFailedAssistant,
          { role: "assistant" as const, content: cleanMsg, is_ready: isReadyFlag, suggestions }
        ];
        setMessages(updated);
      } else {
        const fallbackText = generateDynamicClientFallback(promptToRetry, lang);
        const updated = [
          ...historyBeforeFailedAssistant,
          {
            role: "assistant" as const,
            content: fallbackText,
            is_offline_fallback: true,
            error_message: res?.message || (lang === "vi" ? "Mất kết nối với AI (Lỗi máy chủ)" : "Lost connection to AI (Server error)"),
            failed_prompt: promptToRetry,
            suggestions,
          }
        ];
        setMessages(updated);
      }
    } catch (err: any) {
      const suggestions = getSmartSuggestions(promptToRetry, lang);
      const fallbackText = generateDynamicClientFallback(promptToRetry, lang);
      const updated = [
        ...historyBeforeFailedAssistant,
        {
          role: "assistant" as const,
          content: fallbackText,
          is_offline_fallback: true,
          error_message: err?.message || (lang === "vi" ? "Mất kết nối với AI (Lỗi mạng)" : "Lost connection to AI (Network error)"),
          failed_prompt: promptToRetry,
          suggestions,
        }
      ];
      setMessages(updated);
    } finally {
      setLoading(false);
      // Restore focus to textarea so user can type immediately
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  };

  const handleSend = async (customText?: string) => {
    const textToSend = (customText !== undefined ? customText : input).trim();
    if (!textToSend || loading || isFinalizing) return;

    const newHistory: ChatMessage[] = [...messages, { role: "user", content: textToSend }];
    setMessages(newHistory);
    setInput("");
    setLoading(true);

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    try {
      const res = await api.chatInterview(newHistory);
      const suggestions = getSmartSuggestions(textToSend, lang);
      if (res.status === "success" && res.message) {
        // Strip [READY] tag from assistant visible message prose
        const cleanMsg = res.message.replace(/\[READY\]/g, "").trim();
        const isReadyFlag = !!(res.is_ready || res.message.includes("[READY]"));
        if (isReadyFlag) {
          setHasReadySignal(true);
        }

        const updatedHistory: ChatMessage[] = [
          ...newHistory,
          { role: "assistant", content: cleanMsg, is_ready: isReadyFlag, suggestions }
        ];
        setMessages(updatedHistory);
      } else {
        // Dynamic client fallback extracting concepts & providing retry
        const fallbackText = generateDynamicClientFallback(textToSend, lang);
        setMessages([
          ...newHistory,
          {
            role: "assistant",
            content: fallbackText,
            is_offline_fallback: true,
            error_message: res?.message || (lang === "vi" ? "Mất kết nối với AI (Lỗi máy chủ)" : "Lost connection to AI (Server error)"),
            failed_prompt: textToSend,
            suggestions,
          }
        ]);
      }
    } catch (err: any) {
      console.error("Chat interview error:", err);
      const suggestions = getSmartSuggestions(textToSend, lang);
      const fallbackText = generateDynamicClientFallback(textToSend, lang);
      setMessages([
        ...newHistory,
        {
          role: "assistant",
          content: fallbackText,
          is_offline_fallback: true,
          error_message: err?.message || (lang === "vi" ? "Mất kết nối với AI (Lỗi mạng hoặc ngoại tuyến)" : "Lost connection to AI (Network error)"),
          failed_prompt: textToSend,
          suggestions,
        }
      ]);
    } finally {
      setLoading(false);
      // Restore focus to textarea so user can type immediately
      setTimeout(() => textareaRef.current?.focus(), 50);
    }
  };

  const triggerFinalize = async () => {
    if (messages.length === 0 && !input.trim()) return;
    setIsFinalizing(true);

    try {
      let historyToUse = [...messages];
      if (input.trim()) {
        historyToUse.push({ role: "user", content: input.trim() });
        setMessages(historyToUse);
        setInput("");
      }

      // Step 1: Call api.refinePrompt (1-2s compression into Refined Narrative Bible)
      let refined = "";
      if (historyToUse.length > 0) {
        try {
          const res = await api.refinePrompt(historyToUse);
          if (res.status === "success" && res.refined_prompt) {
            refined = res.refined_prompt;
          }
        } catch (e) {
          console.error("Refine prompt API error:", e);
        }
      }

      // Fallback if refine returned empty
      if (!refined) {
        const userTexts = historyToUse.filter((m) => m.role === "user").map((m) => m.content);
        refined = userTexts.join("\n\n") || (lang === "vi" ? "Một câu chuyện kịch tính, lôi cuốn." : "A captivating, thrilling story.");
      }

      // Step 2: Trigger seamless transition to StoryEditor
      await onStartWriting({
        refinedPrompt: refined,
        chatHistory: historyToUse,
        storyLength,
        modelTier,
      });
    } catch (err) {
      console.error("Error finalizing intake prompt:", err);
      const fallbackPrompt = messages.map((m) => m.content).join("\n") || input.trim();
      await onStartWriting({
        refinedPrompt: fallbackPrompt || "Một câu chuyện kịch tính, lôi cuốn.",
        chatHistory: messages,
        storyLength,
        modelTier,
      });
    } finally {
      setIsFinalizing(false);
    }
  };

  const handleResetChat = () => {
    if (messages.length === 0) return;
    const confirmMsg = t.intake_clear_confirm || (lang === "vi"
      ? "Bạn có chắc muốn xóa lịch sử trò chuyện và bắt đầu lại ý tưởng mới?"
      : "Are you sure you want to clear chat history and start a new story concept?");
    if (window.confirm(confirmMsg)) {
      setMessages([]);
      setInput("");
      setHasReadySignal(false);
      onClearHistory?.();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
  };

  return (
    <div className="flex flex-col h-full w-full bg-[#FAF7F2] text-neutral-900 relative font-sans overflow-hidden">
      {/* Animated WeaveSilk Generative Art Background */}
      <AnimatedWeavesilkBackground intensity={0.85} interactive={true} />

      <header className="h-14 border-b border-neutral-300/80 px-4 sm:px-6 flex items-center justify-between shrink-0 bg-[#FAF7F2]/90 backdrop-blur-md z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded border border-neutral-300 bg-white text-neutral-950 flex items-center justify-center shrink-0 shadow-xs">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="max-w-[94px] truncate whitespace-nowrap text-xs font-bold tracking-tight text-neutral-950 sm:max-w-none sm:text-sm">
                {t.intake_header_title || "NarrAI Co-creator"}
              </h2>
              <span className="hidden text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded border border-neutral-300 bg-white text-neutral-800 sm:inline-flex">
                Q&A
              </span>
            </div>
            <p className="text-[11px] text-neutral-600 hidden md:block">
              {t.intake_header_sub || (lang === "vi"
                ? "Đa thể loại • Lịch sử Dân tộc chuẩn mực • Hư cấu tự do • Bảo hộ IP"
                : "Multi-genre • Authentic History • Creative Liberty • IP Protection")}
            </p>
          </div>
        </div>

        {/* Action Header Controls */}
        <div className="flex items-center gap-2 font-mono text-xs">
          {/* Reset Intake Chat Button */}
          {messages.length > 0 && (
            <button
              onClick={handleResetChat}
              disabled={loading || isFinalizing}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded border border-neutral-300 bg-white hover:bg-neutral-100 text-neutral-900 transition-colors disabled:opacity-40 cursor-pointer shadow-xs"
              title={t.intake_clear_chat || (lang === "vi" ? "Làm mới trò chuyện" : "Reset intake chat")}
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>{lang === "vi" ? "Làm mới" : "Reset"}</span>
            </button>
          )}

          {/* Prominent Action Button: "Bắt đầu viết truyện ngay" / "Chốt cốt truyện" */}
          <button
            onClick={triggerFinalize}
            disabled={(messages.length === 0 && !input.trim()) || isFinalizing || isGenerating}
            className="px-3.5 py-1.5 rounded text-xs font-bold bg-neutral-950 text-white hover:bg-neutral-800 transition-colors flex items-center gap-1.5 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer shadow-sm"
            title={
              isReady
                ? (lang === "vi" ? "AI đã sẵn sàng! Chốt cốt truyện và chuyển thẳng sang chấp bút bản thảo" : "Ready! Finalize plot and start drafting manuscript")
                : (lang === "vi" ? "Bắt đầu viết truyện ngay với ý tưởng hiện tại" : "Start writing story now with current ideas")
            }
          >
            {isFinalizing ? (
              <span>[Đang xử lý...]</span>
            ) : isReady ? (
              <>
                <PenTool className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Bắt đầu viết ngay</span>
                <span className="sm:hidden">Viết ngay</span>
                <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
              </>
            ) : (
              <>
                <PenTool className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{t.intake_finalize_plot || (lang === "vi" ? "Chốt cốt truyện" : "Finalize plot")}</span>
                <span className="sm:hidden">Chốt</span>
                <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
              </>
            )}
          </button>
        </div>
      </header>

      {/* Main Conversation Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8 pb-6 relative z-10">
        <div className="max-w-4xl mx-auto w-full px-4 flex flex-col min-h-full justify-between">

          {/* Empty State: Warm Hero & 4 Starter Prompt Pills */}
          {messages.length === 0 && (
            <div className="my-auto py-6 sm:py-10 text-center flex flex-col items-center animate-fadeIn">
              <div className="px-3 py-1 rounded border border-neutral-300 bg-white/95 backdrop-blur-md text-neutral-950 font-mono text-sm font-bold mb-4 shadow-xs">
                [NARR AI]
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-neutral-950 tracking-tight mb-2 drop-shadow-xs">
                {t.intake_welcome_title || (lang === "vi" ? "Bạn đang ấp ủ câu chuyện gì hôm nay?" : "What story are you dreaming of today?")}
              </h1>
              <p className="text-xs sm:text-sm text-neutral-600 max-w-lg mb-8 leading-relaxed">
                {t.intake_welcome_subtitle || (lang === "vi"
                  ? "Trò chuyện tự do bằng bất kỳ ý tưởng nào. NarrAI am hiểu mọi thể loại văn học, tôn trọng sự thật lịch sử và đồng hành cùng bạn từ ý niệm đầu tiên đến tác phẩm hoàn chỉnh."
                  : "Chat freely with any premise. NarrAI understands all literary genres, honors historical truth, and walks with you from initial spark to complete masterpiece.")}
              </p>

              {/* Starter Prompt Suggestion Pills */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5 w-full text-left font-mono">
                {starterIdeas.map((item) => {
                  const IconComp = item.icon;
                  return (
                    <button
                      key={item.id}
                      onClick={() => handleSend(item.prompt)}
                      className="p-5 rounded min-h-[140px] border border-neutral-300/80 bg-white hover:border-neutral-950 hover:shadow-lg transition-all backdrop-blur-md text-left group shadow-xs flex flex-col justify-between cursor-pointer"
                    >
                      <div>
                        <div className="flex items-center gap-2 mb-2 font-sans">
                          <IconComp className="w-4 h-4 text-neutral-950 shrink-0" />
                          <span className="text-xs sm:text-sm font-bold text-neutral-950">
                            {item.title}
                          </span>
                        </div>
                        <span className="inline-block text-[10px] font-mono px-2 py-0.5 rounded mb-2.5 border border-neutral-200 text-neutral-700 bg-neutral-100">
                          {item.badge}
                        </span>
                        <p className="text-xs font-sans text-neutral-600 line-clamp-3 leading-relaxed">
                          {item.prompt}
                        </p>
                      </div>
                      <div className="mt-3 flex items-center gap-1.5 text-xs font-mono font-bold text-neutral-950 opacity-0 group-hover:opacity-100 transition-opacity">
                        <span>{lang === "vi" ? "Bắt đầu khám phá" : "Explore concept"}</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Active Message History with Spacious Bubbles & Markdown */}
          {messages.length > 0 && (
            <div className="space-y-6 pb-6">
              {messages.map((msg, index) => {
                const isUser = msg.role === "user";
                return (
                  <div
                    key={index}
                    className={`flex items-start gap-3.5 ${isUser ? "flex-row-reverse" : "flex-row"} animate-fadeIn`}
                  >
                    {/* Avatar */}
                    <div
                      className={`w-9 h-9 rounded flex items-center justify-center shrink-0 border font-mono text-xs font-bold ${
                        isUser
                          ? "bg-neutral-950 text-white border-neutral-800"
                          : "bg-white text-neutral-950 border-neutral-300"
                      }`}
                    >
                      {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                    </div>

                    {/* Bubble Content */}
                    <div
                      className={`max-w-[88%] sm:max-w-[80%] px-4.5 py-3.5 rounded-xl ${
                        isUser
                          ? "bg-neutral-950 text-white shadow-sm"
                          : "bg-white border border-neutral-300/80 text-neutral-950 shadow-xs"
                      }`}
                    >
                      <FormattedMarkdown content={msg.content} isUser={isUser} />

                      {/* Interactive Suggestion Pills (Clickable Choices) */}
                      {!isUser && (() => {
                        const promptContext = msg.failed_prompt || (index > 0 ? messages[index - 1]?.content : "");
                        const sugList = (msg.suggestions && msg.suggestions.length > 0)
                          ? msg.suggestions
                          : getSmartSuggestions(promptContext || msg.content, lang);
                        if (!sugList || sugList.length === 0) return null;
                        return (
                          <div className="mt-3 pt-2.5 border-t border-neutral-200 space-y-2">
                            <div className="text-[11px] font-mono font-bold text-neutral-500 uppercase flex items-center gap-1.5">
                              <Sparkles className="w-3.5 h-3.5 text-neutral-900 shrink-0" />
                              <span>{lang === "vi" ? "Gợi ý lựa chọn nhanh (Bấm để chọn):" : "Quick suggestions (Click to select):"}</span>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {sugList.map((sug, sIdx) => {
                                const isDraftNow = sug.includes("viết truyện ngay") || sug.includes("Start writing") || sug.includes("hành trình tu tiên ngay") || sug.includes("điều tra phá án ngay") || sug.includes("start drafting");
                                return (
                                  <button
                                    key={sIdx}
                                    type="button"
                                    onClick={() => isDraftNow ? triggerFinalize() : handleSend(sug)}
                                    disabled={loading || isFinalizing}
                                    className={`px-3 py-1.5 rounded-lg text-xs font-sans border transition-all text-left flex items-center gap-1.5 cursor-pointer shadow-xs active:scale-95 ${
                                      isDraftNow
                                        ? "bg-neutral-950 text-white hover:bg-neutral-800 border-neutral-950 font-bold"
                                        : "border-neutral-300 bg-neutral-100 hover:bg-neutral-950 hover:text-white text-neutral-800"
                                    }`}
                                  >
                                    <span>{sug}</span>
                                    <ArrowRight className="w-3 h-3 shrink-0" />
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        );
                      })()}

                      {/* Offline Fallback Connection Status & Retry Button */}
                      {!isUser && msg.is_offline_fallback && (
                        <div className="mt-3 pt-2.5 border-t border-neutral-200 flex flex-wrap items-center justify-between gap-2 font-mono text-xs">
                          <div className="flex items-center gap-1.5 font-bold text-neutral-600">
                            <RefreshCw className="w-3.5 h-3.5" />
                            <span>{lang === "vi" ? "Mất kết nối AI (Gợi ý dự phòng)" : "Lost AI connection (Fallback preview)"}</span>
                          </div>
                          <button
                            onClick={() => handleRetry(index, msg.failed_prompt)}
                            disabled={loading || isFinalizing}
                            className="px-2.5 py-1 rounded text-xs font-bold bg-neutral-200 hover:bg-neutral-300 text-neutral-900 transition-all disabled:opacity-40 flex items-center gap-1"
                            title={lang === "vi" ? "Thử lại kết nối đến máy chủ AI" : "Retry connection to AI server"}
                          >
                            <RefreshCw className="w-3 h-3" />
                            <span>{lang === "vi" ? "Thử lại" : "Retry"}</span>
                          </button>
                        </div>
                      )}

                      {/* Ready Badge if assistant flagged readiness */}
                      {!isUser && msg.is_ready && (
                        <div className="mt-3 pt-2.5 border-t border-neutral-200 flex items-center justify-between font-mono text-xs">
                          <div className="flex items-center gap-1.5 font-bold text-neutral-950">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>{lang === "vi" ? "Cốt truyện đã định hình" : "Plot formed"}</span>
                          </div>
                          <button
                            onClick={triggerFinalize}
                            className="px-2.5 py-1 rounded text-xs font-bold bg-neutral-950 text-white hover:bg-neutral-800 transition-all flex items-center gap-1"
                          >
                            <span>{t.intake_start_writing_now || (lang === "vi" ? "Viết ngay" : "Write now")}</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Typing State */}
              {loading && (
                <div className="flex items-start gap-3.5 animate-fadeIn">
                  <div className="w-9 h-9 rounded bg-white border border-neutral-300 text-neutral-950 flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div className="px-4.5 py-3.5 rounded-xl bg-white border border-neutral-300/80 flex items-center gap-2 font-mono text-xs text-neutral-700 shadow-xs">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>
                      {lang === "vi" ? "NarrAI đang suy nghĩ..." : "NarrAI is formulating..."}
                    </span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}

        </div>
      </div>

      {/* Bottom Input Dock */}
      <div className="shrink-0 p-3 sm:p-4 bg-[#FAF7F2]/90 backdrop-blur-md border-t border-neutral-300/80 z-20">
        <div className="max-w-4xl mx-auto w-full px-4">

          {/* Quick Guidance & Readiness Notification Banner if ready */}
          {isReady && messages.length > 0 && !isFinalizing && (
            <div className="mb-2 px-3 py-1.5 rounded-lg bg-white border border-neutral-300/90 flex items-center justify-between text-xs text-neutral-950 animate-fadeIn font-mono shadow-xs">
              <div className="flex items-center gap-1.5 font-bold">
                <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                <span className="font-sans font-normal">
                  {lang === "vi"
                    ? "Cốt truyện đã đủ độ chín! Bạn có thể bấm 'Bắt đầu viết truyện ngay' bất cứ lúc nào."
                    : "Plot premise is well formed! You can click 'Start writing story now' at any time."}
                </span>
              </div>
              <button
                onClick={triggerFinalize}
                className="font-bold underline hover:text-neutral-700 flex items-center gap-1 ml-2 shrink-0"
              >
                <span>{t.intake_jump_to_manuscript || (lang === "vi" ? "Chấp bút ngay" : "Draft now")}</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          )}

          {/* Input Capsule */}
          <div className="bg-white border border-neutral-300/80 rounded-xl p-2.5 sm:p-3 flex flex-col gap-2.5 shadow-sm">

            {/* Controls Bar: Model Tier Selector & Story Length Pill */}
            <div className="flex items-center justify-between gap-2 flex-wrap border-b border-neutral-200 pb-2 px-1 font-mono text-xs">
              {/* Compact model selector */}
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] font-bold text-neutral-500 uppercase shrink-0">
                  {t.intake_model_tier_label || (lang === "vi" ? "Mô hình:" : "Model:")}
                </span>
                <select
                  value={modelTier}
                  onChange={(e) => setModelTier(e.target.value as ModelTier)}
                  className="text-[11px] font-mono bg-neutral-100 text-neutral-900 border border-neutral-300 rounded px-2 py-1 outline-none cursor-pointer max-w-[120px] sm:max-w-[150px]"
                  title={lang === "vi" ? "Chọn cấp độ mô hình AI" : "Select AI model tier"}
                >
                  <option value="fast">{lang === "vi" ? "Nhanh" : "Fast"}</option>
                  <option value="versatile">{lang === "vi" ? "Linh hoạt" : "Versatile"}</option>
                  <option value="premium">{lang === "vi" ? "Cao cấp" : "Premium"}</option>
                </select>
              </div>

              {/* Story Length Pill Selector */}
              <div className="flex items-center gap-1 bg-neutral-100 p-1 rounded-lg border border-neutral-200">
                <span className="text-[11px] font-bold text-neutral-500 px-1.5 hidden lg:inline uppercase">
                  {t.intake_length_label || (lang === "vi" ? "Độ dài:" : "Length:")}
                </span>
                {(["short", "medium", "long"] as StoryLength[]).map((len) => {
                  const isSelected = storyLength === len;
                  const labelMap = {
                    short: t.intake_len_short || (lang === "vi" ? "Ngắn" : "Short"),
                    medium: t.intake_len_medium || (lang === "vi" ? "Vừa" : "Medium"),
                    long: t.intake_len_long || (lang === "vi" ? "Tiểu thuyết" : "Novel"),
                  };
                  return (
                    <button
                      key={len}
                      type="button"
                      onClick={() => setStoryLength(len)}
                      className={`px-2.5 py-1 rounded text-xs font-mono transition-all ${
                        isSelected
                          ? "bg-neutral-950 text-white font-bold shadow-xs"
                          : "text-neutral-600 hover:text-neutral-950"
                      }`}
                    >
                      {labelMap[len]}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Input Row: Auto-expanding Textarea & Send Button */}
            <div className="flex items-end gap-2">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleTextareaInput}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={loading || isFinalizing}
                placeholder={
                  t.intake_input_placeholder || (lang === "vi"
                    ? "Nhập ý tưởng câu chuyện của bạn... (Enter để gửi, Shift+Enter xuống dòng)"
                    : "Type your story concept... (Enter to send, Shift+Enter for newline)")
                }
                className="flex-1 max-h-40 min-h-[44px] bg-transparent resize-none px-3 py-2 text-sm text-neutral-950 placeholder-neutral-400 outline-none leading-relaxed font-sans"
              />

              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading || isFinalizing}
                className="px-4 h-10 rounded-lg bg-neutral-950 text-white hover:bg-neutral-800 flex items-center justify-center gap-1.5 shrink-0 transition-colors disabled:opacity-30 disabled:cursor-not-allowed font-mono text-xs font-bold shadow-xs"
                title={t.intake_send || (lang === "vi" ? "Gửi ý tưởng" : "Send idea")}
              >
                <Send className="w-3.5 h-3.5" />
                <span>{lang === "vi" ? "Gửi" : "Send"}</span>
              </button>
            </div>
          </div>

          {/* Bottom Guardrail Footer */}
          <div className="flex items-center justify-between mt-2 px-2 text-[10px] sm:text-[11px] text-neutral-600 font-mono">
            <div className="flex min-w-0 flex-1 items-center gap-1.5">
              <span>[BẢO MẬT]</span>
              <span className="min-w-0 truncate font-sans">
                {t.intake_guardrail_notice || (lang === "vi"
                  ? "Tự do hư cấu cá nhân • Tôn trọng lịch sử Dân tộc • Bảo mật tác quyền"
                  : "Creative freedom • Historical authenticity • IP copyright protected")}
              </span>
            </div>

            {messages.length > 0 && (
              <button
                onClick={triggerFinalize}
                disabled={isFinalizing}
                className="font-bold text-neutral-950 hover:underline flex items-center gap-1 shrink-0 ml-2"
              >
                <span>[{t.intake_start_writing_now || (lang === "vi" ? "Bắt đầu viết" : "Start writing")}] -&gt;</span>
              </button>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}

export default UnifiedIntakeChat;
