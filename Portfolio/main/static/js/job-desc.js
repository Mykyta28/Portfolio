const jobs = document.querySelectorAll(".job-item");

jobs.forEach(item => {
    const job = item.querySelector(".job");
    const description = item.querySelector(".work-description");

    job.addEventListener("click", () => {
        item.classList.toggle("active");
    });
});