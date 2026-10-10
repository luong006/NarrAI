import os
"""
Memory Extractor Agent — Trích xuất và cập nhật bộ nhớ truyện & Dynamic Scene-Graph sau mỗi chương.
Dùng model nhẹ qwen/qwen3.8-27b để tiết kiệm token và tốc độ.
"""
import json
import re
from typing import Optional
from llm.groq_client import GroqClient
from agents.story_memory import StoryBible, StoryMemory

try:
    from backend.models.scene_graph import (
        DynamicSceneGraph,
        SpaceEnclosure,
        CharacterEntity,
        BoundaryType,
        VitalityState,
    )
except ImportError:
    try:
        from models.scene_graph import (
            DynamicSceneGraph,
            SpaceEnclosure,
            CharacterEntity,
            BoundaryType,
            VitalityState,
        )
    except ImportError:
        DynamicSceneGraph = None
        SpaceEnclosure = None
        CharacterEntity = None
        BoundaryType = None
        VitalityState = None


class MemoryExtractor:
    def __init__(self):
        self.llm = GroqClient(model_name="qwen/qwen3.8-27b", api_key=os.environ.get("GROQ_API_KEY_BIBLE"))

    def extract_bible(self, refined_prompt: str) -> StoryBible:
        system_prompt = """Ban la chuyen gia phan tich cot truyen. Doc ban phac thao cot truyen va trich xuat thong tin thanh JSON.

DAU RA BAT BUOC la JSON voi cau truc:
{
    "title": "Tieu de truyen",
    "genre": "The loai (vi du: Fantasy, Romance, Kinh di...)",
    "characters": [
        {"name": "Ten nhan vat", "appearance": "Mo ta ngoai hinh chi tiet", "personality": "Tinh cach", "role": "Vai tro trong truyen"}
    ],
    "world_setting": "Boi canh the gioi va thoi gian",
    "main_plot": "Tom tat cot truyen chinh (timeline su kien)",
    "writing_style": "Phong cach viet mong muon"
}

CHI TRA VE JSON. KHONG GIAI THICH GI THEM."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"BAN PHAC THAO COT TRUYEN:\n{refined_prompt}\n\nHay trich xuat JSON:"}
        ]

        try:
            response = self.llm.chat(messages, temperature=0.3, max_tokens=2000)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0), strict=False)
            else:
                data = json.loads(response, strict=False)

            bible = StoryBible(
                title=data.get("title", ""),
                genre=data.get("genre", ""),
                characters=data.get("characters", []),
                world_setting=data.get("world_setting", ""),
                main_plot=data.get("main_plot", ""),
                writing_style=data.get("writing_style", ""),
                refined_prompt=refined_prompt
            )
            return bible
        except Exception as e:
            print(f"MemoryExtractor.extract_bible error: {e}")
            return StoryBible(
                title="Truyen chua dat ten",
                refined_prompt=refined_prompt,
                main_plot=refined_prompt[:500]
            )

    def extract_memory(self, new_chapter_text: str, current_memory: StoryMemory) -> StoryMemory:
        # Spatial context info
        active_enc_name = "Chưa rõ"
        entity_locations = {}
        if current_memory.dynamic_scene_graph:
            enc = current_memory.dynamic_scene_graph.get_active_enclosure()
            if enc:
                active_enc_name = enc.name
            for cid, char in current_memory.dynamic_scene_graph.entities.items():
                entity_locations[char.name] = char.current_location_id or active_enc_name

        system_prompt = f"""Ban la chuyen gia phan tich noi dung truyen va Dynamic Scene-Graph. Doc chuong truyen moi viet va trich xuat thong tin de cap nhat bo nho va trang thai khong gian.

THONG TIN HIEN TAI:
- So chuong da viet: {current_memory.current_chapter}
- Khong gian phan canh hien tai: {active_enc_name}
- Vi tri nhan vat hien tai: {json.dumps(entity_locations, ensure_ascii=False) if entity_locations else 'Chua ro'}
- Nhan vat da biet: {json.dumps(current_memory.character_states, ensure_ascii=False) if current_memory.character_states else 'Chua co'}
- Tuyen truyen dang mo: {json.dumps(current_memory.unresolved_threads, ensure_ascii=False) if current_memory.unresolved_threads else 'Chua co'}

