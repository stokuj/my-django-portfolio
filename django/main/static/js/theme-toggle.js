document.addEventListener("DOMContentLoaded", () => {
    const root = document.documentElement;
    const ctl = document.querySelector(".theme-controller");
    const themeColorMeta = document.querySelector('meta[name="theme-color"]');
    const defaultTheme = "fantasy3";
    const allowedThemes = new Set(["fantasy3", "dim2"]);
    const legacyThemeMap = { fantasy2: "fantasy3" };
    const savedThemeRaw = localStorage.getItem("theme");
    const savedTheme = legacyThemeMap[savedThemeRaw] || savedThemeRaw;

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
        if (savedThemeRaw !== savedTheme) {
            localStorage.setItem("theme", savedTheme);
        }
    } else {
        root.setAttribute("data-theme", defaultTheme);
        localStorage.setItem("theme", defaultTheme);
        updateThemeColor();
    }

    if (!ctl) {
        return;
    }

    ctl.addEventListener("change", (event) => {
        const theme = event.target.checked ? event.target.value : defaultTheme;
        root.setAttribute("data-theme", theme);
        localStorage.setItem("theme", theme);
        updateThemeColor();
    });
});
