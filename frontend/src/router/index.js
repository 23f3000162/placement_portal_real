import { createRouter, createWebHistory } from "vue-router"

import Login from "../views/Login.vue"
import Register from "../views/Register.vue"
import AdminDashboard from "../views/Admin.vue"
import StudentDashboard from "../views/Student.vue"
import CompanyDashboard from "../views/Company.vue"

const routes = [
    {
        path: "/",
        redirect: "/login"
    },
    {
        path: "/login",
        component: Login
    },
    {
        path: "/register",
        component: Register
    },
    {
        path: "/admin-dashboard",
        component: AdminDashboard,
        meta: { requiresAuth: true, roles: ["admin"] }
    },
    {
        path: "/student-dashboard",
        component: StudentDashboard,
        meta: { requiresAuth: true, roles: ["student"] }
    },
    {
        path: "/company-dashboard",
        component: CompanyDashboard,
        meta: { requiresAuth: true, roles: ["company"] }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to) => {
    const token = localStorage.getItem("token")
    const role = localStorage.getItem("role")

    if (to.meta.requiresAuth && !token) {
        return "/login"
    }

    if (to.meta.roles && !to.meta.roles.includes(role)) {
        return "/login"
    }

    return true
})

export default router
