const addSightingsBtn = document.getElementById("addSightingsBtn");
const addSightingsModal = document.getElementById("addSightingsModal");

if (addSightingsBtn && addSightingsModal) {
  addSightingsBtn.addEventListener("click", () => {
    // Get report ID from the open info modal
    const reportIdElement = document.getElementById("reportIdField");
    const reportId = reportIdElement ? reportIdElement.value : null;

    const reportInput = addSightingsModal.querySelector('input[name="report_id"]');
    if (reportInput && reportId) {
      reportInput.value = reportId;
    }

    addSightingsModal.classList.add("show");
    document.body.style.overflow = "hidden";
  });

  // Close modal (click X or background)
  addSightingsModal.addEventListener("click", (e) => {
    if (e.target.classList.contains("close") || e.target === addSightingsModal) {
      addSightingsModal.classList.remove("show");
      document.body.style.overflow = "";
    }
  });
}

const fileInput = document.getElementById("images");
const uploadContent = document.getElementById("uploadContent");

fileInput.addEventListener("change", (event) => {
  const files = event.target.files;
  if (files.length > 0) {
    let previewHTML = '<div class="preview-container">';
    for (const file of files) {
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => {
          previewHTML += `<img src="${e.target.result}" alt="Preview">`;
          uploadContent.innerHTML = previewHTML + "</div>";
        };
        reader.readAsDataURL(file);
      }
    }
  } else {
    // reset if no file selected
    uploadContent.innerHTML = `
      <i data-lucide="images"></i>
      <p class="poppins-regular">
          Click to
          <span class="browse poppins-medium">Browse</span> and upload
            images
      </p>
      <small class="poppins-regular">PNG, JPG</small>
          `;
  }
});

document.getElementById("addSightingsForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const form = e.target;
  const url = form.getAttribute("action");
  const formData = new FormData(form);

  try {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (result.status === "success") {
      Swal.fire({
        position: "top-end",
        icon: "success",
        title: result.message,
        showConfirmButton: false,
        timer: 1500,
        customClass: {
          popup: "my-swal-popup",
          title: "poppins-medium my-swal-title",
          icon: "my-swal-icon",
        },
      });

      // Close modal and reset form after short delay
      setTimeout(() => {
        form.reset();
        document.getElementById("addSightingsModal").classList.remove("show");
        document.body.style.overflow = "";
      }, 1600);
    } else {
      Swal.fire({
        position: "top-end",
        icon: "error",
        title: result.message,
        showConfirmButton: false,
        timer: 1500,
        customClass: {
          popup: "my-swal-popup",
          title: "poppins-medium my-swal-title",
          icon: "my-swal-icon",
        },
      });
    }
  } catch (err) {
    Swal.fire({
      position: "top-end",
      icon: "error",
      title: "Something went wrong while submitting your sighting.",
      showConfirmButton: false,
      timer: 1500,
      customClass: {
        popup: "my-swal-popup",
        title: "poppins-medium my-swal-title",
        icon: "my-swal-icon",
      },
    });
  }
});

const viewSightingsBtn = document.getElementById("viewSightingsBtn");
const sightingsModal = document.getElementById("sightingsModal");

if (viewSightingsBtn && sightingsModal) {
  const sightingsBody = sightingsModal.querySelector(".sightings-body");
  const modalTitle = sightingsModal.querySelector(".modal-title");

  viewSightingsBtn.addEventListener("click", function () {
    const reportIdField = document.getElementById("reportIdField");
    const reportId = reportIdField ? reportIdField.value : null;

    if (!reportId) {
      alert("No report selected.");
      return;
    }

    modalTitle.textContent = `Sightings for Case ID - ${reportId}`;
    sightingsBody.innerHTML = `<p class="poppins-regular subtext">Loading sightings...</p>`;

    sightingsModal.classList.add("show");

    fetch(`/cases/${reportId}/sightings/`)
      .then((response) => response.json())
      .then((data) => {
        sightingsBody.innerHTML = "";
        if (data.sightings.length === 0) {
          sightingsBody.innerHTML = `<p class="poppins-regular subtext">No sightings reported yet for this case.</p>`;
          return;
        }

        data.sightings.forEach((s) => {
          const item = document.createElement("div");
          item.classList.add("sighting-item", "poppins-regular");

          item.innerHTML = `
            <div class="sighting-header">
              <div class="info-group"><i data-lucide="calendar-clock"></i><span>${s.date_seen}, ${s.time_seen}</span></div>
              <div class="info-group"><i data-lucide="map-pinned"></i><span>${s.location}</span></div>
              <div class="info-group"><i data-lucide="user"></i><span>${s.volunteer}</span></div>
            </div>
            <p>${s.description}</p>
          `;

          if (s.media && s.media.length > 0) {
            const seePhotosBtn = document.createElement("button");
            seePhotosBtn.classList.add("see-more");
            seePhotosBtn.dataset.media = JSON.stringify(s.media);
            seePhotosBtn.innerHTML = `
              <span class="poppins-regular">See Photos</span>
              <i data-lucide="arrow-right"></i>
            `;
            seePhotosBtn.addEventListener("click", () => {
              const media = JSON.parse(seePhotosBtn.dataset.media);
              openImageModal(media);
            });
            item.appendChild(seePhotosBtn);
          }

          sightingsBody.appendChild(item);
        });

        lucide.createIcons();
      })
      .catch((err) => {
        console.error(err);
        sightingsBody.innerHTML = `<p class="poppins-regular subtext">Error loading sightings.</p>`;
      });
  });

  // Close modal
  sightingsModal.addEventListener("click", (e) => {
    if (e.target.classList.contains("close") || e.target === sightingsModal) {
      sightingsModal.classList.remove("show");
    }
  });
}

// ---------- Image Modal Logic ----------
let currentIndex = 0;
let currentMedia = [];

function openImageModal(mediaArray) {
  currentMedia = mediaArray;
  currentIndex = 0;
  showImage();

  const imgModal = document.getElementById("imgModal");
  imgModal.style.display = "flex"; // show modal
  document.body.style.overflow = "hidden";
}

function closeImageModal() {
  const imgModal = document.getElementById("imgModal");
  imgModal.style.display = "none";
  document.body.style.overflow = "";
}

function changeImage(direction) {
  if (!currentMedia.length) return;
  currentIndex = (currentIndex + direction + currentMedia.length) % currentMedia.length;
  showImage();
}

function showImage() {
  const modalImg = document.getElementById("modalImg");
  const dotsContainer = document.getElementById("mediaDots");

  modalImg.src = currentMedia[currentIndex].url;

  // Rebuild dots
  dotsContainer.innerHTML = "";
  currentMedia.forEach((_, i) => {
    const dot = document.createElement("span");
    dot.classList.add("dot");
    if (i === currentIndex) dot.classList.add("active");
    dot.addEventListener("click", () => {
      currentIndex = i;
      showImage();
    });
    dotsContainer.appendChild(dot);
  });
}
