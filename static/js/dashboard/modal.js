const modal = document.getElementById("imgModal");
const modalImg = document.getElementById("modalImg");
const dotsContainer = document.getElementById("mediaDots");
const prevArrow = document.getElementById("prevArrow");
const nextArrow = document.getElementById("nextArrow");

let currentIndex = 0;
let currentImages = [];

// Open modal and load all images for a given report
function openImageModal(reportId, startIndex = 0) {
  const imgs = document.querySelectorAll(`img[data-report-id="${reportId}"]`);
  currentImages = Array.from(imgs).map((img) => img.src);

  if (currentImages.length === 0) return;

  currentIndex = startIndex;
  showImage(currentIndex);
  renderDots();

  modal.style.display = "flex";

  // ✅ Hide arrows and dots if only 1 image
  if (currentImages.length === 1) {
    prevArrow.style.display = "none";
    nextArrow.style.display = "none";
    dotsContainer.style.display = "none";
  } else {
    prevArrow.style.display = "";
    nextArrow.style.display = "";
    dotsContainer.style.display = "";
  }
}

function closeImageModal() {
  modal.style.display = "none";
}

function changeImage(direction) {
  if (!currentImages.length) return;
  currentIndex = (currentIndex + direction + currentImages.length) % currentImages.length;
  showImage(currentIndex);
  updateDots();
}

function showImage(index) {
  modalImg.src = currentImages[index];
}

function renderDots() {
  dotsContainer.innerHTML = "";
  currentImages.forEach((_, i) => {
    const dot = document.createElement("span");
    dot.classList.add("dot");
    if (i === currentIndex) dot.classList.add("active");
    dot.addEventListener("click", () => {
      currentIndex = i;
      showImage(currentIndex);
      updateDots();
    });
    dotsContainer.appendChild(dot);
  });
}

function updateDots() {
  const dots = dotsContainer.querySelectorAll(".dot");
  dots.forEach((dot, i) => dot.classList.toggle("active", i === currentIndex));
}

// Close modal when background is clicked
modal.addEventListener("click", (e) => {
  if (e.target === modal) closeImageModal();
});
