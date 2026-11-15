
(() => {
  const API_URL = `${window.SMARTTIME_API_BASE || "http://127.0.0.1:8000/api"}/auth/change-password/`;
  let dialog;

  function makeDialog() {
    if (dialog) return dialog;
    dialog = document.createElement("dialog");
    dialog.className = "password-change-dialog";
    dialog.setAttribute("aria-labelledby", "password-change-title");
    dialog.innerHTML = `
      <form id="adminPasswordChangeForm">
        <h2 id="password-change-title">Change Password</h2>
        <p>Enter your current password, then choose and confirm a new one.</p>
        <label for="currentPassword">Current password</label>
        <input id="currentPassword" name="current_password" type="password" autocomplete="current-password" required>
        <label for="newPassword">New password</label>
        <input id="newPassword" name="new_password" type="password" minlength="8" autocomplete="new-password" required>
        <label for="confirmNewPassword">Confirm new password</label>
        <input id="confirmNewPassword" name="confirm_password" type="password" minlength="8" autocomplete="new-password" required>
        <p id="passwordChangeMessage" class="password-change-message" role="status" aria-live="polite"></p>
        <div class="password-change-actions">
          <button type="button" id="cancelPasswordChange">Cancel</button>
          <button type="submit" class="password-change-submit">Save new password</button>
        </div>
      </form>`;
    document.body.append(dialog);

    const form = dialog.querySelector("#adminPasswordChangeForm");
    const message = dialog.querySelector("#passwordChangeMessage");
    const submit = dialog.querySelector(".password-change-submit");
    dialog.querySelector("#cancelPasswordChange").addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener("close", () => {
      form.reset();
      message.textContent = "";
      message.classList.remove("success");
      submit.disabled = false;
      submit.textContent = "Save new password";
    });
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      message.classList.remove("success");
      message.textContent = "";
      const token = localStorage.getItem("smartTimeToken");
      if (!token) {
        message.textContent = "Your session has expired. Please log in again.";
        return;
      }
      const values = Object.fromEntries(new FormData(form).entries());
      if (values.new_password !== values.confirm_password) {
        message.textContent = "New password and confirmation do not match.";
        return;
      }
      submit.disabled = true;
      submit.textContent = "Saving…";
      try {
        const response = await fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Token ${token}` },
          body: JSON.stringify(values),
        });
        const result = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(result.error || "Password could not be changed.");
        localStorage.setItem("smartTimeToken", result.token);
        form.reset();
        message.textContent = "Password changed successfully.";
        message.classList.add("success");
      } catch (error) {
        message.textContent = error.message || "Password could not be changed.";
      } finally {
        submit.disabled = false;
        submit.textContent = "Save new password";
      }
    });
    return dialog;
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button || (button.textContent || "").trim().toLowerCase() !== "change password") return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const profileButton = document.querySelector(".admin-profile-button");
    if (profileButton) profileButton.click();
    const modal = makeDialog();
    if (!modal.open) modal.showModal();
    modal.querySelector("#currentPassword").focus();
  }, true);
})();
