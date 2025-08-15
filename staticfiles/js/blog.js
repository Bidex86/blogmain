document.addEventListener("DOMContentLoaded", function () {
    // Reply form toggle
    document.querySelectorAll('.reply-toggle').forEach(btn => {
        btn.addEventListener('click', function () {
            const targetId = this.dataset.target;
            const targetForm = document.getElementById(targetId);

            // Hide all other forms
            document.querySelectorAll('.reply-form').forEach(form => {
                if (form.id !== targetId) form.classList.add('d-none');
            });

            // Toggle selected form
            if (targetForm) {
                targetForm.classList.toggle('d-none');
                if (!targetForm.classList.contains('d-none')) {
                    const textarea = targetForm.querySelector('textarea');
                    if (textarea) textarea.focus();
                }
            }
        });
    });

    // Replies toggle
    document.querySelectorAll('.reply-count-toggle').forEach(btn => {
        btn.addEventListener('click', function () {
            const targetId = this.dataset.target;
            const repliesContainer = document.getElementById(targetId);

            if (repliesContainer) {
                repliesContainer.classList.toggle('d-none');
                if (repliesContainer.classList.contains('d-none')) {
                    this.innerHTML = `<i class="fa fa-comments"></i> View ${this.dataset.count} replies`;
                } else {
                    this.innerHTML = `<i class="fa fa-comments"></i> Hide replies`;
                }
            }
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("tags-input");
    const suggestionsBox = document.getElementById("tag-suggestions");
    const selectedTagsContainer = document.getElementById("selected-tags");
    let selectedTags = [];

    input.addEventListener("input", async function () {
        const query = this.value.trim();
        suggestionsBox.innerHTML = "";

        if (query.length > 0) {
            const response = await fetch(`/tags/suggestions/?q=${query}`);
            const data = await response.json();

            data.tags.forEach(tag => {
                const div = document.createElement("div");
                div.classList.add("suggestion-item");
                div.textContent = tag;
                div.addEventListener("click", () => addTag(tag));
                suggestionsBox.appendChild(div);
            });
        }
    });

    input.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && this.value.trim() !== "") {
            e.preventDefault();
            addTag(this.value.trim());
        }
    });

    function addTag(tag) {
        if (!selectedTags.includes(tag)) {
            selectedTags.push(tag);

            const tagEl = document.createElement("span");
            tagEl.classList.add("tag");
            tagEl.innerHTML = `${tag} <span class="remove-tag">&times;</span>`;

            tagEl.querySelector(".remove-tag").addEventListener("click", () => {
                selectedTags = selectedTags.filter(t => t !== tag);
                tagEl.remove();
                updateInputValue();
            });

            selectedTagsContainer.appendChild(tagEl);
            updateInputValue();
        }
        input.value = "";
        suggestionsBox.innerHTML = "";
    }

    function updateInputValue() {
        input.value = selectedTags.join(", ");
    }
});
