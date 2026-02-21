document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("mobile-menu-button");
    const menu = document.getElementById("mobile-menu");

    if (!button || !menu) {
        return;
    }

    const setMenuState = (isOpen) => {
        menu.classList.toggle("hidden", !isOpen);
        button.setAttribute("aria-expanded", String(isOpen));
    };

    setMenuState(false);

    button.addEventListener("click", () => {
        const isOpen = button.getAttribute("aria-expanded") === "true";
        setMenuState(!isOpen);
    });

    menu.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
            setMenuState(false);
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setMenuState(false);
            button.focus();
        }
    });

    document.addEventListener("click", (event) => {
        if (!menu.contains(event.target) && !button.contains(event.target)) {
            setMenuState(false);
        }
    });
});
