<script setup>
defineProps({ eyebrow: String, title: String, description: String })
</script>

<template>
  <section class="page-banner">
    <div class="container">
      <p class="eyebrow">{{ eyebrow }}</p>
      <h1>{{ title }}</h1>
      <p>{{ description }}</p>
    </div>
  </section>
</template>
