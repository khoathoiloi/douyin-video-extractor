import os
import json
import base64
import urllib.request
import re
from typing import Dict, Any, List

class MultiLayerVideoAnalyzer:
    SCHEMA_PROMPT = """
You are a top-tier Douyin/TikTok video analyst.
Analyze the video multi-dimensionally: Subjects, Appearance, Environment, Actions, Camera, Multi-Categories, and Chinese Keywords.

Return ONLY valid JSON matching this schema:
{
  "summary": "Brief natural description",
  "subjects": ["female / male / animal / car / food / product / etc."],
  "appearance": ["clothing style", "hair", "colors", "accessories"],
  "environment": ["bedroom / street / restaurant / studio / beach / etc."],
  "actions": ["dancing / changing clothes / walking / cooking / etc."],
  "camera": ["selfie / POV / cinematic / close-up / wide shot / handheld / tripod"],
  "categories": ["Fashion", "Beauty", "Comedy", "Dance", "Food", "Vlog", "Transformation"],
  "emotional_tone": ["energetic", "confident", "cheerful", "cool"],
  "keywords": {
    "primary": ["女生变装", "美女变装"],
    "action": ["变装", "换装", "转场", "卡点"],
    "scene": ["室内", "卧室", "镜子前"],
    "style": ["氛围感", "高级感", "时尚"],
    "trend": ["变装挑战", "热门", "爆款"]
  },
  "queries": {
    "exact": ["女生变装挑战", "美女变装转场"],
    "high_similarity": ["女生快速换装", "变装卡点舞"],
    "visual": ["女生镜子前变装", "室内美女变装"],
    "action": ["丝滑变装转场", "卡点变装视频"],
    "scene": ["卧室变装日常", "街头变装秀"],
    "trend": ["全网超火变装", "热门变装合集"],
    "broad": ["变装", "换装", "卡点舞"]
  }
}
"""

    @classmethod
    def analyze(
        cls,
        keyframe_items: List[Dict[str, Any]],
        ocr_items: List[Dict[str, Any]],
        asr_data: Dict[str, Any],
        metadata: Dict[str, Any],
        user_hint: str = "",
        api_key: str = ""
    ) -> Dict[str, Any]:
        transcript = asr_data.get("transcript", "")
        ocr_texts = [o.get("text", "") for o in ocr_items if isinstance(o, dict)]

        if api_key:
            try:
                context_str = f"Transcript: {transcript}\nOCR Text: {', '.join(ocr_texts)}\nUser Note: {user_hint}\nDuration: {metadata.get('duration')}s"
                parts = [{"text": cls.SCHEMA_PROMPT + f"\n\nContext:\n{context_str}"}]
                for item in keyframe_items[:3]:
                    fp = item.get("path")
                    if fp and os.path.exists(fp):
                        with open(fp, "rb") as f:
                            b64_img = base64.b64encode(f.read()).decode("utf-8")
                        parts.append({"inline_data": {"mime_type": "image/jpeg", "data": b64_img}})

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": parts}],
                    "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=18) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    txt = res["candidates"][0]["content"]["parts"][0]["text"]
                    txt = re.sub(r"^```json\s*", "", txt.strip(), flags=re.MULTILINE)
                    txt = re.sub(r"```$", "", txt.strip(), flags=re.MULTILINE)
                    return json.loads(txt)
            except Exception as e:
                print(f"[MultiLayerAnalyzer] API Fallback: {e}")

        # Intelligent Fallback Engine
        combined = (transcript + " " + " ".join(ocr_texts) + " " + user_hint).lower()

        if any(w in combined for w in ["pijama", "đồ ngủ", "睡衣", "pajama"]):
            return {
                "summary": "Video gái xinh mặc đồ ngủ pijama biến hình và sinh hoạt tại nhà.",
                "subjects": ["female", "creator", "model"],
                "appearance": ["đồ ngủ pijama lụa", "phong cách ngọt ngào", "mặt mộc xinh xắn"],
                "environment": ["bedroom", "living room", "home"],
                "actions": ["changing clothes", "posing", "stretching", "smiling"],
                "camera": ["close-up", "POV", "mirror selfie"],
                "categories": ["Fashion", "Beauty", "Lifestyle"],
                "emotional_tone": ["healing", "sweet", "cozy"],
                "keywords": {
                    "primary": ["居家睡衣美女", "丝绸睡衣变装", "甜美睡衣日常"],
                    "action": ["睡衣伸懒腰", "睡衣卡点换装", "慵懒起床日常"],
                    "scene": ["温暖卧室床头", "晨光洒进房间", "居家温馨客厅"],
                    "style": ["甜美纯欲", "慵懒氛围感", "自然清新"],
                    "trend": ["睡衣变装天花板", "居家慵懒写真", "睡衣挑战"]
                },
                "queries": {
                    "exact": ["居家睡衣美女", "丝绸睡衣变装", "甜美睡衣日常"],
                    "high_similarity": ["睡衣小姐姐", "居家小甜心", "纯欲睡衣风"],
                    "visual": ["温暖卧室睡衣写真", "晨光睡衣自拍", "镜子前睡衣变装"],
                    "action": ["睡衣卡点换装", "睡衣伸懒腰", "抱枕甜美互动"],
                    "scene": ["卧室温馨日常", "居家生活记录"],
                    "trend": ["穿睡衣也能这么惊艳", "居家慵懒氛围感天花板"],
                    "broad": ["睡衣", "居家穿搭", "睡衣美女", "变装"]
                }
            }
        elif any(w in combined for w in ["che mặt", "kín mặt", "khẩu trang", "遮脸", "挡脸", "mask", "covering face", "cover face"]):
            return {
                "summary": "Video gái xinh che mặt tạo điểm nhấn thần thái và ánh mắt cuốn hút.",
                "subjects": ["female", "mysterious creator", "model"],
                "appearance": ["khẩu trang", "tay che mặt", "mắt đẹp", "phong cách bí ẩn"],
                "environment": ["street", "studio", "neon room", "car"],
                "actions": ["covering face", "eye contact", "posing", "revealing"],
                "camera": ["close-up", "eye focus", "slow motion"],
                "categories": ["Beauty", "Fashion", "Vlog"],
                "emotional_tone": ["mysterious", "cool", "attractive"],
                "keywords": {
                    "primary": ["遮脸神秘氛围感", "半遮面绝美神颜", "手机挡脸拍照"],
                    "action": ["手机半挡脸", "纤手轻掩面颊", "眼神杀放电"],
                    "scene": ["昏暗氛围感室内", "逆光街头剪影", "镜子前自拍角"],
                    "style": ["暗黑氛围感", "高级高级感", "眼神杀"],
                    "trend": ["遮脸变装", "露眼杀", "神秘感美女"]
                },
                "queries": {
                    "exact": ["遮脸神秘氛围感", "半遮面绝美神颜"],
                    "high_similarity": ["遮脸气质女神", "露眼杀小姐姐", "神秘感女生"],
                    "visual": ["昏暗室内眼神特写", "逆光街头遮脸剪影"],
                    "action": ["手机半挡脸拍照", "眼神杀放电瞬间", "慢镜头遮脸转场"],
                    "scene": ["镜前遮脸自拍", "街头氛围感抓拍"],
                    "trend": ["仅凭一双眼睛惊艳全网", "氛围感拉满的遮脸瞬间"],
                    "broad": ["遮脸", "半遮面", "眼神杀", "氛围感美女"]
                }
            }
        elif any(w in combined for w in ["cô gái nấu ăn", "girl cooking", "cooking girl", "bếp", "nấu ăn", "做饭", "下厨"]):
            return {
                "summary": "Video cô gái xinh đẹp nấu ăn và hướng dẫn làm món ngon tại nhà.",
                "subjects": ["female", "chef", "food creator"],
                "appearance": ["tạp dề xinh xắn", "trang phục làm bếp gọn gàng"],
                "environment": ["kitchen", "dining room", "home yard"],
                "actions": ["cooking", "chopping", "stir-frying", "tasting", "smiling"],
                "camera": ["close-up", "top-down", "POV", "tripod"],
                "categories": ["Food", "Cooking", "Lifestyle"],
                "emotional_tone": ["healing", "mouth-watering", "warm"],
                "keywords": {
                    "primary": ["美女下厨做饭", "治愈系沉浸式做饭", "独居女孩一人食"],
                    "action": ["熟练切菜备料", "大火翻炒颠勺", "秘制酱汁调配"],
                    "scene": ["暖光温馨厨房", "烟火气小院", "整洁料理台"],
                    "style": ["治愈系", "高清ASMR", "烟火气"],
                    "trend": ["仙女的厨房日常", "既有颜值做饭又好吃", "一人食Vlog"]
                },
                "queries": {
                    "exact": ["美女下厨做饭", "治愈系沉浸式做饭", "独居女孩一人食"],
                    "high_similarity": ["温柔做饭博主", "厨房美厨娘", "精致料理女孩"],
                    "visual": ["沉浸式厨房做饭", "暖光温馨做饭日常"],
                    "action": ["熟练切菜备料", "大火翻炒颠勺", "尝一口满足微笑"],
                    "scene": ["温馨厨房做饭日常", "庭院柴火饭"],
                    "trend": ["既有颜值做饭又好吃", "下班后的治愈一人食"],
                    "broad": ["做饭", "美女做饭", "家常菜", "一人食"]
                }
            }
        elif any(w in combined for w in ["mèo", "cat", "kitty", "kitten", "猫", "萌宠"]):
            return {
                "summary": "Video những khoảnh khắc đáng yêu, hài hước và ngộ nghĩnh của mèo cưng.",
                "subjects": ["cat", "kitten", "pet creator"],
                "appearance": ["lông mềm mượt", "mắt tròn xoe", "tai vểnh đáng yêu"],
                "environment": ["living room", "cat bed", "window sill"],
                "actions": ["kneading", "head tilt", "playing", "purring", "sleeping"],
                "camera": ["macro close-up", "low angle", "POV"],
                "categories": ["Pets", "Animals", "Lifestyle"],
                "emotional_tone": ["healing", "cute", "adorable"],
                "keywords": {
                    "primary": ["治愈系可爱猫咪", "萌宠猫咪日常", "软萌幼猫撒娇"],
                    "action": ["踩奶呼噜噜", "歪头杀萌化人心", "翻肚皮求摸摸"],
                    "scene": ["温暖猫窝", "阳光窗台", "客厅地毯"],
                    "style": ["治愈系", "超萌慢动作", "温馨日常"],
                    "trend": ["成精的小猫咪", "猫咪迷惑行为", "云吸猫"]
                },
                "queries": {
                    "exact": ["治愈系可爱猫咪", "萌宠猫咪日常", "软萌幼猫撒娇"],
                    "high_similarity": ["软萌小奶猫", "胖嘟嘟英短", "粘人小猫咪"],
                    "visual": ["阳光窗台猫咪特写", "慢动作小猫踩奶"],
                    "action": ["踩奶呼噜噜", "歪头杀萌化人心", "翻肚皮求摸摸"],
                    "scene": ["室内猫窝日常", "地毯玩耍瞬间"],
                    "trend": ["谁能拒绝一只粘人的小猫咪", "看完直接被可爱化了"],
                    "broad": ["猫咪", "可爱猫咪", "萌宠", "吸猫"]
                }
            }
        elif any(w in combined for w in ["ô tô", "xe hơi", "siêu xe", "car", "supercar", "汽车", "超跑"]):
            return {
                "summary": "Video trải nghiệm, đánh giá xe ô tô, siêu xe sang trọng và âm thanh pô.",
                "subjects": ["car", "supercar", "driver", "reviewer"],
                "appearance": ["nội thất sang trọng", "nước sơn bóng bẩy", "mâm xe thể thao"],
                "environment": ["racetrack", "garage", "highway", "mountain road"],
                "actions": ["accelerating", "drifting", "exhaust revving", "driving"],
                "camera": ["tracking shot", "drone", "in-car POV", "cinematic"],
                "categories": ["Automotive", "Supercars", "Technology"],
                "emotional_tone": ["thrilling", "exciting", "premium"],
                "keywords": {
                    "primary": ["豪华超跑声浪", "酷炫汽车大片", "沉浸式新车测评"],
                    "action": ["轰油门炸街声浪", "弹射起步加速", "丝滑漂移过弯"],
                    "scene": ["赛道狂飙现场", "深夜地下车库", "沿海公路自驾"],
                    "style": ["电影质感", "超跑声浪ASMR", "速度与激情"],
                    "trend": ["男人的终极梦想座驾", "汽车大片", "声浪测评"]
                },
                "queries": {
                    "exact": ["豪华超跑声浪", "酷炫汽车大片", "沉浸式新车测评"],
                    "high_similarity": ["顶级超跑车主", "资深汽车测评人", "赛道性能车"],
                    "visual": ["深夜地库汽车大片", "公路飞驰电影运镜"],
                    "action": ["轰油门炸街声浪", "弹射起步加速", "丝滑漂移过弯"],
                    "scene": ["专业赛道现场", "深夜地下车库"],
                    "trend": ["男人的终极梦想座驾", "感受顶级超跑的推背感"],
                    "broad": ["汽车", "超跑", "赛车", "新车测评"]
                }
            }
        elif any(w in combined for w in ["phong cảnh", "scenery", "landscape", "thiên nhiên", "风景", "自然"]):
            return {
                "summary": "Video phong cảnh thiên nhiên tuyệt đẹp với góc quay 4K và flycam.",
                "subjects": ["landscape", "nature", "mountains", "ocean", "sky"],
                "appearance": ["màu sắc tự nhiên rực rỡ", "ánh sáng bình minh/hoàng hôn"],
                "environment": ["mountain", "sea", "forest", "lake", "waterfall"],
                "actions": ["flowing", "time lapse", "drone flying", "sunset glowing"],
                "camera": ["drone 4K", "wide landscape", "time-lapse"],
                "categories": ["Travel", "Nature", "Scenery"],
                "emotional_tone": ["healing", "peaceful", "magnificent"],
                "keywords": {
                    "primary": ["绝美大自然风光", "治愈系唯美风景", "4K超高清自然大片"],
                    "action": ["日出云海翻涌", "暮色晚霞漫天", "航拍俯瞰大地"],
                    "scene": ["雪山之巅", "蔚蓝海岸线", "宁静森林湖泊"],
                    "style": ["4K超高清", "壁纸级风光", "治愈系白噪音"],
                    "trend": ["走遍中国绝美山河", "治愈大自然", "延时风景"]
                },
                "queries": {
                    "exact": ["绝美大自然风光", "治愈系唯美风景", "4K超高清自然大片"],
                    "high_similarity": ["航拍风光摄影", "大自然壮丽奇观", "走遍中国绝美山河"],
                    "visual": ["4K航拍视觉盛宴", "雪山云海日出延时"],
                    "action": ["日出云海翻涌", "暮色晚霞漫天", "溪流瀑布潺潺"],
                    "scene": ["雪山之巅风光", "蔚蓝海岸线景观"],
                    "trend": ["治愈一切不开心的大自然", "随手一截就是壁纸的风光"],
                    "broad": ["风景", "大自然", "旅行", "航拍大片"]
                }
            }
        elif any(w in combined for w in ["thời trang", "fashion", "ootd", "outfit", "phối đồ", "穿搭", "时尚"]):
            return {
                "summary": "Video gợi ý phối đồ thời trang, biến hình trang phục và phong cách sành điệu.",
                "subjects": ["fashion model", "creator", "female"],
                "appearance": ["outfit sành điệu", "phụ kiện cao cấp", "tone màu thời thượng"],
                "environment": ["urban street", "studio", "fashion boutique"],
                "actions": ["fashion walk", "posing", "outfit transition", "accessories showcase"],
                "camera": ["full body", "panning", "slow-mo runway"],
                "categories": ["Fashion", "Beauty", "OOTD"],
                "emotional_tone": ["confident", "stylish", "chic"],
                "keywords": {
                    "primary": ["流行时尚穿搭", "高级感氛围感变装", "每日出街OOTD"],
                    "action": ["走秀转场变身", "优雅摆pose定格", "快速换装搭配"],
                    "scene": ["现代都市街头", "极简风摄影棚", "潮流买手店"],
                    "style": ["高级感", "显瘦搭配", "早秋氛围感"],
                    "trend": ["一周穿搭不重样", "普通人高级感穿搭", "穿搭天花板"]
                },
                "queries": {
                    "exact": ["流行时尚穿搭", "高级感氛围感变装", "每日出街OOTD"],
                    "high_similarity": ["时尚穿搭博主", "显高显瘦搭配指南", "潮流模特穿搭"],
                    "visual": ["都市街拍高级感穿搭", "摄影棚变装秀"],
                    "action": ["走秀转场变身", "快速换装搭配", "优雅摆pose定格"],
                    "scene": ["现代都市街头街拍", "潮流买手店试衣"],
                    "trend": ["普通人也能穿出高级感", "早秋氛围感穿搭天花板"],
                    "broad": ["穿搭", "时尚", "OOTD", "变装"]
                }
            }
        elif any(w in combined for w in ["review đồ ăn", "food review", "ẩm thực", "quán ăn", "ăn uống", "美食测评", "探店"]):
            return {
                "summary": "Video review ẩm thực, trải nghiệm các món ăn đường phố và quán ăn nổi tiếng.",
                "subjects": ["food reviewer", "mukbang creator", "chef"],
                "appearance": ["món ăn hấp dẫn", "biểu cảm ăn ngon miệng"],
                "environment": ["night market", "street stall", "famous restaurant"],
                "actions": ["eating", "reviewing", "tasting", "ranking", "unboxing"],
                "camera": ["macro food close-up", "POV tasting", "table view"],
                "categories": ["Food", "Review", "Mukbang"],
                "emotional_tone": ["mouth-watering", "fun", "enthusiastic"],
                "keywords": {
                    "primary": ["街头美食大探店", "爆款美食真实测评", "深夜路边摊开箱"],
                    "action": ["咬下一口酥脆爆汁", "大口吃肉满足瞬间", "真实打分点评"],
                    "scene": ["热闹夜市大排档", "人气爆棚老字号", "街头特色小馆"],
                    "style": ["真实测评", "第一视角探店", "烟火气"],
                    "trend": ["必吃神仙小吃", "全网吹爆的网红餐厅", "100元吃遍夜市"]
                },
                "queries": {
                    "exact": ["街头美食大探店", "爆款美食真实测评", "深夜路边摊开箱"],
                    "high_similarity": ["美食探店博主", "必吃神仙小吃", "大胃王吃播测评"],
                    "visual": ["夜市大排档探店实录", "高清美食爆汁特写"],
                    "action": ["咬下一口酥脆爆汁", "大口吃肉满足瞬间", "真实打分点评"],
                    "scene": ["热闹夜市大排档", "人气爆棚老字号小店"],
                    "trend": ["这家路边摊千万别错过", "亲测全网吹爆的网红餐厅"],
                    "broad": ["美食测评", "探店", "路边摊", "吃播"]
                }
            }
        elif any(w in combined for w in ["hài", "cười", "drama", "tiểu phẩm", "funny", "comedy", "搞笑", "沙雕"]):
            return {
                "summary": "Tiểu phẩm kịch bản hài hước tình huống bất ngờ.",
                "subjects": ["comedian", "male", "female", "group"],
                "appearance": ["trang phục đời thường", "biểu cảm đa dạng"],
                "environment": ["office", "living room", "street"],
                "actions": ["acting", "talking", "pranking", "reacting"],
                "camera": ["handheld", "POV", "medium shot"],
                "categories": ["Comedy", "Drama", "Storytelling"],
                "emotional_tone": ["funny", "hilarious", "surprising"],
                "keywords": {
                    "primary": ["搞笑短剧", "沙雕日常", "爆笑反转"],
                    "action": ["神级反转", "整蛊互动", "一本正经搞笑"],
                    "scene": ["办公室", "家庭生活", "校园"],
                    "style": ["幽默段子", "戏精表演", "快节奏剪辑"],
                    "trend": ["今日份快乐源泉", "笑到肚子疼", "大冤种日常"]
                },
                "queries": {
                    "exact": ["爆笑反转短剧", "搞笑沙雕日常"],
                    "high_similarity": ["戏精同事搞笑日常", "情侣互坑名场面"],
                    "visual": ["办公室搞笑短片", "沙雕名场面合集"],
                    "action": ["意想不到的结局", "神级反转打脸"],
                    "scene": ["职场爆笑日常", "家庭沙雕瞬间"],
                    "trend": ["全网笑点合集", "笑死人的宝藏短剧"],
                    "broad": ["搞笑", "沙雕", "短剧", "段子"]
                }
            }
        else:
            # Default / Dance / Transformation / Hot trend / Beauty Girl
            return {
                "summary": "Video gái xinh, nhảy hiện đại, biến hình thời trang bắt nhịp âm nhạc Douyin.",
                "subjects": ["female", "young creator", "dancer"],
                "appearance": ["trang phục thời trang", "makeup cuốn hút", "tóc đẹp"],
                "environment": ["bedroom", "dance studio", "neon stage", "street"],
                "actions": ["dancing", "changing clothes", "rhythm syncing", "posing"],
                "camera": ["full-body", "cinematic", "tripod", "close-up"],
                "categories": ["Dance", "Fashion", "Beauty", "Transformation"],
                "emotional_tone": ["energetic", "confident", "attractive"],
                "keywords": {
                    "primary": ["抖音高颜值女神", "绝美神仙颜值", "气质纯欲天花板"],
                    "action": ["变装卡点", "慢摇舞", "丝滑转场", "踩点律动"],
                    "scene": ["室内练舞室", "氛围感卧室", "霓虹舞台"],
                    "style": ["氛围感", "高级感", "甜酷风", "时尚"],
                    "trend": ["卡点舞挑战", "爆款翻跳", "心动女嘉宾"]
                },
                "queries": {
                    "exact": ["抖音高颜值女神", "绝美神仙颜值", "气质纯欲天花板"],
                    "high_similarity": ["高颜值小姐姐", "甜美系校花", "氛围感美女"],
                    "visual": ["氛围感练舞室热舞", "镜子前丝滑变装", "霓虹灯光舞台跳舞"],
                    "action": ["变装卡点惊艳瞬间", "对镜微笑放电", "唯美回眸一笑"],
                    "scene": ["阳光微风户外", "室内唯美光影"],
                    "trend": ["看一眼就沦陷的颜值", "这才是真正的有效颜值"],
                    "broad": ["美女", "高颜值", "变装", "女神"]
                }
            }
