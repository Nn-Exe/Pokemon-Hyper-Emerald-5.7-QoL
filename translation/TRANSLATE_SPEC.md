# Translation task spec (Pokémon Hyper Emerald: Lost Artifacts — fan translation completion)

You are translating leftover Chinese strings from a Pokémon Emerald ROM hack into English.

## Input / Output
- Input: a JSON array of strings (simplified Chinese with embedded tokens).
- Output: write a JSON **object** mapping EVERY input string (exact original as key) to its English translation, using
  `json.dump(result, open(OUTPUT_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)`.
- Every input key must appear in the output. Verify count before finishing.

## Token rules (critical)
- Keep these tokens EXACTLY as-is, placed naturally in the English sentence:
  `[BUF01]` … `[BUF0F]`, `[FC....]`, `[F8..]`, `[F9..]`, `[F7]`, `[S..]`, `[Lv]`
  - [BUF01] = player's name. [BUF02]/[BUF03]/[BUF04] = dynamic strings (a name, item, Pokémon, or number). [BUF06] = rival name. Treat as proper-noun placeholders.
  - [FC....] are formatting/color codes: keep them at roughly the same relative position (start/end of the text).
- `\p` = page break. Keep `\p` between paragraphs (you may merge/split sentences within a page, but keep the same number of `\p` tokens when feasible; never output more text pages than the source had).
- `\n` and `\l` in the source are just line breaks: DO NOT output `\n` or `\l` at all — replace with a normal space. (Re-wrapping is done later automatically.)
- Chinese punctuation (。,!?、~—:) → normal English punctuation.
- If a string is garbled nonsense (random characters, not real Chinese), map it to exactly `@@SKIP@@`.

## Style
- Concise, natural video-game English matching official Pokémon localization tone.
- Use OFFICIAL Pokémon terminology: 宝可梦=Pokémon (write POKéMON as just Pokémon), 训练家=Trainer, 道馆=Gym, 道馆馆主=Gym Leader, 徽章=Badge, 招式=move, 特性=Ability, 属性=type, 携带道具=held item, 树果=Berry, 精灵球=Poké Ball, 图鉴=Pokédex, 亲密度=friendship, 努力值=EVs, 个体值=IVs, 性格=Nature, 异常状态=status condition, 秘传学习器=HM, 招式学习器=TM, 超级进化=Mega Evolution, 极巨化=Dynamax, 超极巨化=Gigantamax, Z招式=Z-Move, 太晶化=Terastallization, 对战开拓区=Battle Frontier, 对战塔=Battle Tower, 四天王=Elite Four, 冠军=Champion, 神奇宝贝中心/宝可梦中心=Pokémon Center, 友好商店=Poké Mart.
- Hoenn place names (official): 未白镇=Littleroot Town, 古辰镇=Oldale Town, 橙华市=Petalburg City, 卡那兹市=Rustboro City, 武斗镇=Dewford Town, 凯那市=Slateport City, 紫堇市=Mauville City, 绿荫镇=Verdanturf Town, 秋叶镇=Fallarbor Town, 釜炎镇=Lavaridge Town, 茵郁市=Fortree City, 水静市=Lilycove City, 绿岭市=Mossdeep City, 琉璃市=Sootopolis City, 浅滩镇=Pacifidlog Town, 彩幽市=Ever Grande City, 送神火山=Mt. Pyre, 烟突山=Mt. Chimney, 天元洞穴=Cave of Origin, 流星瀑布=Meteor Falls, 新紫堇=New Mauville, 幻岛=Mirage Island, 石之洞窟=Granite Cave, 日照沙漠 etc. Region names: 丰缘=Hoenn, 关都=Kanto, 城都=Johto, 神奥=Sinnoh, 合众=Unova, 卡洛斯=Kalos, 阿罗拉=Alola, 伽勒尔=Galar. 芳缘 also = Hoenn.
- Characters: 小遥=May, 小胜=Brendan, 米可利=Wallace, 大吾=Steven, 渡=Lance, 火箭队=Team Rocket, 水舰队=Team Aqua, 熔岩队=Team Magma, 赤焰松=Maxie, 水梧桐=Archie, 小田卷博士=Prof. Birch.
- Pokémon species names: use official English names (e.g. 皮卡丘=Pikachu, 烈空坐=Rayquaza, 固拉多=Groudon, 盖欧卡=Kyogre, 木守宫=Treecko, 火稚鸡=Torchic, 水跃鱼=Mudkip, 大尾狸=Zigzagoon... translate any species name to its official English name).
- Pokédex entries: write in the crisp Pokédex style ("It ..." / "Its ...", ~2 sentences).
- Trainer speech: keep personality (e.g. a rapper says "yo", verbal tics like 的说 can become a quirky tic or be dropped naturally).
- Keep it short enough for a GBA textbox: aim ≤ ~90 characters per \p page when possible.
