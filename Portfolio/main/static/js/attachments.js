const fileInput = document.getElementById("attachment");
const fileName = document.getElementById("file-name");

let selectedFiles = [];

fileInput.addEventListener("change", () => {
    const newFiles = Array.from(fileInput.files);


    newFiles.forEach(newFile => {
        const isDuplicate = selectedFiles.some(existingFile =>
            existingFile.name === newFile.name &&
            existingFile.size === newFile.size
        );

        if (!isDuplicate) {
            selectedFiles.push(newFile);
        }
    });


    fileName.textContent = selectedFiles.length > 0
        ? selectedFiles.map(f => f.name).join(", ")
        : "No file selected";
});

// clear files
document.getElementById("clear-files").addEventListener("click", () => {
    selectedFiles = []
    fileName.textContent = "No file selected"
    fileInput.value = ''
})