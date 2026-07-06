<template>
  <div class="dashboard-page">
    <AppHeader
      title="Admin Dashboard"
      subtitle="Manage placement records"
    />

    <div class="admin-shell">
      <aside class="sidebar">
        <div class="brand">
          <div class="brand-mark">A</div>
          <div>
            <p class="brand-kicker">Admin Portal</p>
            <h1>Dashboard</h1>
          </div>
        </div>

        <nav class="menu">
          <button
            v-for="item in menuItems"
            :key="item.key"
            class="menu-item"
            :class="{ active: activeTab === item.key }"
            @click="activeTab = item.key"
          >
            <span class="menu-dot"></span>
            {{ item.label }}
          </button>
        </nav>

      </aside>

      <main class="content">
        <div v-if="error" class="alert">{{ error }}</div>
        <div v-if="success" class="success-banner">{{ success }}</div>

        <section v-if="activeTab === 'overview'" class="panel">
          <div class="hero">
            <div>
              <p class="eyebrow">Overview</p>
              <h2>Placement Summary</h2>
              <p>Students, companies, drives and applications.</p>
            </div>
            <div class="hero-badge">
              <span>Portal Status</span>
              <strong>Active</strong>
              <button class="report-btn" :disabled="reportLoading" @click="downloadMonthlyReport">
                {{ reportLoading ? 'Preparing...' : 'Download Monthly Report' }}
              </button>
            </div>
          </div>

          <div class="stats-grid">
            <div class="stat-card" v-for="stat in stats" :key="stat.label">
              <span>{{ stat.label }}</span>
              <strong>{{ stat.value }}</strong>
            </div>
          </div>
        </section>

        <section v-else-if="activeTab === 'students'" class="panel">
          <p class="eyebrow">Registered Students</p>
          <h3>Student Records</h3>
          <p class="panel-text">View and manage student accounts.</p>

          <div class="search-row">
            <input v-model.trim="studentSearch" type="search" placeholder="Search students by name or email" />
          </div>

          <div class="list-grid">
            <article v-for="student in filteredStudents" :key="student.id" class="list-card">
              <div>
                <h4>{{ student.name }}</h4>
                <p>{{ student.email }}</p>
              </div>
              <div class="card-actions">
                <span class="pill" :class="student.status === 'Blocked' ? 'danger' : 'success'">
                  {{ student.status }}
                </span>
                <button class="reject-btn" :disabled="loading" @click="toggleStudentBlock(student.id)">
                  {{ student.status === 'Blocked' ? 'Activate' : 'Deactivate' }}
                </button>
              </div>
            </article>
          </div>
        </section>

        <section v-else-if="activeTab === 'companies'" class="panel">
          <p class="eyebrow">Registered Companies</p>
          <h3>Company Approvals</h3>
          <p class="panel-text">Review registered and pending companies.</p>

          <div class="search-row">
            <input v-model.trim="companySearch" type="search" placeholder="Search companies by name or email" />
          </div>

          <div class="list-grid">
            <article v-for="company in filteredCompanies" :key="company.id" class="list-card">
              <div>
                <h4>{{ company.name }}</h4>
                <p>{{ company.email }}</p>
                <p v-if="company.description">{{ company.description }}</p>
              </div>
              <div class="card-actions">
                <span class="pill" :class="company.status === 'Approved' ? 'success' : 'warning'">
                  {{ company.status }}
                </span>
                <button
                  v-if="company.status !== 'Approved'"
                  class="approve-btn"
                  :disabled="loading"
                  @click="approveCompany(company.id)"
                >
                  {{ loading ? '...' : 'Approve' }}
                </button>
                <button
                  class="reject-btn"
                  :disabled="loading"
                  @click="rejectCompany(company.id)"
                >
                  {{ company.status === 'Approved' ? 'Deactivate' : 'Reject' }}
                </button>
              </div>
            </article>
          </div>
        </section>

        <section v-else-if="activeTab === 'drives'" class="panel">
          <p class="eyebrow">Ongoing Drives</p>
          <h3>Drive Status</h3>
          <p class="panel-text">Review and approve placement drives.</p>

          <div class="list-grid">
            <article v-for="drive in drives" :key="drive.id" class="list-card">
              <div>
                <h4>{{ drive.title }}</h4>
                <p>{{ drive.company }}</p>
                <p>{{ drive.description }}</p>
                <p>{{ drive.salary }} | {{ drive.experience }} | {{ drive.location }}</p>
                <p>Starting Date: {{ drive.drive_date }}</p>
                <p>Last Date: {{ drive.application_deadline }}</p>
              </div>
              <div class="card-actions">
                <span class="pill" :class="drive.status === 'Approved' ? 'success' : 'warning'">
                  {{ drive.status }}
                </span>
                <button
                  v-if="drive.status !== 'Approved'"
                  class="approve-btn"
                  :disabled="loading"
                  @click="approveDrive(drive.id)"
                >
                  Approve
                </button>
                <button
                  v-if="drive.status !== 'Approved'"
                  class="reject-btn"
                  :disabled="loading"
                  @click="rejectDrive(drive.id)"
                >
                  Reject
                </button>
              </div>
            </article>
          </div>
        </section>

        <section v-else-if="activeTab === 'studentApplications'" class="panel">
          <p class="eyebrow">Student Applications</p>
          <h3>Application Records</h3>
          <p class="panel-text">Student applications and current status.</p>

          <div class="list-grid">
            <article v-for="application in studentApplications" :key="application.id" class="list-card">
              <div class="app-info">
                <h4>{{ application.name }}</h4>
                <p class="app-meta">{{ application.email }}</p>
                <p>{{ application.company_name }} — {{ application.drive_name }}</p>
                <p class="app-date">Applied: {{ application.created_at }}</p>
              </div>
              <div class="card-actions">
                <span class="pill" :class="application.status === 'shortlisted' ? 'success' : application.status === 'rejected' ? 'danger' : 'neutral'">
                  {{ application.status }}
                </span>
                <a
                  v-if="application.resume_url"
                  :href="resumeLink(application.resume_url)"
                  target="_blank"
                  rel="noopener"
                  class="resume-link"
                >
                  View Resume
                </a>
                <span v-else class="no-resume">No Resume</span>
              </div>
            </article>
          </div>
        </section>
      </main>
    </div>

    <AppFooter />
  </div>
