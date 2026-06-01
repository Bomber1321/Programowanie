function toggleCheckboxesByNames(employeeId) {
    const checkboxes = document.querySelectorAll(`input[name^="availability_${employeeId}_"]`);
    if (checkboxes.length === 0) {
        return;
    }
    const isChecked = checkboxes[0].checked;
    checkboxes.forEach(checkbox => {
        checkbox.checked = !isChecked;
    });
    updateRequirementTotals();
}

function toggleCheckboxesByDays(dayIndex) {
    const checkboxes = document.querySelectorAll(`input[name$="_${dayIndex}"]`);
    if (checkboxes.length === 0) {
        return;
    }
    const isChecked = checkboxes[0].checked;
    checkboxes.forEach(checkbox => {
        checkbox.checked = !isChecked;
    });
    updateRequirementTotals();
}

function toggleCheckboxesAll() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    if (checkboxes.length === 0) {
        return;
    }
    const isChecked = checkboxes[0].checked;
    checkboxes.forEach(checkbox => {
        checkbox.checked = !isChecked;
    });
    updateRequirementTotals();
}

function updateRequirementTotals() {
    const checkedCounts = {};
    document.querySelectorAll('.availability-checkbox').forEach(checkbox => {
        if (!checkbox.checked) {
            return;
        }

        const dayIndex = checkbox.dataset.dayIndex;
        const positionId = checkbox.dataset.positionId;
        if (!dayIndex || !positionId) {
            return;
        }

        const key = `${dayIndex}:${positionId}`;
        checkedCounts[key] = (checkedCounts[key] || 0) + 1;
    });

    document.querySelectorAll('.requirements-column').forEach(cell => {
        const dayIndex = cell.dataset.dayIndex;
        const positionId = cell.dataset.positionId;
        const baseRequired = Number(cell.dataset.baseRequired) || 0;
        const covered = checkedCounts[`${dayIndex}:${positionId}`] || 0;
        const remaining = Math.max(baseRequired - covered, 0);
        cell.textContent = remaining;
    });
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.availability-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateRequirementTotals);
    });
    updateRequirementTotals();
});