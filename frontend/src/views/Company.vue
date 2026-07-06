<template>
  <div class="dashboard-page">
    <AppHeader
      title="Company Dashboard"
      subtitle="Manage recruitment details"
    />

    <div class="company-shell">
      <aside class="sidebar">
        <div class="brand">
          <div class="brand-mark">C</div>
          <div>
            <p class="brand-kicker">Company Portal</p>
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
        <p v-if="error" class="error-banner">{{ error }}</p>
        <p v-if="success" class="success-banner">{{ success }}</p>

        <section v-if="activeTab === 'overview'" class="panel">
          <div class="hero">
            <div>
              <p class="eyebrow">Overview</p>
              <h3>Recruitment Summary</h3>
              <p>Drives, applications and company details.</p>
            </div>
            <div class="hero-badge">
              <span>Company</span>
              <strong>{{ profile.company_name || profile.name }}</strong>
            </div>
          </div>

          <div class="stats-grid">
            <div v-for="stat in stats" :key="stat.label" class="stat-card">
              <span>{{ stat.label }}</span>
              <strong>{{ stat.value }}</strong>
            </div>
          </div>

          <div class="quick-list">
            <div class="quick-card">
              <span>Description</span>
              <p>{{ profile.description || "No company description added yet." }}</p>
            </div>
            <div class="quick-card">
              <span>Email</span>
              <p>{{ profile.email }}</p>
            </div>
          </div>
        </section>

        <section v-else-if="activeTab === 'drives'" class="panel">
          <p class="eyebrow">My Drives</p>
          <h3>Placement Drives</h3>
          <p class="panel-text">Create a drive and submit it for admin approval.</p>

          <div class="create-drive">
            <input v-model="newDrive.title" type="text" placeholder="Job title" />
            <div class="field-with-unit">
              <input v-model="newDrive.salary" type="number" min="0" step="0.1" placeholder="CTC" />
              <span>LPA</span>
            </div>
            <input v-model="newDrive.experience" type="text" placeholder="Experience" />
            <input v-model="newDrive.location" type="text" placeholder="Location" />
            <label class="date-field">
              <span>Starting Date</span>
              <input v-model="newDrive.driveDate" type="date" />
            </label>
            <label class="date-field">
              <span>Last Date</span>
              <input v-model="newDrive.applicationDeadline" type="date" />
            </label>
            <input v-model="newDrive.cgpaRequired" type="number" step="0.01" min="0" max="10" placeholder="Minimum CGPA" />
            <select v-model="newDrive.branchRequired">
              <option value="">All branches</option>
              <option v-for="branch in branchOptions" :key="branch" :value="branch">
                {{ branch }}
              </option>
            </select>
            <textarea v-model="newDrive.description" rows="3" placeholder="Job description"></textarea>
            <button class="approve-btn" @click="createDrive">Create Drive</button>
          </div>

          <p v-if="drives.length === 0" class="empty-state">
            No drives created.
          </p>

          <div v-else class="list-grid">
            <article v-for="drive in drives" :key="drive.id" class="list-card">
              <div>
                <h4>{{ drive.title }}</h4>
                <p>{{ drive.description }}</p>
                <p>{{ drive.salary }} | {{ drive.experience }} | {{ drive.location }}</p>
                <p>Starting Date: {{ drive.drive_date }}</p>
                <p>Last Date: {{ drive.application_deadline }}</p>
              </div>
              <div class="card-actions">
                <span class="pill">{{ drive.company }}</span>
                <span class="pill" :class="drive.status === 'Approved' ? 'success' : 'warning'">
                  {{ drive.status }}
                </span>
              </div>
            </article>
          </div>
        </section>

        <section v-else-if="activeTab === 'applications'" class="panel">
          <p class="eyebrow">Applications</p>
          <h3>Candidate Applications</h3>
          <p class="panel-text">Review applicants and update their status.</p>

          <p v-if="applications.length === 0" class="empty-state">
            No applications received.
          </p>

          <div v-else class="list-grid">
            <article v-for="application in applications" :key="application.id" class="list-card">
              <div>
                <h4>{{ application.student_name }}</h4>
                <p>{{ application.drive_name }}</p>
                <p>{{ application.salary }} | {{ application.experience }} | {{ application.location }}</p>
                <p>Starting Date: {{ application.drive_date }}</p>
                <p v-if="application.resume_file">
                  Resume:
                  <a :href="resumeLink(application.resume_url)" target="_blank" rel="noopener">
                    {{ application.resume_file }}
                  </a>
                </p>
              </div>
              <div class="card-actions">
                <span class="pill" :class="statusClass(application.status)">
                  {{ statusLabel(application.status) }}
                </span>
                <button
                  v-if="canUpdateApplication(application.status)"
                  class="approve-btn"
                  :disabled="loading"
                  @click="setApplicationStatus(application.id, 'select')"
                >
                  Approve
                </button>
                <button
                  v-if="canUpdateApplication(application.status)"
                  class="approve-btn"
                  :disabled="loading"
                  @click="openInterviewModal(application)"
                >
                  Shortlist
                </button>
                <button
                  v-if="canUpdateApplication(application.status)"
                  class="approve-btn reject-btn"
                  :disabled="loading"
                  @click="setApplicationStatus(application.id, 'reject')"
                >
                  Reject
                </button>
              </div>
              <div v-if="application.interview_scheduled_at" class="interview-note">
                Interview: {{ application.interview_scheduled_at }}
                <span v-if="application.interview_mode"> | {{ application.interview_mode }}</span>
                <span v-if="application.interview_location"> | {{ application.interview_location }}</span>
              </div>
            </article>
          </div>
        </section>

        <section v-else-if="activeTab === 'profile'" class="panel">
          <p class="eyebrow">Profile</p>
          <h3>Company Profile</h3>
          <p class="panel-text">Update company name, email and description.</p>

          <div class="profile-form">
            <label>
              <span>Company Name</span>
              <input
                v-model.trim="profileForm.company_name"
                type="text"
                placeholder="Company name"
              />
            </label>
            <label>
              <span>Email</span>
              <input
                v-model.trim="profileForm.email"
                type="email"
                placeholder="company@example.com"
              />
            </label>
            <label class="description-field">
              <span>Description</span>
              <textarea
                v-model.trim="profileForm.description"
                rows="5"
                placeholder="Company description"
              ></textarea>
            </label>
          </div>

          <div class="profile-actions">
            <button class="approve-btn save-profile-btn" :disabled="loading" @click="saveProfile">
              {{ loading ? "Saving..." : "Save Changes" }}
            </button>
            <button class="cancel-btn" :disabled="loading" @click="resetProfileForm">
              Cancel
            </button>
          </div>
        </section>

      </main>
    </div>

    <AppFooter />

    <div v-if="interviewModal.show" class="modal-overlay" @click.self="closeInterviewModal">
      <div class="modal-box">
        <div class="modal-head">
          <div>
            <p class="eyebrow">Interview Schedule</p>
            <h3>{{ interviewModal.studentName }}</h3>
            <p>{{ interviewModal.driveName }}</p>
          </div>
          <button class="modal-close" @click="closeInterviewModal">x</button>
        </div>

        <div class="interview-form">
          <label>
            <span>Date</span>
            <input v-model="interviewModal.date" type="date" />
          </label>
          <label>
            <span>Time</span>
            <input v-model="interviewModal.time" type="time" />
          </label>
          <label>
            <span>Mode</span>
            <select v-model="interviewModal.mode">
              <option value="In-person">In-person</option>
              <option value="Online">Online</option>
              <option value="Phone">Phone</option>
            </select>
          </label>
          <label>
            <span>Location / Link</span>
            <input v-model.trim="interviewModal.location" type="text" placeholder="Office address or meeting link" />
          </label>
        </div>

        <div class="modal-actions">
          <button class="approve-btn" :disabled="loading" @click="submitInterviewSchedule">
            {{ loading ? "Scheduling..." : "Schedule & Mail" }}
          </button>
          <button class="cancel-btn" :disabled="loading" @click="closeInterviewModal">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import AppHeader from "../components/AppHeader.vue"
