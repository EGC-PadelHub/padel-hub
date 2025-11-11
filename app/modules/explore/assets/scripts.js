document.addEventListener('DOMContentLoaded', () => {
    // Configura los listeners cuando el DOM está listo
    send_query();
});

function send_query() {

    console.log("send query listener attached...")

    const filters = document.querySelectorAll('#filters input, #filters select, #filters [type="radio"]');

    filters.forEach(filter => {
        filter.addEventListener('input', () => {
            
            // --- INICIO DE LA CORRECCIÓN ---

            // 1. Mover el token FUERA del criteria
            const csrfToken = document.getElementById('csrf_token').value;

            // 2. Añadir 'author' y mantener 'query' (como tenías)
            const searchCriteria = {
                query: document.querySelector('#filter_title').value,
                author: document.querySelector('#filter_author').value, // <-- AÑADIDO
                publication_type: document.querySelector('#publication_type').value,
                sorting: document.querySelector('[name="sorting"]:checked').value,
            };

            console.log("Enviando criterios:", searchCriteria);

            fetch('/explore', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken // 3. Mover el token a los HEADERS
                },
                body: JSON.stringify(searchCriteria), // El body ya no lleva el token
            })
            // --- FIN DE LA CORRECCIÓN ---
                .then(response => {
                    if (!response.ok) {
                        // Si el token estaba mal, esto se activa
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    // ... (tu lógica de pintar el HTML está PERFECTA) ...
                    // ... (la dejo sin cambios) ...

                    console.log(data);
                    document.getElementById('results').innerHTML = '';

                    // results counter
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
                                            <span class="badge bg-primary" style="cursor: pointer;" onclick="set_publication_type_as_query('${dataset.publication_type}')">${dataset.publication_type}</span>
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
                    // El error 500 del CSRF te llevaría aquí
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
    // --- CORRECCIÓN 3 (Bug de ID) ---
    const queryInput = document.getElementById('filter_title'); // Apuntar al ID correcto
    queryInput.value = tagName.trim();
    queryInput.dispatchEvent(new Event('input', {bubbles: true}));
}

function set_publication_type_as_query(publicationType) {
    const publicationTypeSelect = document.getElementById('publication_type');
    for (let i = 0; i < publicationTypeSelect.options.length; i++) {
        if (publicationTypeSelect.options[i].text === publicationType.trim()) {
            publicationTypeSelect.value = publicationTypeSelect.options[i].value;
            break;
        }
    }
    publicationTypeSelect.dispatchEvent(new Event('input', {bubbles: true}));
}

document.getElementById('clear-filters').addEventListener('click', clearFilters);

function clearFilters() {

    // --- CORRECCIÓN 4 (Limpieza) ---

    // 1. Resetear el título
    let queryInput = document.querySelector('#filter_title'); // Apuntar al ID correcto
    queryInput.value = "";

    // 2. AÑADIDO: Resetear el autor
    let authorInput = document.querySelector('#filter_author');
    authorInput.value = "";

    // 3. Resetear el tipo de publicación
    let publicationTypeSelect = document.querySelector('#publication_type');
    publicationTypeSelect.value = "any";

    // 4. Resetear el orden
    let sortingOptions = document.querySelectorAll('[name="sorting"]');
    sortingOptions.forEach(option => {
        option.checked = option.value == "newest";
    });

    // 5. Lanzar la búsqueda (solo necesitamos disparar un evento)
    queryInput.dispatchEvent(new Event('input', {bubbles: true}));
}

document.addEventListener('DOMContentLoaded', () => {
    // Esta parte está bien, es la que lanza la primera consulta
    // cuando se carga la página (o si vienes de una URL con params)
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