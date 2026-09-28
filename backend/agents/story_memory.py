"""
Story Memory Module
Enforces memory continuity, narrative beats, and Dynamic Scene-Graph Ontology (DSGO) state.
"""
import json
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

try:
    from backend.models.scene_graph import (
        DynamicSceneGraph,
        CharacterEntity,
        SpaceEnclosure,
        EraGenreConstraint,
        BoundaryType,
        VitalityState,
        EntityRole,
    )
except ImportError:
    try:
        from models.scene_graph import (
            DynamicSceneGraph,
            CharacterEntity,
            SpaceEnclosure,
            EraGenreConstraint,
            BoundaryType,
            VitalityState,
            EntityRole,
        )
    except ImportError:
        DynamicSceneGraph = None
        CharacterEntity = None
        SpaceEnclosure = None
        EraGenreConstraint = None
        BoundaryType = None
        VitalityState = None
        EntityRole = None


@dataclass
class StoryBible:
    title: str = ""
    genre: str = ""
    characters: list = field(default_factory=list)
    world_setting: str = ""
    main_plot: str = ""
    writing_style: str = ""
    refined_prompt: str = ""
    narrative_beats: List[str] = field(default_factory=list)
    narrative_mode: str = "hu_cau_tu_do"
    cultural_tier: int = 1

    def __post_init__(self):
        if self.characters is None:
            self.characters = []
        if self.narrative_beats is None:
            self.narrative_beats = []

    def to_prompt_block(self):
        chars_text = ""
        for c in self.characters:
            name = c.get("name", "?")
            appearance = c.get("appearance", "")
            personality = c.get("personality", "")
            role = c.get("role", "")
            chars_text += f"\n  - {name}: {role}. Ngoai hinh: {appearance}. Tinh cach: {personality}."
        
        beats_text = ""
        if self.narrative_beats:
            beats_text = "\nCau truc 5 nhip kich tinh (Narrative Beats):"
            for b in self.narrative_beats:
                beats_text += f"\n  * {b}"

        mode_line = f"\nChe do sang tac: {self.narrative_mode}" if self.narrative_mode else ""

        return (
            f"=== STORY BIBLE ===\n"
            f"Tieu de: {self.title}\n"
            f"The loai: {self.genre}{mode_line}\n"
            f"Boi canh: {self.world_setting}\n"
            f"Nhan vat chinh:{chars_text}\n"
            f"Cot truyen chinh: {self.main_plot}\n"
            f"Phong cach viet: {self.writing_style}{beats_text}\n"
        )

    def to_dict(self):
        return {
            "title": self.title,
            "genre": self.genre,
            "characters": self.characters,
            "world_setting": self.world_setting,
            "main_plot": self.main_plot,
            "writing_style": self.writing_style,
            "refined_prompt": self.refined_prompt,
            "narrative_beats": list(self.narrative_beats),
            "narrative_mode": self.narrative_mode,
            "cultural_tier": self.cultural_tier,
        }

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            return cls()
        return cls(
            title=d.get("title", ""),
            genre=d.get("genre", ""),
            characters=d.get("characters") or [],
            world_setting=d.get("world_setting", ""),
            main_plot=d.get("main_plot", ""),
            writing_style=d.get("writing_style", ""),
            refined_prompt=d.get("refined_prompt", ""),
            narrative_beats=d.get("narrative_beats") or [],
            narrative_mode=d.get("narrative_mode", "hu_cau_tu_do"),
            cultural_tier=d.get("cultural_tier", 1),
        )


