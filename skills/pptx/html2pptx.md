# HTML 转 PowerPoint 指南

使用 `html2pptx.js` 库将 HTML 幻灯片转换为 PowerPoint 演示文稿，实现精确定位。

## 目录

1. [创建 HTML 幻灯片](#创建-html-幻灯片)
2. [使用 html2pptx 库](#使用-html2pptx-库)
3. [使用 PptxGenJS](#使用-pptxgenjs)

---

## 创建 HTML 幻灯片

每个 HTML 幻灯片必须包含正确的 body 尺寸：

### 布局尺寸

- **16:9**（默认）：`width: 720pt; height: 405pt`
- **4:3**：`width: 720pt; height: 540pt`
- **16:10**：`width: 720pt; height: 450pt`

### 支持的元素

- `<p>`、`<h1>`-`<h6>` - 带样式的文本
- `<ul>`、`<ol>` - 列表（禁止使用手动项目符号 •、-、*）
- `<b>`、`<strong>` - 粗体文本（行内格式）
- `<i>`、`<em>` - 斜体文本（行内格式）
- `<u>` - 下划线文本（行内格式）
- `<span>` - 带 CSS 样式的行内格式（粗体、斜体、下划线、颜色）
- `<br>` - 换行符
- 带背景/边框的 `<div>` - 转换为形状
- `<img>` - 图片
- `class="placeholder"` - 图表预留空间（返回 `{ id, x, y, w, h }`）

### 关键文本规则

**所有文本必须放在 `<p>`、`<h1>`-`<h6>`、`<ul>` 或 `<ol>` 标签内：**
- ✅ 正确：`<div><p>文本内容</p></div>`
- ❌ 错误：`<div>文本内容</div>` - **文本将不会出现在 PowerPoint 中**
- ❌ 错误：`<span>文本</span>` - **文本将不会出现在 PowerPoint 中**
- `<div>` 或 `<span>` 中没有文本标签包裹的文本将被静默忽略

**禁止使用手动项目符号（•、-、*等）** - 请使用 `<ul>` 或 `<ol>` 列表代替

**只能使用通用的网页安全字体：**
- ✅ 网页安全字体：`Arial`、`Helvetica`、`Times New Roman`、`Georgia`、`Courier New`、`Verdana`、`Tahoma`、`Trebuchet MS`、`Impact`、`Comic Sans MS`
- ❌ 错误：`'Segoe UI'`、`'SF Pro'`、`'Roboto'`、自定义字体 - **可能导致渲染问题**

### 样式设置

- 在 body 上使用 `display: flex` 以防止外边距折叠破坏溢出验证
- 使用 `margin` 控制间距（padding 包含在尺寸内）
- 行内格式：使用 `<b>`、`<i>`、`<u>` 标签或带 CSS 样式的 `<span>`
  - `<span>` 支持：`font-weight: bold`、`font-style: italic`、`text-decoration: underline`、`color: #rrggbb`
  - `<span>` 不支持：`margin`、`padding`（PowerPoint 文本运行中不支持）
  - 示例：`<span style="font-weight: bold; color: #667eea;">粗体蓝色文本</span>`
- Flexbox 布局有效 - 位置根据渲染布局计算
- CSS 中使用带 `#` 前缀的十六进制颜色
- **文本对齐**：需要时使用 CSS `text-align`（`center`、`right` 等）作为 PptxGenJS 文本格式的提示，以处理文本长度略有偏差的情况

### 形状样式（仅限 DIV 元素）

**重要：背景、边框和阴影只能用于 `<div>` 元素，不能用于文本元素（`<p>`、`<h1>`-`<h6>`、`<ul>`、`<ol>`）**

- **背景**：仅 `<div>` 元素的 CSS `background` 或 `background-color`
  - 示例：`<div style="background: #f0f0f0;">` - 创建带背景的形状
- **边框**：`<div>` 元素的 CSS `border` 转换为 PowerPoint 形状边框
  - 支持统一边框：`border: 2px solid #333333`
  - 支持部分边框：`border-left`、`border-right`、`border-top`、`border-bottom`（渲染为线条形状）
  - 示例：`<div style="border-left: 8pt solid #E76F51;">`
- **圆角**：`<div>` 元素的 CSS `border-radius` 用于圆角
  - `border-radius: 50%` 或更高创建圆形
  - 小于 50% 的百分比相对于形状的较小尺寸计算
  - 支持 px 和 pt 单位（例如 `border-radius: 8pt;`、`border-radius: 12px;`）
  - 示例：100x200px 的框上 `<div style="border-radius: 25%;">` = 100px 的 25% = 25px 圆角半径
- **阴影**：`<div>` 元素的 CSS `box-shadow` 转换为 PowerPoint 阴影
  - 仅支持外部阴影（内部阴影被忽略以防止损坏）
  - 示例：`<div style="box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.3);">`
  - 注意：PowerPoint 不支持内部/内嵌阴影，将被跳过

### 图标和渐变

- **关键：禁止使用 CSS 渐变（`linear-gradient`、`radial-gradient`）** - 它们无法转换为 PowerPoint
- **必须先使用 Sharp 创建渐变/图标 PNG，然后在 HTML 中引用**
- 渐变：将 SVG 光栅化为 PNG 背景图片
- 图标：将 react-icons SVG 光栅化为 PNG 图片
- 所有视觉效果必须在 HTML 渲染之前预渲染为光栅图像

**使用 Sharp 光栅化图标：**

```javascript
const React = require('react');
const ReactDOMServer = require('react-dom/server');
const sharp = require('sharp');
const { FaHome } = require('react-icons/fa');

async function rasterizeIconPng(IconComponent, color, size = "256", filename) {
  const svgString = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color: `#${color}`, size: size })
  );

  // 使用 Sharp 将 SVG 转换为 PNG
  await sharp(Buffer.from(svgString))
    .png()
    .toFile(filename);

  return filename;
}

// 用法：在 HTML 中使用前先光栅化图标
const iconPath = await rasterizeIconPng(FaHome, "4472c4", "256", "home-icon.png");
// 然后在 HTML 中引用：<img src="home-icon.png" style="width: 40pt; height: 40pt;">
```

**使用 Sharp 光栅化渐变：**

```javascript
const sharp = require('sharp');

async function createGradientBackground(filename) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="562.5">
    <defs>
      <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#COLOR1"/>
        <stop offset="100%" style="stop-color:#COLOR2"/>
      </linearGradient>
    </defs>
    <rect width="100%" height="100%" fill="url(#g)"/>
  </svg>`;

  await sharp(Buffer.from(svg))
    .png()
    .toFile(filename);

  return filename;
}

// 用法：在 HTML 之前创建渐变背景
const bgPath = await createGradientBackground("gradient-bg.png");
// 然后在 HTML 中：<body style="background-image: url('gradient-bg.png');">
```

### 示例

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #ffffff; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #f5f5f5; font-family: Arial, sans-serif;
  display: flex;
}
.content { margin: 30pt; padding: 40pt; background: #ffffff; border-radius: 8pt; }
h1 { color: #2d3748; font-size: 32pt; }
.box {
  background: #70ad47; padding: 20pt; border: 3px solid #5a8f37;
  border-radius: 12pt; box-shadow: 3px 3px 10px rgba(0, 0, 0, 0.25);
}
</style>
</head>
<body>
<div class="content">
  <h1>食谱标题</h1>
  <ul>
    <li><b>项目：</b>描述</li>
  </ul>
  <p>文本包含 <b>粗体</b>、<i>斜体</i>、<u>下划线</u>。</p>
  <div id="chart" class="placeholder" style="width: 350pt; height: 200pt;"></div>

  <!-- 文本必须在 <p> 标签内 -->
  <div class="box">
    <p>5</p>
  </div>
</div>
</body>
</html>
```

## 使用 html2pptx 库

### 依赖项

以下库已全局安装，可直接使用：
- `pptxgenjs`
- `playwright`
- `sharp`

### 基本用法

```javascript
const pptxgen = require('pptxgenjs');
const html2pptx = require('./html2pptx');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_16x9';  // 必须与 HTML body 尺寸匹配

const { slide, placeholders } = await html2pptx('slide1.html', pptx);

// 将图表添加到占位符区域
if (placeholders.length > 0) {
    slide.addChart(pptx.charts.LINE, chartData, placeholders[0]);
}

await pptx.writeFile('output.pptx');
```

### API 参考

#### 函数签名
```javascript
await html2pptx(htmlFile, pres, options)
```

#### 参数
- `htmlFile`（字符串）：HTML 文件路径（绝对或相对路径）
- `pres`（pptxgen）：已设置布局的 PptxGenJS 演示文稿实例
- `options`（对象，可选）：
  - `tmpDir`（字符串）：生成文件的临时目录（默认：`process.env.TMPDIR || '/tmp'`）
  - `slide`（对象）：要复用的现有幻灯片（默认：创建新幻灯片）

#### 返回值
```javascript
{
    slide: pptxgenSlide,           // 创建/更新的幻灯片
    placeholders: [                 // 占位符位置数组
        { id: string, x: number, y: number, w: number, h: number },
        ...
    ]
}
```

### 验证

该库会自动验证并收集所有错误后再抛出：

1. **HTML 尺寸必须与演示文稿布局匹配** - 报告尺寸不匹配
2. **内容不能溢出 body** - 报告溢出的精确测量值
3. **CSS 渐变** - 报告不支持的渐变用法
4. **文本元素样式** - 报告文本元素上的背景/边框/阴影（仅允许用于 div）

**所有验证错误会一次性收集并报告**，让您可以一次修复所有问题，而不是逐个修复。

### 使用占位符

```javascript
const { slide, placeholders } = await html2pptx('slide.html', pptx);

// 使用第一个占位符
slide.addChart(pptx.charts.BAR, data, placeholders[0]);

// 按 ID 查找
const chartArea = placeholders.find(p => p.id === 'chart-area');
slide.addChart(pptx.charts.LINE, data, chartArea);
```

### 完整示例

```javascript
const pptxgen = require('pptxgenjs');
const html2pptx = require('./html2pptx');

async function createPresentation() {
    const pptx = new pptxgen();
    pptx.layout = 'LAYOUT_16x9';
    pptx.author = '您的姓名';
    pptx.title = '我的演示文稿';

    // 幻灯片 1：标题
    const { slide: slide1 } = await html2pptx('slides/title.html', pptx);

    // 幻灯片 2：带图表的内容
    const { slide: slide2, placeholders } = await html2pptx('slides/data.html', pptx);

    const chartData = [{
        name: '销售额',
        labels: ['第一季度', '第二季度', '第三季度', '第四季度'],
        values: [4500, 5500, 6200, 7100]
    }];

    slide2.addChart(pptx.charts.BAR, chartData, {
        ...placeholders[0],
        showTitle: true,
        title: '季度销售额',
        showCatAxisTitle: true,
        catAxisTitle: '季度',
        showValAxisTitle: true,
        valAxisTitle: '销售额（千元）'
    });

    // 保存
    await pptx.writeFile({ fileName: 'presentation.pptx' });
    console.log('演示文稿创建成功！');
}

createPresentation().catch(console.error);
```

## 使用 PptxGenJS

使用 `html2pptx` 将 HTML 转换为幻灯片后，您将使用 PptxGenJS 添加图表、图片和其他动态内容。

### ⚠️ 关键规则

#### 颜色
- **在 PptxGenJS 中使用十六进制颜色时禁止使用 `#` 前缀** - 会导致文件损坏
- ✅ 正确：`color: "FF0000"`、`fill: { color: "0066CC" }`
- ❌ 错误：`color: "#FF0000"`（会破坏文档）

### 添加图片

始终根据实际图片尺寸计算宽高比：

```javascript
// 获取图片尺寸：identify image.png | grep -o '[0-9]* x [0-9]*'
const imgWidth = 1860, imgHeight = 1519;  // 来自实际文件
const aspectRatio = imgWidth / imgHeight;

const h = 3;  // 最大高度
const w = h * aspectRatio;
const x = (10 - w) / 2;  // 在 16:9 幻灯片上居中

slide.addImage({ path: "chart.png", x, y: 1.5, w, h });
```

### 添加文本

```javascript
// 带格式的富文本
slide.addText([
    { text: "粗体 ", options: { bold: true } },
    { text: "斜体 ", options: { italic: true } },
    { text: "普通" }
], {
    x: 1, y: 2, w: 8, h: 1
});
```

### 添加形状

```javascript
// 矩形
slide.addShape(pptx.shapes.RECTANGLE, {
    x: 1, y: 1, w: 3, h: 2,
    fill: { color: "4472C4" },
    line: { color: "000000", width: 2 }
});

// 圆形
slide.addShape(pptx.shapes.OVAL, {
    x: 5, y: 1, w: 2, h: 2,
    fill: { color: "ED7D31" }
});

// 圆角矩形
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 1, y: 4, w: 3, h: 1.5,
    fill: { color: "70AD47" },
    rectRadius: 0.2
});
```

### 添加图表

**大多数图表必需**：使用 `catAxisTitle`（类别）和 `valAxisTitle`（数值）设置坐标轴标签。

**图表数据格式：**
- 简单条形图/折线图使用**包含所有标签的单个系列**
- 每个系列创建单独的图例条目
- labels 数组定义 X 轴值

**时间序列数据 - 选择正确的粒度：**
- **< 30 天**：使用日粒度（例如 "10-01"、"10-02"）- 避免月度聚合导致单点图表
- **30-365 天**：使用月粒度（例如 "2024-01"、"2024-02"）
- **> 365 天**：使用年粒度（例如 "2023"、"2024"）
- **验证**：只有 1 个数据点的图表可能表示该时间段的聚合方式不正确

```javascript
const { slide, placeholders } = await html2pptx('slide.html', pptx);

// 正确：包含所有标签的单个系列
slide.addChart(pptx.charts.BAR, [{
    name: "2024年销售额",
    labels: ["第一季度", "第二季度", "第三季度", "第四季度"],
    values: [4500, 5500, 6200, 7100]
}], {
    ...placeholders[0],  // 使用占位符位置
    barDir: 'col',       // 'col' = 垂直条形，'bar' = 水平条形
    showTitle: true,
    title: '季度销售额',
    showLegend: false,   // 单系列不需要图例
    // 必需的坐标轴标签
    showCatAxisTitle: true,
    catAxisTitle: '季度',
    showValAxisTitle: true,
    valAxisTitle: '销售额（千元）',
    // 可选：控制缩放（根据数据范围调整最小值以获得更好的可视化效果）
    valAxisMaxVal: 8000,
    valAxisMinVal: 0,  // 计数/金额使用 0；对于聚集数据（例如 4500-7100），考虑从接近最小值开始
    valAxisMajorUnit: 2000,  // 控制 Y 轴标签间距以防止拥挤
    catAxisLabelRotate: 45,  // 如果拥挤则旋转标签
    dataLabelPosition: 'outEnd',
    dataLabelColor: '000000',
    // 单系列图表使用单色
    chartColors: ["4472C4"]  // 所有条形相同颜色
});
```

#### 散点图

**重要**：散点图数据格式不同寻常 - 第一个系列包含 X 轴值，后续系列包含 Y 值：

```javascript
// 准备数据
const data1 = [{ x: 10, y: 20 }, { x: 15, y: 25 }, { x: 20, y: 30 }];
const data2 = [{ x: 12, y: 18 }, { x: 18, y: 22 }];

const allXValues = [...data1.map(d => d.x), ...data2.map(d => d.x)];

slide.addChart(pptx.charts.SCATTER, [
    { name: 'X轴', values: allXValues },  // 第一个系列 = X 值
    { name: '系列 1', values: data1.map(d => d.y) },  // 仅 Y 值
    { name: '系列 2', values: data2.map(d => d.y) }   // 仅 Y 值
], {
    x: 1, y: 1, w: 8, h: 4,
    lineSize: 0,  // 0 = 无连接线
    lineDataSymbol: 'circle',
    lineDataSymbolSize: 6,
    showCatAxisTitle: true,
    catAxisTitle: 'X 轴',
    showValAxisTitle: true,
    valAxisTitle: 'Y 轴',
    chartColors: ["4472C4", "ED7D31"]
});
```

#### 折线图

```javascript
slide.addChart(pptx.charts.LINE, [{
    name: "温度",
    labels: ["一月", "二月", "三月", "四月"],
    values: [32, 35, 42, 55]
}], {
    x: 1, y: 1, w: 8, h: 4,
    lineSize: 4,
    lineSmooth: true,
    // 必需的坐标轴标签
    showCatAxisTitle: true,
    catAxisTitle: '月份',
    showValAxisTitle: true,
    valAxisTitle: '温度（°F）',
    // 可选：Y 轴范围（根据数据范围设置最小值以获得更好的可视化效果）
    valAxisMinVal: 0,     // 用于从 0 开始的范围（计数、百分比等）
    valAxisMaxVal: 60,
    valAxisMajorUnit: 20,  // 控制 Y 轴标签间距以防止拥挤（例如 10、20、25）
    // valAxisMinVal: 30,  // 推荐：对于聚集在某范围内的数据（例如 32-55 或评分 3-5），从接近最小值开始以显示变化
    // 可选：图表颜色
    chartColors: ["4472C4", "ED7D31", "A5A5A5"]
});
```

#### 饼图（不需要坐标轴标签）

**关键**：饼图需要**单个数据系列**，所有类别在 `labels` 数组中，对应值在 `values` 数组中。

```javascript
slide.addChart(pptx.charts.PIE, [{
    name: "市场份额",
    labels: ["产品 A", "产品 B", "其他"],  // 所有类别在一个数组中
    values: [35, 45, 20]  // 所有值在一个数组中
}], {
    x: 2, y: 1, w: 6, h: 4,
    showPercent: true,
    showLegend: true,
    legendPos: 'r',  // 右侧
    chartColors: ["4472C4", "ED7D31", "A5A5A5"]
});
```

#### 多数据系列

```javascript
slide.addChart(pptx.charts.LINE, [
    {
        name: "产品 A",
        labels: ["第一季度", "第二季度", "第三季度", "第四季度"],
        values: [10, 20, 30, 40]
    },
    {
        name: "产品 B",
        labels: ["第一季度", "第二季度", "第三季度", "第四季度"],
        values: [15, 25, 20, 35]
    }
], {
    x: 1, y: 1, w: 8, h: 4,
    showCatAxisTitle: true,
    catAxisTitle: '季度',
    showValAxisTitle: true,
    valAxisTitle: '收入（百万元）'
});
```

### 图表颜色

**关键**：使用十六进制颜色时**不要**加 `#` 前缀 - 加了会导致文件损坏。

**使图表颜色与您选择的设计调色板一致**，确保数据可视化有足够的对比度和区分度。调整颜色以实现：
- 相邻系列之间有强烈对比
- 在幻灯片背景上可读
- 可访问性（避免仅使用红绿组合）

```javascript
// 示例：海洋风格调色板的图表颜色（调整对比度）
const chartColors = ["16A085", "FF6B9D", "2C3E50", "F39C12", "9B59B6"];

// 单系列图表：所有条形/点使用一种颜色
slide.addChart(pptx.charts.BAR, [{
    name: "销售额",
    labels: ["第一季度", "第二季度", "第三季度", "第四季度"],
    values: [4500, 5500, 6200, 7100]
}], {
    ...placeholders[0],
    chartColors: ["16A085"],  // 所有条形相同颜色
    showLegend: false
});

// 多系列图表：每个系列不同颜色
slide.addChart(pptx.charts.LINE, [
    { name: "产品 A", labels: ["第一季度", "第二季度", "第三季度"], values: [10, 20, 30] },
    { name: "产品 B", labels: ["第一季度", "第二季度", "第三季度"], values: [15, 25, 20] }
], {
    ...placeholders[0],
    chartColors: ["16A085", "FF6B9D"]  // 每个系列一种颜色
});
```

### 添加表格

表格可以使用基本或高级格式添加：

#### 基本表格

```javascript
slide.addTable([
    ["表头 1", "表头 2", "表头 3"],
    ["第 1 行，第 1 列", "第 1 行，第 2 列", "第 1 行，第 3 列"],
    ["第 2 行，第 1 列", "第 2 行，第 2 列", "第 2 行，第 3 列"]
], {
    x: 0.5,
    y: 1,
    w: 9,
    h: 3,
    border: { pt: 1, color: "999999" },
    fill: { color: "F1F1F1" }
});
```

#### 自定义格式表格

```javascript
const tableData = [
    // 自定义样式的表头行
    [
        { text: "产品", options: { fill: { color: "4472C4" }, color: "FFFFFF", bold: true } },
        { text: "收入", options: { fill: { color: "4472C4" }, color: "FFFFFF", bold: true } },
        { text: "增长", options: { fill: { color: "4472C4" }, color: "FFFFFF", bold: true } }
    ],
    // 数据行
    ["产品 A", "5000万元", "+15%"],
    ["产品 B", "3500万元", "+22%"],
    ["产品 C", "2800万元", "+8%"]
];

slide.addTable(tableData, {
    x: 1,
    y: 1.5,
    w: 8,
    h: 3,
    colW: [3, 2.5, 2.5],  // 列宽
    rowH: [0.5, 0.6, 0.6, 0.6],  // 行高
    border: { pt: 1, color: "CCCCCC" },
    align: "center",
    valign: "middle",
    fontSize: 14
});
```

#### 合并单元格的表格

```javascript
const mergedTableData = [
    [
        { text: "第一季度业绩", options: { colspan: 3, fill: { color: "4472C4" }, color: "FFFFFF", bold: true } }
    ],
    ["产品", "销售额", "市场份额"],
    ["产品 A", "2500万元", "35%"],
    ["产品 B", "1800万元", "25%"]
];

slide.addTable(mergedTableData, {
    x: 1,
    y: 1,
    w: 8,
    h: 2.5,
    colW: [3, 2.5, 2.5],
    border: { pt: 1, color: "DDDDDD" }
});
```

### 表格选项

常用表格选项：
- `x, y, w, h` - 位置和尺寸
- `colW` - 列宽数组（英寸）
- `rowH` - 行高数组（英寸）
- `border` - 边框样式：`{ pt: 1, color: "999999" }`
- `fill` - 背景颜色（不带 # 前缀）
- `align` - 文本对齐："left"、"center"、"right"
- `valign` - 垂直对齐："top"、"middle"、"bottom"
- `fontSize` - 文本大小
- `autoPage` - 内容溢出时自动创建新幻灯片
