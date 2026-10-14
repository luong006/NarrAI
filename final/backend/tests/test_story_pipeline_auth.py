import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from routers import story_pipeline_router


class StoryPipelineAuthorizationTests(unittest.TestCase):
    def test_story_pipeline_requires_configured_moderator(self):
        db = Mock()

        with self.assertRaises(HTTPException) as unauthenticated:
            asyncio.run(story_pipeline_router.require_pipeline_moderator(token=None, db=db))
        self.assertEqual(unauthenticated.exception.status_code, 401)

        user = SimpleNamespace(username="reader")
        db.query.return_value.filter.return_value.first.return_value = user
        with patch.object(
            story_pipeline_router, "decode_access_token", lambda _: {"sub": "reader"}
        ):
            with patch.dict(os.environ, {"NARRAI_MODERATOR_USERNAMES": "moderator"}):
                with self.assertRaises(HTTPException) as forbidden:
                    asyncio.run(
                        story_pipeline_router.require_pipeline_moderator(
                            token="valid", db=db
                        )
                    )
                self.assertEqual(forbidden.exception.status_code, 403)

            with patch.dict(
                os.environ, {"NARRAI_MODERATOR_USERNAMES": " READER, other "}
            ):
                authorized = asyncio.run(
                    story_pipeline_router.require_pipeline_moderator(
                        token="valid", db=db
                    )
                )
        self.assertIs(authorized, user)
