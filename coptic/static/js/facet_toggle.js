document.addEventListener("DOMContentLoaded", function() {
    const facets = document.querySelectorAll('.facet');

    facets.forEach(facet => {
        console.log('Processing .facet tag');
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
            console.log('Adding toggle button');
            facet.appendChild(toggle);
        }
    });
});