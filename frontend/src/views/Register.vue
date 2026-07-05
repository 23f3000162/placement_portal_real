<template>
    <div class="auth-page">
        <div class="auth-card">
            <div class="auth-header">
                <p class="eyebrow">Placement Portal</p>
                <h1>Register</h1>
                <p class="subtitle">Create a student or company account.</p>
            </div>

            <div class="form-group">
                <label>Name</label>
                <input type="text" v-model="username" placeholder="Enter your name" />
            </div>

            <div class="form-group">
                <label>Email</label>
                <input type="email" v-model="email" placeholder="Enter your email" />
            </div>

            <div class="form-group">
                <label>Password</label>
                <input type="password" v-model="password" placeholder="Enter your password" />
            </div>

            <button class="primary-btn" @click="UserRegister('student')">
             Register as student
            </button>
            <button class="primary-btn company-btn" @click="UserRegister('company')">
                Register as company
            </button>
            <button class="secondary-btn" @click="$router.push('/login')">
                Already registered? Login
            </button>
        </div>

    </div>
</template>

<script>

import axios from "axios"

export default {

    data() {

        return {

            username: "",
            email: "",
            password: ""

        }

    },

    methods: {

        async UserRegister(role) {

            try {

                const response = await axios.post(

                    "http://127.0.0.1:5000/register",

                    {
                        username: this.username,
                        email: this.email,
                        password: this.password,
                        role: role
                    }

                )

                alert(response.data.message)

                console.log(response.data)
                this.$router.push("/login")

            }

            catch (error) {

                console.log(error)

                alert(error.response.data.message)

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
  max-width: 460px;
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

.company-btn {
  margin-top: 10px;
  background: #374151;
}

.secondary-btn {
  margin-top: 10px;
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}
</style>
