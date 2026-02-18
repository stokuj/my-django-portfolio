document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("searchInput");
    const clearButton = document.getElementById("clearButton");
    const tagButtons = document.querySelectorAll("#tagFilter button");
    const projectCards = document.querySelectorAll(".project-card");
    const emptyState = document.getElementById("emptyState");
    const projectGrid = document.getElementById("projectGrid");
    const projectGridSkeleton = document.getElementById("projectGridSkeleton");

    if (!searchInput || !clearButton || !emptyState || !projectGrid || !projectGridSkeleton) {
        return;
    }

    let activeTag = "all";

    function applyFilters() {
        const searchTerm = searchInput.value.trim().toLowerCase();
        clearButton.classList.toggle("hidden", searchTerm.length === 0);

        let visibleCount = 0;

        projectCards.forEach((card) => {
            const title = card.dataset.title || "";
            const description = card.dataset.description || "";
            const tags = (card.dataset.tags || "").split("|").filter(Boolean);

            const matchesSearch = !searchTerm || title.includes(searchTerm) || description.includes(searchTerm);
            const matchesTag = activeTag === "all" || tags.includes(activeTag);
            const visible = matchesSearch && matchesTag;

            card.style.display = visible ? "flex" : "none";
            if (visible) {
                visibleCount += 1;
            }
        });

        emptyState.classList.toggle("hidden", visibleCount > 0);
    }

    searchInput.addEventListener("input", applyFilters);
    clearButton.addEventListener("click", () => {
        searchInput.value = "";
        searchInput.focus();
        applyFilters();
    });

    tagButtons.forEach((button) => {
        button.addEventListener("click", () => {
            activeTag = button.dataset.tag;

            tagButtons.forEach((btn) => {
                btn.classList.remove("btn-primary");
                btn.classList.add("btn-outline");
            });

            button.classList.remove("btn-outline");
            button.classList.add("btn-primary");

            applyFilters();
        });
    });

    applyFilters();
    projectGrid.classList.remove("hidden");
    projectGridSkeleton.classList.add("hidden");
});
