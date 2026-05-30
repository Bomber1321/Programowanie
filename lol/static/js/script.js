function toggleCheckboxesByNames(employeeId) {
    const checkboxes = document.querySelectorAll(`input[name^="availability_${employeeId}_"]`);
    const isChecked = checkboxes[0].checked;
    checkboxes.forEach(checkbox => {
        checkbox.checked = !isChecked;
    });
}

function toggleCheckboxesByDays(dayIndex) {
    const checkboxes = document.querySelectorAll(`input[name$="_${dayIndex}"]`);
    const isChecked = checkboxes[0].checked;
    checkboxes.forEach(checkbox => {
        checkbox.checked = !isChecked;
    });
}

function toggleCheckboxesAll() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    const isChecked = checkboxes[0].checked;
    checkboxes.forEach(checkbox => {
        checkbox.checked = !isChecked;
    });
}
