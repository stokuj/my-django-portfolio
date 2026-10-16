document.addEventListener("DOMContentLoaded", () => {
    const root = document.documentElement;
    const ctl = document.querySelector(".theme-controller");
    const themeColorMeta = document.querySelector('meta[name="theme-color"]');
    const defaultTheme = "fantasy3";
    const allowedThemes = new Set(["fantasy3", "dim2"]);

    // Storage can throw (blocked cookies, private mode); the theme then lasts for the session only.
    const saveTheme = (theme) => {
        try {
            localStorage.setItem("theme", theme);
        } catch (e) {}
    };
    let savedTheme = null;
    try {
        savedTheme = localStorage.getItem("theme");
    } catch (e) {}

    const updateThemeColor = () => {
        if (!themeColorMeta) {
            return;
        }

        const background = getComputedStyle(root).getPropertyValue("--color-base-100").trim();
        if (background) {
            themeColorMeta.setAttribute("content", background);
        }
    };

    if (savedTheme && allowedThemes.has(savedTheme)) {
        root.setAttribute("data-theme", savedTheme);
        updateThemeColor();
        if (ctl && ctl.value === savedTheme) {
            ctl.checked = true;
        }
    } else {
        root.setAttribute("data-theme", defaultTheme);
        saveTheme(defaultTheme);
        updateThemeColor();
    }

    if (!ctl) {
        return;
    }

    ctl.addEventListener("change", (event) => {
        const theme = event.target.checked ? event.target.value : defaultTheme;
        root.setAttribute("data-theme", theme);
        saveTheme(theme);
        updateThemeColor();
    });
});
