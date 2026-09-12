import os
import requests
from urllib.parse import quote
from time import sleep
import sys

# ------------------ 宠物数据（同上） ------------------
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

BASE_URL = "https://otf-pub-cdn.ourteacher.cc/uploads/pet_videos"
ROOT_DIR = "animal-video"
RETRY_TIMES = 3
TIMEOUT = 30

# ------------------ 尝试导入 tqdm（可选） ------------------
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("💡 提示：安装 tqdm (pip install tqdm) 可获得更炫酷的进度条")

def download_video(series, name, idx, total):
    """下载单个视频，返回是否成功"""
    encoded_series = quote(series, safe='')
    encoded_name = quote(name, safe='')
    url = f"{BASE_URL}/{encoded_series}/{encoded_name}.webm"

    series_dir = os.path.join(ROOT_DIR, series)
    os.makedirs(series_dir, exist_ok=True)
    local_path = os.path.join(series_dir, f"{name}.webm")

    if os.path.exists(local_path):
        # 已存在则跳过（不计入失败）
        print(f"⏭️  [{idx}/{total}] 已存在，跳过: {series}/{name}")
        return True

    for attempt in range(1, RETRY_TIMES + 1):
        try:
            # 显示当前尝试（详细错误会用）
            print(f"⬇️  [{idx}/{total}] {series}/{name}.webm (尝试 {attempt}/{RETRY_TIMES})")
            resp = requests.get(url, stream=True, timeout=TIMEOUT)
            if resp.status_code == 200:
                with open(local_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"✅ [{idx}/{total}] 完成: {series}/{name}")
                return True
            else:
                # 详细错误：状态码
                print(f"⚠️  [{idx}/{total}] HTTP {resp.status_code}，URL: {url}")
        except requests.exceptions.Timeout:
            print(f"❌ [{idx}/{total}] 超时 (尝试 {attempt}/{RETRY_TIMES})")
        except requests.exceptions.ConnectionError as e:
            print(f"❌ [{idx}/{total}] 连接错误: {e}")
        except Exception as e:
            print(f"❌ [{idx}/{total}] 未知异常: {type(e).__name__} - {e}")

        if attempt < RETRY_TIMES:
            sleep(2)
        else:
            print(f"❌ [{idx}/{total}] 放弃: {series}/{name} (多次失败)")

    return False

def main():
    os.makedirs(ROOT_DIR, exist_ok=True)

    # 构造所有任务的列表 (series, name)
    tasks = []
    for series, names in PETS.items():
        for name in names:
            tasks.append((series, name))
    total = len(tasks)
    success = 0
    failure_list = []

    print(f"📦 共 {total} 个视频待下载\n")

    if HAS_TQDM:
        # 带进度条的迭代
        pbar = tqdm(tasks, desc="总进度", unit="个")
        for idx, (series, name) in enumerate(pbar, 1):
            # 更新进度条描述
            pbar.set_postfix_str(f"当前: {series}/{name}")
            ok = download_video(series, name, idx, total)
            if ok:
                success += 1
            else:
                failure_list.append(f"{series}/{name}")
            pbar.update(1)
        pbar.close()
    else:
        # 纯文本进度（无 tqdm）
        for idx, (series, name) in enumerate(tasks, 1):
            ok = download_video(series, name, idx, total)
            if ok:
                success += 1
            else:
                failure_list.append(f"{series}/{name}")
            # 打印简单百分比
            pct = (idx / total) * 100
            print(f"📊 整体进度: {idx}/{total} ({pct:.1f}%)\n")

    print("\n" + "="*50)
    print(f"🎉 下载完成！成功 {success}/{total} 个")
    if failure_list:
        print("❌ 失败列表：")
        for f in failure_list:
            print(f"  - {f}")
    else:
        print("🎊 全部下载成功！")

if __name__ == "__main__":
    main()