</template>

<script>
import AppHeader from "../components/AppHeader.vue"
import AppFooter from "../components/AppFooter.vue"
import api from "../services/api"

export default {
  name: "admin-dashboard",
  components: {
    AppHeader,
    AppFooter
  },
  data() {
    return {
      activeTab: "overview",
      loading: false,
      reportLoading: false,
      error: "",
      success: "",
      studentSearch: "",
      companySearch: "",
      menuItems: [
        { key: "overview", label: "Overview" },
        { key: "students", label: "Registered Students" },
        { key: "companies", label: "Registered Companies" },
        { key: "drives", label: "Placement Drives" },
        { key: "studentApplications", label: "Student Applications" }
      ],
      stats: [],
      students: [],
      companies: [],
      drives: [],
      studentApplications: []
    }
  },
  computed: {
    filteredStudents() {
      const q = this.studentSearch.toLowerCase()
      if (!q) return this.students
      return this.students.filter((student) =>
        `${student.name} ${student.email}`.toLowerCase().includes(q)
      )
    },
    filteredCompanies() {
      const q = this.companySearch.toLowerCase()
      if (!q) return this.companies
      return this.companies.filter((company) =>
        `${company.name} ${company.email}`.toLowerCase().includes(q)
      )
    }
  },
  mounted() {
    this.loadDashboard()
  },
  methods: {
    async loadDashboard() {
      this.loading = true
      this.error = ""

      try {
        const [
          summaryResponse,
          studentsResponse,
          companiesResponse,
          drivesResponse,
          studentApplicationsResponse
        ] = await Promise.all([
          api.get("/admin/summary"),
          api.get("/admin/students"),
          api.get("/admin/companies"),
          api.get("/admin/drives"),
          api.get("/admin/student-applications")
        ])

        this.stats = summaryResponse.data.stats || []
        this.students = studentsResponse.data || []
        this.companies = (companiesResponse.data || []).map((company) => ({
          id: company.id,
          name: company.name,
          email: company.email || "",
          description: company.description || "",
          status: company.status || "Pending"
        }))
        this.drives = (drivesResponse.data || []).map((drive) => ({
          id: drive.id,
          title: drive.name,
          company: drive.company,
          description: drive.description || "",
          salary: drive.salary || "",
          experience: drive.experience || "",
          drive_date: drive.drive_date || "",
          application_deadline: drive.application_deadline || "",
          location: drive.location || "",
          status: drive.status || "Live"
        }))
        this.studentApplications = (studentApplicationsResponse.data || []).map((application) => ({
          id: application.id,
          name: application.student_name,
          email: application.student_email || "",
          company_name: application.company_name,
          drive_name: application.drive_name,
          status: application.status,
          created_at: application.created_at || "",
          resume_url: application.resume_url || ""
        }))
      } catch (error) {
        this.error = error?.response?.data?.message || "Dashboard data load nahi ho paya."
      } finally {
        this.loading = false
      }
    },
    async toggleStudentBlock(studentId) {
      this.loading = true
      this.error = ""
      try {
        await api.post(`/admin/block-student/${studentId}`)
        await this.loadDashboard()
      } catch (error) {
        this.error = error?.response?.data?.message || "Student status update nahi ho paya."
      } finally {
        this.loading = false
      }
    },
    async approveCompany(companyId) {
      this.loading = true
      this.error = ""
      try {
        await api.post(`/admin/approve-company/${companyId}`)
        await this.loadDashboard()
      } catch (error) {
        this.error = error?.response?.data?.message || "Company approve nahi ho payi."
      } finally {
        this.loading = false
      }
    },
    async rejectCompany(companyId) {
      this.loading = true
      this.error = ""
      try {
        await api.post(`/admin/reject-company/${companyId}`)
        await this.loadDashboard()
      } catch (error) {
        this.error = error?.response?.data?.message || "Company status update nahi ho paya."
      } finally {
        this.loading = false
      }
    },
    resumeLink(url) {
      if (!url) return "#"
      if (url.startsWith("http")) return url
      return `${api.defaults.baseURL}${url}`
    },
    async approveDrive(driveId) {
      this.loading = true
      this.error = ""
      this.success = ""
      try {
        const response = await api.post(`/admin/approve-drive/${driveId}`)
        await this.loadDashboard()
        this.showMailResult(response.data)
      } catch (error) {
        this.error = error?.response?.data?.message || "Drive approve nahi ho payi."
      } finally {
        this.loading = false
      }
    },
    async rejectDrive(driveId) {
      this.loading = true
      this.error = ""
      try {
        await api.post(`/admin/reject-drive/${driveId}`)
        await this.loadDashboard()
      } catch (error) {
        this.error = error?.response?.data?.message || "Drive reject nahi ho payi."
      } finally {
        this.loading = false
      }
    },
    async downloadMonthlyReport() {
      this.reportLoading = true
      this.error = ""

      try {
        const response = await api.get("/admin/monthly-report/download", {
          responseType: "blob"
        })

        const blob = new Blob([response.data], {
          type: response.headers["content-type"] || "text/html"
        })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement("a")
        const disposition = response.headers["content-disposition"] || ""
        const match = disposition.match(/filename="?([^"]+)"?/i)

        link.href = url
        link.download = match ? match[1] : "monthly_report.html"
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)

        if (response.headers["x-mail-sent"] === "false") {
          this.error = `Report downloaded, but email failed: ${response.headers["x-mail-error"] || "mail error"}`
        } else {
          this.success = "Monthly report downloaded and emailed to admin."
        }
      } catch (error) {
        this.error = error?.response?.data?.message || "Monthly report download nahi ho paya."
      } finally {
        this.reportLoading = false
      }
    },
    showMailResult(data) {
      if (data?.mail_sent === false) {
        this.error = `${data.message || "Action complete, but email failed"}: ${data.mail_error || "mail error"}`
      } else if (data?.message) {
        this.success = data.message
      }
    }
  }
}
</script>

