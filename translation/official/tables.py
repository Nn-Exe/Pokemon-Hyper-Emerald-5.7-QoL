"""Names that sit inside the hack's tables (no pointer reaches them, so the text scans never saw them).
TRAINERS: the Chinese name as it decodes -> English (11 characters at most; the hack's trainer table has 12-byte names).
Canon characters get their official English names; the hack's own people keep the names earlier dialogue translations
gave them, or a plain transliteration."""

TRAINER_TABLE, TRAINER_SIZE, TRAINER_FIRST, TRAINER_LAST = 0x090019F8, 40, 0x0399, 0x054A

TRAINERS = {
    "阿金": "Gold", "小冰": "Xiao Bing", "路比": "Ruby", "诚儿": "Cheng'er", "扎克": "Zack", "鲍勃": "Bob", "妮娜": "Nina",
    "真弥和依": "Mami & Yori", "直也": "Naoya", "小春": "Koharu", "胜也": "Katsuya", "淳也": "Junya", "弗拉达利": "Lysandre",
    "扎奥博": "Faba", "和树": "Kazuki", "丰次": "Toyoji", "胜和爱理": "Sheng&Aili", "忠叶和凤": "Zhong&Feng", "芽衣": "Mei",
    "巡音": "Megurine", "伊扎克": "Yzak", "弘人": "Hiroto", "今朝子": "Kesako", "瓦吉": "Waji", "绠衣响": "Gengyi",
    "银河团员": "Grunt",
    "金斗": "Jindou", "奥痕": "Aohen", "翠訾": "Cuizi", "艾希": "Ashe", "角虫": "Jiaochong", "苦草": "Kucao", "柩司": "Jiusi",
    "健泰": "Kenta", "临溪": "Linxi", "菲雨": "Feiyu", "序锋": "Xufeng", "绠樱": "Gengying", "谷雨": "Guyu", "魔罗": "Moluo",
    "李狗蛋": "Li Goudan", "心染": "Xinran", "枫墨": "Fengmo", "艾梦": "Aimon",
    "小热": "Xiaore", "诸斗": "Zhudou", "日天": "Ritian", "吴大德": "Wu Dade", "王小明": "Xiaoming", "纸": "Paper",
    "张黄天": "Huangtian", "美玲": "Meiling", "迕兰": "Wulan", "闻雪&闻月": "Wenxue&Yue", "花花": "Huahua",
    "安某蓝": "An Moulan", "天子": "Tenshi", "古晴": "Guqing", "零八": "Lingba", "津沙魅": "Jinshamei", "步楗": "Bujian",
    "阿骏": "Ajun", "树井": "Shujing", "欧雷": "Oulei", "紫苑&女苑": "Shion&Jo'on", "玄清": "Xuanqing",
    "清明&重阳": "Qing&Chong", "秃老头": "Old Baldy", "魔理沙": "Marisa", "拉鸥": "Laou", "火鸟": "Firebird",
    "黑椰&白菇": "Heiye&Baigu", "高攀": "Gaopan", "石峰": "Shifeng", "波迪": "Bodie", "君格尔": "Junger", "卫宫": "Emiya",
    "原太": "Genta", "幽香": "Yuuka", "阿不思": "Albus", "艾蕾西亚": "Alesia", "奥户": "Aohu", "伊娃": "Eva",
    "奥拉姆": "Oram", "吉尔苏": "Gilsu", "托鲁芬": "Thorfinn", "约克森": "Yorkson", "汕尾": "Shanwei", "朝画": "Chaohua",
    "花甲鸟": "Huajia", "修次": "Shuji", "空军": "Skunked", "马里亚纳": "Mariana", "罗纳多": "Ronaldo", "优利娜": "Yulina",
    "本拉灯": "Ben Lamp", "悠库": "Yuku", "娜露": "Naru", "霍多": "Hodor", "泼该": "Pogai", "库苏力": "Kusuli",
    "王马": "Ouma", "洛克": "Rock", "柯依": "Koyi", "奇诺": "Kino", "德克斯特": "Dexter", "潘洽": "Pancha",
    "龙渊": "Longyuan", "安娜": "Anna", "阿尔斯": "Ars", "娜塔莉亚": "Natalia", "比西摩": "Bisimo", "海音": "Haiyin",
    "汉塞尔": "Hansel", "格雷特": "Gretel", "艾尔露卡": "Elruka", "伊莉娜": "Irina", "维诺姆": "Venom", "铃木": "Suzuki",
    "玛格丽特": "Margaret", "阿库姒": "Akusi", "亚历克斯": "Alex", "索恩斯": "Thorns", "首藤": "Shuto",
    "三六悔": "Sanliuhui", "格雷": "Gray", "诺克特": "Noct", "水公": "Shuigong", "布拉达斯": "Bradas", "威利斯": "Willis",
    "优拉": "Eula", "密鲁": "Milu", "阿莱": "Alai", "平安名": "Heanna", "艾里克": "Eric", "瓦卡特": "Wakat",
    "空珧塔": "Kongyaota", "莫吉托": "Mojito", "海东": "Haidong", "卡恰": "Kacha", "力奇": "Ricky", "涅墨西斯": "Nemesis",
    "阿尾": "Awei", "奥尔加": "Orga", "友奈": "Yuna", "密度电势": "Density", "阿杰": "Ah Jie", "翔子": "Shoko",
    "刹那": "Setsuna", "拉娜": "Lana", "田所浩二": "Tadokoro", "加纳鄂": "Ganae", "莱维亚": "Levia", "亚连": "Allen",
    "莉莉安娜": "Liliana", "佚雷利安": "Yirelian", "光我": "Kouga", "卢迪": "Rudy", "托里崖兹": "Toriyaz",
    "剑楗&雪碧": "Jian&Sprite", "樵": "Qiao", "小蕾": "Xiaolei", "华腾": "Huateng", "睦月": "Mutsuki", "髅芽": "Louya",
    "澌人": "Siren", "星空&司": "Hoshi&Tsuka", "布鲁斯": "Bruce", "柩子": "Jiuzi", "阿特拉斯": "Atlas", "彩羽": "Caiyu",
    "伊利丹": "Illidan", "四斋": "Sizhai", "小智": "Ash", "红发女路人": "Redhead",
    "小遥": "May", "佑树": "Brendan", "小照": "Akari", "吾思": "Cogita", "明耀": "Rei", "步美": "Elaine", "望罗": "Volo", "猫猫": "Maomao", "刚石": "Adaman", "珠贝": "Irida",
    "丹帝": "Leon", "小光": "Dawn", "明辉": "Lucas", "赤红": "Red", "青绿": "Blue", "碧蓝": "Green", "小银": "Silver",
    "克丽丝": "Kris", "琴音": "Lyra", "布莱克": "Black", "斗子": "Hilda", "黑次": "Blake", "鸣依": "Rosa", "修": "Hugh",
    "黑连": "Cheren", "朗日": "Elio", "美月": "Selene", "哈乌": "Hau", "莉莉艾": "Lillie", "露莎米奈": "Lusamine",
    "格拉吉欧": "Gladion", "艾克斯": "X", "莎莉娜": "Serena", "创人": "Victor", "希露朵": "Gloria", "沙菲雅": "Sapphire",
    "帕拉妮姒": "Palanis", "达克多": "Dakuduo", "阿渡": "Lance", "大吾": "Steven", "阿戴克": "Alder", "艾莉丝": "Iris",
    "卡露妮": "Diantha", "羽路": "Yulu",
}

