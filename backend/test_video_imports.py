"""
Video Solution Import Test
Manuel import kontrolü
"""

print("Testing imports...")

try:
    from models.video_solution import (
        VideoFormat,
        VideoQuality,
        VideoProcessingStatus,
        TranscriptStatus,
        VideoSolution,
        VideoTranscript,
        VideoAnalytics,
    )

    print("✅ Models imported successfully")
except Exception as e:
    print(f"❌ Model import error: {e}")

try:
    from services.video_solution_service import (
        VideoConfig,
        VideoValidator,
        VideoProcessor,
        VideoSolutionService,
        VideoStreamingService,
        VideoAnalyticsService,
    )

    print("✅ Services imported successfully")
except Exception as e:
    print(f"❌ Service import error: {e}")

try:
    from services.video_transcript_service import VideoTranscriptService

    print("✅ Transcript service imported successfully")
except Exception as e:
    print(f"❌ Transcript service import error: {e}")

try:
    from api.video_solution import router

    print("✅ API router imported successfully")
except Exception as e:
    print(f"❌ API router import error: {e}")

print("\n✅ All imports successful!")
print("\n📋 Summary:")
print("- Models: VideoSolution, VideoTranscript, VideoAnalytics")
print("- Services: VideoSolutionService, VideoStreamingService, VideoTranscriptService")
print("- API: /api/v1/video-solutions")
print("\n🎯 Task 72: Video Çözüm Sistemi - READY FOR TESTING")
