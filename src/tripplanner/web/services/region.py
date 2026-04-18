from __future__ import annotations

import re

_CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")

_CHINESE_CITIES: set[str] = {
    "beijing", "shanghai", "guangzhou", "shenzhen", "chengdu",
    "hangzhou", "wuhan", "xian", "chongqing", "nanjing",
    "tianjin", "suzhou", "changsha", "zhengzhou", "dongguan",
    "qingdao", "shenyang", "ningbo", "kunming", "dalian",
    "xiamen", "fuzhou", "wuxi", "hefei", "harbin",
    "jinan", "changchun", "shijiazhuang", "nanning", "guiyang",
    "nanchang", "lanzhou", "taiyuan", "haikou", "hohhot",
    "lhasa", "yinchuan", "xining", "urumqi", "baotou",
    "luoyang", "wenzhou", "foshan", "zhuhai", "zhongshan",
    "huizhou", "shantou", "quanzhou", "yantai", "weihai",
    "nanjing", "sanya", "lijiang", "dali", "yangshuo",
    "guilin", "zhangjiajie", "jiuquan", "dunhuang", "emeishan",
    "北京", "上海", "广州", "深圳", "成都",
    "杭州", "武汉", "西安", "重庆", "南京",
    "天津", "苏州", "长沙", "郑州", "东莞",
    "青岛", "沈阳", "宁波", "昆明", "大连",
    "厦门", "福州", "无锡", "合肥", "哈尔滨",
    "济南", "长春", "石家庄", "南宁", "贵阳",
    "南昌", "兰州", "太原", "海口", "呼和浩特",
    "拉萨", "银川", "西宁", "乌鲁木齐", "包头",
    "洛阳", "温州", "佛山", "珠海", "中山",
    "惠州", "汕头", "泉州", "烟台", "威海",
    "三亚", "丽江", "大理", "阳朔", "桂林",
    "张家界", "敦煌", "峨眉山",
}


def is_chinese_destination(city: str) -> bool:
    """Check if a city name refers to a Chinese destination.

    Detects Chinese characters (CJK Unified Ideographs) and matches
    against a set of known Chinese city names in pinyin and Chinese.
    """
    if _CJK_PATTERN.search(city):
        return True
    return city.strip().lower() in _CHINESE_CITIES