DAU RA BAT BUOC la JSON:
{{
    "chapter_summary": "Tom tat chuong nay trong 2-3 cau (duoi 100 tu)",
    "character_states": {{"Ten nhan vat": "Trang thai/cam xuc hien tai sau chuong nay"}},
    "new_threads": ["Tuyen truyen MOI xuat hien trong chuong nay"],
    "resolved_threads": ["Tuyen truyen DA DUOC GIAI QUYET trong chuong nay"],
    "relationships": {{"NhanVat1-NhanVat2": "Mo ta moi quan he hien tai"}},
    "spatial_transitions": [
        {{"character": "Ten nhan vat", "new_location": "Ten dia diem/phong moi neu co di chuyen trong chuong", "action": "buoc vao / roi phong / len xe"}}
    ],
    "active_scene_location": "Ten khong gian phan canh ket thuc chuong (neu thay doi, con khong de null)"
}}

CHI TRA VE JSON. KHONG GIAI THICH."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"CHUONG MOI VIET:\n{new_chapter_text[:4000]}\n\nHay trich xuat JSON:"}
        ]

        try:
            response = self.llm.chat(messages, temperature=0.3, max_tokens=1800)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0), strict=False)
            else:
                data = json.loads(response, strict=False)

            # Update memory summaries and states
            current_memory.chapter_summaries.append(
                data.get("chapter_summary", f"Chuong {current_memory.current_chapter}")
            )

            new_states = data.get("character_states", {})
            current_memory.character_states.update(new_states)

            new_threads = data.get("new_threads", [])
            for t in new_threads:
                if t and t not in current_memory.unresolved_threads:
                    current_memory.unresolved_threads.append(t)

            resolved = data.get("resolved_threads", [])
            for t in resolved:
                if t in current_memory.unresolved_threads:
                    current_memory.unresolved_threads.remove(t)

            new_relations = data.get("relationships", {})
            current_memory.relationship_map.update(new_relations)

            # Auto-init dynamic_scene_graph if not present
            if current_memory.dynamic_scene_graph is None:
                current_memory.init_scene_graph_from_bible()

            # Process spatial transitions
            if current_memory.dynamic_scene_graph:
                sg = current_memory.dynamic_scene_graph

                # 1. Check spatial transitions for specific characters
                transitions = data.get("spatial_transitions") or []
                for tr in transitions:
                    if not isinstance(tr, dict):
                        continue
                    char_name = tr.get("character", "").strip()
                    new_loc = tr.get("new_location", "").strip()
                    if not char_name or not new_loc:
                        continue

                    # Find matching character
                    target_char = None
                    for cid, c in sg.entities.items():
                        if c.name.lower() == char_name.lower() or char_name.lower() in [a.lower() for a in c.aliases]:
                            target_char = c
                            break

                    if target_char:
                        # Find or create enclosure for new_loc
                        target_enc_id = None
                        for eid, enc in sg.enclosures.items():
                            if enc.name.lower() == new_loc.lower():
                                target_enc_id = eid
                                break

                        if not target_enc_id and SpaceEnclosure is not None:
                            # Create new enclosure node
                            target_enc_id = new_loc.lower().replace(" ", "_")[:30]
                            new_enc = SpaceEnclosure(
                                id=target_enc_id,
                                name=new_loc,
                                boundary_type=BoundaryType.INDOOR_ENCLOSED,
                                architectural_anchor=f"inside {new_loc}, interior enclosure",
                                persistent_fixtures=[],
                                lighting_atmosphere="",
                                negative_drift_tokens=["outdoor", "street", "trees", "cars", "sky"],
                                connected_enclosures=[sg.active_enclosure_id] if sg.active_enclosure_id else []
                            )
                            sg.add_enclosure(new_enc)
                            if sg.active_enclosure_id and sg.active_enclosure_id in sg.enclosures:
                                sg.enclosures[sg.active_enclosure_id].connected_enclosures.append(target_enc_id)

                        if target_enc_id:
                            target_char.current_location_id = target_enc_id

                # 2. Check scene transition gating for active enclosure
                active_loc = data.get("active_scene_location")
                if active_loc and isinstance(active_loc, str) and active_loc.strip():
                    sg.gate_scene_transition(active_loc)
                else:
                    # Check the chapter text tail for transition verbs
                    sg.gate_scene_transition(new_chapter_text[-1200:])

            return current_memory

        except Exception as e:
            print(f"MemoryExtractor.extract_memory error: {e}")
            current_memory.chapter_summaries.append(
                f"Chuong {current_memory.current_chapter} (tu dong tom tat that bai)"
            )
            return current_memory
