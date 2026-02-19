document.addEventListener("DOMContentLoaded", () => {
    const root = document.documentElement;
    const ctl = document.querySelector(".theme-controller");
    const defaultTheme = "fantasy3";
    const allowedThemes = new Set(["fantasy3", "dim2"]);
    const legacyThemeMap = { fantasy2: "fantasy3" };
    const savedThemeRaw = localStorage.getItem("theme");
    const savedTheme = legacyThemeMap[savedThemeRaw] || savedThemeRaw;

    if (savedTheme && allowedThemes.has(savedTheme)) {
        root.setAttribute("data-theme", savedTheme);
        if (ctl && ctl.value === savedTheme) {
            ctl.checked = true;
        }
        if (savedThemeRaw !== savedTheme) {
            localStorage.setItem("theme", savedTheme);
        }
    } else {
        root.setAttribute("data-theme", defaultTheme);
        localStorage.setItem("theme", defaultTheme);
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
