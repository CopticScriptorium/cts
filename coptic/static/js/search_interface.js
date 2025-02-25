document.addEventListener("DOMContentLoaded", function() {
    const facets = document.querySelectorAll('.facet');

    facets.forEach(facet => {        
        // console.log('Processing .facet tag');
        const ul = facet.querySelector('ul.expandable-list');

        if (ul.scrollHeight > ul.clientHeight) {
            const toggle = document.createElement('div');
            toggle.className = 'toggle';
            toggle.innerText = 'Show More ▼';
            toggle.onclick = function() {
                ul.classList.toggle('expanded');
                if (ul.classList.contains('expanded')) {
                    this.innerText = 'Show Less ▲';
                } else {
                    this.innerText = 'Show More ▼';
                }
            };
           // console.log('Adding toggle button');
            facet.appendChild(toggle);
        }
    });
});

document.onreadystatechange = function () {
    if (document.readyState == "interactive") {
        // Get search term from URL hash if present
        const text_hash = document.location.hash.split("#text=") || [];
        if (text_hash.length > 1) {
            const searchTerm = decodeURIComponent(text_hash[1]);
            console.log("Searching for:", searchTerm);

            // Create a text node of the search term to escape special characters
            const searchTextNode = document.createTextNode(searchTerm);
            const searchText = searchTextNode.textContent;

            // Find all text nodes in the document
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );

            const textNodes = [];
            let node;
            while (node = walker.nextNode()) {
                textNodes.push(node);
            }

            textNodes.forEach(node => {
                const index = node.textContent.toLocaleUpperCase().indexOf(searchText.toLocaleUpperCase());
                if (index >= 0) {
                    
                    // Create highlight span
                    const span = document.createElement('span');
                    span.className = 'search-highlight';
                    span.style.backgroundColor = 'yellow';

                    // Split text node and insert highlight
                    const before = node.textContent.substring(0, index);
                    const after = node.textContent.substring(index + searchText.length);
                    const beforeNode = document.createTextNode(before);
                    const afterNode = document.createTextNode(after);
                    const highlightNode = document.createTextNode(searchText);
                    span.appendChild(highlightNode);

                    const parent = node.parentNode;
                    parent.insertBefore(beforeNode, node);
                    parent.insertBefore(span, node);
                    parent.insertBefore(afterNode, node);
                    parent.removeChild(node);

                    // Scroll the first match into view
                    span.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }
            });
        }
    }
};