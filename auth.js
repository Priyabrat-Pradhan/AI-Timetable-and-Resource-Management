const API_BASE = window.SMARTTIME_API_BASE || "http://127.0.0.1:8000/api";

document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  if (loginForm) loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const result = await apiRequest("/auth/login/", {
        role: document.getElementById("role").value,
        email: document.getElementById("email").value.trim().toLowerCase(),
        password: document.getElementById("password").value,
      });
      const { token, user } = result;
      localStorage.setItem("smartTimeToken", token);
      localStorage.setItem("smartTimeUser", JSON.stringify(user));
      localStorage.setItem("smartTimeUserId", String(user.id || ""));
      localStorage.setItem("loggedIn", "true");
      localStorage.setItem("userRole", user.role);
      localStorage.setItem("userEmail", user.email);
      localStorage.setItem("userName", user.name);
      if (user.role === "faculty") {
        localStorage.setItem("facultyName", user.name);
        localStorage.setItem("facultyId", user.user_id || "");
        window.location.replace("./faculty-dashboard.html");
      } else if (user.role === "student") {
        window.location.replace("./student-dashboard.html");
      } else {
        window.location.replace("./admin.html");
      }
    } catch (error) { alert(error.message); }
  });

  const registerForm = document.getElementById("registerForm");
  if (registerForm) registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const role = document.getElementById("registerRole").value;
    const idField = document.getElementById(role === "faculty" ? "facultyId" : "studentId");
    const password = document.getElementById("registerPassword").value;
    const message = document.getElementById("registerMessage");
    if (password !== document.getElementById("confirmPassword").value) {
      showMessage(message, "Passwords do not match.", "error"); return;
    }
    if (!document.getElementById("terms").checked) {
      showMessage(message, "Please agree to the terms and conditions.", "error"); return;
    }
    try {
      await apiRequest("/auth/register/", {
        name: document.getElementById("registerName").value.trim(),
        role,
        email: document.getElementById("registerEmail").value.trim().toLowerCase(),
        phone: document.getElementById("registerPhone").value.trim(),
        user_id: idField?.value.trim() || "",
        password,
      });
      showMessage(message, "Account created. Redirecting to login…", "success");
      setTimeout(() => { window.location.href = "./login.html"; }, 1000);
    } catch (error) { showMessage(message, error.message, "error"); }
  });

  const role = document.getElementById("registerRole");
  if (role) {
    const updateIdFields = () => {
      document.getElementById("studentIdGroup").style.display = role.value === "student" ? "block" : "none";
      document.getElementById("facultyIdGroup").style.display = role.value === "faculty" ? "block" : "none";
    };
    role.addEventListener("change", updateIdFields); updateIdFields();
  }
  const toggle = document.getElementById("togglePassword");
  if (toggle) toggle.addEventListener("click", () => togglePassword("password", toggle));
});

async function apiRequest(path, body) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  } catch { throw new Error("Cannot reach the Django server. Start the backend and try again."); }
  const data = response.status === 204 ? {} : await response.json().catch(() => ({}));
  if (response.status >= 500) throw new Error("Django is running but cannot complete the request. Check that MySQL is running and the project migrations are applied.");
  if (!response.ok) throw new Error(data.error || data.detail || "The request could not be completed.");
  return data;
}

function togglePassword(inputId, button) {
  const input = document.getElementById(inputId); if (!input) return;
  const show = input.type === "password"; input.type = show ? "text" : "password"; button.textContent = show ? "🙈" : "👁";
}
window.togglePassword = togglePassword;

function showMessage(element, message, type) {
  if (!element) return; element.textContent = message; element.className = `message ${type}`;
}
