import json
import re
import urllib.request
from typing import List, Dict, Any

class QueryGenerator:
    @classmethod
    def generate_20_queries(
        cls,
        profile: Dict[str, Any],
        api_key: str = "",
        provider: str = "gemini"
    ) -> List[Dict[str, Any]]:
        """
        Generates exactly 20 Chinese Douyin search queries grouped into 6 categories:
        - core_topic (4)
        - people_or_objects (3)
        - actions (4)
        - scene (3)
        - content_format (3)
        - long_tail (3)
        """
        if api_key and provider == "gemini":
            try:
                prompt = f"""
You are an expert Douyin SEO & search algorithm strategist.
Based on this video content profile:
{json.dumps(profile, ensure_ascii=False, indent=2)}

Generate EXACTLY 20 natural Chinese Douyin search queries.
Group them into categories:
1. core_topic (4 queries)
2. people_or_objects (3 queries)
3. actions (3 queries)
4. scene (3 queries)
5. content_format (3 queries)
6. long_tail (4 queries)

Rules:
- Natural Chinese search queries (2 to 12 Chinese characters)
- No complete sentences, no punctuation
- Preserve exact brand/person/product names if observed
- Assign relevance score (0.0 to 1.0) and a brief reason in Chinese.

Return ONLY valid JSON in this format:
{{
  "queries": [
    {{
      "query": "夜市美食",
      "category": "core_topic",
      "reason": "视频核心主题",
      "score": 0.95
    }}
  ]
}}
"""
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"}
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    txt = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    txt = re.sub(r"^```json\s*", "", txt.strip(), flags=re.MULTILINE)
                    txt = re.sub(r"```$", "", txt.strip(), flags=re.MULTILINE)
                    data = json.loads(txt)
                    queries = data.get("queries", [])
                    if len(queries) >= 15:
                        return queries[:20]
            except Exception as e:
                print(f"[QueryGenerator] AI Query generation fallback: {e}")

        # Intelligent Offline 20-Query Generation Pipeline
        main_topic = profile.get("main_topic", "Dance")
        content_format = profile.get("content_format", "dance_cover")
        
        # Determine theme dictionary
        topic_lower = (str(main_topic) + " " + str(content_format) + " " + json.dumps(profile.get("search_concepts", []), ensure_ascii=False)).lower()

        if "pijama" in topic_lower or "睡衣" in topic_lower or "pajama" in topic_lower:
            queries_data = [
                # core_topic (4)
                {"query": "居家睡衣美女", "category": "core_topic", "reason": "核心睡衣主题", "score": 0.98},
                {"query": "丝绸睡衣变装", "category": "core_topic", "reason": "睡衣变装热门词", "score": 0.95},
                {"query": "甜美睡衣日常", "category": "core_topic", "reason": "甜美居家风格", "score": 0.92},
                {"query": "慵懒睡衣写真", "category": "core_topic", "reason": "氛围感睡衣写真", "score": 0.90},
                # people_or_objects (3)
                {"query": "睡衣小姐姐", "category": "people_or_objects", "reason": "人物属性标签", "score": 0.88},
                {"query": "居家小甜心", "category": "people_or_objects", "reason": "创作者形象", "score": 0.86},
                {"query": "纯欲睡衣风", "category": "people_or_objects", "reason": "穿搭风格细分", "score": 0.85},
                # actions (4)
                {"query": "睡衣伸懒腰", "category": "actions", "reason": "慵懒日常动作", "score": 0.93},
                {"query": "慵懒起床日常", "category": "actions", "reason": "晨起互动动作", "score": 0.89},
                {"query": "睡衣卡点换装", "category": "actions", "reason": "变装转场动作", "score": 0.88},
                {"query": "抱枕甜美互动", "category": "actions", "reason": "道具互动动作", "score": 0.84},
                # scene (3)
                {"query": "温暖卧室床头", "category": "scene", "reason": "卧室温馨场景", "score": 0.89},
                {"query": "晨光洒进房间", "category": "scene", "reason": "自然光影场景", "score": 0.87},
                {"query": "居家温馨客厅", "category": "scene", "reason": "室内客厅场景", "score": 0.84},
                # content_format (3)
                {"query": "居家生活Vlog", "category": "content_format", "reason": "Vlog生活格式", "score": 0.91},
                {"query": "睡衣变装卡点", "category": "content_format", "reason": "卡点视频格式", "score": 0.89},
                {"query": "慵懒慢速直拍", "category": "content_format", "reason": "直拍慢动作格式", "score": 0.86},
                # long_tail (3)
                {"query": "穿睡衣也能这么惊艳", "category": "long_tail", "reason": "长尾高互动搜索词", "score": 0.92},
                {"query": "居家慵懒氛围感天花板", "category": "long_tail", "reason": "长尾赞叹搜索词", "score": 0.90},
                {"query": "睡衣变装前后对比", "category": "long_tail", "reason": "长尾对比搜索词", "score": 0.88}
            ]
        elif "che mặt" in topic_lower or "遮脸" in topic_lower or "mask" in topic_lower or "covering face" in topic_lower or "cover face" in topic_lower:
            queries_data = [
                # core_topic (4)
                {"query": "遮脸神秘氛围感", "category": "core_topic", "reason": "核心遮脸氛围感", "score": 0.98},
                {"query": "半遮面绝美神颜", "category": "core_topic", "reason": "半遮面神仙颜值", "score": 0.95},
                {"query": "手机挡脸拍照", "category": "core_topic", "reason": "拍照姿势热门词", "score": 0.92},
                {"query": "口罩美女神态", "category": "core_topic", "reason": "口罩遮脸高赞词", "score": 0.89},
                # people_or_objects (3)
                {"query": "遮脸气质女神", "category": "people_or_objects", "reason": "人物形象定位", "score": 0.88},
                {"query": "露眼杀小姐姐", "category": "people_or_objects", "reason": "眼神特征标签", "score": 0.87},
                {"query": "神秘感女生", "category": "people_or_objects", "reason": "神秘气质人设", "score": 0.85},
                # actions (4)
                {"query": "手机半挡脸", "category": "actions", "reason": "挡脸标志动作", "score": 0.94},
                {"query": "纤手轻掩面颊", "category": "actions", "reason": "手部遮面动作", "score": 0.89},
                {"query": "眼神杀放电", "category": "actions", "reason": "眼神互动细节", "score": 0.88},
                {"query": "慢慢移开遮挡", "category": "actions", "reason": "转场悬念动作", "score": 0.85},
                # scene (3)
                {"query": "昏暗氛围感室内", "category": "scene", "reason": "室内暗光氛围", "score": 0.89},
                {"query": "逆光街头剪影", "category": "scene", "reason": "街头逆光场景", "score": 0.87},
                {"query": "镜子前自拍角", "category": "scene", "reason": "镜前拍摄场景", "score": 0.84},
                # content_format (3)
                {"query": "氛围感眼神特写", "category": "content_format", "reason": "特写剪辑格式", "score": 0.91},
                {"query": "慢镜头遮脸转场", "category": "content_format", "reason": "慢动作转场格式", "score": 0.88},
                {"query": "悬念变装视频", "category": "content_format", "reason": "悬念内容形态", "score": 0.86},
                # long_tail (3)
                {"query": "遮住脸也能感受到的美", "category": "long_tail", "reason": "长尾情感搜索词", "score": 0.92},
                {"query": "仅凭一双眼睛惊艳全网", "category": "long_tail", "reason": "长尾惊艳高赞词", "score": 0.90},
                {"query": "氛围感拉满的遮脸瞬间", "category": "long_tail", "reason": "长尾氛围感词", "score": 0.88}
            ]
        elif "cô gái nấu ăn" in topic_lower or "girl_cooking" in topic_lower or "美女做饭" in topic_lower or "cooking girl" in topic_lower:
            queries_data = [
                # core_topic (4)
                {"query": "美女下厨做饭", "category": "core_topic", "reason": "美女做饭核心词", "score": 0.98},
                {"query": "治愈系沉浸式做饭", "category": "core_topic", "reason": "沉浸式治愈流派", "score": 0.95},
                {"query": "独居女孩一人食", "category": "core_topic", "reason": "一人食热门主题", "score": 0.93},
                {"query": "仙女的厨房日常", "category": "core_topic", "reason": "精致厨房生活", "score": 0.90},
                # people_or_objects (3)
                {"query": "温柔做饭博主", "category": "people_or_objects", "reason": "创作者温柔属性", "score": 0.88},
                {"query": "厨房美厨娘", "category": "people_or_objects", "reason": "厨娘人物设定", "score": 0.87},
                {"query": "精致料理女孩", "category": "people_or_objects", "reason": "精致生活形象", "score": 0.85},
                # actions (4)
                {"query": "熟练切菜备料", "category": "actions", "reason": "刀工备料动作", "score": 0.93},
                {"query": "大火翻炒颠勺", "category": "actions", "reason": "烹饪翻炒动作", "score": 0.89},
                {"query": "秘制酱汁调配", "category": "actions", "reason": "调料步骤特写", "score": 0.87},
                {"query": "尝一口满足微笑", "category": "actions", "reason": "品尝满足神态", "score": 0.86},
                # scene (3)
                {"query": "暖光温馨厨房", "category": "scene", "reason": "暖色调厨房", "score": 0.89},
                {"query": "烟火气小院", "category": "scene", "reason": "庭院烟火场景", "score": 0.87},
                {"query": "整洁料理台", "category": "scene", "reason": "料理台场景", "score": 0.84},
                # content_format (3)
                {"query": "沉浸式ASMR做饭", "category": "content_format", "reason": "ASMR音效格式", "score": 0.91},
                {"query": "一人食治愈Vlog", "category": "content_format", "reason": "治愈Vlog格式", "score": 0.88},
                {"query": "1分钟快手菜教程", "category": "content_format", "reason": "短视频教程格式", "score": 0.86},
                # long_tail (3)
                {"query": "既有颜值做饭又好吃", "category": "long_tail", "reason": "长尾双向赞叹词", "score": 0.92},
                {"query": "下班后的治愈一人食", "category": "long_tail", "reason": "长尾生活共鸣词", "score": 0.90},
                {"query": "一个人也要好好吃饭", "category": "long_tail", "reason": "长尾情感金句", "score": 0.88}
            ]
        elif "mèo" in topic_lower or "cat" in topic_lower or "猫" in topic_lower or "cute_pets" in topic_lower:
            queries_data = [
                # core_topic (4)
                {"query": "治愈系可爱猫咪", "category": "core_topic", "reason": "核心治愈猫咪主题", "score": 0.98},
                {"query": "萌宠猫咪日常", "category": "core_topic", "reason": "猫咪萌宠日常", "score": 0.95},
                {"query": "软萌幼猫撒娇", "category": "core_topic", "reason": "小奶猫撒娇热词", "score": 0.93},
                {"query": "成精的小猫咪", "category": "core_topic", "reason": "趣味猫咪名场面", "score": 0.90},
                # people_or_objects (3)
                {"query": "软萌小奶猫", "category": "people_or_objects", "reason": "幼猫品种标签", "score": 0.89},
                {"query": "胖嘟嘟英短", "category": "people_or_objects", "reason": "英短品种特征", "score": 0.86},
                {"query": "粘人小猫咪", "category": "people_or_objects", "reason": "性格特征标签", "score": 0.85},
                # actions (4)
                {"query": "踩奶呼噜噜", "category": "actions", "reason": "踩奶治愈动作", "score": 0.94},
                {"query": "歪头杀萌化人心", "category": "actions", "reason": "歪头萌态动作", "score": 0.90},
                {"query": "追逐激光逗猫棒", "category": "actions", "reason": "玩耍互动动作", "score": 0.87},
                {"query": "翻肚皮求摸摸", "category": "actions", "reason": "撒娇求抚摸动作", "score": 0.86},
                # scene (3)
                {"query": "温暖猫窝", "category": "scene", "reason": "室内猫窝场景", "score": 0.89},
                {"query": "阳光窗台", "category": "scene", "reason": "阳光窗边场景", "score": 0.87},
                {"query": "客厅地毯玩耍", "category": "scene", "reason": "地毯玩耍场景", "score": 0.84},
                # content_format (3)
                {"query": "萌宠治愈Vlog", "category": "content_format", "reason": "萌宠Vlog形态", "score": 0.92},
                {"query": "慢动作猫咪特写", "category": "content_format", "reason": "慢动作特写格式", "score": 0.88},
                {"query": "猫咪迷惑行为大赏", "category": "content_format", "reason": "合集盘点格式", "score": 0.86},
                # long_tail (3)
                {"query": "谁能拒绝一只粘人的小猫咪", "category": "long_tail", "reason": "长尾高互动文案词", "score": 0.92},
                {"query": "看完直接被可爱化了", "category": "long_tail", "reason": "长尾情绪赞叹词", "score": 0.90},
                {"query": "云吸猫快乐日常", "category": "long_tail", "reason": "长尾吸猫搜索词", "score": 0.88}
            ]
        elif "ô tô" in topic_lower or "xe hơi" in topic_lower or "car" in topic_lower or "汽车" in topic_lower or "超跑" in topic_lower:
            queries_data = [
                # core_topic (4)
                {"query": "豪华超跑声浪", "category": "core_topic", "reason": "超跑声浪核心词", "score": 0.98},
                {"query": "酷炫汽车大片", "category": "core_topic", "reason": "汽车视觉大片", "score": 0.95},
                {"query": "沉浸式新车测评", "category": "core_topic", "reason": "新车测评核心词", "score": 0.92},
                {"query": "汽车改装名场面", "category": "core_topic", "reason": "改装车热门词", "score": 0.89},
                # people_or_objects (3)
                {"query": "顶级超跑车主", "category": "people_or_objects", "reason": "车主人群属性", "score": 0.88},
                {"query": "资深汽车测评人", "category": "people_or_objects", "reason": "专业车评人属性", "score": 0.87},
                {"query": "赛道性能车", "category": "people_or_objects", "reason": "车型细分标签", "score": 0.85},
                # actions (4)
                {"query": "轰油门炸街声浪", "category": "actions", "reason": "声浪轰鸣动作", "score": 0.94},
                {"query": "弹射起步加速", "category": "actions", "reason": "直线加速动作", "score": 0.90},
                {"query": "丝滑漂移过弯", "category": "actions", "reason": "漂移技巧动作", "score": 0.88},
                {"query": "沉浸式洗车贴膜", "category": "actions", "reason": "汽车美容动作", "score": 0.85},
                # scene (3)
                {"query": "赛道狂飙现场", "category": "scene", "reason": "专业赛道场景", "score": 0.89},
                {"query": "深夜地下车库", "category": "scene", "reason": "地库夜间场景", "score": 0.87},
                {"query": "沿海公路自驾", "category": "scene", "reason": "公路风景场景", "score": 0.84},
                # content_format (3)
                {"query": "电影感运镜车片", "category": "content_format", "reason": "电影运镜格式", "score": 0.91},
                {"query": "沉浸式第一视角试驾", "category": "content_format", "reason": "POV试驾格式", "score": 0.88},
                {"query": "超跑声浪ASMR", "category": "content_format", "reason": "声浪ASMR格式", "score": 0.86},
                # long_tail (3)
                {"query": "男人的终极梦想座驾", "category": "long_tail", "reason": "长尾梦想情怀词", "score": 0.92},
                {"query": "感受顶级超跑的推背感", "category": "long_tail", "reason": "长尾体验搜索词", "score": 0.90},
                {"query": "极致视听汽车大片", "category": "long_tail", "reason": "长尾视听大片词", "score": 0.88}
            ]
        elif "phong cảnh" in topic_lower or "scenery" in topic_lower or "landscape" in topic_lower or "风景" in topic_lower or "nature" in topic_lower:
            queries_data = [
                # core_topic (4)
                {"query": "绝美大自然风光", "category": "core_topic", "reason": "大自然风光核心词", "score": 0.98},
                {"query": "治愈系唯美风景", "category": "core_topic", "reason": "唯美治愈风光", "score": 0.95},
                {"query": "4K超高清自然大片", "category": "core_topic", "reason": "高清风景大片", "score": 0.92},
                {"query": "走遍中国绝美山河", "category": "core_topic", "reason": "山河旅行大片", "score": 0.90},
                # people_or_objects (3)
                {"query": "航拍风光摄影师", "category": "people_or_objects", "reason": "摄影师身份标签", "score": 0.88},
                {"query": "独行旅行者", "category": "people_or_objects", "reason": "旅行者人设", "score": 0.86},
                {"query": "大自然壮丽奇观", "category": "people_or_objects", "reason": "自然地貌特征", "score": 0.85},
                # actions (4)
                {"query": "日出云海翻涌", "category": "actions", "reason": "云海动态景象", "score": 0.94},
                {"query": "暮色晚霞漫天", "category": "actions", "reason": "晚霞变幻瞬间", "score": 0.90},
                {"query": "溪流瀑布潺潺", "category": "actions", "reason": "流水水景动态", "score": 0.87},
                {"query": "航拍俯瞰大地", "category": "actions", "reason": "俯瞰航拍动作", "score": 0.85},
                # scene (3)
                {"query": "雪山之巅", "category": "scene", "reason": "雪山宏伟场景", "score": 0.89},
                {"query": "蔚蓝海岸线", "category": "scene", "reason": "大海沙滩场景", "score": 0.87},
                {"query": "宁静森林湖泊", "category": "scene", "reason": "森林湖泊场景", "score": 0.84},
                # content_format (3)
                {"query": "4K航拍视觉盛宴", "category": "content_format", "reason": "4K航拍格式", "score": 0.91},
                {"query": "治愈风景延时摄影", "category": "content_format", "reason": "延时摄影格式", "score": 0.89},
                {"query": "沉浸式自然音效", "category": "content_format", "reason": "白噪音音效格式", "score": 0.86},
                # long_tail (3)
                {"query": "治愈一切不开心的大自然", "category": "long_tail", "reason": "长尾治愈解压词", "score": 0.92},
                {"query": "随手一截就是壁纸的风光", "category": "long_tail", "reason": "长尾壁纸级风光词", "score": 0.90},
                {"query": "感受地球的震撼之美", "category": "long_tail", "reason": "长尾震撼视觉词", "score": 0.88}
            ]
        elif "thời trang" in topic_lower or "fashion" in topic_lower or "outfit" in topic_lower or "穿搭" in topic_lower or "时尚" in topic_lower:
            queries_data = [
                # core_topic (4)
                {"query": "流行时尚穿搭", "category": "core_topic", "reason": "时尚穿搭核心词", "score": 0.98},
                {"query": "高级感氛围感变装", "category": "core_topic", "reason": "高级感变装热词", "score": 0.95},
                {"query": "每日出街OOTD", "category": "core_topic", "reason": "每日穿搭OOTD", "score": 0.92},
                {"query": "显高显瘦搭配指南", "category": "core_topic", "reason": "实用搭配指南", "score": 0.89},
                # people_or_objects (3)
                {"query": "时尚穿搭博主", "category": "people_or_objects", "reason": "博主创作者属性", "score": 0.88},
                {"query": "潮流模特", "category": "people_or_objects", "reason": "模特形象定位", "score": 0.87},
                {"query": "气质时髦精", "category": "people_or_objects", "reason": "时髦人群标签", "score": 0.85},
                # actions (4)
                {"query": "走秀转场变身", "category": "actions", "reason": "走秀转场动作", "score": 0.94},
                {"query": "优雅摆pose定格", "category": "actions", "reason": "摆拍定格动作", "score": 0.89},
                {"query": "快速换装搭配", "category": "actions", "reason": "换装动作特写", "score": 0.88},
                {"query": "细节首饰展示", "category": "actions", "reason": "首饰细节展示", "score": 0.85},
                # scene (3)
                {"query": "现代都市街头", "category": "scene", "reason": "街拍街景场景", "score": 0.89},
                {"query": "极简风摄影棚", "category": "scene", "reason": "摄影棚极简场景", "score": 0.87},
                {"query": "潮流买手店", "category": "scene", "reason": "时尚买手店场景", "score": 0.84},
                # content_format (3)
                {"query": "一周不重样OOTD", "category": "content_format", "reason": "合集系列格式", "score": 0.92},
                {"query": "电影质感变装秀", "category": "content_format", "reason": "变装短片形态", "score": 0.88},
                {"query": "胶囊衣橱搭配合集", "category": "content_format", "reason": "实用搭配合集", "score": 0.86},
                # long_tail (3)
                {"query": "普通人也能穿出高级感", "category": "long_tail", "reason": "长尾实用技巧词", "score": 0.92},
                {"query": "早秋氛围感穿搭天花板", "category": "long_tail", "reason": "长尾趋势热度词", "score": 0.90},
                {"query": "谁穿谁好看的时髦公式", "category": "long_tail", "reason": "长尾干货公式词", "score": 0.88}
            ]
        elif "review đồ ăn" in topic_lower or "food review" in topic_lower or "美食测评" in topic_lower or "探店" in topic_lower or "ẩm thực" in topic_lower or "cooking" in topic_lower:
            queries_data = [
                # core_topic (4)
                {"query": "街头美食大探店", "category": "core_topic", "reason": "探店核心主题", "score": 0.98},
                {"query": "爆款美食真实测评", "category": "core_topic", "reason": "美食测评核心词", "score": 0.95},
                {"query": "深夜路边摊开箱", "category": "core_topic", "reason": "深夜美食热门词", "score": 0.92},
                {"query": "必吃神仙小吃", "category": "core_topic", "reason": "小吃推荐高频词", "score": 0.89},
                # people_or_objects (3)
                {"query": "美食探店博主", "category": "people_or_objects", "reason": "探店创作者属性", "score": 0.88},
                {"query": "大胃王吃播达人", "category": "people_or_objects", "reason": "吃播创作者人设", "score": 0.86},
                {"query": "路边摊老手艺人", "category": "people_or_objects", "reason": "特色人物属性", "score": 0.85},
                # actions (4)
                {"query": "咬下一口酥脆爆汁", "category": "actions", "reason": "试吃口感动作", "score": 0.94},
                {"query": "大口吃肉满足瞬间", "category": "actions", "reason": "吃播满足表情", "score": 0.90},
                {"query": "真实打分点评", "category": "actions", "reason": "测评点评动作", "score": 0.87},
                {"query": "隐藏菜单解锁", "category": "actions", "reason": "探寻菜单动作", "score": 0.84},
                # scene (3)
                {"query": "热闹夜市大排档", "category": "scene", "reason": "夜市烟火气场景", "score": 0.89},
                {"query": "人气爆棚老字号", "category": "scene", "reason": "老字号小店场景", "score": 0.87},
                {"query": "街头特色小馆", "category": "scene", "reason": "街头餐馆场景", "score": 0.84},
                # content_format (3)
                {"query": "探店第一视角", "category": "content_format", "reason": "POV探店格式", "score": 0.91},
                {"query": "避雷种草吃播", "category": "content_format", "reason": "测评种草格式", "score": 0.88},
                {"query": "100元吃遍夜市挑战", "category": "content_format", "reason": "挑战赛内容形态", "score": 0.86},
                # long_tail (3)
                {"query": "这家路边摊千万别错过", "category": "long_tail", "reason": "长尾探店推荐词", "score": 0.92},
                {"query": "亲测全网吹爆的网红餐厅", "category": "long_tail", "reason": "长尾真实测评词", "score": 0.90},
                {"query": "舌尖上的极致美味", "category": "long_tail", "reason": "长尾美味赞美词", "score": 0.88}
            ]
        elif "hài" in topic_lower or "drama" in topic_lower or "funny" in topic_lower or "搞笑" in topic_lower or "沙雕" in topic_lower:
            queries_data = [
                # core_topic (4)
                {"query": "搞笑沙雕日常", "category": "core_topic", "reason": "核心沙雕搞笑主题", "score": 0.98},
                {"query": "爆笑反转短剧", "category": "core_topic", "reason": "剧情反转高赞词", "score": 0.95},
                {"query": "幽默段子名场面", "category": "core_topic", "reason": "段子合集热词", "score": 0.91},
                {"query": "大冤种爆笑时刻", "category": "core_topic", "reason": "热梗高频词", "score": 0.89},
                # people_or_objects (3)
                {"query": "戏精同事日常", "category": "people_or_objects", "reason": "职场人物设定", "score": 0.88},
                {"query": "搞笑闺蜜互坑", "category": "people_or_objects", "reason": "朋友互动人物", "score": 0.86},
                {"query": "怨种情侣名场面", "category": "people_or_objects", "reason": "情侣搞笑人设", "score": 0.85},
                # actions (4)
                {"query": "神级反转打脸", "category": "actions", "reason": "剧情冲突动作", "score": 0.94},
                {"query": "笑到肚子疼的瞬间", "category": "actions", "reason": "用户情绪动作", "score": 0.90},
                {"query": "一本正经搞笑", "category": "actions", "reason": "表演风格", "score": 0.87},
                {"query": "疯狂整蛊搞笑", "category": "actions", "reason": "整蛊互动动作", "score": 0.84},
                # scene (3)
                {"query": "职场办公室爆笑", "category": "scene", "reason": "办公室场景", "score": 0.89},
                {"query": "家庭沙雕日常", "category": "scene", "reason": "家庭生活场景", "score": 0.87},
                {"query": "校园搞笑名场面", "category": "scene", "reason": "校园场景", "score": 0.83},
                # content_format (3)
                {"query": "反转搞笑微短剧", "category": "content_format", "reason": "短剧内容形态", "score": 0.92},
                {"query": "高能爆笑剪辑合集", "category": "content_format", "reason": "剪辑合集格式", "score": 0.88},
                {"query": "沙雕配音名场面", "category": "content_format", "reason": "配音二创格式", "score": 0.86},
                # long_tail (3)
                {"query": "笑到停不下来的宝藏视频", "category": "long_tail", "reason": "长尾高互动搜索", "score": 0.91},
                {"query": "意想不到的结局系列", "category": "long_tail", "reason": "长尾剧情词", "score": 0.89},
                {"query": "今日份快乐源泉合集", "category": "long_tail", "reason": "长尾日常搜索词", "score": 0.87}
            ]
        else:
            # Default / Beautiful Girl / High Aesthetic / Dance Trend
            queries_data = [
                # core_topic (4)
                {"query": "抖音高颜值女神", "category": "core_topic", "reason": "核心高颜值女神主题", "score": 0.98},
                {"query": "绝美神仙颜值", "category": "core_topic", "reason": "神仙颜值高赞词", "score": 0.95},
                {"query": "气质纯欲天花板", "category": "core_topic", "reason": "气质天花板核心词", "score": 0.93},
                {"query": "氛围感美女", "category": "core_topic", "reason": "氛围感高频搜索", "score": 0.90},
                # people_or_objects (3)
                {"query": "高颜值小姐姐", "category": "people_or_objects", "reason": "创作者形象标签", "score": 0.88},
                {"query": "甜美系校花", "category": "people_or_objects", "reason": "甜美风格定位", "score": 0.87},
                {"query": "氧气美少女", "category": "people_or_objects", "reason": "清纯美少女属性", "score": 0.85},
                # actions (4)
                {"query": "对镜微笑放电", "category": "actions", "reason": "微笑放电特写", "score": 0.94},
                {"query": "撩发心动瞬间", "category": "actions", "reason": "撩发心动动作", "score": 0.90},
                {"query": "唯美回眸一笑", "category": "actions", "reason": "回眸神态抓拍", "score": 0.88},
                {"query": "甜美wink互动", "category": "actions", "reason": "镜头甜美互动", "score": 0.86},
                # scene (3)
                {"query": "阳光微风户外", "category": "scene", "reason": "户外自然光场景", "score": 0.89},
                {"query": "室内唯美光影", "category": "scene", "reason": "室内光影氛围", "score": 0.87},
                {"query": "浪漫咖啡厅", "category": "scene", "reason": "咖啡厅休闲场景", "score": 0.84},
                # content_format (3)
                {"query": "颜值慢动作特写", "category": "content_format", "reason": "慢动作特写格式", "score": 0.92},
                {"query": "一镜到底对拍", "category": "content_format", "reason": "一镜到底直拍格式", "score": 0.88},
                {"query": "氛围感短视频", "category": "content_format", "reason": "短视频氛围形态", "score": 0.86},
                # long_tail (3)
                {"query": "看一眼就沦陷的颜值", "category": "long_tail", "reason": "长尾惊叹高互动词", "score": 0.92},
                {"query": "这才是真正的有效颜值", "category": "long_tail", "reason": "长尾热点赞赏词", "score": 0.90},
                {"query": "谁懂这种氛围感美女", "category": "long_tail", "reason": "长尾情感共鸣词", "score": 0.88}
            ]

        return queries_data[:20]

    @classmethod
    def expand_query(cls, base_query: str) -> List[str]:
        """
        Expands a high-value query into 3-5 semantic variants without concept drift.
        """
        variants_map = {
            "热门卡点舞": ["热门卡点舞教程", "热门卡点舞翻跳", "卡点舞慢动作", "爆款卡点舞合集"],
            "抖音热门热舞": ["抖音热搜舞蹈", "全网爆款热舞", "抖音热门舞蹈推荐", "近期超火热舞"],
            "美女跳舞名场面": ["高颜值美女跳舞", "心动美女跳舞合集", "唯美跳舞名场面", "气质美女热舞"],
            "居家睡衣美女": ["甜美睡衣变装", "居家睡衣日常", "睡衣拍照姿势", "纯欲睡衣穿搭"],
            "遮脸神秘氛围感": ["半遮面拍照技巧", "口罩遮脸氛围感", "神秘眼神杀合集", "遮脸变装转场"],
            "美女下厨做饭": ["仙女做饭日常", "沉浸式做饭教程", "治愈系一人食", "精致女孩下厨"],
            "治愈系可爱猫咪": ["小奶猫撒娇日常", "可爱猫咪迷惑行为", "治愈系萌宠合集", "成精小猫咪名场面"],
            "豪华超跑声浪": ["超跑声浪炸街", "沉浸式超跑试驾", "顶级超跑大片", "汽车改装声浪"],
            "绝美大自然风光": ["治愈系大自然大片", "4K高清风景壁纸", "航拍中国绝美山河", "唯美风景摄影"],
            "流行时尚穿搭": ["显瘦时尚穿搭指南", "早秋氛围感OOTD", "高级感变装穿搭", "一周穿搭不重样"],
            "街头美食大探店": ["夜市爆款小吃测评", "隐藏路边摊美食", "真实探店避雷指南", "全网吹爆美食测评"],
            "搞笑沙雕日常": ["沙雕搞笑合集", "每日爆笑日常", "沙雕名场面合集", "爆笑日常合集"]
        }
        for k, v in variants_map.items():
            if k in base_query or base_query in k:
                return v
                
        # Heuristic suffix expansion
        return [
            f"{base_query}教程",
            f"{base_query}合集",
            f"超火{base_query}",
            f"{base_query}推荐"
        ]
