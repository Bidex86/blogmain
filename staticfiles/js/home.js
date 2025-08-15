document.addEventListener("DOMContentLoaded", () => {
    const loadMoreBtn = document.getElementById("load-more");
    const postsContainer = document.getElementById("posts-container");

    if (loadMoreBtn) {
        loadMoreBtn.addEventListener("click", function () {
            const nextPage = this.getAttribute("data-next-page");

            fetch(`?page=${nextPage}`, { 
                headers: { "X-Requested-With": "XMLHttpRequest" }
            })
            .then(response => response.text())
            .then(data => {
                const parser = new DOMParser();
                const html = parser.parseFromString(data, "text/html");
                const newPosts = html.querySelector(".posts-grid");
                const newButton = html.querySelector("#load-more");

                if (newPosts) {
                    postsContainer.querySelector(".posts-grid").insertAdjacentHTML('beforeend', newPosts.innerHTML);
                }

                if (newButton) {
                    this.setAttribute("data-next-page", newButton.dataset.nextPage);
                } else {
                    this.remove();
                }

                // Update URL for SEO tracking (browser history)
                window.history.pushState(null, "", `?page=${nextPage}`);
            });
        });
    }
});

