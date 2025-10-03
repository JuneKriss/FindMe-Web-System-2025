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
