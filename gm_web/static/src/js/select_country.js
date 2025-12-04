document.addEventListener('DOMContentLoaded', () => {
    console.log('Country Picker initialized');
    const display = document.getElementById('country-display');
    const hidden = document.getElementById('country-id');
    const modal = document.getElementById('country-modal');
    const search = document.getElementById('country-search');
    const list = document.getElementById('country-list');
    let countries = [];

    if (!display || !hidden || !modal || !search || !list) {
      console.warn('Country Picker: Elements not found on page.');
      return;
    }

    function getCSRFToken() {
      const token = document.querySelector('meta[name="csrf-token"]');
      return token ? token.getAttribute('content') : '';
    }

    function renderList(data) {
      if (!data || !data.length) {
        console.log("No countries to render");
        return;
      }

      list.innerHTML = '';
      console.log(`Rendering ${data.length} countries`);
    
      data.forEach(c => {
        const li = document.createElement('li');
        li.innerHTML = `
          ${c.flag_url ? `<img src="${c.flag_url}" alt="${c.name}" style="width: 20px; height: 14px; margin-right: 10px; object-fit: cover;" />` : ''}
          ${c.name}
        `;
        li.style.display = 'flex';
        li.style.alignItems = 'center';
        li.style.cursor = 'pointer';
        li.style.padding = '5px';
        li.addEventListener('click', () => {
          display.value = c.name;
          hidden.value = c.id;
          modal.style.display = 'none';
          modal.classList.remove('show');
        });
        list.appendChild(li);
      });
    }

    function fetchCountries() {
      console.log('Fetching countries...');
      fetch('/country/list', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
          jsonrpc: "2.0",
          method: "call",
          params: {}
        })
      })
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        if (data.result) {
          countries = data.result;
        } else if (Array.isArray(data)) {
          countries = data;
        } else {
          throw new Error("Unexpected data format");
        }
        renderList(countries);
      })
      .catch(err => {
        console.error('Error fetching country list:', err);
        countries = [
          {id: 1, name: 'United States'},
          {id: 2, name: 'Canada'},
          {id: 3, name: 'United Kingdom'},
          {id: 4, name: 'Australia'},
          {id: 5, name: 'Germany'},
          {id: 6, name: 'France'},
          {id: 7, name: 'Japan'},
          {id: 8, name: 'Singapore'},
          {id: 9, name: 'Malaysia'},
          {id: 10, name: 'Indonesia'}
        ];
        renderList(countries);
        console.log("Using fallback country list");
      });
    }

    display.addEventListener('click', () => {
      modal.style.display = 'flex';
      modal.classList.add('show');
      search.value = '';
      search.focus();
      fetchCountries();
    });

    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
      }
    });

    search.addEventListener('input', () => {
      const term = search.value.toLowerCase();
      const filtered = countries.filter(c => c.name.toLowerCase().includes(term));
      renderList(filtered);
    });

    const firstNameInput = document.querySelector("#firstname");
    const lastNameInput = document.querySelector("#lastname");
    const nameInput = document.querySelector("#name");

    function updateNameField() {
      const firstName = firstNameInput.value.trim();
      const lastName = lastNameInput.value.trim();
      nameInput.value = `${firstName} ${lastName}`.trim();
    }

    if (firstNameInput && lastNameInput && nameInput) {
      firstNameInput.addEventListener("input", updateNameField);
      lastNameInput.addEventListener("input", updateNameField);
    }

    // Initial fetch
    fetchCountries();
});
