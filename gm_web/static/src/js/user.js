/** @odoo-module **/

document.addEventListener("DOMContentLoaded", function () {
    const settingsButton = document.getElementById('settingsButton');
    const dropdownMenu = document.getElementById('settingsMenu');

    function closeDropdown() {
        dropdownMenu.classList.remove('open');
        settingsButton.setAttribute('aria-expanded', 'false');
    }

    function openDropdown() {
        dropdownMenu.classList.add('open');
        settingsButton.setAttribute('aria-expanded', 'true');
        dropdownMenu.focus();
    }

    settingsButton?.addEventListener('click', () => {
        if (dropdownMenu.classList.contains('open')) {
            closeDropdown();
        } else {
            openDropdown();
        }
    });

    document.addEventListener('click', (event) => {
        if (!dropdownMenu.contains(event.target) && !settingsButton.contains(event.target)) {
            closeDropdown();
        }
    });

    settingsButton?.addEventListener('keydown', (event) => {
        if (['ArrowDown', 'Enter', ' '].includes(event.key)) {
            event.preventDefault();
            openDropdown();
        }
        if (event.key === 'Escape') {
            closeDropdown();
            settingsButton.focus();
        }
    });

    dropdownMenu?.addEventListener('keydown', (event) => {
        const focusableItems = Array.from(dropdownMenu.querySelectorAll('a[role="menuitem"]'));
        let index = focusableItems.indexOf(document.activeElement);

        if (event.key === 'Escape') {
            closeDropdown();
            settingsButton.focus();
        } else if (event.key === 'ArrowDown') {
            event.preventDefault();
            index = (index + 1) % focusableItems.length;
            focusableItems[index].focus();
        } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            index = (index - 1 + focusableItems.length) % focusableItems.length;
            focusableItems[index].focus();
        }
    });
});
