lucide.createIcons();

const setupModal = (triggerSelector, modalId) => {
  const triggers = document.querySelectorAll(triggerSelector);
  const modal = document.getElementById(modalId);
  const path = window.location.pathname; // get current path
  const label = path.startsWith("/cases/") || path === "/cases/" ? "Case" : "Report";
  if (!modal) return;

  const closeBtn = modal.querySelector(".close");

  const slugify = (text) =>
    text
      .toString()
      .toLowerCase()
      .trim()
      // replace any sequence of non-alphanumeric chars with a single dash
      .replace(/[^a-z0-9]+/g, "-")
      // remove leading/trailing dashes
      .replace(/^-+|-+$/g, "");

  // Open modal
  triggers.forEach((trigger) => {
    trigger.addEventListener("click", (e) => {
      // If this is the report details modal, inject data
      if (modalId === "infoModal") {
        const row = e.target.closest("tr");
        if (row) {
          const rawDate = row.dataset.last_seen_date || "";

          modal.querySelector("#report_id").innerHTML =
            `<h3 class="poppins-medium" id="report_id">${label} #${row.dataset.id}</h3>`;
          modal.querySelector("#fullName").value = row.dataset.name || "";
          modal.querySelector("#age").value = row.dataset.age || "";
          modal.querySelector("#gender").value = row.dataset.gender || "";

          // Date conversion
          if (rawDate) {
            const dateObj = new Date(rawDate);
            if (!isNaN(dateObj)) {
              // Get local YYYY-MM-DD instead of UTC
              const year = dateObj.getFullYear();
              const month = String(dateObj.getMonth() + 1).padStart(2, "0");
              const day = String(dateObj.getDate()).padStart(2, "0");
              const formattedDate = `${year}-${month}-${day}`;
              modal.querySelector("#last_seen_date").value = formattedDate;
            }
          }

          modal.querySelector("#last_seen_time").value = row.dataset.last_seen_time || "";
          modal.querySelector("#clothing").value = row.dataset.clothing || "";
          modal.querySelector("#description").value = row.dataset.description || "";
          modal.querySelector("#reported_at").value = row.dataset.created || "";

          const statusSelect = modal.querySelector("#statusSelect");
          if (statusSelect) {
            statusSelect.value = row.dataset.status || "";
          }

          const statusBadge = modal.querySelector(".status-badge");
          const statusText = row.dataset.status || "Unknown";
          statusBadge.className = `poppins-regular status-badge ${slugify(statusText)}`;
          statusBadge.innerHTML = `<span class="status-dot ${slugify(statusText)}"></span> ${statusText}`;

          const reportIdField = modal.querySelector("#reportIdField");
          if (reportIdField) {
            reportIdField.value = row.dataset.id;
          }

          //Handle Media
          const mediaData = row.dataset.media ? JSON.parse(row.dataset.media) : [];
          const mediaContainer = modal.querySelector(".media");
          const dotsContainer = modal.querySelector(".mediaDots");

          // Clear old content
          mediaContainer.innerHTML = "";
          dotsContainer.innerHTML = "";

          // Build image slides
          mediaData.forEach((m, index) => {
            const img = document.createElement("img");
            img.src = m.url;
            img.alt = "Report image";
            img.style.display = index === 0 ? "block" : "none";
            img.classList.add("clickable-img");
            mediaContainer.appendChild(img);

            // Dot
            const dot = document.createElement("span");
            dot.className = "dot" + (index === 0 ? " active" : "");
            dotsContainer.appendChild(dot);
          });

          // Carousel navigation (prev/next)
          let currentIndex = 0;
          const slides = mediaContainer.querySelectorAll("img");
          const dots = dotsContainer.querySelectorAll(".dot");

          const showSlide = (i) => {
            slides.forEach((s, idx) => {
              s.style.display = idx === i ? "block" : "none";
              dots[idx].classList.toggle("active", idx === i);
            });
            currentIndex = i;
          };

          modal.querySelector("#prevArrow").onclick = () => {
            if (slides.length > 0) showSlide((currentIndex - 1 + slides.length) % slides.length);
          };
          modal.querySelector("#nextArrow").onclick = () => {
            if (slides.length > 0) showSlide((currentIndex + 1) % slides.length);
          };
        }
      }

      modal.classList.add("show");
    });
  });

  // Close modal by button
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      modal.classList.remove("show");
    });
  }

  // Close modal by clicking outside content
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.classList.remove("show");
    }
  });
};

// Setup both modals
setupModal('[data-lucide="file-search"]', "infoModal");
setupModal('[data-lucide="pen"]', "infoModal");
setupModal(".head .left button", "addReportModal");

//Handle Image/Media Clicks
const modal = document.getElementById("imgModal");
const modalImg = document.getElementById("modalImg");
const closeBtn = modal.querySelector(".close");

// open modal when image is clicked
function openImageModal(imgElement) {
  modal.style.display = "flex";
  modalImg.src = imgElement.src;
}

// close modal when clicking close button
function closeImageModal() {
  modal.style.display = "none";
}

// Close when clicking background
modal.addEventListener("click", (e) => {
  if (e.target === modal) {
    closeImageModal();
  }
});

// Close when clicking the "X"
closeBtn.addEventListener("click", closeImageModal);

// Attach to all images you want to enlarge
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("clickable-img")) {
    openImageModal(e.target);
  }
});

//Dashboard Redirect
window.addEventListener("load", () => {
  const params = new URLSearchParams(window.location.search);
  const reportId = params.get("report_id");
  if (!reportId) return;

  // Wait for DOM + Lucide icons to be ready
  setTimeout(() => {
    const row = document.querySelector(`tr[data-id="${reportId}"]`);
    if (row) {
      // Try to find the Lucide icon (either <i> or <svg>)
      const infoIcon =
        row.querySelector('[data-lucide="file-search"]') ||
        row.querySelector(".lucide-file-search");

      if (infoIcon) {
        infoIcon.dispatchEvent(new Event("click", { bubbles: true }));
      } else {
        Swal.fire({
          title: "Icon not found",
          text: "We couldn’t find the report details icon for this entry.",
          icon: "warning",
          confirmButtonText: "OK",
          customClass: { confirmButton: "poppins-medium" },
        });
      }
    } else {
      Swal.fire({
        title: "Report not found",
        text: "The report you're trying to view doesn't exist or was removed.",
        icon: "warning",
        confirmButtonText: "OK",
        customClass: { confirmButton: "poppins-medium" },
      });
    }
  }, 400); // small delay ensures DOM + Lucide finished rendering
});