class StoryMemory:
    def __init__(self, story_bible=None, dynamic_scene_graph: Optional[Any] = None):
        self.session_id = str(uuid.uuid4())
        self.story_bible = story_bible or StoryBible()
        self.chapter_summaries = []
        self.character_states = {}
        self.unresolved_threads = []
        self.relationship_map = {}
        self.current_chapter = 0
        self.full_text = ""
        self.dynamic_scene_graph = dynamic_scene_graph

    @property
    def scene_graph(self):
        return self.dynamic_scene_graph

    @scene_graph.setter
    def scene_graph(self, value):
        self.dynamic_scene_graph = value

    def init_scene_graph_from_bible(self) -> Optional[Any]:
        """
        Auto-bootstraps a DynamicSceneGraph from StoryBible characters and world setting
        if dynamic_scene_graph is not already set.
        """
        if self.dynamic_scene_graph is not None:
            return self.dynamic_scene_graph

        if DynamicSceneGraph is None or CharacterEntity is None or SpaceEnclosure is None:
            return None

        # Build EraGenreConstraint & Enclosure based on narrative mode & cultural tier
        raw_mode = getattr(self.story_bible, "narrative_mode", "HU_CAU_TU_DO")
        c_tier = getattr(self.story_bible, "cultural_tier", 1)
        setting_text = self.story_bible.world_setting or ""
        genre_lower = (self.story_bible.genre or "").lower()
        setting_lower = setting_text.lower()

        is_historical = (
            raw_mode in ("CHINH_SU", "DA_SU") or
            any(k in genre_lower for k in ["lịch sử", "dã sử", "chính sử", "chiến tranh", "cổ trang", "triều đại"]) or
            any(k in setting_lower for k in ["bạch đằng", "vạn kiếp", "thăng long", "hoa lư", "ngọc hồi", "đại việt", "nhà trần", "nhà lê"])
        )

        enc_id = "primary_enclosure"

        if is_historical:
            era_name = "vietnamese_canonical"
            genre_name = self.story_bible.genre or ("Chính sử Việt Nam" if raw_mode == "CHINH_SU" else "Dã sử Việt Nam")
            world_axioms = [
                "Bối cảnh lịch sử Việt Nam, tuân thủ dữ kiện lịch sử và trang phục văn hóa bản địa.",
                "Tuân thủ chuẩn mực ngôn ngữ và xưng hô thời đại."
            ]
            era_banlist = []
            setting_name = setting_text[:60] if setting_text else "Doanh trại / Phủ đường"
            is_outdoor = any(w in setting_lower for w in ["sông", "chiến trường", "bạch đằng", "làng", "rừng", "núi", "doanh trại ngoài trời"])
            boundary_type = BoundaryType.OUTDOOR_BOUNDED if is_outdoor else BoundaryType.INDOOR_ENCLOSED
            architectural_anchor = f"{setting_name}, bối cảnh lịch sử Việt Nam"
            persistent_fixtures = (
                ["bản đồ quân sự", "bàn chỉ huy", "cột gỗ chạm khắc"]
                if is_outdoor else
                ["cột gỗ chạm khắc", "ngai vàng hoặc bàn gỗ", "đèn dầu"]
            )
            lighting_atm = "ánh lửa bập bùng cùng ánh sáng tự nhiên"
            negative_drift = ["smartphone", "neon", "car", "modern building", "school uniform", "hanfu", "kimono"]
        elif c_tier == 3:
            era_name = "open_domain"
            genre_name = self.story_bible.genre or "Open Domain Fiction"
            world_axioms = ["Thế giới giả tưởng / viễn tưởng tự do, tuân thủ logic nội tại của tác phẩm."]
            era_banlist = []
            setting_name = setting_text[:60] if setting_text else "Không gian bối cảnh"
            boundary_type = BoundaryType.INDOOR_ENCLOSED
            architectural_anchor = f"{setting_name}, bối cảnh tự do"
            persistent_fixtures = ["nội thất đặc trưng", "thiết bị chuyên dụng"]
            lighting_atm = "ánh sáng môi trường tự nhiên"
            negative_drift = []
        else:
            # Modern / Campus default for backward compatibility
            era_name = "modern_2020s"
            genre_name = self.story_bible.genre or "Modern Campus Light Novel"
            world_axioms = ["Công nghệ hiện đại, không có ma pháp", "Tuân thủ định luật vật lý"]
            era_banlist = ["hanfu", "robes", "sword", "magic", "cultivation"]
            setting_name = setting_text[:60] if setting_text else "Lớp học"
            boundary_type = BoundaryType.INDOOR_ENCLOSED
            architectural_anchor = f"inside {setting_name[:50]}, enclosed interior"
            persistent_fixtures = ["wooden desks", "room door", "chalkboard"]
            lighting_atm = "diffused daylight streaming through window"
            negative_drift = ["outdoor", "street", "trees", "cars", "sky"]

        era_constraint = EraGenreConstraint(
            era_name=era_name,
            genre_name=genre_name,
            world_axioms=world_axioms,
            era_banlist=era_banlist,
            cultural_tier=c_tier,
            narrative_mode=raw_mode
        )

        initial_enclosure = SpaceEnclosure(
            id=enc_id,
            name=setting_name,
            boundary_type=boundary_type,
            architectural_anchor=architectural_anchor,
            persistent_fixtures=persistent_fixtures,
            lighting_atmosphere=lighting_atm,
            negative_drift_tokens=negative_drift,
            connected_enclosures=[]
        )

        # Build Character entities
        characters_dict = {}
        for c in self.story_bible.characters:
            c_name = c.get("name", "").strip()
            if not c_name:
                continue
            c_id = c_name.lower().replace(" ", "_")
            c_appearance = c.get("appearance", "")
            c_role = c.get("role", "supporting").lower()
            role_enum = EntityRole.LEAD if "chính" in c_role or "lead" in c_role else EntityRole.SUPPORTING

            char_ent = CharacterEntity(
                id=c_id,
                name=c_name,
                aliases=[c_name],
                visual_dna=f"{c_name} ({c_appearance})" if c_appearance else c_name,
                vitality_state=VitalityState.ALIVE,
                current_location_id=enc_id,
                psychological_state="bình tĩnh",
                role=role_enum
            )
            characters_dict[c_id] = char_ent
            initial_enclosure.active_entities.append(c_id)

        dsg = DynamicSceneGraph(
            session_id=self.session_id,
            era_genre=era_constraint,
            entities=characters_dict,
            enclosures={enc_id: initial_enclosure},
            active_enclosure_id=enc_id,
            cultural_tier=c_tier,
            narrative_mode=raw_mode
        )
        self.dynamic_scene_graph = dsg
        return dsg

    def to_prompt_block(self):
        summaries = ""
        for i, s in enumerate(self.chapter_summaries, 1):
            summaries += f"\n  Chuong {i}: {s}"
        states = ""
        for name, state in self.character_states.items():
            states += f"\n  - {name}: {state}"
        threads = ""
        for t in self.unresolved_threads:
            threads += f"\n  - {t}"
        relations = ""
        for pair, desc in self.relationship_map.items():
            relations += f"\n  - {pair}: {desc}"

        sg_block = ""
        if self.dynamic_scene_graph:
            enc = self.dynamic_scene_graph.get_active_enclosure()
            char_locations = []
            for cid, char in self.dynamic_scene_graph.entities.items():
                loc_name = char.current_location_id or "Chưa rõ"
                if char.current_location_id and char.current_location_id in self.dynamic_scene_graph.enclosures:
                    loc_name = self.dynamic_scene_graph.enclosures[char.current_location_id].name
                char_locations.append(f"{char.name} -> {loc_name}")

            loc_summary = ", ".join(char_locations) if char_locations else "Chưa rõ"
            fixtures_str = ", ".join(enc.persistent_fixtures) if enc and enc.persistent_fixtures else "Đạo cụ nội thất"
            axioms_str = "; ".join(self.dynamic_scene_graph.era_genre.world_axioms) if self.dynamic_scene_graph.era_genre.world_axioms else "Tuân thủ logic thực tế"

            sg_block = (
                f"=== DYNAMIC SCENE-GRAPH (RÀNG BUỘC 3 CHIỀU) ===\n"
                f"1. THỜI ĐẠI & THỂ LOẠI: {self.dynamic_scene_graph.era_genre.era_name} | {self.dynamic_scene_graph.era_genre.genre_name}\n"
                f"   - Quy tắc thế giới: {axioms_str}\n"
                f"2. KHÔNG GIAN PHÂN CẢNH HIỆN TẠI (ACTIVE ENCLOSURE):\n"
                f"   - Vị trí: {enc.name if enc else 'Chưa xác định'} ({enc.boundary_type.value if enc else ''})\n"
                f"   - Neo giữ kiến trúc: {enc.architectural_anchor if enc else 'Không gian khép kín'}\n"
                f"   - Đạo cụ cố định: {fixtures_str}\n"
                f"   - Vị trí nhân vật: {loc_summary}\n"
                f"   - QUY TẮC PHÂN CẢNH: TUYỆT ĐỐI KHÔNG tự ý đổi bối cảnh ra ngoài trời/đường phố nếu không có hành động di chuyển rõ ràng.\n"
                f"================================================\n\n"
            )

        return (
            f"{sg_block}=== LONG-TERM MEMORY ===\n"
            f"So chuong da viet: {self.current_chapter}\n"
            f"Tom tat cac chuong:{summaries or ' (Chua co)'}\n"
            f"Trang thai nhan vat:{states or ' (Chua co)'}\n"
            f"Tuyen truyen chua giai quyet:{threads or ' (Chua co)'}\n"
            f"Moi quan he nhan vat:{relations or ' (Chua co)'}\n"
        )

    def get_short_context(self, max_chars=6000):
        if len(self.full_text) <= max_chars:
            return self.full_text
        return self.full_text[-max_chars:]

    def append_chapter(self, chapter_text):
        self.current_chapter += 1
        if self.full_text:
            self.full_text += "\n\n" + chapter_text
        else:
            self.full_text = chapter_text

    def to_dict(self):
        d = {
            "session_id": self.session_id,
            "story_bible": self.story_bible.to_dict(),
            "chapter_summaries": self.chapter_summaries,
            "character_states": self.character_states,
            "unresolved_threads": self.unresolved_threads,
            "relationship_map": self.relationship_map,
            "current_chapter": self.current_chapter,
            "full_text": self.full_text,
            "dynamic_scene_graph": self.dynamic_scene_graph.to_dict() if self.dynamic_scene_graph else None,
        }
        return d

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            return cls()
        mem = cls()
        mem.session_id = d.get("session_id", str(uuid.uuid4()))
        mem.story_bible = StoryBible.from_dict(d.get("story_bible", {}))
        mem.chapter_summaries = d.get("chapter_summaries", [])
        mem.character_states = d.get("character_states", {})
        mem.unresolved_threads = d.get("unresolved_threads", [])
        mem.relationship_map = d.get("relationship_map", {})
        mem.current_chapter = d.get("current_chapter", 0)
        mem.full_text = d.get("full_text", "")

        # Support both dynamic_scene_graph and scene_graph keys
        sg_data = d.get("dynamic_scene_graph") or d.get("scene_graph")
        if sg_data and isinstance(sg_data, dict) and DynamicSceneGraph is not None:
            try:
                mem.dynamic_scene_graph = DynamicSceneGraph.from_dict(sg_data)
            except Exception:
                mem.dynamic_scene_graph = None
        else:
            mem.dynamic_scene_graph = None

        return mem