<style scoped>
.dashboard-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.admin-shell {
  flex: 1;
  display: grid;
  grid-template-columns: 260px 1fr;
}

.sidebar {
  padding: 20px;
  background: #111827;
  color: #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 20px;
  border-right: 1px solid #374151;
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
  background: #3b82f6;
  color: #fff;
  font-weight: 700;
}

.brand-kicker, .eyebrow {
  margin: 0;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #9ca3af;
}

.brand h1 {
  margin: 2px 0 0;
  font-size: 1.1rem;
  color: #fff;
}

.menu {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.menu-item {
  width: 100%;
  border: none;
  background: transparent;
  color: #d1d5db;
  padding: 10px 12px;
  border-radius: 8px;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.menu-item:hover {
  background: #1f2937;
  color: #fff;
}

.menu-item.active {
  background: #1d4ed8;
  color: #fff;
}

.menu-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.content {
  padding: 24px;
  min-width: 0;
}

.alert {
  margin-bottom: 14px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  font-weight: 600;
}

.success-banner {
  margin-bottom: 14px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  font-weight: 600;
}

.panel {
  padding: 20px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.hero h2, .panel h3 {
  margin: 4px 0 8px;
  color: #111827;
}

.hero p, .panel-text {
  margin: 0;
  color: #6b7280;
}

.hero-badge {
  padding: 14px 18px;
  border-radius: 8px;
  background: #111827;
  color: #fff;
}

.hero-badge span {
  font-size: 0.8rem;
  color: #9ca3af;
  display: block;
}

.report-btn {
  margin-top: 12px;
  width: 100%;
  border: none;
  border-radius: 8px;
  padding: 10px 12px;
  background: #ffffff;
  color: #111827;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.report-btn:hover:enabled {
  transform: translateY(-1px);
  opacity: 0.96;
}

.report-btn:disabled {
  cursor: wait;
  opacity: 0.7;
}

.stats-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.stat-card {
  padding: 16px;
  border-radius: 8px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.stat-card span {
  display: block;
  color: #6b7280;
  font-size: 0.88rem;
  margin-bottom: 6px;
}

.stat-card strong {
  font-size: 1.8rem;
  color: #111827;
}

.list-grid {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.search-row {
  margin-top: 16px;
}

.search-row input {
  width: 100%;
  max-width: 420px;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.95rem;
  outline: none;
}

.search-row input:focus {
  border-color: #2563eb;
}

.list-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
}

.list-card h4 {
  margin: 0 0 4px;
  color: #111827;
}

.list-card p {
  margin: 0;
  color: #6b7280;
  font-size: 0.9rem;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.pill {
  padding: 4px 10px;
  border-radius: 20px;
  background: #dbeafe;
  color: #1e40af;
  font-size: 0.8rem;
  font-weight: 600;
}

.pill.warning {
  background: #fef3c7;
  color: #92400e;
}

.pill.success {
  background: #d1fae5;
  color: #065f46;
}

.pill.danger {
  background: #fee2e2;
  color: #991b1b;
}

.pill.neutral {
  background: #dbeafe;
  color: #1e40af;
}

.approve-btn {
  border: 1px solid #16a34a;
  background: #f0fdf4;
  color: #166534;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
}

.approve-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.reject-btn {
  border: 1px solid #dc2626;
  background: #fef2f2;
  color: #991b1b;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
}

.reject-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.resume-link {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 6px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 0.82rem;
  font-weight: 600;
  text-decoration: none;
  border: 1px solid #bfdbfe;
}

.no-resume {
  font-size: 0.82rem;
  color: #9ca3af;
}

.app-meta {
  color: #3b82f6;
  font-size: 0.88rem;
}

.app-date {
  color: #9ca3af;
  font-size: 0.82rem;
}

@media (max-width: 900px) {
  .admin-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: none;
    border-bottom: 1px solid #374151;
  }

  .list-card {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
