document.addEventListener("DOMContentLoaded", function () {


    const presentCheckbox = document.getElementById("id_is_present");
    const endDateField = document.getElementById("id_end_date");

    if (!presentCheckbox || !endDateField) {
        return;
    }

    function toggleEndDate() {

        if (presentCheckbox.checked) {
            endDateField.value = "";
            endDateField.disabled = true;
        } else {
            endDateField.disabled = false;
        }
    }

    presentCheckbox.addEventListener("change", toggleEndDate);

    toggleEndDate();
});
