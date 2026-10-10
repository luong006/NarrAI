"""
Models package for NarrAI backend.
"""
try:
    from backend.models.scene_graph import (
        CharacterEntity,
        ItemEntity,
        SpaceEnclosure,
        EraGenreConstraint,
        DynamicSceneGraph,
        VitalityState,
        EntityRole,
        BoundaryType,
        EraType,
        sanitize_spatial_prompt,
        sanitize_era_prompt,
    )
except ImportError:
    from models.scene_graph import (
        CharacterEntity,
        ItemEntity,
        SpaceEnclosure,
        EraGenreConstraint,
        DynamicSceneGraph,
        VitalityState,
        EntityRole,
        BoundaryType,
        EraType,
        sanitize_spatial_prompt,
        sanitize_era_prompt,
    )

__all__ = [
    "CharacterEntity",
    "ItemEntity",
    "SpaceEnclosure",
    "EraGenreConstraint",
    "DynamicSceneGraph",
    "VitalityState",
    "EntityRole",
    "BoundaryType",
    "EraType",
    "sanitize_spatial_prompt",
    "sanitize_era_prompt",
]
