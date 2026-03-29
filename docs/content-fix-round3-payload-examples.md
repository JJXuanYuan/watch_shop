# Round 3 Full Payload Examples

These are review-oriented full `PUT /api/v1/admin/products/{id}` payload examples for the 5 core products.

Important:

- the execution script still fetches the current admin product detail first
- then it merges only the rich fields from [`scripts/content_patch_round3_payloads.json`](../scripts/content_patch_round3_payloads.json)
- therefore the script dry-run output is the final review source before production execution

The examples below are the intended full payload shape, aligned with the current catalog baseline.

## Product 1: Chronos S1 智能腕表 (`id=1`)

```json
{
  "name": "Chronos S1 智能腕表",
  "short_title": "Chronos S1",
  "subtitle": "全天候心率监测与双频 GPS",
  "category_id": 1,
  "price": 1999.0,
  "original_price": 2299.0,
  "stock": 120,
  "sales": 58,
  "status": "on_sale",
  "cover_image": "/media/products/chronos-s1-cover.jpg",
  "hero_image": "/media/products/chronos-s1-hero.jpg",
  "banner_images": [
    "/media/products/chronos-s1-1.jpg",
    "/media/products/chronos-s1-2.jpg"
  ],
  "selling_points": ["双频 GPS", "全天候心率监测", "NFC 快捷支付"],
  "material": "钛金属表壳",
  "crystal": "双面蓝宝石玻璃",
  "movement_or_function": "多功能智能模组",
  "power_reserve": "14 天综合续航",
  "water_resistance": "50 米防水",
  "strap_material": "氟橡胶表带",
  "story_blocks": [
    {
      "label": "佩戴体验",
      "title": "全天候佩戴与健康记录",
      "subtitle": "更轻，更适合日常通勤",
      "content": "以轻量化表壳结合全天候传感器，兼顾日常佩戴、睡眠追踪和轻运动记录。",
      "image": "/media/products/chronos-s1-hero.jpg"
    },
    {
      "label": "功能亮点",
      "title": "双频 GPS 与 NFC 让通勤和运动更顺手",
      "subtitle": "覆盖出行与训练两类高频场景",
      "content": "在城市跑步、通勤支付和日常提醒之间切换时，核心功能保持直接可用，减少频繁打开手机的依赖。",
      "image": "/media/products/chronos-s1-cover.jpg"
    }
  ],
  "detail_content": "旗舰级智能腕表，支持运动记录、睡眠分析和 NFC 便捷支付。",
  "sort_order": 1,
  "is_featured": true
}
```

## Product 2: Pulse Mini 轻量智能表 (`id=2`)

```json
{
  "name": "Pulse Mini 轻量智能表",
  "short_title": "Pulse Mini",
  "subtitle": "轻薄机身，适合日常通勤佩戴",
  "category_id": 1,
  "price": 999.0,
  "original_price": 1299.0,
  "stock": 240,
  "sales": 132,
  "status": "on_sale",
  "cover_image": "/media/products/pulse-mini-cover.jpg",
  "hero_image": "/media/products/pulse-mini-hero.jpg",
  "banner_images": [
    "/media/products/pulse-mini-1.jpg",
    "/media/products/pulse-mini-2.jpg"
  ],
  "selling_points": ["轻量机身", "10 天续航", "基础健康监测"],
  "material": "铝合金表壳",
  "crystal": "强化镜面玻璃",
  "movement_or_function": "日常健康监测模组",
  "power_reserve": "10 天综合续航",
  "water_resistance": "50 米防水",
  "strap_material": "硅胶表带",
  "story_blocks": [
    {
      "label": "轻量设计",
      "title": "更适合通勤佩戴的体积控制",
      "subtitle": "长时间佩戴更轻松",
      "content": "通过更紧凑的壳体比例和更轻的材质组合，减轻日常连续佩戴时的手腕负担。",
      "image": "/media/products/pulse-mini-hero.jpg"
    },
    {
      "label": "日常续航",
      "title": "保留高频提醒与监测功能，同时拉长续航",
      "subtitle": "更适合通勤与轻运动用户",
      "content": "把消息提醒、步数、心率等常用能力集中在稳定的续航表现上，降低频繁充电带来的打断感。",
      "image": "/media/products/pulse-mini-cover.jpg"
    }
  ],
  "detail_content": "主打轻盈与长续航，适合日常健康监测和基础运动记录。",
  "sort_order": 2,
  "is_featured": false
}
```

## Product 3: Voyager M 自动机械表 (`id=3`)

