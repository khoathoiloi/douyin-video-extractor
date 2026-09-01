import os
import uuid
import json
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

from ..core.models import Video, VideoAnalysis, SearchQuery, SearchResult, Job
from ..core.config import settings
from ..pipeline.video_processor import VideoProcessor
from ..pipeline.asr_service import ASRService
from ..pipeline.ocr_service import OCRService
from ..pipeline.multimodal_analyzer import MultimodalAnalyzer
from ..pipeline.query_generator import QueryGenerator
from ..pipeline.ranking_engine import RankingEngine
from ..pipeline.reranker import LLMReranker
from ..pipeline.deduplicator import Deduplicator
from ..providers.factory import get_search_provider

class PipelineJobRunner:
    @staticmethod
    def update_job(db: Session, job_id: str, stage: str, status: str, progress: int, error: str = None):
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.stage = stage
            job.status = status
            job.progress_percent = progress
            if error:
                job.error_message = error
            db.commit()

    @classmethod
    async def run_full_pipeline(cls, video_id: str, job_id: str, db: Session, user_hint: str = ""):
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            cls.update_job(db, job_id, "failed", "failed", 0, "Video record not found")
            return

        try:
            # Stage 1: Processing Video (15%)
            cls.update_job(db, job_id, "processing", "in_progress", 15)
            video_dir = os.path.dirname(video.file_path)
            frames_dir = os.path.join(video_dir, f"frames_{video.id}")
            audio_path = os.path.join(video_dir, f"audio_{video.id}.mp3")

            meta = VideoProcessor.get_video_metadata(video.file_path)
            video.duration = meta.get("duration", 0)
            video.width = meta.get("width", 0)
            video.height = meta.get("height", 0)
            db.commit()

            frame_paths = VideoProcessor.extract_frames(video.file_path, frames_dir, num_frames=5)
            extracted_audio = VideoProcessor.extract_audio(video.file_path, audio_path)

            # Stage 2: Analyzing (40%)
            cls.update_job(db, job_id, "analyzing", "in_progress", 40)
            asr_res = ASRService.transcribe(extracted_audio, api_key=settings.GEMINI_API_KEY)
            ocr_texts = OCRService.extract_ocr_from_frames(frame_paths, api_key=settings.GEMINI_API_KEY)

            profile = MultimodalAnalyzer.analyze(
                frame_paths=frame_paths,
                transcript_data=asr_res,
                ocr_texts=ocr_texts,
                api_key=settings.GEMINI_API_KEY,
                provider=settings.AI_PROVIDER,
                user_hint=user_hint
            )

            # Save Analysis Profile
            analysis = db.query(VideoAnalysis).filter(VideoAnalysis.video_id == video.id).first()
            if not analysis:
                analysis = VideoAnalysis(id=str(uuid.uuid4()), video_id=video.id)
                db.add(analysis)

            analysis.summary = profile.get("summary", "")
            analysis.main_topic = profile.get("main_topic", "")
            analysis.secondary_topics = json.dumps(profile.get("secondary_topics", []), ensure_ascii=False)
            analysis.people = json.dumps(profile.get("people", []), ensure_ascii=False)
            analysis.objects = json.dumps(profile.get("objects", []), ensure_ascii=False)
            analysis.actions = json.dumps(profile.get("actions", []), ensure_ascii=False)
            analysis.locations = json.dumps(profile.get("locations", []), ensure_ascii=False)
            analysis.products = json.dumps(profile.get("products", []), ensure_ascii=False)
            analysis.brands = json.dumps(profile.get("brands", []), ensure_ascii=False)
            analysis.spoken_language = profile.get("spoken_language", "vi")
            analysis.transcript = profile.get("transcript", "")
            analysis.ocr_text = json.dumps(profile.get("ocr_text", []), ensure_ascii=False)
            analysis.visual_style = json.dumps(profile.get("visual_style", []), ensure_ascii=False)
            analysis.camera_style = json.dumps(profile.get("camera_style", []), ensure_ascii=False)
            analysis.content_format = profile.get("content_format", "")
            analysis.emotional_tone = json.dumps(profile.get("emotional_tone", []), ensure_ascii=False)
            analysis.narrative_structure = profile.get("narrative_structure", "")
            analysis.key_moments = json.dumps(profile.get("key_moments", []), ensure_ascii=False)
            analysis.search_concepts = json.dumps(profile.get("search_concepts", []), ensure_ascii=False)
            db.commit()

            # Stage 3: Generating Queries (60%)
            cls.update_job(db, job_id, "generating_queries", "in_progress", 60)
            raw_queries = QueryGenerator.generate_20_queries(profile, api_key=settings.GEMINI_API_KEY)
            
            # Clear old queries
            db.query(SearchQuery).filter(SearchQuery.video_id == video.id).delete()
            
            query_objects = []
            for q in raw_queries:
                variants = QueryGenerator.expand_query(q["query"])
                sq = SearchQuery(
                    id=str(uuid.uuid4()),
                    video_id=video.id,
                    query=q["query"],
                    category=q.get("category", "core_topic"),
                    reason=q.get("reason", ""),
                    score=float(q.get("score", 0.9)),
                    is_enabled=True,
                    is_custom=False,
                    expanded_variants=json.dumps(variants, ensure_ascii=False)
                )
                db.add(sq)
                query_objects.append(sq)
            db.commit()

            # Stage 4: Searching Douyin (75%)
            cls.update_job(db, job_id, "searching", "in_progress", 75)
            provider = get_search_provider()
            raw_candidates = []

            # Search top 5 enabled queries
            active_queries = [q for q in query_objects if q.is_enabled][:5]
            for sq in active_queries:
                cand_list = await provider.search(sq.query, limit=10)
                for c in cand_list:
                    raw_candidates.append({
                        "video_id": video.id,
                        "query_id": sq.id,
                        "platform": c.platform,
                        "remote_video_id": c.video_id,
                        "url": c.url,
                        "author": c.author,
                        "title": c.title,
                        "description": c.description,
                        "hashtags": c.hashtags,
                        "cover_url": c.cover_url,
                        "publish_time": c.publish_time,
                        "like_count": c.like_count,
                        "comment_count": c.comment_count,
                        "share_count": c.share_count,
                        "search_query": sq.query
                    })

            # Stage 5: Ranking & Deduplication (90%)
            cls.update_job(db, job_id, "ranking", "in_progress", 90)
            
            # Score each candidate
            for cand in raw_candidates:
                scores = RankingEngine.calculate_scores(profile, cand)
                cand["relevance_score"] = scores["semantic_similarity"]
                cand["final_score"] = scores["final_score"]

            # Deduplicate
            unique_candidates = Deduplicator.deduplicate(raw_candidates)

            # LLM Reranking on Top 30
            reranked = LLMReranker.rerank_candidates(profile, unique_candidates, top_n=30, api_key=settings.GEMINI_API_KEY)

            # Save Results
            db.query(SearchResult).filter(SearchResult.video_id == video.id).delete()
            for r in reranked:
                sr = SearchResult(
                    id=str(uuid.uuid4()),
                    video_id=video.id,
                    query_id=r.get("query_id", ""),
                    platform=r.get("platform", "douyin"),
                    remote_video_id=r.get("remote_video_id", ""),
                    url=r.get("url", ""),
                    author=r.get("author", ""),
                    title=r.get("title", ""),
                    description=r.get("description", ""),
                    hashtags=json.dumps(r.get("hashtags", []), ensure_ascii=False),
                    cover_url=r.get("cover_url", ""),
                    publish_time=r.get("publish_time", ""),
                    like_count=r.get("like_count", 0),
                    comment_count=r.get("comment_count", 0),
                    share_count=r.get("share_count", 0),
                    search_query=r.get("search_query", ""),
                    relevance_score=r.get("relevance_score", 0.0),
                    final_score=r.get("final_score", 0.0)
                )
                db.add(sr)
            db.commit()

            # Clean temporary frame files
            try:
                for f in os.listdir(frames_dir):
                    os.remove(os.path.join(frames_dir, f))
                os.rmdir(frames_dir)
            except Exception:
                pass

            # Stage 6: Completed (100%)
            cls.update_job(db, job_id, "completed", "completed", 100)

        except Exception as e:
            print(f"[PipelineJobRunner] Error: {e}")
            cls.update_job(db, job_id, "failed", "failed", 0, str(e))
