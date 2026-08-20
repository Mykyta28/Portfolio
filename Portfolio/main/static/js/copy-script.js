function copyText(id, button) {
    const text = document.getElementById(id).textContent;

    navigator.clipboard.writeText(text).then(() => {
        const icon = button.querySelector("i");

        icon.className = "fa-solid fa-check";

        setTimeout(() => {
            icon.className = "fa-regular fa-copy";
        }, 1500);
    });
}