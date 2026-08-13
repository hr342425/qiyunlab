<script setup>
import PageBanner from '../components/PageBanner.vue'

const version = __BUILD_ID__
const scenes = [
  { image: `/1.webp?v=${version}`, title: 'BIM 与实景融合', text: '将工程 BIM 模型与现场实景底图叠加呈现，集中展示建设进度、工程量与关键节点信息，让复杂施工状态更直观、更易掌握。' },
  { image: `/2.webp?v=${version}`, title: '全线建设态势总览', text: '基于 GIS 空间底座汇聚沿线标段、投资、进度及预警信息，形成覆盖项目全局的数字化视图，为建设管理与协同决策提供支撑。' },
  { image: `/3.webp?v=${version}`, title: '无人机巡检协同', text: '融合无人机巡检任务、实时画面与现场环境数据，辅助巡检过程管理、异常发现和任务追踪，提升大范围工程现场的精细化管控能力。' },
]

const videoUrl = `/plyh.mp4?v=${version}`
</script>

<template>
  <PageBanner eyebrow="CUSTOMER STORIES" title="客户案例" description="以先进计算与数字孪生技术连接真实工程场景，让复杂项目看得见、管得住、协同更高效。" />

  <section class="section case-feature">
    <div class="container">
      <div class="case-heading">
        <div><p class="eyebrow">FEATURED PROJECT</p><h2>平陆运河数字孪生应用</h2></div>
        <p>栖云科技将 nuVision 的 GIS+BIM 融合与大场景轻量化能力应用于平陆运河项目，面向建设管理、智慧工地、综合监控、安全管控与应急指挥等场景，构建统一、直观的数字化工程视图。</p>
      </div>
      <div class="case-video-wrap">
        <video :src="videoUrl" controls preload="metadata" playsinline aria-label="栖云科技在平陆运河项目中的应用视频">您的浏览器暂不支持视频播放。</video>
        <div class="video-caption"><span>PROJECT VIDEO</span><p>平陆运河项目应用展示 · 02:48</p></div>
      </div>
    </div>
  </section>

  <section class="section muted scene-section">
    <div class="container">
      <div class="section-heading"><p class="eyebrow">APPLICATION SCENARIOS</p><h2>nuVision 场景化应用</h2><p>轻量化承载大规模 GIS、BIM 与实景数据，在保留既有业务能力的同时，让多源工程信息流畅呈现、高效协同。</p></div>
      <div class="scene-grid">
        <figure v-for="scene in scenes" :key="scene.title" class="scene-card">
          <div class="scene-image"><img :src="scene.image" :alt="scene.title" loading="lazy" /></div>
          <figcaption><h3>{{ scene.title }}</h3><p>{{ scene.text }}</p></figcaption>
        </figure>
      </div>
    </div>
  </section>

  <section class="section case-value">
    <div class="container case-value-grid">
      <div><p class="eyebrow">PROJECT VALUE</p><h2>让大型工程的数字化管理更轻、更快、更直观</h2></div>
      <div class="value-list">
        <article><strong>01</strong><div><h3>多源数据融合</h3><p>统一承载 GIS、BIM、航拍模型与现场业务数据，减少信息孤岛。</p></div></article>
        <article><strong>02</strong><div><h3>大场景轻量呈现</h3><p>降低复杂模型对客户端硬件的依赖，改善模型加载和交互体验。</p></div></article>
        <article><strong>03</strong><div><h3>建设过程协同</h3><p>以空间场景串联进度、巡检和预警信息，辅助跨部门协同管理。</p></div></article>
      </div>
    </div>
  </section>
</template>
