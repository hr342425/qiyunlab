<script setup>
defineProps({ items: Array })
</script>

<template>
  <section class="section">
    <div class="container cards">
      <article v-for="(item, index) in items" :key="item.title" class="card">
        <p class="card-number">0{{ index + 1 }}</p>
        <h3>{{ item.title }}</h3>
        <p>{{ item.text }}</p>
      </article>
    </div>
  </section>
</template>
