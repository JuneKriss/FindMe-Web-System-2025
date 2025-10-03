const setupModal = (triggerSelector, modalId) => {
  const triggers = document.querySelectorAll(triggerSelector);
  const modal = document.getElementById(modalId);
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

          modal.querySelector(
            "#report_id"
          ).innerHTML = `<h3 class="poppins-medium" id="report_id">Report #${row.dataset.id}</h3>`;
          modal.querySelector("#fullName").value = row.dataset.name || "";
          modal.querySelector("#age").value = row.dataset.age || "";
          modal.querySelector("#gender").value = row.dataset.gender || "";

          // Date conversion
          if (rawDate) {
            const dateObj = new Date(rawDate);
            if (!isNaN(dateObj)) {
              const formattedDate = dateObj.toISOString().split("T")[0]; // "YYYY-MM-DD"
              modal.querySelector("#last_seen_date").value = formattedDate;
            }
          }

          modal.querySelector("#last_seen_time").value =
            row.dataset.last_seen_time || "";
          modal.querySelector("#clothing").value = row.dataset.clothing || "";
          modal.querySelector("#description").value =
            row.dataset.description || "";
          modal.querySelector("#reported_at").value = row.dataset.created || "";

          const statusSelect = modal.querySelector("#statusSelect");
          if (statusSelect) {
            statusSelect.value = row.dataset.status || "";
          }

          const statusBadge = modal.querySelector(".status-badge");
          const statusText = row.children[4].textContent.trim();
          statusBadge.className = `poppins-regular status-badge ${slugify(
            statusText
          )}`;
          statusBadge.innerHTML = `<span class="status-dot ${slugify(
            statusText
          )}"></span> ${statusText}`;

          const reportIdField = modal.querySelector("#reportIdField");
          if (reportIdField) {
            reportIdField.value = row.dataset.id;
          }

          //Handle Media
          const mediaData = row.dataset.media
            ? JSON.parse(row.dataset.media)
            : [];
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
            if (slides.length > 0)
              showSlide((currentIndex - 1 + slides.length) % slides.length);
          };
          modal.querySelector("#nextArrow").onclick = () => {
            if (slides.length > 0)
              showSlide((currentIndex + 1) % slides.length);
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
setupModal('[data-lucide="file-search"]', "infoModal"); // Report details modal
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
