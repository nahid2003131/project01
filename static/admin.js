const search = document.querySelector('.input-group input');
const tableRows = document.querySelectorAll('tbody tr');
const tableHeadings = document.querySelectorAll('thead th');

// 1. Searching for specific data of HTML table
search.addEventListener('input', searchTable);

function searchTable() {
    const searchData = search.value.toLowerCase();

    tableRows.forEach(row => {
        const rowData = row.textContent.toLowerCase();
        const isVisible = rowData.includes(searchData);
        row.classList.toggle('hide', !isVisible);

        // Remove inline style to avoid gaps
        if (!isVisible) {
            row.style.removeProperty('background-color');
        }
    });

    const visibleRows = document.querySelectorAll('tbody tr:not(.hide)');
    visibleRows.forEach((visibleRow, i) => {
        visibleRow.style.backgroundColor = (i % 2 === 0) ? 'transparent' : '#0000000b';
    });
}

// 2. Sorting | Ordering data of HTML table
tableHeadings.forEach((head, i) => {
    let sortAsc = true;
    head.addEventListener('click', () => {
        tableHeadings.forEach(head => head.classList.remove('active'));
        head.classList.add('active');

        document.querySelectorAll('td').forEach(td => td.classList.remove('active'));
        tableRows.forEach(row => {
            row.querySelectorAll('td')[i].classList.add('active');
        });

        head.classList.toggle('asc', sortAsc);
        sortAsc = !sortAsc;

        sortTable(i, sortAsc);
    });
});


