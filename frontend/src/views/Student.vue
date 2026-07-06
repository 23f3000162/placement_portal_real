<template>
  <div class="student-dashboard-page">
    <AppHeader
      title="Student Dashboard"
      subtitle="Placement details and applications"
    />

    <div class="student-shell">
      <aside class="sidebar">
        <div class="sidebar-top">
          <div class="brand">
            <div class="brand-mark">S</div>
            <div>
              <p class="brand-kicker">Student Portal</p>
              <h1>Dashboard</h1>
            </div>
          </div>

          <p class="sidebar-note">
            Student placement portal
          </p>
        </div>

        <nav class="menu">
          <button
            v-for="item in menuItems"
            :key="item.key"
            class="menu-item"
            :class="{ active: activeTab === item.key }"
            @click="activeTab = item.key"
          >
            <span class="menu-icon">{{ item.icon }}</span>
            <span>
              <strong>{{ item.label }}</strong>
              <small>{{ item.subtext }}</small>
            </span>
          </button>
        </nav>

      </aside>

      <main class="content">
        <div v-if="error" class="error-banner">
          {{ error }}
        </div>
        <div v-if="success" class="success-banner">
          {{ success }}
        </div>

        <section v-if="activeTab === 'overview'" class="panel overview-panel">
          <div class="hero">
            <div>
              <p class="eyebrow">Overview</p>
              <h2>Welcome {{ studentName }}</h2>
              <p class="panel-text">Your placement summary.</p>
            </div>

            <div class="hero-badge">
              <span>Department</span>
              <strong>{{ department }}</strong>
              <small>{{ profileForm.rollNo }}</small>
            </div>
          </div>

          <div class="stats-grid">
            <article class="stat-card accent">
              <span>Applied Drives</span>
              <strong>{{ totalAppliedDrives }}</strong>
              <small>Total applications</small>
            </article>
            <article class="stat-card">
              <span>Shortlisted</span>
              <strong>{{ shortlistedCount }}</strong>
              <small>Shortlisted applications</small>
            </article>
            <article class="stat-card">
              <span>Companies</span>
              <strong>{{ companies.length }}</strong>
              <small>Available companies</small>
            </article>
          </div>

          <div class="feature-grid">
            <button class="feature-card" @click="activeTab = 'organizations'">
              <span>Companies</span>
              <strong>Open Drives</strong>
              <small>View and apply for drives.</small>
            </button>
            <button class="feature-card" @click="activeTab = 'history'">
              <span>History</span>
              <strong>Application Status</strong>
              <small>View application results.</small>
            </button>
          </div>
        </section>

        <section v-else-if="activeTab === 'organizations'" class="panel">
          <div class="section-head">
            <div>
              <p class="eyebrow">Companies & Drives</p>
              <h3>Available Drives</h3>
            </div>
            <button class="back-btn" @click="activeTab = 'overview'">Back</button>
          </div>

          <div class="search-row">
            <input
              v-model.trim="searchText"
              type="search"
              placeholder="Search companies or drives"
              @keyup.enter="loadDashboard"
            />
            <button class="back-btn" @click="loadDashboard">Search</button>
          </div>

          <div class="companies-with-drives">
            <div v-for="(company, companyIndex) in companies" :key="company.name" class="company-section">
              <div class="company-header" @click="toggleCompany(companyIndex)">
                <div>
                  <h4>{{ company.name }}</h4>
                  <p>{{ company.drives.length }} open drives</p>
                </div>
                <span class="toggle-icon">{{ expandedCompanies[companyIndex] ? '▼' : '▶' }}</span>
              </div>

              <div v-if="expandedCompanies[companyIndex]" class="company-details">
                <p class="panel-text">{{ company.description }}</p>

                <div class="drives-section">
                  <div v-if="company.drives.length === 0" class="no-drives">
                    <p>No open drives available</p>
                  </div>
                  <div v-for="drive in company.drives" :key="drive.id" class="drive-card">
                    <div class="drive-info">
                      <h5>{{ drive.title }}</h5>
                      <p class="drive-meta">{{ drive.salary }} | {{ drive.experience }} | {{ drive.location }}</p>
                      <p class="drive-date">Starting Date: {{ drive.drive_date }}</p>
                      <p class="drive-date">Last Date: {{ drive.application_deadline }}</p>
                    </div>
                    <button
                      class="apply-btn"
                      :disabled="drive.applied || loading"
                      @click="openApplyModal(drive.id, company.name)"
                    >
                      {{ drive.applied ? '✓ Applied' : 'Apply' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section v-else-if="activeTab === 'history'" class="panel history-panel">
          <div class="card-head">
            <div>
              <p class="eyebrow">Application History</p>
              <h3>Application Records</h3>
            </div>
            <div class="history-actions">
              <button class="back-btn" :disabled="exportLoading" @click="exportApplications">
                {{ exportLoading ? 'Exporting...' : 'Export CSV' }}
              </button>
              <a
                v-if="exportDownloadUrl"
                class="download-link"
                :href="exportDownloadUrl"
                target="_blank"
                rel="noopener"
              >
                Download CSV
              </a>
              <button class="back-btn" @click="activeTab = 'overview'">Back</button>
            </div>
          </div>
          <p v-if="exportStatus" class="export-status">{{ exportStatus }}</p>

          <div class="history-grid">
            <div class="history-meta-card">
              <span>Student Name</span>
              <strong>{{ studentName }}</strong>
            </div>
            <div class="history-meta-card">
              <span>Department</span>
              <strong>{{ department }}</strong>
            </div>
            <div class="history-meta-card">
              <span>Shortlisted</span>
              <strong>{{ shortlistedCount }}</strong>
            </div>
          </div>

          <div class="history-list">
            <article v-for="(row, index) in historyRows" :key="row.jobTitle + index" class="history-row">
              <div>
                <span class="history-index">0{{ index + 1 }}</span>
                <h4>{{ row.jobTitle }}</h4>
                <p>{{ row.interview }} interview</p>
              </div>
              <div class="history-result" :class="historyClass(row.result)">
                {{ row.result }}
              </div>
              <p class="history-remark">{{ row.remark }}</p>
            </article>
          </div>
        </section>

        <section v-else class="panel profile-panel">
          <div class="card-head">
            <div>
              <p class="eyebrow">Profile</p>
              <h3>Edit your profile</h3>
            </div>
            <button class="back-btn" @click="activeTab = 'overview'">Back</button>
          </div>

          <div class="profile-grid">
            <label>
              <span>Name</span>
              <input v-model="profileForm.name" type="text" />
            </label>
            <label>
              <span>Department</span>
              <input v-model="profileForm.department" type="text" />
            </label>
            <label>
              <span>CGPA</span>
              <input v-model="profileForm.cgpa" type="number" step="0.01" min="0" max="10" />
            </label>
            <label>
              <span>Email</span>
              <input v-model="profileForm.email" type="email" />
            </label>
            <label>
              <span>Roll No.</span>
              <input v-model="profileForm.rollNo" type="text" />
            </label>
          </div>

          <div class="action-row">
            <button class="apply-btn" @click="saveProfile">Save Changes</button>
            <button class="ghost-btn" @click="activeTab = 'overview'">Cancel</button>
          </div>
        </section>
      </main>
    </div>

    <!-- resume popup -->
    <div v-if="applyModal.show" class="modal-overlay" @click.self="closeApplyModal">
      <div class="modal-box">
        <div class="modal-head">
          <div>
            <p class="eyebrow">Apply Now</p>
            <h3>{{ applyModal.companyName }}</h3>
          </div>
          <button class="modal-close" @click="closeApplyModal">✕</button>
        </div>

        <div class="upload-area">
          <label class="upload-label">
            <span>Resume Upload (Optional)</span>
            <div class="file-drop" @click="$refs.resumeInput.click()">
              <span v-if="!applyModal.file">📄 Click to select PDF / DOC</span>
              <span v-else class="file-selected">✓ {{ applyModal.file.name }}</span>
            </div>
            <input
              ref="resumeInput"
              type="file"
              accept=".pdf,.doc,.docx"
              style="display:none"
              @change="applyModal.file = $event.target.files[0] || null"
            />
          </label>
        </div>

        <div v-if="error" class="error-banner" style="margin-top:12px">{{ error }}</div>

        <div class="modal-actions">
          <button class="apply-btn" :disabled="loading" @click="submitApply">
            {{ loading ? 'Applying...' : 'Submit Application' }}
          </button>
          <button class="ghost-btn" @click="closeApplyModal">Cancel</button>
        </div>
      </div>
    </div>

    <AppFooter />
  </div>
</template>

<script>
import AppHeader from "../components/AppHeader.vue"
import AppFooter from "../components/AppFooter.vue"
import api from "../services/api"

export default {
  name: "student-dashboard",
  components: {
    AppHeader,
    AppFooter
  },
  data() {
    return {
      activeTab: "overview",
      selectedCompanyIndex: 0,
      resumeFile: null,
      loading: false,
      error: "",
      success: "",
      exportLoading: false,
      exportStatus: "",
      exportDownloadUrl: "",
      exportPollTimer: null,
      expandedCompanies: {},
      searchText: "",
      applyModal: {
        show: false,
        driveId: null,
        companyName: '',
        file: null
      },
      menuItems: [
        { key: "overview", label: "Overview", subtext: "Placement summary", icon: "01" },
        { key: "organizations", label: "Companies", subtext: "Available drives", icon: "02" },
        { key: "history", label: "History", subtext: "Application status", icon: "03" },
        { key: "profile", label: "Profile", subtext: "Student details", icon: "04" }
      ],
      studentName: "Pqrst",
      department: "Computer Science",
      profileForm: {
        name: "Pqrst",
        department: "Computer Science",
        email: "pqrst@example.com",
        rollNo: "N/A",
        cgpa: ""
      },
      companies: [],
      historyRows: []
    }
  },
  mounted() {
    this.loadDashboard()
  },
  computed: {
    selectedCompany() {
      return (
        this.companies[this.selectedCompanyIndex] || {
          name: "No company selected",
          description: "",
          industry: "",
          status: "",
          drives: []
        }
      )
    },
    shortlistedCount() {
      return this.historyRows.filter((row) => row.result === "Short Listed").length
    },
    totalAppliedDrives() {
      let count = 0
      this.companies.forEach((company) => {
        count += company.drives.filter((drive) => drive.applied).length
      })
      return count
    }
  },
  methods: {
    async loadDashboard() {
      this.loading = true
      this.error = ""

      try {
        console.log("Loading summary...")
        const summaryResponse = await api.get("/student/summary")
        console.log("Summary loaded:", summaryResponse.data)

        console.log("Loading companies...")
        const companiesResponse = await api.get("/student/companies", {
          params: { q: this.searchText }
        })
        console.log("Companies loaded:", companiesResponse.data)

        console.log("Loading history...")
        const historyResponse = await api.get("/student/history")
        console.log("History loaded:", historyResponse.data)

        const summary = summaryResponse.data || {}

        this.studentName = summary.student?.name || summary.profile?.name || this.studentName
        this.department = summary.department || this.department
        this.profileForm.name = summary.profile?.name || this.profileForm.name
        this.profileForm.department = summary.department || this.profileForm.department
        this.profileForm.email = summary.profile?.email || this.profileForm.email
        this.profileForm.cgpa = summary.profile?.cgpa ?? this.profileForm.cgpa

        this.companies = (companiesResponse.data || []).map((company) => {
          return {
            name: company.name,
            industry: company.description || "",
            status: company.status || "Open",
            description: company.description || "",
            drives: (company.drives || []).map((drive) => ({
              id: drive.id,
              title: drive.title,
              salary: drive.salary || "",
              experience: drive.experience || "",
              drive_date: drive.drive_date || "",
              application_deadline: drive.application_deadline || "",
              location: drive.location || "",
              applied: Boolean(drive.applied)
            }))
          }
        })

        // close all company details
        const expanded = {}
        this.companies.forEach((_, index) => {
          expanded[index] = false
        })
        this.expandedCompanies = expanded

        this.historyRows = historyResponse.data || []
      } catch (error) {
        this.error = error?.response?.data?.message || "Dashboard data load nahi ho paya."
      } finally {
        this.loading = false
      }
    },
    async exportApplications() {
      this.exportLoading = true
      this.exportStatus = "CSV export started..."
      this.exportDownloadUrl = ""
      this.error = ""
      this.success = ""

      try {
        const response = await api.post("/student/export-csv")
        const taskId = response.data?.task_id
        if (!taskId) {
          this.exportLoading = false
          this.error = "Export task start nahi ho paya."
          return
        }
        this.pollExportStatus(taskId)
      } catch (error) {
        this.exportLoading = false
        this.error = error?.response?.data?.message || "CSV export start nahi ho paya."
      }
    },
    async pollExportStatus(taskId) {
      window.clearTimeout(this.exportPollTimer)
      try {
        const response = await api.get(`/student/task-status/${taskId}`)
        const data = response.data || {}
        if (data.state === "SUCCESS") {
          this.exportLoading = false
          this.exportStatus = `CSV ready. Total applications: ${data.total_applications || 0}`
          if (data.mail_sent === false) {
            this.error = `CSV ready, but email failed: ${data.mail_error || "mail error"}`
          } else {
            this.success = "CSV export ready. Email alert bhi bhej diya gaya hai."
          }
          this.exportDownloadUrl = data.download_url
            ? `${api.defaults.baseURL}${data.download_url}`
            : ""
          return
        }
        if (data.state === "FAILURE" || data.state === "FAILED") {
          this.exportLoading = false
          this.exportStatus = ""
          this.error = data.status || data.message || "CSV export fail ho gaya."
          return
        }
        this.exportStatus = data.status || "Export in progress..."
        this.exportPollTimer = window.setTimeout(() => this.pollExportStatus(taskId), 1500)
      } catch (error) {
        this.exportLoading = false
        this.error = error?.response?.data?.message || "Export status check nahi ho paya."
      }
    },
    openApplyModal(driveId, companyName) {
      this.applyModal = { show: true, driveId, companyName, file: null }
      this.error = ''
    },
    closeApplyModal() {
      this.applyModal = { show: false, driveId: null, companyName: '', file: null }
      this.error = ''
    },
    async submitApply() {
      this.loading = true
      this.error = ''
      try {
        const formData = new FormData()
        if (this.applyModal.file) {
          formData.append('resume', this.applyModal.file)
        }
        await api.post(`/student/apply-drive/${this.applyModal.driveId}`, formData)
        this.closeApplyModal()
        await this.loadDashboard()
      } catch (error) {
        this.error = error?.response?.data?.message || 'Apply nahi ho paya.'
      } finally {
        this.loading = false
      }
    },
    selectCompany(index) {
      this.selectedCompanyIndex = index
    },
    toggleCompany(index) {
      this.expandedCompanies = { ...this.expandedCompanies, [index]: !this.expandedCompanies[index] }
    },
    async quickApplyDrive(driveId, companyName) {
      this.loading = true
      this.error = ""

      try {
        const formData = new FormData()
        // add resume
        if (this.resumeFile) {
          formData.append("resume", this.resumeFile)
        }
        
        // send application
        await api.post(`/student/apply-drive/${driveId}`, formData)
        
        // clear resume
        this.resumeFile = null
        
        // load new data
        await this.loadDashboard()
        this.error = ""
      } catch (error) {
        const errorMsg = error?.response?.data?.message || "Apply nahi ho paya."
        this.error = errorMsg
      } finally {
        this.loading = false
      }
    },
    selectAppliedDrive(index) {
      // old apply method
    },
    selectDriveById(id) {
      // old close method
    },
    handleResumeUpload(event) {
      const file = event.target.files && event.target.files[0]
      this.resumeFile = file || null
    },
    async applySelectedDrive() {
      if (!this.selectedDrive.id || this.selectedDrive.applied) {
        return
      }

      if (!this.resumeFile) {
        this.error = "Resume upload karo pehle."
        return
      }

      this.loading = true
      this.error = ""

      try {
        const formData = new FormData()
        formData.append("resume", this.resumeFile)

        await api.post(`/student/apply-drive/${this.selectedDrive.id}`, formData)
        await this.loadDashboard()
        this.resumeFile = null
        this.activeTab = "history"
      } catch (error) {
        this.error = error?.response?.data?.message || "Apply nahi ho paya."
      } finally {
        this.loading = false
      }
    },
    async saveProfile() {
      this.loading = true
      this.error = ""
      try {
        await api.put("/student/profile", {
          name: this.profileForm.name,
          department: this.profileForm.department,
          cgpa: this.profileForm.cgpa
        })
        this.studentName = this.profileForm.name
        this.department = this.profileForm.department
        await this.loadDashboard()
        this.activeTab = "overview"
      } catch (error) {
        this.error = error?.response?.data?.message || "Profile save nahi ho paya."
      } finally {
        this.loading = false
      }
    },
    historyClass(result) {
      if (result === "Short Listed") return "success"
      if (result === "Rejected") return "danger"
      return "neutral"
    },
    logout() {
      localStorage.removeItem("token")
      localStorage.removeItem("role")
      this.$router.push("/login")
    }
  },
  beforeUnmount() {
    window.clearTimeout(this.exportPollTimer)
  }
}
</script>

<style scoped>
.student-dashboard-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.student-shell {
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

.sidebar-top {
  display: flex;
  flex-direction: column;
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
  background: #0ea5e9;
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

.sidebar-note {
  margin: 0;
  color: #9ca3af;
  font-size: 0.88rem;
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
  gap: 10px;
  cursor: pointer;
}

.menu-item:hover {
  background: #1f2937;
  color: #fff;
}

.menu-item.active {
  background: #0369a1;
  color: #fff;
}

.menu-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1f2937;
  color: #fff;
  font-size: 0.75rem;
  font-weight: 700;
  flex: none;
}

.menu-item strong {
  font-size: 0.9rem;
  display: block;
}

.menu-item small {
  color: #9ca3af;
  font-size: 0.78rem;
}

.content {
  padding: 24px;
  min-width: 0;
}

.error-banner {
  margin-bottom: 14px;
  padding: 12px 14px;
  border-radius: 8px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  font-weight: 600;
}

.success-banner {
  margin-bottom: 14px;
  padding: 12px 14px;
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
  margin-bottom: 16px;
}

.hero h2, .panel h3 {
  margin: 4px 0 8px;
  color: #111827;
}

.panel-text {
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
  display: block;
  font-size: 0.8rem;
  color: #9ca3af;
}

.hero-badge strong {
  display: block;
  font-size: 1rem;
}

.hero-badge small {
  color: #6b7280;
  font-size: 0.82rem;
}

.stats-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

.stat-card {
  padding: 16px;
  border-radius: 8px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.stat-card.accent {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.stat-card span {
  display: block;
  color: #6b7280;
  font-size: 0.88rem;
  margin-bottom: 6px;
}

.stat-card strong {
  display: block;
  font-size: 1.8rem;
  color: #111827;
}

.stat-card small {
  color: #9ca3af;
  font-size: 0.8rem;
}

.feature-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.feature-card {
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 6px;
  cursor: pointer;
}

.feature-card:hover {
  background: #f3f4f6;
}

.feature-card span {
  color: #0ea5e9;
  font-size: 0.8rem;
  text-transform: uppercase;
  font-weight: 600;
}

.feature-card strong {
  color: #111827;
  font-size: 0.95rem;
}

.feature-card small {
  color: #6b7280;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.history-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}

.export-status {
  margin: -4px 0 14px;
  color: #374151;
  font-size: 0.9rem;
  font-weight: 600;
}

.download-link {
  border: 1px solid #0ea5e9;
  background: #eff6ff;
  color: #0369a1;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.history-meta-card {
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  border-radius: 8px;
  padding: 12px;
}

.history-meta-card span {
  display: block;
  color: #6b7280;
  font-size: 0.85rem;
  margin-bottom: 4px;
}

.history-meta-card strong {
  display: block;
  color: #111827;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
  flex-wrap: wrap;
}

.history-row h4 {
  margin: 0 0 4px;
  color: #111827;
}

.history-row p {
  margin: 0;
  color: #6b7280;
  font-size: 0.9rem;
}

.history-index {
  color: #0ea5e9;
  font-weight: 700;
  display: block;
  margin-bottom: 4px;
}

.history-result {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.82rem;
  font-weight: 600;
}

.history-result.success {
  background: #d1fae5;
  color: #065f46;
}

.history-result.danger {
  background: #fee2e2;
  color: #991b1b;
}

.history-result.neutral {
  background: #dbeafe;
  color: #1e40af;
}

.history-remark {
  color: #6b7280;
  font-size: 0.88rem;
}

.back-btn, .ghost-btn {
  border: 1px solid #d1d5db;
  background: #f9fafb;
  color: #374151;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 0.9rem;
  cursor: pointer;
}

.action-row {
  margin-top: 16px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.search-row {
  margin: 16px 0;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.search-row input {
  flex: 1;
  min-width: 220px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px 12px;
  font: inherit;
}

.apply-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  background: #0ea5e9;
  color: #fff;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.apply-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #9ca3af;
}

.profile-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.profile-grid label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #6b7280;
  font-size: 0.9rem;
}

.profile-grid input {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px 12px;
  font: inherit;
  color: #111827;
  background: #fff;
}

.companies-with-drives {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.company-section {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.company-header {
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.company-header:hover {
  background: #f3f4f6;
}

.company-header h4 {
  margin: 0 0 2px;
  color: #111827;
}

.company-header p {
  margin: 0;
  color: #6b7280;
  font-size: 0.88rem;
}

.toggle-icon {
  color: #6b7280;
  font-size: 0.75rem;
}

.company-details {
  padding: 14px 16px;
}

.drives-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.no-drives {
  padding: 10px;
  text-align: center;
  color: #9ca3af;
  font-size: 0.9rem;
}

.drive-card {
  padding: 12px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.drive-info {
  flex: 1;
  min-width: 0;
}

.drive-info h5 {
  margin: 0 0 4px;
  color: #111827;
  font-size: 0.92rem;
}

.drive-meta {
  margin: 0 0 2px;
  color: #6b7280;
  font-size: 0.85rem;
}

.drive-date {
  margin: 0;
  color: #9ca3af;
  font-size: 0.8rem;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  padding: 20px;
}

.modal-box {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  width: 100%;
  max-width: 440px;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.modal-head h3 {
  margin: 4px 0 0;
  color: #111827;
}

.modal-close {
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  color: #6b7280;
  border-radius: 6px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex: none;
}

.upload-label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #6b7280;
  font-size: 0.9rem;
  font-weight: 600;
}

.file-drop {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  color: #6b7280;
  background: #f9fafb;
}

.file-selected {
  color: #16a34a;
  font-weight: 600;
}

.modal-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 900px) {
  .student-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: none;
    border-bottom: 1px solid #374151;
  }

  .profile-grid {
    grid-template-columns: 1fr;
  }

  .history-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
