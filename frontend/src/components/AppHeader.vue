<template>
  <header class="app-header">
    <div class="header-inner">
      <div class="brand">
        <div class="brand-mark">P</div>
        <div>
          <p class="brand-kicker">Portal</p>
          <h1>{{ title }}</h1>
          <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
        </div>
      </div>

      <button class="logout-btn" @click="logout">Logout</button>
    </div>
  </header>
</template>

<script>
export default {
  name: "app-header",
  props: {
    title: {
      type: String,
      default: "Dashboard"
    },
    subtitle: {
      type: String,
      default: ""
    }
  },
  methods: {
    logout() {
      localStorage.removeItem("token")
      localStorage.removeItem("role")
      this.$router.push("/login")
    }
  }
}
</script>

<style scoped>
.app-header {
  padding: 14px 20px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #111827;
  color: #fff;
  font-weight: 700;
}

.brand-kicker {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #6b7280;
}

h1 {
  margin: 0;
  font-size: 1.1rem;
  color: #111827;
}

.subtitle {
  margin: 2px 0 0;
  font-size: 0.85rem;
  color: #6b7280;
}

.logout-btn {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 8px 16px;
  background: #111827;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
</style>
