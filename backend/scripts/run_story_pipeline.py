#!/usr/bin/env python3
"""
NarrAI AI Story Pipeline Runner (GitHub Actions / Scheduled Automation Worker)
Usage:
    python run_story_pipeline.py [--limit 3] [--story-id <slug>]
"""

import sys
import os
import argparse
import asyncio
import json

# Add backend directory to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env"))

from services.story_pipeline_manager import StoryPipelineManager

async def main():
    parser = argparse.ArgumentParser(description="NarrAI AI Story Pipeline Runner")
    parser.add_argument("--limit", type=int, default=3, help="Maximum number of stories to process per run (default: 3)")
    parser.add_argument("--story-id", type=str, default=None, help="Process a specific story ID")
    args = parser.parse_args()

    print("================================================================")
    print("🚀 NÁRRAI AI STORY PIPELINE AUTOMATION WORKER")
    print("================================================================")

    manager = StoryPipelineManager()
    overview = manager.get_overview()

    print(f"📊 Trạng thái hàng đợi hiện tại:")
    print(f"   - Tổng số đề bài: {overview['totalStories']}")
    print(f"   - Chờ xử lý (pending): {overview['pending']}")
    print(f"   - Đang biên soạn: {overview['inProgress']}")
    print(f"   - Thất bại (failed): {overview['failed']}")
    print(f"   - PR đã tạo: {overview['prCreated']}")
    print(f"   - Đã merge: {overview['merged']}")
    print("----------------------------------------------------------------")

    if args.story_id:
        print(f"🎯 Xử lý riêng đề bài: '{args.story_id}'...")
        res = await manager.run_single_story(args.story_id)
        if res.get("success"):
            print(f"✅ Hoàn thành xuất sắc: '{res.get('title')}'")
            print(f"   - Trạng thái: {res.get('status')}")
            print(f"   - Số từ: {res.get('validation', {}).get('wordCount')} từ")
            print(f"   - PR URL: {res.get('pr', {}).get('prUrl')}")
            sys.exit(0)
        else:
            print(f"❌ Xử lý thất bại cho '{args.story_id}': {res.get('error') or res.get('errors')}")
            sys.exit(1)
    else:
        if overview["pending"] == 0:
            print("✨ Không có đề bài nào đang ở trạng thái 'pending'. Kết thúc phiên làm việc.")
            sys.exit(0)

        print(f"🔄 Bắt đầu chạy pipeline hàng loạt (Tối đa {args.limit} đề bài/tuần)...")
        batch_res = await manager.run_batch_pipeline(limit=args.limit)
        print(f"🎉 Hoàn thành xử lý {batch_res['processedCount']} đề bài.")
        for r in batch_res["results"]:
            status_icon = "✅" if r.get("success") else "❌"
            print(f"   {status_icon} [{r.get('storyId') or 'unknown'}] - Success: {r.get('success')}")

if __name__ == "__main__":
    asyncio.run(main())
