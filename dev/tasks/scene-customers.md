# Codex 任务单：场景客人（Scene Customers）

> 状态：草案，未执行。用户 2026-10-30 13:12 暂停了 Codex；只有用户明确说“开始/可以跑”后才能运行。
> 来源：CrazyGames 换装榜前列靠“身份 + 场景”（偶像直播、红毯明星、博主）取胜。

## 目标
在不改核心玩法的前提下，让部分客人带“身份”，并在对应试穿场景亮相时给奖励，让试穿从“看一眼”变成订单的收尾。

## 范围（只做这些）

### 1. 新增 3 个身份客人主题
在 `js/data.js` 的 `themes` 后追加（保持现有 6 个的下标不变，旧存档的 `o.person` 不能错位）：

| id | 中文 | 英文 | 偏好 pref | 推荐场景 |
|---|---|---|---|---|
| `streamer` | 直播博主 | Livestreamer | color:pink, charm:crystal, pattern:hearts | `mirror_lounge` |
| `redcarpet` | 红毯明星 | Red-carpet star | color:black, material:glitter, heel:block | `redcarpet`（新场景） |
| `bridal` | 婚纱拍摄 | Bridal shoot | color:cream, material:satin, decoration:big | `balcony` |

- 每个主题加 `scene` 字段（推荐场景 id）；现有 6 个主题也补上：date→car, tea→vanity, school→salon, wedding→balcony, everyday→car, party→mirror_lounge。
- `asset` 先复用现有客人立绘（streamer→c_pink, redcarpet→c_buns, bridal→c_bride），不新画人。
- 身份客人从第 2 章开始出现（通过 `A.Boutique.customers(s)` 的解锁逻辑），每天最多 1 位。
- I18N 中英都加：主题名、心愿句（如“今晚直播要穿，想要一双会被弹幕夸的鞋！”）、亮相台词。

### 2. 新增试穿场景 `redcarpet`
- `js/showcase.js` 的 `scenes` 加 `{id:'redcarpet',en:'Red carpet',zh:'红毯之夜',price:600,image:'scenes/scene_redcarpet'}`。
- 背景图：用 gpt-image-2 生成 1 张，风格与现有 `scene_balcony` / `scene_vanity` 一致（暖色、手绘质感、薄荷绿+糖果粉点缀），再按现有 `fixed_*` 流程出近景图。相机、地面高度必须按同一 610×620 固定机位对齐，脚贴地。
- 在新场景完成前，`redcarpet` 主题的推荐场景回退为 `mirror_lounge`，功能可先合入。

### 3. 场景亮相奖励
- 交付后进入试穿时，若当前所选场景 === 客人主题的 `scene`：
  - 本单金币 +20%（在 `scoreOrder` 结算后单独一行“场景加成”，不改星级判定）；
  - 客人说一句专属亮相台词（每个主题 1 句，中英）。
- 订单气泡里加一个小场景图标提示“推荐在 XX 亮相”；场景未解锁时显示锁和价格，不强制。
- 每单只结算一次，重进试穿不能重复领取（存 `artwork.sceneBonusClaimed`）。

### 4. 拍照卡（轻量）
- 亮相成功后，在作品集该作品上加一个“✦ 场景亮相”角标和客人台词，不生成新图片文件。

## 不做
- 不改合成/订单数值、不改星级规则、不加新货币。
- 不碰鞋/腿/脚渲染（`fitting2d.js`、`fitting-rigid.js`、`worn-body-fidelity.js`）——用户正在自己画穿鞋效果。
- 不改 `js/audio.js` 里 githack→jsDelivr 路由和对应断言。

## 硬约束
- 不覆盖：`assets/src-user-legs-20261029/*`、`qa/research-rigid/out4/flat-pink-satin-black-hires.png`、`qa/research-rigid/gen5/flat-leg-front.png`、`qa/research-rigid/gen5/flat-leg-rear.png`。
- 不删 `qa/`、`dev/codex_ledger.csv`、`dev/codex_tokens.csv`、`dev/codex_pause_until`。
- 旧存档兼容：没有 `scene` 字段、没有新主题的存档能正常加载。
- 中英文案都要；7 个目标视口布局不溢出。

## 验收
1. `find . -name '*.js' -not -path './dist/*' -exec node --check {} \;`、`node smoke-test.js`、`node qa/audio-test.js`、`node qa/pacing-test.js` 全过。
2. 新增 Node 测试 `qa/scene-customer-test.js`：
   - 旧存档（无新主题）加载后 `o.person` 指向不变；
   - 场景匹配时金币 = 基础 × 1.2（取整规则与现有一致），不匹配时不变；
   - 同一作品二次进入试穿不重复加成。
3. Chromium 截图（1336×790、390×844）：身份客人订单气泡（含场景提示）、匹配场景亮相台词、结算“场景加成”行。拼成一张验收图 `qa/contact/scene-customers-<时间>.jpg`。
4. 每个阶段写 `PROGRESS.md` 并 git commit。