import AppFooter from "../components/AppFooter.vue"
import api from "../services/api"

export default {
  name: "company-dashboard",
  components: {
    AppHeader,
    AppFooter
  },
  data() {
    return {
      activeTab: "overview",
      loading: false,
      error: "",
      success: "",
      newDrive: {
        title: "",
        description: "",
        salary: "",
        experience: "",
        location: "",
        driveDate: "",
        applicationDeadline: "",
        cgpaRequired: "",
        branchRequired: ""
      },
      interviewModal: {
        show: false,
        applicationId: null,
        studentName: "",
        driveName: "",
        date: "",
        time: "10:00",
        mode: "In-person",
        location: ""
      },
      menuItems: [
        { key: "overview", label: "Overview" },
        { key: "drives", label: "My Drives" },
        { key: "applications", label: "Applications" },
        { key: "profile", label: "Profile" }
      ],
      branchOptions: [
        "CSE",
        "IT",
        "ECE",
        "EE",
        "ME",
        "CE",
        "AI/ML",
        "MBA"
      ],
      profile: {},
      profileForm: {
        company_name: "",
        email: "",
        description: ""
      },
      stats: [],
      drives: [],
      applications: []
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
        const [summaryResponse, drivesResponse, applicationsResponse] = await Promise.all([
          api.get("/company/summary"),
          api.get("/company/drives"),
          api.get("/company/applications")
        ])

        const summary = summaryResponse.data || {}

        this.profile = summary.profile || {}
        this.resetProfileForm()
        this.stats = summary.stats || []
        this.drives = (drivesResponse.data || []).map((drive) => ({
          id: drive.id,
          title: drive.title,
          company: drive.company,
          description: drive.description || "",
          salary: drive.salary || "",
          experience: drive.experience || "",
          drive_date: drive.drive_date || "",
          application_deadline: drive.application_deadline || "",
          location: drive.location || "",
          status: drive.status || drive.window || "Live"
        }))
        this.applications = (applicationsResponse.data || []).map((application) => ({
          id: application.id,
          student_name: application.student_name,
          drive_name: application.drive_name,
          status: application.status,
          salary: application.salary || "",
          experience: application.experience || "",
          drive_date: application.drive_date || "",
          application_deadline: application.application_deadline || "",
          location: application.location || "",
          resume_file: application.resume_file || "",
          resume_url: application.resume_url || "",
          interview_scheduled_at: application.interview_scheduled_at || "",
          interview_mode: application.interview_mode || "",
          interview_location: application.interview_location || ""
        }))
      } catch (error) {
        this.error = error?.response?.data?.message || "Dashboard data load nahi ho paya."
      } finally {
        this.loading = false
      }
    },
    resetProfileForm() {
      this.profileForm = {
        company_name: this.profile.company_name || this.profile.name || "",
        email: this.profile.email || "",
        description: this.profile.description || ""
      }
    },
    async saveProfile() {
      const companyName = this.profileForm.company_name.trim()
      const email = this.profileForm.email.trim()

      if (!companyName) {
        this.error = "Company name required hai."
        return
      }
      if (!email || !email.includes("@")) {
        this.error = "Valid email required hai."
        return
      }

      this.loading = true
      this.error = ""
      this.success = ""

      try {
        const response = await api.put("/company/profile", {
          company_name: companyName,
          email,
          description: this.profileForm.description.trim()
        })
        this.profile = response.data?.profile || {
          company_name: companyName,
          name: companyName,
          email,
          description: this.profileForm.description.trim()
        }
        this.resetProfileForm()
        this.success = response.data?.message || "Company profile updated successfully."
        await this.loadDashboard()
        this.activeTab = "profile"
      } catch (error) {
        this.error = error?.response?.data?.message || "Profile save nahi ho paya."
      } finally {
        this.loading = false
      }
    },
    async createDrive() {
      const title = this.newDrive.title.trim()
      if (!title) {
        this.error = "Drive title required hai."
        return
      }
      if (!this.newDrive.driveDate || !this.newDrive.applicationDeadline) {
        this.error = "Starting date aur last date required hai."
        return
      }
      if (this.newDrive.applicationDeadline < this.newDrive.driveDate) {
        this.error = "Last date starting date se pehle nahi ho sakti."
        return
      }

      this.loading = true
      this.error = ""
      const salary = this.newDrive.salary ? `${this.newDrive.salary} LPA` : ""

      try {
        await api.post("/company/drives", {
          title,
          description: this.newDrive.description.trim(),
          salary,
          experience: this.newDrive.experience.trim(),
          location: this.newDrive.location.trim(),
          drive_date: this.newDrive.driveDate,
          application_deadline: this.newDrive.applicationDeadline,
          cgpa_required: this.newDrive.cgpaRequired,
          branch_required: this.newDrive.branchRequired
        })
        this.newDrive = {
          title: "",
          description: "",
          salary: "",
          experience: "",
          location: "",
          driveDate: "",
          applicationDeadline: "",
          cgpaRequired: "",
          branchRequired: ""
        }
        await this.loadDashboard()
      } catch (error) {
        this.error = error?.response?.data?.message || "Drive create nahi ho paya."
      } finally {
        this.loading = false
      }
    },
    async setApplicationStatus(applicationId, action) {
      this.loading = true
      this.error = ""
      this.success = ""

      try {
        const response = await api.post(`/company/applications/${applicationId}/${action}`)
        await this.loadDashboard()
        this.showMailResult(response.data)
      } catch (error) {
        this.error = error?.response?.data?.message || "Application update nahi ho payi."
      } finally {
        this.loading = false
      }
    },
    openInterviewModal(application) {
      const tomorrow = new Date()
      tomorrow.setDate(tomorrow.getDate() + 1)
      const defaultDate = tomorrow.toISOString().slice(0, 10)
      this.interviewModal = {
        show: true,
        applicationId: application.id,
        studentName: application.student_name,
        driveName: application.drive_name,
        date: defaultDate,
        time: "10:00",
        mode: application.interview_mode || "In-person",
        location: application.interview_location || application.location || ""
      }
      this.error = ""
      this.success = ""
    },
    closeInterviewModal() {
      this.interviewModal = {
        show: false,
        applicationId: null,
        studentName: "",
        driveName: "",
        date: "",
        time: "10:00",
        mode: "In-person",
        location: ""
      }
    },
    async submitInterviewSchedule() {
      if (!this.interviewModal.date || !this.interviewModal.time) {
        this.error = "Interview date aur time required hai."
        return
      }

      this.loading = true
      this.error = ""
      this.success = ""

      try {
        const response = await api.post(`/company/applications/${this.interviewModal.applicationId}/shortlist`, {
          interview_scheduled_at: `${this.interviewModal.date}T${this.interviewModal.time}`,
          interview_mode: this.interviewModal.mode,
          interview_location: this.interviewModal.location
        })
        this.closeInterviewModal()
        await this.loadDashboard()
        this.showMailResult(response.data)
      } catch (error) {
        this.error = error?.response?.data?.message || "Interview schedule nahi ho paya."
      } finally {
        this.loading = false
      }
    },
    showMailResult(data) {
      if (data?.mail_sent === false) {
        this.error = `${data.message || "Action complete, but email failed"}: ${data.mail_error || "mail error"}`
      } else if (data?.message) {
        this.success = data.message
      }
    },
    resumeLink(resumeUrl) {
      if (!resumeUrl) return ""
      if (resumeUrl.startsWith("http")) return resumeUrl
      return `${api.defaults.baseURL}${resumeUrl}`
    },
    canUpdateApplication(status) {
      return (status || "pending").toLowerCase() === "pending"
    },
    statusLabel(status) {
      const value = (status || "pending").toLowerCase()
      if (value === "approved") return "Approved"
      if (value === "shortlisted") return "Shortlisted"
      if (value === "rejected") return "Rejected"
      return "Pending"
    },
    statusClass(status) {
      const value = (status || "pending").toLowerCase()
      if (value === "approved" || value === "shortlisted") return "success"
      if (value === "rejected") return "danger"
      return "warning"
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

.company-shell {
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
  background: #f59e0b;
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
  background: #b45309;
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

.hero h3, .panel h3 {
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
  display: block;
  font-size: 0.8rem;
  color: #9ca3af;
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

.quick-list {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.quick-card, .profile-box {
  padding: 14px;
  border-radius: 8px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}

.quick-card span, .profile-box span {
  display: block;
  color: #6b7280;
  font-size: 0.85rem;
  margin-bottom: 4px;
}

.quick-card p, .profile-box strong {
  margin: 0;
  color: #111827;
}

.profile-form {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.profile-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.profile-form label span {
  color: #374151;
  font-size: 0.88rem;
  font-weight: 600;
}

.profile-form input,
.profile-form textarea {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px 12px;
  background: #fff;
  color: #111827;
}

.profile-form input:focus,
.profile-form textarea:focus {
  outline: none;
  border-color: #b45309;
  box-shadow: 0 0 0 3px rgba(180, 83, 9, 0.12);
}

.profile-form textarea {
  resize: vertical;
}

.description-field {
  grid-column: 1 / -1;
}

.profile-actions {
  margin-top: 14px;
  display: flex;
  gap: 10px;
}

.save-profile-btn {
  padding: 9px 16px;
}

.cancel-btn {
  border: 1px solid #d1d5db;
  background: #fff;
  color: #374151;
  border-radius: 6px;
  padding: 9px 16px;
  font-weight: 600;
  cursor: pointer;
}

.cancel-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.empty-state {
  margin: 16px 0 0;
  padding: 14px 16px;
  border-radius: 8px;
  border: 1px dashed #d1d5db;
  background: #f9fafb;
  color: #6b7280;
}

.create-drive {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
}

.create-drive input,
.create-drive select {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px 12px;
  font: inherit;
  background: #fff;
}

.date-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.date-field span {
  color: #374151;
  font-size: 0.84rem;
  font-weight: 600;
}

.field-with-unit {
  display: flex;
  align-items: center;
  min-width: 0;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.field-with-unit input {
  min-width: 0;
  flex: 1;
  border: none;
  border-radius: 0;
}

.field-with-unit span {
  padding: 0 12px;
  color: #6b7280;
  font-size: 0.9rem;
  white-space: nowrap;
}

.create-drive textarea {
  grid-column: 1 / -1;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px 12px;
  font: inherit;
  background: #fff;
  resize: vertical;
}

.list-grid {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.list-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
}

.interview-note {
  grid-column: 1 / -1;
  padding-top: 10px;
  border-top: 1px solid #e5e7eb;
  color: #374151;
  font-size: 0.88rem;
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

.pill.success {
  background: #d1fae5;
  color: #065f46;
}

.pill.warning {
  background: #fef3c7;
  color: #92400e;
}

.pill.danger {
  background: #fee2e2;
  color: #991b1b;
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
  opacity: 0.55;
  cursor: not-allowed;
}

.reject-btn {
  border-color: #dc2626;
  background: #fef2f2;
  color: #991b1b;
}

.pending-btn {
  border-color: #d97706;
  background: #fffbeb;
  color: #92400e;
}

.error-banner {
  margin: 0 0 14px;
  padding: 12px 14px;
  border-radius: 8px;
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.success-banner {
  margin: 0 0 14px;
  padding: 12px 14px;
  border-radius: 8px;
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(17, 24, 39, 0.55);
}

.modal-box {
  width: min(460px, 100%);
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
  padding: 20px;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.22);
}

.modal-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.modal-head h3 {
  margin: 4px 0;
  color: #111827;
}

.modal-head p {
  margin: 0;
  color: #6b7280;
}

.modal-close {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: #fff;
  color: #374151;
  cursor: pointer;
}

.interview-form {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.interview-form label {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.interview-form label:last-child {
  grid-column: 1 / -1;
}

.interview-form span {
  color: #374151;
  font-size: 0.84rem;
  font-weight: 600;
}

.interview-form input,
.interview-form select {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px 12px;
  font: inherit;
  background: #fff;
}

.modal-actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

@media (max-width: 900px) {
  .company-shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: none;
    border-bottom: 1px solid #374151;
  }

	  .profile-form {
	    grid-template-columns: 1fr;
	  }

  .list-card {
    grid-template-columns: 1fr;
  }

  .interview-form {
    grid-template-columns: 1fr;
  }
	}
</style>
