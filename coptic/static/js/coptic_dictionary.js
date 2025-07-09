document.addEventListener("DOMContentLoaded", () => {
    // Base URL for links
    const baseUrl = "https://coptic-dictionary.org/results.cgi?quick_search=";

    // Select all elements with class "norm"
    document.querySelectorAll('.norm').forEach(tag => {
        if (!tag.dataset.linkified) { // Check if already processed
            console.log('Processing .norm tag');

            const link = tag.querySelector('a'); // Find the existing <a> element
            if (link) {
                const originalHref = link.getAttribute('href').trim(); // Get the original href
                if (originalHref) {
                    link.href = baseUrl + encodeURIComponent(originalHref); // Prepend the base URL
                    console.log(encodeURIComponent(originalHref));

                    // Mark as processed
                    tag.dataset.linkified = "true";
                }
            }
        }
    });
});
