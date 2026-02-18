document.addEventListener("DOMContentLoaded", () => {
    const root = document.documentElement;
    const ctl = document.querySelector(".theme-controller");
    const defaultTheme = "fantasy3";
    const savedTheme = localStorage.getItem("theme");

    if (savedTheme) {
        root.setAttribute("data-theme", savedTheme);
        if (ctl && ctl.value === savedTheme) {
            ctl.checked = true;
        }
    }

    if (!ctl) {
        return;
    }

    ctl.addEventListener("change", (event) => {
        const theme = event.target.checked ? event.target.value : defaultTheme;
        root.setAttribute("data-theme", theme);
        localStorage.setItem("theme", theme);
    });
});