```json
{
  "name": "Voyager M 自动机械表",
  "short_title": "Voyager M",
  "subtitle": "蓝宝石镜面与 80 小时动储",
  "category_id": 2,
  "price": 4599.0,
  "original_price": 4999.0,
  "stock": 36,
  "sales": 21,
  "status": "on_sale",
  "cover_image": "/media/products/voyager-m-cover.jpg",
  "hero_image": "/media/products/voyager-m-hero.jpg",
  "banner_images": [
    "/media/products/voyager-m-1.jpg",
    "/media/products/voyager-m-2.jpg"
  ],
  "selling_points": ["80 小时动储", "蓝宝石镜面", "316L 精钢表壳"],
  "material": "316L 精钢表壳",
  "crystal": "双面蓝宝石玻璃",
  "movement_or_function": "自动机械机芯",
  "power_reserve": "80 小时动力储备",
  "water_resistance": "100 米防水",
  "strap_material": "精钢表链",
  "story_blocks": [
    {
      "label": "机芯表现",
      "title": "长动储让日常佩戴节奏更从容",
      "subtitle": "减少频繁上链带来的打断",
      "content": "80 小时动力储备更适合轮换佩戴场景，即便短时间摘下后再次佩戴，也能保持更稳定的状态。",
      "image": "/media/products/voyager-m-hero.jpg"
    },
    {
      "label": "材质细节",
      "title": "镜面和表壳光泽控制更偏正式佩戴",
      "subtitle": "兼顾通勤与正装场景",
      "content": "蓝宝石镜面与精钢打磨共同强化了盘面的清晰度和表壳边界感，使整体观感更利落。",
      "image": "/media/products/voyager-m-cover.jpg"
    }
  ],
  "detail_content": "经典三针自动机械款，兼顾通勤与正式场合佩戴需求。",
  "sort_order": 1,
  "is_featured": true
}
```

## Product 4: Navigator Pro GMT (`id=4`)

```json
{
  "name": "Navigator Pro GMT",
  "short_title": "Navigator Pro GMT",
  "subtitle": "双时区表盘设计",
  "category_id": 2,
  "price": 6899.0,
  "original_price": null,
  "stock": 18,
  "sales": 9,
  "status": "on_sale",
  "cover_image": "/media/products/navigator-pro-cover.jpg",
  "hero_image": "/media/products/navigator-pro-hero.jpg",
  "banner_images": [
    "/media/products/navigator-pro-1.jpg",
    "/media/products/navigator-pro-2.jpg"
  ],
  "selling_points": ["GMT 双时区", "72 小时动储", "夜光盘面"],
  "material": "316L 精钢表壳",
  "crystal": "蓝宝石玻璃",
  "movement_or_function": "GMT 自动机械机芯",
  "power_reserve": "72 小时动力储备",
  "water_resistance": "100 米防水",
  "strap_material": "真皮表带",
  "story_blocks": [
    {
      "label": "差旅场景",
      "title": "跨时区读取更直接",
      "subtitle": "落地后的时间切换更省心",
      "content": "GMT 指针与 24 小时刻度可以把本地时间和异地时间同时保留在盘面上，适合差旅与跨区沟通场景。",
      "image": "/media/products/navigator-pro-hero.jpg"
    },
    {
      "label": "夜间识读",
      "title": "夜光盘面强化航班和酒店切换时的可读性",
      "subtitle": "面向夜航与候机场景",
      "content": "在弱光环境下，夜光时标与清晰的时区信息能更快完成读时，减少频繁掏手机确认时间的动作。",
      "image": "/media/products/navigator-pro-cover.jpg"
    }
  ],
  "detail_content": "适合差旅和跨时区出行的 GMT 表款，兼具质感与功能性。",
  "sort_order": 2,
  "is_featured": false
}
```

## Product 5: Saffiano 真皮表带 (`id=5`)

```json
{
  "name": "Saffiano 真皮表带",
  "short_title": "Saffiano 表带",
  "subtitle": "适配 20mm 通用表耳",
  "category_id": 3,
  "price": 299.0,
  "original_price": 399.0,
  "stock": 320,
  "sales": 207,
  "status": "on_sale",
  "cover_image": "/media/products/saffiano-strap-cover.jpg",
  "hero_image": "/media/products/saffiano-strap-hero.jpg",
  "banner_images": [
    "/media/products/saffiano-strap-1.jpg",
    "/media/products/saffiano-strap-2.jpg"
  ],
  "selling_points": ["快拆结构", "20mm 通用表耳", "Saffiano 纹理"],
  "material": "头层牛皮",
  "crystal": "不适用",
  "movement_or_function": "快拆更换结构",
  "power_reserve": "不适用",
  "water_resistance": "生活防泼溅",
  "strap_material": "Saffiano 真皮",
  "story_blocks": [
    {
      "label": "风格延展",
      "title": "快速切换不同佩戴风格",
      "subtitle": "让同一只表覆盖更多场景",
      "content": "通过更换表带，就能把偏正式、偏通勤或更轻松的穿搭方向快速切换出来，提升单只腕表的搭配弹性。",
      "image": "/media/products/saffiano-strap-hero.jpg"
    },
    {
      "label": "结构细节",
      "title": "快拆结构降低更换门槛",
      "subtitle": "适合日常轮换和备用表带",
      "content": "20mm 通用表耳与快拆结构组合，适合日常自己更换，不需要额外工具也能完成大部分场景下的表带切换。",
      "image": "/media/products/saffiano-strap-cover.jpg"
    }
  ],
  "detail_content": "快拆结构，适配多种表壳，适合作为表带替换与风格扩展。",
  "sort_order": 1,
  "is_featured": false
}
```
