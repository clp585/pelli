#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Contract Smoke Test

Tests the /api/video endpoint contract:
- POST /api/video with minimal PNG
- Read SSE stream until complete/error
- Assert: data.video starts with /output/
- Assert: data.artifact_type exists
- Assert: data.cost_usd exists

Fast and deterministic (no external dependencies beyond Flask).
"""

import io
import json
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app


def test_video_contract():
    """Test /api/video endpoint contract: video URL format, artifact_type, and cost_usd"""
    with app.test_client() as client:
        # Create a tiny in-memory PNG image (1x1 pixel)
        # Minimal valid PNG: 89 50 4E 47 0D 0A 1A 0A + IHDR + IEND
        png_data = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
            b'\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00'
            b'\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        # POST to /api/video
        response = client.post(
            "/api/video",
            data={
                "shot_preset": "cinematic_orbit",
                "duration_s": "5",
                "fps": "24",
                "aspect": "16:9",
                "image": (io.BytesIO(png_data), "test.png")
            },
            content_type="multipart/form-data"
        )
        
        if response.status_code != 200:
            print(f"FAIL: POST /api/video returned HTTP {response.status_code}, expected 200")
            return False
        
        try:
            data = json.loads(response.data)
        except json.JSONDecodeError:
            print(f"FAIL: POST /api/video returned invalid JSON: {response.data[:100]}")
            return False
        
        if data.get("status") != "started" or "job_id" not in data:
            print(f"FAIL: POST /api/video returned unexpected response: {data}")
            return False
        
        job_id = data["job_id"]
        
        # Read SSE events from /api/stream/<job_id>
        stream_response = client.get(f"/api/stream/{job_id}")
        if stream_response.status_code != 200:
            print(f"FAIL: GET /api/stream/{job_id} returned HTTP {stream_response.status_code}, expected 200")
            return False
        
        # Parse SSE events (with timeout)
        timeout = 15.0  # 15 seconds max
        start_time = time.time()
        complete_event = None
        error_event = None
        
        # Read SSE stream (test client buffers entire response)
        stream_data = stream_response.data.decode('utf-8')
        
        # Parse SSE format: "data: {json}\n\n" or ": keepalive\n\n"
        # Split by double newline to get events
        events = stream_data.split('\n\n')
        
        for event_block in events:
            if time.time() - start_time > timeout:
                print(f"FAIL: Timeout waiting for complete/error event after {timeout}s")
                return False
            
            event_block = event_block.strip()
            if not event_block:
                continue
            
            # Skip keepalive comments
            if event_block.startswith(':'):
                continue
            
            # Parse "data: {json}" format
            if event_block.startswith('data: '):
                try:
                    event_data = json.loads(event_block[6:])  # Remove "data: " prefix
                    event_type = event_data.get('type')
                    
                    if event_type == 'complete':
                        complete_event = event_data
                        break
                    elif event_type == 'error':
                        error_event = event_data
                        break
                except json.JSONDecodeError:
                    continue  # Skip invalid JSON lines
        
        if error_event:
            print(f"FAIL: Received error event: {error_event.get('message', 'Unknown error')}")
            return False
        
        if not complete_event:
            print("FAIL: No complete event received within timeout")
            return False
        
        # Assert contract: complete.data.video starts with /output/
        if 'data' not in complete_event:
            print("FAIL: complete event missing 'data' field")
            return False
        
        data = complete_event['data']
        if 'video' not in data:
            print("FAIL: complete.data missing 'video' field")
            return False
        
        video_url = data['video']
        if not video_url.startswith('/output/'):
            print(f"FAIL: complete.data.video does not start with /output/: {video_url}")
            return False
        
        # Assert contract: complete.data.artifact_type is present
        if 'artifact_type' not in data:
            print("FAIL: complete.data missing 'artifact_type' field")
            return False
        
        artifact_type = data['artifact_type']
        if artifact_type not in ['video', 'file']:
            print(f"FAIL: complete.data.artifact_type has unexpected value: {artifact_type}")
            return False
        
        # Assert contract: complete.data.cost_usd is present
        if 'cost_usd' not in data:
            print("FAIL: complete.data missing 'cost_usd' field")
            return False
        
        cost_usd = data['cost_usd']
        if not isinstance(cost_usd, (int, float)) or cost_usd < 0:
            print(f"FAIL: complete.data.cost_usd has invalid value: {cost_usd}")
            return False
        
        print(f"PASS: /api/video contract verified (video={video_url}, artifact_type={artifact_type}, cost_usd={cost_usd})")
        return True


def main():
    """Run the video contract test"""
    try:
        success = test_video_contract()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"FAIL: Test raised exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

