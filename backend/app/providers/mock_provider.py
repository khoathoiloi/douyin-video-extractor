import hashlib
import time
from typing import List, Optional
from datetime import datetime
from .base import DouyinSearchProvider, NormalizedSearchResult

class MockDouyinSearchProvider(DouyinSearchProvider):
    async def search(self, query: str, limit: int = 20) -> List[NormalizedSearchResult]:
        results = []
        creators = ["舞蹈小甜心", "卡点达人阿强", "流行趋势榜", "爆款创作社", "心动女生", "美食大赏", "时尚穿搭志", "萌宠星球"]
        title_templates = [
            "全网超火爆款推荐 #{query} #热点",
            "点赞破百万神仙名场面 #{query} #精选",
            "沉浸式体验与高光瞬间 #{query} #热门",
            "这才是真正的天花板级别 #{query} #推荐",
            "看一遍就停不下来的精彩合集 #{query} #合集",
            "最新流行趋势全网都在看 #{query} #爆款",
            "今日份高赞精选内容 #{query} #分享",
            "视觉震撼名场面合辑 #{query} #大片",
            "全网超高人气必看系列 #{query} #热搜",
            "高质量创作合集回顾 #{query} #精选",
            "超惊艳镜头语言与细节展示 #{query} #原创",
            "全网都在学的神仙教程 #{query} #教程"
        ]
        q_hash = hashlib.md5(query.encode("utf-8")).hexdigest()[:6]
        
        for i in range(limit):
            sub_hash = hashlib.md5(f"{query}_{i}".encode("utf-8")).hexdigest()[:8]
            aweme_id = f"7268{q_hash}{sub_hash}"[:19]
            author_idx = (i + int(q_hash, 16)) % len(creators)
            tpl = title_templates[i % len(title_templates)]
            title_text = f"【{query} #{i+1}】{tpl.replace('{query}', query)}"

            results.append(NormalizedSearchResult(
                platform="douyin",
                video_id=aweme_id,
                url=f"https://www.douyin.com/video/{aweme_id}",
                author=creators[author_idx],
                title=title_text,
                description=f"精选高赞推荐，一定要看到最后 #{query}",
                hashtags=[f"#{query}", "#热门", "#爆款"],
                cover_url=f"https://p3-pc.douyinpic.com/origin/tos-cn-p-0015/{aweme_id}.jpeg",
                publish_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
                like_count=(i + 1) * 28500 + 12000,
                comment_count=(i + 1) * 1200 + 450,
                share_count=(i + 1) * 850 + 200,
                search_query=query
            ))
        return results

    async def get_video(self, url: str) -> Optional[NormalizedSearchResult]:
        aweme_id = "7268899827364121914"
        return NormalizedSearchResult(
            platform="douyin",
            video_id=aweme_id,
            url=f"https://www.douyin.com/video/{aweme_id}",
            author="Mock Creator",
            title="Mock Douyin Video Title",
            description="Mock video description",
            hashtags=["#mock"],
            cover_url="",
            publish_time=datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            like_count=100000,
            search_query="mock"
        )