ITEM_TABLE, ITEM_SIZE = 0x08FC2C7C, 44            # name[14] first
ITEMS = {  # battle-shop copies of ordinary items (same descriptions as the originals), and one Mega Stone
    697: "Feraligatrite", 754: "Life Orb", 755: "Assault Vest", 756: "Eviolite", 757: "Rocky Helmet", 758: "Light Ball",
    759: "Leftovers", 760: "Scope Lens", 761: "Throat Spray", 762: "Lum Berry", 763: "Sitrus Berry", 764: "Aguav Berry",
    765: "Charti Berry", 766: "Weak Policy", 767: "Focus Sash",
}

SPECIES_TABLE, SPECIES_SIZE = 0x08F2B790, 11
SPECIES = {  # the hack's four restored fossil Pokémon (Electric, Dragon, Water, Ice / Rock), named after the fossil each
            # is: 化石雷鸟 / 巨龙 / 鳃鱼 / 海兽, as Emerald-length names in the style of the items (Fossilized Bird...)
    990: "Foss.Bird", 991: "Foss.Drake", 992: "Foss.Fish", 993: "Foss.Dino",
}

MOVE_TABLE, MOVE_SIZE = 0x09D30258, 13
MOVES = {937: "Petal Dance"}

DEX_TABLE, DEX_SIZE, DEX_FIRST, DEX_LAST = 0x09250000, 32, 906, 959       # filler entries: Bulbasaur's text, category 种子
DEX_CATEGORY = "Seed"

# the hack's battle engine, reached as anchor + offset
TURNS_LEFT = (0x09D76FF1, "Turns left:")           # 13 bytes are copied from here
# field-effect names for "{side}'s {effect} effect: N turn(s) remaining." - 5-byte slots (two hanzi), so the English
# goes to a new block and the code that forms each address is re-aimed: (the instruction or literal, old, new)
EFFECTS = ["Swamp", "Sea of Fire", "Rainbow", "Wildfire", "Vine Lash", "Cannonade", "Volcalith"]
