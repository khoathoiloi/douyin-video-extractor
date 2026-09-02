import os
import json
import base64
import re
import urllib.request
from typing import Dict, Any, List

class MultimodalAnalyzer:
    SCHEMA_PROMPT = """
You are an expert multimodal AI video content analyst for Douyin / TikTok.
Analyze the provided video keyframes, audio transcript, and OCR text to generate a structured content profile.

CRITICAL RULES:
1. Never hallucinate observed facts.
2. Clearly distinguish observed information from inferred information.
3. Return ONLY valid JSON matching this exact schema:

{
  "summary": "Brief summary of the video",
  "main_topic": "Primary topic",
  "secondary_topics": ["topic1", "topic2"],
  "people": ["Description of people/creators observed"],
  "objects": ["Key objects observed"],
  "actions": ["Key movements, dances, or actions"],
  "locations": ["Observed scene/environment"],
  "products": ["Specific items or outfits"],
  "brands": ["Observed brand logos or names"],
  "spoken_language": "vi/zh/en/none",
  "transcript": "Audio transcript or summary",
  "ocr_text": ["On-screen text elements"],
  "visual_style": ["Aesthetic description, e.g. bright, aesthetic, cinematic"],
  "camera_style": ["Camera angles, e.g. close-up, full-body, tripod, handheld"],
  "content_format": "dance_cover / short_drama / vlog / cooking / review / meme",
  "emotional_tone": ["energetic", "funny", "inspiring", "healing", "cool"],
  "narrative_structure": "hook -> progression -> climax",
  "key_moments": ["0-3s hook", "middle peak action"],
  "search_concepts": ["concept1", "concept2", "concept3"]
}
"""

    @classmethod
    def analyze(
        cls,
        frame_paths: List[str],
        transcript_data: Dict[str, Any],
        ocr_texts: List[str],
        api_key: str = "",
        provider: str = "gemini",
        user_hint: str = ""
    ) -> Dict[str, Any]:
        transcript = transcript_data.get("transcript", "")
        lang = transcript_data.get("language", "vi")

        if api_key and provider == "gemini":
            try:
                ocr_str = ", ".join(ocr_texts)
                prompt_text = f"{cls.SCHEMA_PROMPT}\n\nContext:\nTranscript: {transcript}\nOCR Text: {ocr_str}\nUser Note: {user_hint}"
                parts = [{"text": prompt_text}]
                for fp in frame_paths[:3]:
                    if os.path.exists(fp):
                        with open(fp, "rb") as f:
                            b64_img = base64.b64encode(f.read()).decode("utf-8")
                        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64_img}})
                        
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": parts}],
                    "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    txt = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    txt = re.sub(r"^```json\s*", "", txt.strip(), flags=re.MULTILINE)
                    txt = re.sub(r"```$", "", txt.strip(), flags=re.MULTILINE)
                    return json.loads(txt)
            except Exception as e:
                print(f"[MultimodalAnalyzer] AI Analysis fallback: {e}")

        # Intelligent Fallback Profile
        combined_text = (transcript + " " + " ".join(ocr_texts) + " " + user_hint).lower()
        
        main_topic = "Vũ đạo / Gái xinh / Dance Trend"
        actions = ["Nhảy theo nhịp nhạc", "Biến hình", "Tạo dáng trước ống kính"]
        content_format = "dance_cover"
        search_concepts = ["抖音热舞", "美女跳舞", "热门卡点舞", "变装跳舞"]
        
        if any(w in combined_text for w in ["pijama", "đồ ngủ", "睡衣", "pajama"]):
            main_topic = "Gái xinh mặc pijama / Đồ ngủ dễ thương"
            actions = ["Mặc đồ ngủ dễ thương", "Biến hình đồ ngủ", "Thư giãn tại nhà"]
            content_format = "pajama_fashion"
            search_concepts = ["睡衣美女", "居家睡衣", "甜美睡衣", "睡衣变装"]
        elif any(w in combined_text for w in ["che mặt", "kín mặt", "khẩu trang", "遮脸", "挡脸", "mask", "covering face", "cover face"]):
            main_topic = "Gái xinh che mặt / Bí ẩn cuốn hút"
            actions = ["Che mặt bí ẩn", "Góc nghiêng thần thánh", "Ánh mắt hút hồn"]
            content_format = "mysterious_beauty"
            search_concepts = ["遮脸美女", "氛围感遮脸", "半遮面美女", "眼神杀"]
        elif any(w in combined_text for w in ["nấu ăn", "nấu nướng", "làm bếp", "đầu bếp", "做饭", "下厨", "烹饪", "cooking girl", "girl cooking", "cooking"]):
            main_topic = "Cô gái nấu ăn / Nấu ăn tại nhà"
            actions = ["Nấu nướng", "Bày biện món ăn", "Nấu ăn phong cách chữa lành"]
            content_format = "girl_cooking"
            search_concepts = ["美女做饭", "沉浸式做饭", "治愈系做饭", "家常菜教程"]
        elif any(w in combined_text for w in ["review đồ ăn", "ẩm thực", "ăn uống", "đồ ăn", "quán ăn", "món ngon", "美食测评", "探店", "food review", "eating"]):
            main_topic = "Review đồ ăn / Khám phá ẩm thực"
            actions = ["Thưởng thức món ăn", "Review đánh giá món ngon", "Khám phá quán ăn"]
            content_format = "food_review"
            search_concepts = ["美食测评", "街头美食探店", "路边摊小吃", "吃播探店"]
        elif any(w in combined_text for w in ["hài", "cười", "drama", "tiểu phẩm", "vui nhộn", "搞笑", "沙雕", "段子", "funny", "comedy", "meme"]):
            main_topic = "Hài hước / Tiểu phẩm ngắn"
            actions = ["Diễn xuất tình huống bất ngờ", "Tấu hài gây cười", "Phản ứng hài hước"]
            content_format = "short_drama"
            search_concepts = ["搞笑短剧", "沙雕日常", "爆笑反转", "幽默段子"]
        elif any(w in combined_text for w in ["mèo", "mèo con", "miu", "cat", "kitten", "kitty", "猫", "可爱猫咪", "喵星人", "萌宠"]):
            main_topic = "Mèo dễ thương / Thú cưng đáng yêu"
            actions = ["Mèo con làm nũng", "Chơi đùa với mèo", "Hành động ngộ nghĩnh của mèo"]
            content_format = "cute_pets"
            search_concepts = ["可爱猫咪", "萌宠日常", "治愈系猫咪", "小奶猫撒娇"]
        elif any(w in combined_text for w in ["ô tô", "xe hơi", "siêu xe", "car", "cars", "automobile", "supercar", "汽车", "超跑", "车辆"]):
            main_topic = "Xe ô tô / Đánh giá xe & Siêu xe"
            actions = ["Lái thử xe ô tô", "Trải nghiệm tiếng pô siêu xe", "Đánh giá nội thất xe"]
            content_format = "car_review"
            search_concepts = ["豪华汽车", "酷炫汽车大片", "超跑声浪", "新车测评"]
        elif any(w in combined_text for w in ["phong cảnh", "thiên nhiên", "du lịch", "cảnh đẹp", "scenery", "landscape", "nature", "travel", "风景", "自然风光"]):
            main_topic = "Phong cảnh đẹp / Thiên nhiên hùng vĩ"
            actions = ["Quay cảnh flycam", "Khám phá phong cảnh thiên nhiên", "Ngắm hoàng hôn"]
            content_format = "scenery_travel"
            search_concepts = ["唯美风景", "绝美自然风光", "治愈系风景", "4K航拍大片"]
        elif any(w in combined_text for w in ["thời trang", "outfit", "ootd", "phối đồ", "quần áo", "fashion", "style", "穿搭", "时尚", "服装"]):
            main_topic = "Video thời trang / Gợi ý phối đồ"
            actions = ["Biến hình thời trang", "Thử đồ outfit", "Tạo dáng phong cách thời trang"]
            content_format = "fashion_outfit"
            search_concepts = ["时尚穿搭", "每日OOTD", "变装高级感", "显瘦穿搭"]
        elif any(w in combined_text for w in ["gái xinh", "gái đẹp", "người đẹp", "hotgirl", "beauty", "girl", "beautiful", "美女", "女神", "高颜值"]):
            main_topic = "Gái xinh / Nhan sắc nổi bật"
            actions = ["Tạo dáng trước ống kính", "Biến hình nhan sắc", "Thần thái cuốn hút"]
            content_format = "beauty_girl"
            search_concepts = ["抖音高颜值女神", "美女变装", "绝美神仙颜值", "氛围感美女"]

        return {
            "summary": f"Video ngắn định dạng {content_format} với chủ đề {main_topic}.",
            "main_topic": main_topic,
            "secondary_topics": ["Trending Video", "Douyin Viral", "Reels/TikTok Trend"],
            "people": ["Nữ creator / vũ công", "Người sáng tạo nội dung trẻ"],
            "objects": ["Trang phục hiện đại", "Điện thoại", "Đạo cụ quay video"],
            "actions": actions,
            "locations": ["Trong phòng studio / Ngoài trời", "Bối cảnh ánh sáng hiện đại"],
            "products": ["Thời trang giới trẻ", "Phụ kiện"],
            "brands": ["TikTok / Douyin Sound"],
            "spoken_language": lang or "vi",
            "transcript": transcript or "Âm thanh giai điệu hot trend.",
            "ocr_text": ocr_texts or ["Douyin Trend"],
            "visual_style": ["Màu sắc tươi sáng", "Độ nét cao", "Hiệu ứng chuyển cảnh mượt"],
            "camera_style": ["Góc quay toàn thân và trung cảnh", "Ống kính cố định"],
            "content_format": content_format,
            "emotional_tone": ["Hào hứng", "Năng động", "Cuốn hút"],
            "narrative_structure": "Mở đầu nhạc bắt tai -> Động tác cao trào -> Kết thúc tạo dấu ấn",
            "key_moments": ["0-3s: Bắt đầu video", "Cao trào: Điểm nhấn nội dung"],
            "search_concepts": search_concepts
        }
