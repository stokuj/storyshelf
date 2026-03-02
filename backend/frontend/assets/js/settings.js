export function initSettings(session) {
    const emailEl = document.getElementById("settings-email");
    if (emailEl && session?.email) {
        emailEl.textContent = session.email;
    }
}
