<template>
  <div class="py-20 text-center text-base-content/60">
    <div class="flex flex-col items-center gap-3">
      <span class="loading loading-spinner loading-lg"></span>
      <span v-if="text">{{ text }}</span>
      <span v-else>Ładowanie...</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: '',
  },
})
</script>
