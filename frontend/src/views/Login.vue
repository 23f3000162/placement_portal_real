<template>
    <div class="auth-page">
        <div class="auth-card">
            <div class="auth-header">
                <p class="eyebrow">Placement Portal</p>
                <h1>Login</h1>
                <p class="subtitle">Enter your account details.</p>
            </div>

            <div class="form-group">
                <label>Email</label>
                <input type="email" v-model="email" placeholder="Enter email" />
            </div>

            <div class="form-group">
                <label>Password</label>
                <input type="password" v-model="password" placeholder="Enter your password" />
            </div>

            <button class="primary-btn" @click="LoginUser">Login</button>
            <button class="secondary-btn" @click="$router.push('/register')">Go to Register</button>
        </div>
    </div>
</template>

<script>
import axios from "axios"

export default {

    data() {
        return {
            email: "",
            password: ""
        }
    },

    methods: {

        async LoginUser() {

            try {

                const response = await axios.post(
                    "http://127.0.0.1:5000/login",
                    {
                        email: this.email,
                        password: this.password
                    }
                )

                localStorage.setItem(
                    "token",
                    response.data.token
                )
                localStorage.setItem(
                    "role",
                    response.data.role
                )

                if (response.data.role === "student") {

                    this.$router.push(
                        "/student-dashboard"
                    )

                }
                else if(response.data.role === "company"){
                    this.$router.push("/company-dashboard")
                }
                else if (response.data.role === "admin") {
                    this.$router.push("/admin-dashboard")
                } 


            }

            catch (error) {

                console.log(error)

                alert(
                    error.response.data.message
                )

            }

        }

    }

}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  padding: 28px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.auth-header {
  margin-bottom: 20px;
}

.eyebrow {
  margin: 0 0 6px;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #6b7280;
}

h1 {
  margin: 0;
  font-size: 1.6rem;
}

.subtitle {
  margin: 8px 0 0;
  color: #6b7280;
}

.form-group {
  margin-bottom: 14px;
}

label {
  display: block;
  margin-bottom: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
}

input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 1rem;
  outline: none;
  background: #fff;
}

input:focus {
  border-color: #6366f1;
}

button {
  width: 100%;
  border: none;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.primary-btn {
  margin-top: 8px;
  background: #111827;
  color: #fff;
}

.secondary-btn {
  margin-top: 10px;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}
</style>
