// A table cell's note (its title: a value, a range, a revert reason, the call it measures) shows on hover, which a
// touch screen does not have. A tap on such a cell writes its note in a line under the table instead.
document.addEventListener('click', (e) => {
    const cell = e.target.closest('.tablewrap td[title], .tablewrap th[title], .scroll td[title], .scroll th[title]');
    if (!cell || e.target.closest('a, summary, button, details')) return;
    const box = cell.closest('.tablewrap, .scroll');
    let out = box.nextElementSibling;
    if (!out || !out.classList.contains('cellnote')) {
        out = document.createElement('p');
        out.className = 'cellnote';
        out.setAttribute('aria-live', 'polite');
        box.after(out);
    }
    // name the cell by its row's first cell and its column's head, where it has them
    const row = cell.parentElement;
    const head = cell.closest('table').querySelector('thead tr:last-child');
    const i = Array.prototype.indexOf.call(row.children, cell);
    const where = [row.firstElementChild !== cell ? row.firstElementChild.textContent.trim() : '', head && head.children[i] && head.children[i] !== cell ? head.children[i].textContent.trim() : '']
        .filter(Boolean).join(' · ');
    out.textContent = (where ? `${where}: ` : '') + cell.title;
});
