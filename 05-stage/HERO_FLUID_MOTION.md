# ✨ 首页交互式流体扭曲动效蒸馏（Hero Fluid Distortion Blueprint）
> 本模块蒸馏自秒哒应用美学黑客松**官网首页**的"交互式流体扭曲动效"——
> 即鼠标移动时背景金色光斑流动晕染的视觉效果。
> 全部经**真实浏览器操作验证** + **JS bundle 源码级逆向**（双重确认）。
---
## 一、这个动效是什么
打开秒哒官网首页，你会看到：
1. 深色科技背景上铺满**微弱的星点矩阵**（呼吸闪烁）
2. 鼠标移动时，一个**金色的光斑跟随鼠标**流动，配合 40px 大模糊形成"流体晕染"
3. 光斑扫过暗色背景 → 视觉上像**流体被鼠标搅动扭曲**
4. 首页大标题有**淡入上浮**的入场动画
这不是一个单一效果，而是 **3 层动效叠加** 营造的"流体扭曲"感。
---
## 二、三层动效源码级拆解
### 层 1：Canvas 星点矩阵（氛围底噪）
```js
// 关键逻辑（源码逆向）
const points = [];           // 星点数组
const grid = 24;             // 24px 网格间距
// 初始化：按网格铺点，每点加随机偏移/相位/大小/速度
for (r...) for (c...)
  points.push({
    px: r*24 + (Math.random()-0.5)*grid*2,   // 随机偏移打破网格感
    py: c*24 + (Math.random()-0.5)*grid*2,
    phase: Math.random()*Math.PI*2,           // 随机相位（不同步呼吸）
    sizeVar: 0.4 + Math.random()*1.8,         // 随机大小 0.4~2.2
    speed: 1.2 + Math.random()*3              // 随机速度 1.2~4.2
  });
// 动画循环（requestAnimationFrame）
function frame(){
  clearRect();
  fillStyle = 'rgba(160,160,160,0.10)';       // 极淡灰
  for (point of points){
    const wave = 0.55 + 0.25*Math.sin(time*speed + phase); // 呼吸波
    const radius = 1.8 * sizeVar * wave;      // 半径随波变化
    const alpha  = 0.1 * wave;                // 透明度随波变化
    arc(px, py, radius, 0, 2PI); fill();      // 画圆点
  }
}
```
**Canvas 配置**：`<canvas class="fixed inset-0 z-[1] pointer-events-none" aria-hidden="true">`
**性能优化**（照抄）：
- 隔帧渲染：`if (a++ % 2 != 0) return;`（只渲染一半帧，视觉无感）
- DPR 上限：`Math.min(devicePixelRatio || 1, 1.5)`
- 页面隐藏暂停：`document.hidden` 时 `cancelAnimationFrame`
### 层 2：鼠标跟随金色光斑（交互核心）
```js
// 关键逻辑（源码逆向）
<div class="fixed inset-0 z-[100] pointer-events-none overflow-hidden">
  <div ref={spot} class="absolute will-change-transform"
       style={{
         width: 300, height: 300,
         background: `radial-gradient(circle at center,
           rgba(251,191,36,0.35) 0%,      // 中心亮金
           rgba(245,158,11,0.14) 35%,     // 中段橙金
           rgba(217,160,80,0.05) 60%,     // 外圈淡金
           transparent 85%)`,              // 边缘消失
         filter: 'blur(40px)'             // 40px 大模糊 → 流体晕染
       }} />
</div>
// 鼠标跟随
window.addEventListener('mousemove', e => {
  spot.style.transform = `translate3d(${e.clientX-150}px, ${e.clientY-150}px, 0)`;
  // -150 让光斑中心对准鼠标（300/2）
}, { passive: true });
```
**核心参数**（照抄即可复刻效果）：
| 参数 | 值 | 作用 |
|---|---|---|
| 尺寸 | 300×300 px | 光斑大小 |
| 偏移 | clientX-150 | 中心对齐鼠标 |
| 模糊 | blur(40px) | 产生流体晕染（关键！）|
| 中心色 | rgba(251,191,36,0.35) | 亮金（琥珀色）|
| 中段色 | rgba(245,158,11,0.14) | 橙金 |
| 外圈色 | rgba(217,160,80,0.05) | 淡金 |
| 层级 | z-[100] 顶层 | 压过所有内容但 pointer-events-none |
| 渲染 | will-change-transform | GPU 加速 |
### 层 3：Hero 大标题入场动画
```js
// 关键逻辑（源码逆向）
title.style.opacity = '0';
title.style.transform = 'translateY(32px)';
requestAnimationFrame(() => {
  title.style.transition =
    'opacity 1.2s cubic-bezier(0.16,1,0.3,1), transform 1.2s cubic-bezier(0.16,1,0.3,1)';
  title.style.opacity = '1';
  title.style.transform = 'translateY(0)';
});
```
- **1.2 秒**、**cubic-bezier(0.16,1,0.3,1)**（缓出，先快后慢）
- 从下 32px 上浮 + 淡入
- 入场时制造"仪式感"，比默认加载高级
---
## 三、为什么"流体扭曲"感这么强（设计原理）
| 因素 | 作用 |
|---|---|
| **暗色背景**（#0a0a0a 系）| 让光斑成为唯一亮色焦点 |
| **金色光斑 + 40px 大模糊** | 边缘羽化 → 流体晕染感 |
| **实时跟随鼠标** | 像手在液体里搅动 → "扭曲"感 |
| **星点底噪** | 光斑扫过星点 → 视差流动感 |
| **高对比** | 金 vs 黑 → 视觉冲击 |
**一句话**：不是真的"扭曲"，而是「暗底 + 大模糊光斑 + 鼠标实时跟随 + 星点底噪」四者组合出的**流体错觉**。
---
## 四、复用配方（做自己的首页直接抄）
### 配方 A：标准「暗色科技 + 流体光斑」首页
```html
<!-- 1. 星点 Canvas（氛围底噪） -->
<canvas class="fixed inset-0 z-[1] pointer-events-none" aria-hidden="true"></canvas>
<!-- 2. 鼠标光斑（流体核心） -->
<div class="fixed inset-0 z-[100] pointer-events-none overflow-hidden">
  <div id="fluid-spot" class="absolute will-change-transform"
       style="width:300px;height:300px;filter:blur(40px);
              background:radial-gradient(circle at center,
                rgba(251,191,36,0.35) 0%, rgba(245,158,11,0.14) 35%,
                rgba(217,160,80,0.05) 60%, transparent 85%);"></div>
</div>
```
```js
// 鼠标跟随（核心 5 行）
const spot = document.getElementById('fluid-spot');
window.addEventListener('mousemove', e => {
  spot.style.transform = `translate3d(${e.clientX-150}px, ${e.clientY-150}px, 0)`;
}, { passive: true });
```
### 配方 B：换色系（不同主题）
| 主题 | 中心色 | 中段色 | 适合 |
|---|---|---|---|
| 金橙（原版）| rgba(251,191,36,.35) | rgba(245,158,11,.14) | 科技/赛事/奢华 |
| 青蓝 | rgba(56,189,248,.35) | rgba(14,165,233,.14) | AI/医疗/极客 |
| 霓虹紫 | rgba(192,132,252,.35) | rgba(168,85,247,.14) | 二次元/娱乐 |
| 治愈绿 | rgba(74,222,128,.35) | rgba(34,197,94,.14) | 健康/环保 |
| 极简白 | rgba(255,255,255,.25) | rgba(255,255,255,.10) | 高端留白 |
### 配方 C：性能瘦身（低端设备）
- 隔帧渲染：`if (frameCount++ % 2 != 0) return;`
- 星点减少：grid 24 → 32
- DPR 上限：1.5
- 页面隐藏时暂停 canvas
---
## 五、检查清单（照这个自查）
- [ ] 是否暗色背景（流体光斑需要高对比衬托）？
- [ ] 光斑是否 40px 以上模糊（太小没流体感）？
- [ ] 是否实时跟随鼠标（translate3d）？
- [ ] 是否 pointer-events-none（不挡按钮点击）？
- [ ] 是否 will-change-transform（GPU 加速不卡顿）？
- [ ] 是否移动端禁用/降级（触屏没有 mousemove）？
- [ ] 星点是否淡到几乎看不见（rgba 0.10，别抢焦点）？
- [ ] 是否隔帧渲染 + DPR 上限（性能）？
- [ ] 大标题是否有入场动画（淡入上浮）？
---
## 六、在黑客松作品中的应用建议
1. **首页 Hero**：直接用配方 A——秒出"高级感"，评委第一眼被抓住
2. **深色科技类**：金橙光斑是安全牌；青蓝适合 AI 主题
3. **注意**：如果作品是浅色/治愈系，别硬套——流体光斑吃暗背景
4. **别过度**：光斑 + 星点已经是完整氛围，再加粒子/动效会乱
5. **配合叙事**：光斑颜色可随产品情绪变化（悲伤→蓝、希望→金）
---
*动效经真实浏览器操作验证 + JS bundle 源码逆向（2026-09-01）。*
*配套模块：UI_AESTHETICS.md（视觉）、UX_INTERACTION.md（信息架构）、UX_INTERACTION_MOTION.md（交互动作）。*
