<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const logoUrl = `/logo.png?v=${__BUILD_ID__}`
const currentSlide = ref(0)
let slideTimer

const expoSlides = [
  { image: `/expo-1.png?v=${__BUILD_ID__}`, tag: 'CHINA—ASEAN EXPO', meta: '2025 · 南宁', title: '栖云科技亮相中国—东盟博览会', caption: '现场交流，共话科学计算产业创新' },
  { image: `/expo-2.png?v=${__BUILD_ID__}`, tag: 'CHINA—ASEAN EXPO', meta: '2025 · 南宁', title: '栖云科技亮相中国—东盟博览会', caption: '面向行业嘉宾展示自主仿真技术成果' },
  { image: `/expo-3.png?v=${__BUILD_ID__}`, tag: 'CHINA—ASEAN EXPO', meta: '2025 · 南宁', title: '栖云科技亮相中国—东盟博览会', caption: '产品现场演示与深度技术交流' },
  { image: `/expo-4.png?v=${__BUILD_ID__}`, tag: 'CHINA—ASEAN EXPO', meta: '2025 · 南宁', title: '栖云科技亮相中国—东盟博览会', caption: '聚焦工程场景，呈现实时计算能力' },
  { image: `/expo-5.png?v=${__BUILD_ID__}`, tag: 'CHINA—ASEAN EXPO', meta: '2025 · 南宁', title: '栖云科技亮相中国—东盟博览会', caption: '先进仿真成果获得现场广泛关注' },
  { image: `/expo-6.png?v=${__BUILD_ID__}`, tag: 'CHINA—ASEAN EXPO', meta: '2025 · 南宁', title: '栖云科技亮相中国—东盟博览会', caption: 'CONQUEST 产品现场交流展示' },
]

const slide = computed(() => expoSlides[currentSlide.value])

function goToSlide(index) {
  currentSlide.value = (index + expoSlides.length) % expoSlides.length
  restartAutoplay()
}

function restartAutoplay() {
  clearInterval(slideTimer)
  slideTimer = setInterval(() => {
    currentSlide.value = (currentSlide.value + 1) % expoSlides.length
  }, 5500)
}

onMounted(restartAutoplay)
onBeforeUnmount(() => clearInterval(slideTimer))
</script>

<template>
  <div class="home-page">
  <section class="hero">
    <div class="container hero-grid">
      <div>
        <p class="eyebrow">ADVANCED SCIENTIFIC COMPUTING</p>
        <h1>定义未来工业<br />仿真范式</h1>
        <p class="hero-copy">深耕高性能计算与工业仿真软件研发，面向高端制造、交通基建、生命健康等行业，提供自主可控的仿真软件与解决方案。</p>
        <div class="button-row">
          <RouterLink class="btn" to="/products">了解产品与服务</RouterLink>
          <RouterLink class="btn secondary" to="/contact">联系我们</RouterLink>
        </div>
      </div>
      <div class="hero-logo"><img :src="logoUrl" alt="公司 Logo" /></div>
    </div>
  </section>
  <section class="section company-news">
    <div class="container news-heading">
      <div><p class="eyebrow">COMPANY NEWS</p><h2>栖云动态</h2></div>
      <div><span class="news-date">{{ slide.meta }}</span><p>{{ slide.title }}</p></div>
    </div>

    <div class="container expo-carousel" @mouseenter="clearInterval(slideTimer)" @mouseleave="restartAutoplay">
      <div class="carousel-stage">
        <button class="carousel-side previous" type="button" aria-label="上一张" @click="goToSlide(currentSlide - 1)">
          <img :src="expoSlides[(currentSlide - 1 + expoSlides.length) % expoSlides.length].image" alt="上一张展会照片" />
        </button>

        <div class="carousel-main">
          <Transition name="news-slide" mode="out-in">
            <img :key="slide.image" :src="slide.image" :alt="slide.caption" />
          </Transition>
          <div class="carousel-overlay">
            <span>{{ slide.tag }}</span>
            <h3>{{ slide.caption }}</h3>
          </div>
        </div>

        <button class="carousel-side next" type="button" aria-label="下一张" @click="goToSlide(currentSlide + 1)">
          <img :src="expoSlides[(currentSlide + 1) % expoSlides.length].image" alt="下一张展会照片" />
        </button>
      </div>

      <div class="carousel-controls">
        <div class="carousel-count"><strong>0{{ currentSlide + 1 }}</strong><span>/ 0{{ expoSlides.length }}</span></div>
        <div class="carousel-dots">
          <button v-for="(_, index) in expoSlides" :key="index" type="button" :class="{ active: index === currentSlide }" :aria-label="`查看第 ${index + 1} 张照片`" @click="goToSlide(index)"><span></span></button>
        </div>
        <div class="carousel-arrows"><button type="button" aria-label="上一张" @click="goToSlide(currentSlide - 1)">←</button><button type="button" aria-label="下一张" @click="goToSlide(currentSlide + 1)">→</button></div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="container">
      <div class="section-heading">
        <p class="eyebrow">ABOUT QIYUN</p>
        <h2>科研成果走向产业应用的核心载体</h2>
        <p>栖云科技是合肥市庐阳区先进科学计算与工业软件研究院旗下核心产业化运营主体，联动祥云汇智科技与北京中心，打通科研攻关、成果孵化和产业落地全链条。</p>
      </div>
      <div class="cards">
        <article class="card"><p class="card-number">01 / 技术底座</p><h3>数据 · 算法 · 算力</h3><p>融合先进计算机技术、数学建模、计算方法与数据分析，解决科学和工程领域的关键问题。</p></article>
        <article class="card"><p class="card-number">02 / 核心团队</p><h3>科学家与产业专家</h3><p>团队成员来自中科院物理所、中国科学技术大学及国内大型信息化企业。</p></article>
        <article class="card"><p class="card-number">03 / 业务领域</p><h3>四大产业方向</h3><p>业务覆盖科学计算、工业软件、数智交通与生命健康四大领域。</p></article>
      </div>
    </div>
  </section>
  </div>
</template>
