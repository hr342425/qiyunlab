<script setup>
import PageBanner from '../components/PageBanner.vue'
import TrialApplication from './ContactView.vue'

const products = [
  { tag: '基础平台', name: 'OpenLab', fullName: '高性能 CAE 仿真云平台', text: '栖云科技核心技术底座，承载底层高性能仿真算法能力，支撑科学计算与多学科工业仿真，为大规模复杂工况分析提供算力和算法基础。' },
  { tag: '数字孪生', name: 'nuVision', fullName: 'GIS+BIM 数字孪生平台轻量化系统', text: '无需改动原有业务系统，即可提升大场景模型加载速度和渲染性能，支持多用户并发并完整保留原有业务功能，降低客户端硬件门槛。' },
  { tag: '数智交通', name: 'CONQUEST', fullName: '大体积混凝土浇筑施工实时计算工具', text: '模拟混凝土水化温度场、应力场及材料应变演化，开展开裂风险分析，为施工现场质量评估与优化管控提供依据。' },
  { tag: '数智交通', name: 'Triass', fullName: '共生型桥梁结构安全计算平台', text: '面向桥梁、边坡、隧道结构安全，实现应力应变监测、高精度计算、异常定位、状态推演和潜在风险预警。' },
  { tag: '数智交通', name: 'gRail', fullName: '轨道生命周期智能仿真分析系统', text: '基于第一性原理物理环境仿真，突破传统 AI 数据获取瓶颈，支持轨道伤损识别、作业优化与风险预警评估。' },
  { tag: '工业与医疗仿真', name: '多领域产品矩阵', fullName: 'fSimulator · MiP · PET 等产品线', text: '覆盖数值核聚变堆，以及流体、固体、电磁、计算光刻、先进动力电池和医疗设备图像仿真等方向。' },
]
</script>

<template>
  <PageBanner eyebrow="PRODUCTS & SOLUTIONS" title="产品与服务" description="以 OpenLab 为技术底座，构建自主可控的高性能仿真产品与行业解决方案。" />
  <section class="section">
    <div class="container product-list">
      <article v-for="product in products" :key="product.name" class="product-card">
        <div><span class="product-tag">{{ product.tag }}</span><h2>{{ product.name }}</h2></div>
        <div class="product-detail">
          <h3>{{ product.fullName }}</h3>
          <p>{{ product.text }}</p>
          <TrialApplication v-if="product.name === 'nuVision'" trial-only />
          <span v-else class="trial-unavailable">暂未开放试用</span>
        </div>
      </article>
    </div>
  </section>
</template>
