# 细粒度拆分规则

这是后续所有 SCI 流程图、框架图、机制图的硬规则。

## 原子单元

1. 方框单独算一个 SVG 单元。
2. 框内文字单独算一个 SVG 单元。
3. 框内公式单独算一个 SVG 单元。
4. 框内图标、神经网络、矩阵、车辆、服务器、盾牌、数据库等图形单独算 SVG 单元。
5. 箭头、连线、虚线框、流程线单独算 SVG 单元。
6. 只有视觉上本来连成一体、并且后期不会拆开调整的内容，才允许作为一个 SVG。

## 组合原则

- `unit_layouts/*.json` 负责记录原子单元的位置和尺寸。
- `assembled_preview_svg/*.svg` 只用于预览和检查，不作为唯一源文件。
- `ppt_ready_preview_svg/*.svg` 可以快速插入 PPT，但必须保留对应原子 SVG 和 layout。
- 任何时候不得只保留合并后的整块图而丢掉原子素材。

## 目录职责

- `01_atomic_svg/frames`：方框、区域框、虚线框。
- `01_atomic_svg/visual`：所有无文字图形。
- `01_atomic_svg/text`：所有文字标签，优先使用 outlined 版。
- `01_atomic_svg/formula`：所有公式，优先使用 outlined 版。
- `01_atomic_svg/connectors`：箭头、线、上传/广播流向线。
- `02_unit_layouts`：每个框或区域的排版 JSON。
- `03_assembled_preview_svg`：把原子素材按 layout 临时拼起来的预览。
- `05_png_preview` 和 `06_contact_sheets`：验收用。

## PPT 工作方式

如果要在 PPT 里精调，用 `01_atomic_svg` 逐个插入。

如果只想快速排版，可先插入 `03_assembled_preview_svg` 或 `04_ppt_ready_preview_svg`，确认视觉后再把需要微调的模块替换成原子单元。
