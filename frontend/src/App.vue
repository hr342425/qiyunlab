<script setup>
import { ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()
const menuOpen = ref(false)
const logoUrl = `/logo.png?v=${__BUILD_ID__}`

const navItems = [
  { label: '首页', to: '/' },
  { label: '产品与服务', to: '/products' },
  { label: '客户案例', to: '/cases' },
  { label: '关于我们', to: '/about' },
  { label: '联系我们', to: '/contact' },
]

watch(() => route.path, () => {
  menuOpen.value = false
  window.scrollTo({ top: 0, behavior: 'smooth' })
})
</script>

<template>
  <div class="site-shell">
    <header class="site-header">
      <div class="container nav-wrap">
        <RouterLink class="brand" to="/" aria-label="返回首页">
          <img :src="logoUrl" alt="公司 Logo" />
          <span class="brand-name">栖云科技</span>
        </RouterLink>

        <button
          class="menu-toggle"
          type="button"
          :aria-expanded="menuOpen"
          aria-label="打开导航菜单"
          @click="menuOpen = !menuOpen"
        >
          <span></span><span></span><span></span>
        </button>

        <nav class="main-nav" :class="{ open: menuOpen }" aria-label="主导航">
          <RouterLink v-for="item in navItems" :key="item.to" :to="item.to">
            {{ item.label }}
          </RouterLink>
        </nav>
      </div>
    </header>

    <main>
      <RouterView />
    </main>

    <footer class="site-footer">
      <div class="container footer-content">
        <div class="footer-brand">
          <img :src="logoUrl" alt="公司 Logo" />
          <div>
            <strong>合肥栖云科技有限公司</strong>
            <p>先进科学计算与工业仿真软件创新企业</p>
          </div>
        </div>
        <p>© {{ new Date().getFullYear() }} 合肥栖云科技有限公司 版权所有</p>
      </div>
    </footer>
  </div>
</template>
