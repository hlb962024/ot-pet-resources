import os
import requests
from urllib.parse import quote
from time import sleep

# ==================== 宠物列表（同毕业视频） ====================
PETS = {
    "山海灵宠": ["毕方", "凤凰", "蛊雕", "精卫", "九尾狐", "天狗"],
    "国风神兽": ["白虎", "独角兽", "多肉精灵", "貔貅", "青龙", "狻猊", "朱雀"],
    "生肖萌宝": ["辰龙", "丑牛", "亥猪", "卯兔", "申猴", "巳蛇", "未羊", "午马", "戌狗", "寅虎", "酉鸡", "子鼠"],
    "萌犬天团": ["比熊", "边牧", "柴犬", "哈士奇", "黑柴", "金毛", "柯基犬", "马尔济斯", "萨摩耶", "西高地", "西施犬", "雪纳瑞"],
    "软萌喵星": ["波斯猫", "布偶猫", "德文卷毛猫", "虎斑猫", "加菲猫", "金渐层", "橘猫", "缅因猫", "暹罗猫", "银渐层猫"],
    "绿野部落": [
        "安哥拉兔", "北极狼", "仓鼠", "垂耳兔", "刺猬", "大象", "大熊猫", "狐狸", "浣熊", "考拉",
        "柯尔鸭", "恐龙", "蓝孔雀", "龙猫", "芦丁鸡", "梅花鹿", "美洲豹", "蜜袋鼬", "绵羊", "狮子",
        "松鼠", "土拨鼠", "蜥蜴", "小香猪", "小熊猫", "玄凤鹦鹉", "雪貂", "驯鹿", "羊驼", "长颈鹿"
    ],
    "水中伙伴": ["巴西龟", "海豹", "海马", "海兔", "寄居蟹", "六角恐龙", "企鹅", "水獭"],
}

# ==================== 配置 ====================
BASE_URL = "https://otf-pub-cdn.ourteacher.cc/uploads/all-pets/feeding-video"
ROOT_DIR = "animal-video-feeding"      # 喂食视频单独文件夹
FORMATS = ["mp4", "webm"]              # 优先尝试 mp4，再尝试 webm
RETRY_TIMES = 3
TIMEOUT = 30
RETRY_DELAY = 2

# ==================== 下载函数 ====================
def build_url(name, ext):
    """构建喂食视频 URL（动物名需 URL 编码）"""
    encoded_name = quote(name, safe='')
    return f"{BASE_URL}/{encoded_name}.{ext}"

def download_feeding_video(series, name, idx, total):
    """
    尝试下载喂食视频，返回 (成功?, 扩展名)
    先试 mp4，再试 webm
    """
    series_dir = os.path.join(ROOT_DIR, series)
    os.makedirs(series_dir, exist_ok=True)

    # 检查是否已存在（任意格式）
    for ext in FORMATS:
        local_path = os.path.join(series_dir, f"{name}.{ext}")
        if os.path.exists(local_path):
            print(f"⏭️  [{idx}/{total}] 已存在，跳过: {series}/{name}.{ext}")
            return True, ext

    # 依次尝试每种格式
    for ext in FORMATS:
        url = build_url(name, ext)
        for attempt in range(1, RETRY_TIMES + 1):
            try:
                print(f"⬇️  [{idx}/{total}] 尝试 {series}/{name}.{ext} (第 {attempt}/{RETRY_TIMES} 次)")
                resp = requests.get(url, stream=True, timeout=TIMEOUT)

                if resp.status_code == 200:
                    local_path = os.path.join(series_dir, f"{name}.{ext}")
                    with open(local_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    print(f"✅ [{idx}/{total}] 成功: {series}/{name}.{ext}")
                    return True, ext

                elif resp.status_code == 404:
                    # 404 表示该格式不存在，直接换下一种格式，不重试
                    print(f"⚠️  [{idx}/{total}] {ext} 不存在 (404)，尝试下一种格式...")
                    break  # 跳出重试循环，换格式

                else:
                    print(f"⚠️  [{idx}/{total}] HTTP {resp.status_code}，URL: {url}")

            except requests.exceptions.Timeout:
                print(f"❌ [{idx}/{total}] 超时 (尝试 {attempt}/{RETRY_TIMES})")
            except requests.exceptions.ConnectionError as e:
                print(f"❌ [{idx}/{total}] 连接错误: {e}")
            except Exception as e:
                print(f"❌ [{idx}/{total}] 未知异常: {type(e).__name__} - {e}")

            if attempt < RETRY_TIMES:
                sleep(RETRY_DELAY)

    # 两种格式都失败
    print(f"❌ [{idx}/{total}] 放弃: {series}/{name} (mp4/webm 均失败)")
    return False, None

# ==================== 主流程 ====================
def main():
    os.makedirs(ROOT_DIR, exist_ok=True)

    # 生成任务列表
    tasks = []
    for series, names in PETS.items():
        for name in names:
            tasks.append((series, name))

    total = len(tasks)
    print(f"🍖 共 {total} 个喂食视频待下载\n")

    success_count = 0
    fail_list = []
    format_stats = {"mp4": 0, "webm": 0}

    for idx, (series, name) in enumerate(tasks, 1):
        ok, ext = download_feeding_video(series, name, idx, total)
        if ok:
            success_count += 1
            if ext:
                format_stats[ext] = format_stats.get(ext, 0) + 1
        else:
            fail_list.append(f"{series}/{name}")

        # 整体进度
        pct = idx / total * 100
        print(f"📊 整体进度: {idx}/{total} ({pct:.1f}%)\n")

    # ==================== 汇总 ====================
    print("=" * 50)
    print(f"🎉 下载完成！成功 {success_count}/{total}")
    print(f"📁 格式统计: MP4={format_stats['mp4']}, WebM={format_stats['webm']}")
    if fail_list:
        print("❌ 失败列表：")
        for f in fail_list:
            print(f"  - {f}")
    else:
        print("🎊 全部成功！")

if __name__ == "__main__":
    main()