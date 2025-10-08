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

//////////////////////////////////////////////////////////////////////////////////////////////////

// Detect current page
const path = window.location.pathname;

// Identify which page we're on
const isReportsPage = path.includes("/reports");
const isClosedCasesPage = path.includes("/cases/closed"); // ✅ matches Django route
const isCasesPage = path.includes("/cases") && !isClosedCasesPage;

// Choose correct endpoint
let endpoint = "";
if (isClosedCasesPage) {
  endpoint = "/cases/closed/search/"; // ✅ match Django search path
} else if (isCasesPage) {
  endpoint = "/cases/search/";
} else if (isReportsPage) {
  endpoint = "/reports/search/";
}

const pagination = document.querySelector(".pagination");

// SEARCH FUNCTION
document.getElementById("search").addEventListener("keyup", function () {
  const query = this.value;
  const sortOption = document.getElementById("sortBtn")?.dataset.sort || "";

  fetch(`${endpoint}?q=${encodeURIComponent(query)}&sort=${sortOption}`)
    .then((response) => response.json())
    .then((data) => updateTable(data.results, isCasesPage, isClosedCasesPage));

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

    let url = `${endpoint}?q=${encodeURIComponent(query)}`;
    if (sortOption && sortOption !== "reset") {
      url += `&sort=${sortOption}`;
      sortBtn.dataset.sort = sortOption;
    } else {
      sortBtn.dataset.sort = "";
    }

    fetch(url)
      .then((response) => response.json())
      .then((data) =>
        updateTable(data.results, isCasesPage, isClosedCasesPage)
      );

    // hide pagination if sorted or searched
    if (pagination) {
      pagination.style.display =
        query.trim() !== "" || (sortOption && sortOption !== "reset")
          ? "none"
          : "flex";
    }
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

    let url = `${endpoint}?q=${encodeURIComponent(query)}`;
    if (filterOption && filterOption !== "reset") {
      url += `&filter=${filterOption}`;
      filterBtn.dataset.filter = filterOption;
    } else {
      filterBtn.dataset.filter = "";
    }

    fetch(url)
      .then((response) => response.json())
      .then((data) =>
        updateTable(data.results, isCasesPage, isClosedCasesPage)
      );

    // hide pagination if filtered or searched
    if (pagination) {
      pagination.style.display =
        query.trim() !== "" || (filterOption && filterOption !== "reset")
          ? "none"
          : "flex";
    }
  });
});

// Function to update the data in table
const updateTable = (results, isCasesPage) => {
  const tbody = document.querySelector("#cases-table tbody");
  tbody.innerHTML = "";

  if (results.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td class="poppins-regular table-empty" colspan="7">
          <span>No matching ${
            isCasesPage || isClosedCasesPage ? "cases" : "reports"
          } found</span>
        </td>
      </tr>`;
    return;
  }

  results.forEach((r) => {
    const statusClass = r.status
      .toLowerCase()
      .replace(/closed\s*-\s*/g, "closed-")
      .replace(/\s+/g, "-");

    if (isCasesPage) {
      // ✅ CASES table row
      tbody.innerHTML += `
        <tr>
          <td class="poppins-regular">${r.report_id}</td>
          <td class="poppins-regular">${r.full_name}</td>
          <td class="poppins-regular">${formatDate(
            r.last_seen_date
          )}, ${formatTime(r.last_seen_time)}</td>
          <td class="poppins-regular">${r.reporter}</td>
          <td class="poppins-regular">${r.created_at}</td>
          <td class="poppins-regular ${statusClass}">${r.status}</td>
          <td>
            <div class="actionIcon">
              <i data-lucide="pen"></i>
              <i data-lucide="message-circle"></i>
            </div>
          </td>
        </tr>`;
    } else {
      // ✅ REPORTS table row
      tbody.innerHTML += `
        <tr
          data-id="${r.report_id}"
          data-name="${r.full_name}"
          data-reporter="${r.reporter}"
          data-created="${r.created_at}"
          data-status="${r.status}"
          data-age="${r.age}"
          data-gender="${r.gender}"
          data-last_seen_date="${r.last_seen_date}"
          data-last_seen_time="${r.last_seen_time}"
          data-clothing="${r.clothing}"
          data-description="${r.notes || ""}"
          data-media='${JSON.stringify(r.media || [])}'
        >
          <td class="poppins-regular">${r.report_id}</td>
          <td class="poppins-regular">${r.full_name}</td>
          <td class="poppins-regular">${r.reporter}</td>
          <td class="poppins-regular">${r.created_at}</td>
          <td class="poppins-regular ${statusClass}">${r.status}</td>
          <td>
            <div class="actionIcon">
              <i data-lucide="file-search"></i>
              <i data-lucide="message-circle"></i>
            </div>
          </td>
        </tr>`;
    }
  });

  if (window.lucide) {
    lucide.createIcons(); // re-render icons
  }

  // ✅ Reinitialize modal triggers for new icons
  setupModal('[data-lucide="file-search"]', "infoModal");
};

// helper functions
function formatDate(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatTime(timeStr) {
  if (!timeStr) return "";
  const [hours, minutes] = timeStr.split(":");
  const date = new Date();
  date.setHours(hours);
  date.setMinutes(minutes);
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}
