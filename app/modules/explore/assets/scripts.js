document.addEventListener('DOMContentLoaded', () => {
    // Configura los listeners cuando el DOM está listo
    send_query();
});

document.addEventListener("DOMContentLoaded", function() {
    const urlParams = new URLSearchParams(window.location.search);
    
    if (urlParams.has('query')) {
        const searchQuery = urlParams.get('query');
        const titleFilterInput = document.getElementById('filter_title');
        
        if (titleFilterInput) {
            titleFilterInput.value = searchQuery;
            titleFilterInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }
});
function send_query() {

    console.log("send query listener attached...")

    const filters = document.querySelectorAll('#filters input, #filters select, #filters [type="radio"]');

    filters.forEach(filter => {
        filter.addEventListener('input', () => {

            const csrfToken = document.getElementById('csrf_token').value;
            
            const tagsInput = document.querySelector('#filter_tags').value;
            const tags = tagsInput ? tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag !== "") : [];

            const searchCriteria = {
                query: document.querySelector('#filter_title').value,
                author: document.querySelector('#filter_author').value, 
                description: document.querySelector('#filter_description').value,
                tags: tags,
                tournament_type: document.querySelector('#tournament_type').value,
                sorting: document.querySelector('[name="sorting"]:checked').value,
            };

            console.log("Enviando criterios:", searchCriteria);

            fetch('/explore', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken 
                },
                body: JSON.stringify(searchCriteria), 
            })
            
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log(data);
                    document.getElementById('results').innerHTML = '';

                    const resultCount = data.length;
                    const resultText = resultCount === 1 ? 'dataset' : 'datasets';
                    document.getElementById('results_number').textContent = `${resultCount} ${resultText} found`;

                    if (resultCount === 0) {
                        console.log("show not found icon");
                        document.getElementById("results_not_found").style.display = "block";
                    } else {
                        document.getElementById("results_not_found").style.display = "none";
                    }


                    data.forEach(dataset => {
                        let card = document.createElement('div');
                        card.className = 'col-12 mb-3'; // Añadido margen
                        card.innerHTML = `
                            <div class="card">
                                <div class="card-body">
                                    <div class="d-flex align-items-center justify-content-between">
                                        <h3><a href="${dataset.url}">${dataset.title}</a></h3>
                                        <div>
                                            <span class="badge bg-primary" style="cursor: pointer;" onclick="set_tournament_type_as_query('${dataset.tournament_type}')">${dataset.tournament_type}</span>
                                        </div>
                                    </div>
                                    <p class="text-secondary">${formatDate(dataset.created_at)}</p>

                                    <div class="row mb-2">

                                        <div class="col-md-4 col-12">
                                            <span class=" text-secondary">
                                                Description
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            <p class="card-text">${dataset.description}</p>
                                        </div>

                                    </div>

                                    <div class="row mb-2">

                                        <div class="col-md-4 col-12">
                                            <span class=" text-secondary">
                                                Authors
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            ${dataset.authors.map(author => `
                                                <p class="p-0 m-0">${author.name}${author.affiliation ? ` (${author.affiliation})` : ''}${author.orcid ? ` (${author.orcid})` : ''}</p>
                                            `).join('')}
                                        </div>

                                    </div>

                                    <div class="row mb-2">

                                        <div class="col-md-4 col-12">
                                            <span class=" text-secondary">
                                                Tags
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            ${dataset.tags.map(tag => `<span class="badge bg-primary me-1" style="cursor: pointer;" onclick="set_tag_as_query('${tag}')">${tag}</span>`).join('')}
                                        </div>

                                    </div>

                                    <div class="row">

                                        <div class="col-md-4 col-12">

                                        </div>
                                        <div class="col-md-8 col-12">
                                            <a href="${dataset.url}" class="btn btn-outline-primary btn-sm" id="search" style="border-radius: 5px;">
                                                View dataset
                                            </a>
                                            <a href="/dataset/download/${dataset.id}" class="btn btn-outline-primary btn-sm" id="search" style="border-radius: 5px;">
                                                Download (${dataset.total_size_in_human_format})
                                            </a>
                                            <a href="/dataset/export/${dataset.id}" class="btn btn-primary btn-sm" id="search" style="border-radius: 5px;">
                                                Download in different formats (ZIP)
                                            </a>
                                        </div>


                                    </div>

                                </div>
                            </div>
                        `;

                        document.getElementById('results').appendChild(card);
                    });
                })
                .catch(error => {
                    console.error('Error fetching search results:', error);
                    document.getElementById("results_not_found").style.display = "block";
                    document.getElementById('results_number').textContent = `0 results found`;
                });
        });
    });
}

function formatDate(dateString) {
    const options = {day: 'numeric', month: 'long', year: 'numeric', hour: 'numeric', minute: 'numeric'};
    const date = new Date(dateString);
    return date.toLocaleString('en-US', options);
}

function set_tag_as_query(tagName) {
    const queryInput = document.getElementById('filter_title'); 
    queryInput.value = tagName.trim();
    queryInput.dispatchEvent(new Event('input', {bubbles: true}));
}

function set_tournament_type_as_query(tournamentType) {
    const tournamentTypeSelect = document.getElementById('tournament_type');
    for (let i = 0; i < tournamentTypeSelect.options.length; i++) {
        if (tournamentTypeSelect.options[i].text === tournamentType.trim()) {
            tournamentTypeSelect.value = tournamentTypeSelect.options[i].value;
            break;
        }
    }
    publicationTypeSelect.dispatchEvent(new Event('input', {bubbles: true}));
}

document.getElementById('clear-filters').addEventListener('click', clearFilters);

function clearFilters() {

    let queryInput = document.querySelector('#filter_title'); 
    queryInput.value = "";

    let authorInput = document.querySelector('#filter_author');
    authorInput.value = "";

    let tournamentTypeSelect = document.querySelector('#tournament_type');
    tournamentTypeSelect.value = "any";

    let sortingOptions = document.querySelectorAll('[name="sorting"]');
    sortingOptions.forEach(option => {
        option.checked = option.value == "newest";
    });

    queryInput.dispatchEvent(new Event('input', {bubbles: true}));
}

document.addEventListener('DOMContentLoaded', () => {

    let urlParams = new URLSearchParams(window.location.search);
    let queryParam = urlParams.get('filter_title');
    if (queryParam && queryParam.trim() !== '') {

        const queryInput = document.getElementById('filter_title');
        queryInput.value = queryParam
        queryInput.dispatchEvent(new Event('input', {bubbles: true}));
        console.log("throw event from URL");

    } else {
        const queryInput = document.getElementById('filter_title');
        queryInput.dispatchEvent(new Event('input', {bubbles: true}));
        console.log("throw event from initial load");
    }
});