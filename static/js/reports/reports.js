document.querySelectorAll(".dropdown .button").forEach((button) => {
  button.addEventListener("click", (e) => {
    const dropdown = e.target.closest(".dropdown");
    dropdown.classList.toggle("active");

    // Close other dropdowns
    document.querySelectorAll(".dropdown").forEach((d) => {
      if (d !== dropdown) d.classList.remove("active");
    });
  });
});

// Handle dropdown item clicks
document.querySelectorAll(".dropdown .dropdown-menu li").forEach((item) => {
  item.addEventListener("click", (e) => {
    const dropdown = e.target.closest(".dropdown");
    const value = e.target.textContent.trim().toLowerCase();

    // Remove active class from all items in this dropdown
    dropdown
      .querySelectorAll("li")
      .forEach((li) => li.classList.remove("active"));

    // Add active style only if not Reset
    if (value !== "reset") {
      e.target.classList.add("active");
    }

    // Close this dropdown
    dropdown.classList.remove("active");

    // 👉 Clear active from the other dropdown
    document.querySelectorAll(".dropdown").forEach((d) => {
      if (d !== dropdown) {
        d.querySelectorAll("li").forEach((li) => li.classList.remove("active"));
      }
    });
  });
});

// Close dropdown if clicked outside
document.addEventListener("click", (e) => {
  if (!e.target.closest(".dropdown")) {
    document
      .querySelectorAll(".dropdown")
      .forEach((d) => d.classList.remove("active"));
  }
});

const pagination = document.querySelector(".pagination");

// SEARCH FUNCTION
document.getElementById("search").addEventListener("keyup", function () {
  const query = this.value;
  const sortOption = document.getElementById("sortBtn").dataset.sort || ""; // keep selected sort

  fetch(`/reports/search/?q=${encodeURIComponent(query)}&sort=${sortOption}`)
    .then((response) => response.json())
    .then((data) => updateTable(data.results));

  // Hide pagination if searching
  if (pagination) {
    pagination.style.display = query.trim() !== "" ? "none" : "flex";
  }
});

// SORT FUNCTION
const sortBtn = document.getElementById("sortBtn");
const sortMenu = sortBtn.nextElementSibling; // the dropdown-menu right after the button

sortMenu.querySelectorAll("li").forEach((item) => {
  item.addEventListener("click", function () {
    const sortOption = this.textContent.trim().toLowerCase();
    const query = document.getElementById("search").value; // keep current search term

    if (sortOption === "reset") {
      sortBtn.dataset.sort = ""; // clear stored sort
      fetch(`/reports/search/?q=${encodeURIComponent(query)}`)
        .then((response) => response.json())
        .then((data) => updateTable(data.results));
    } else {
      sortBtn.dataset.sort = sortOption;
      fetch(
        `/reports/search/?q=${encodeURIComponent(query)}&sort=${sortOption}`
      )
        .then((response) => response.json())
        .then((data) => updateTable(data.results));
    }

    // if (pagination) {
    //   pagination.style.display =
    //     query.trim() !== "" || sortOption ? "none" : "flex";
    // }
  });
});

// FILTER FUNCTION
const filterBtn = document.getElementById("filterBtn");
const filterMenu = filterBtn.nextElementSibling; // dropdown-menu after button

filterMenu.querySelectorAll("li").forEach((item) => {
  item.addEventListener("click", function () {
    const filterOption = this.textContent.trim().toLowerCase();
    filterBtn.dataset.filter = filterOption; // store chosen filter
    const query = document.getElementById("search").value; // keep current search term

    let url = `/reports/search/?q=${encodeURIComponent(query)}`;

    // Add filter if not reset
    if (filterOption && filterOption !== "reset") {
      url += `&filter=${filterOption}`;
    }

    fetch(url)
      .then((response) => response.json())
      .then((data) => updateTable(data.results));
  });
});

// Function to update the data in table
function updateTable(results) {
  const tbody = document.querySelector("#cases-table tbody");
  tbody.innerHTML = "";

  if (results.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td class="poppins-regular table-empty" colspan="6">
          <span>No matching reports found</span>
        </td>
      </tr>`;
    return;
  }

  results.forEach((r) => {
    tbody.innerHTML += `
      <tr>
        <td class="poppins-regular">${r.id}</td>
        <td class="poppins-regular">${r.full_name}</td>
        <td class="poppins-regular">${r.reporter}</td>
        <td class="poppins-regular">${r.created_at}</td>
        <td class="poppins-regular ${r.status.toLowerCase()}">${r.status}</td>
        <td>
          <div class="actionIcon">
            <i data-lucide="file-search"></i>
            <i data-lucide="message-circle"></i>
          </div>
        </td>
      </tr>`;
  });

  if (window.lucide) {
    lucide.createIcons(); // re-render icons
  }
}

lucide.createIcons();
