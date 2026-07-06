<template>
  <footer class="app-footer">
    <div class="footer-inner">
      <p>© {{ year }} Placement Portal. All rights reserved.</p>
    </div>
  </footer>
</template>

<script>
export default {
  name: "app-footer",
  computed: {
    year() {
      return new Date().getFullYear()
    }
  }
}
</script>

<style scoped>
.app-footer {
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  background: #fff;
  text-align: center;
  color: #6b7280;
  font-size: 0.9rem;
}

.footer-inner p {
  margin: 0;
}
</style>
