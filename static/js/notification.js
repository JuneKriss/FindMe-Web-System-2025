if (window.lucide) {
  lucide.createIcons(); // re-render icons
}

// Mark as read
const checkIcons = document.querySelectorAll(".mark-read");

checkIcons.forEach((icon) => {
  icon.addEventListener("click", () => {
    const notifId = icon.getAttribute("data-id");

    fetch(`/notifications/mark-read/${notifId}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          const notifDiv = icon.closest(".notification");
          notifDiv.classList.add("read");

          icon.classList.add("fade-out");
          setTimeout(() => icon.remove(), 200);
        }
      })
      .catch((err) => console.error("Error:", err));
  });
});

// Delete notification
const deleteIcons = document.querySelectorAll(".delete-notif");
deleteIcons.forEach((icon) => {
  icon.addEventListener("click", () => {
    const notifId = icon.getAttribute("data-id");

    fetch(`/notifications/delete/${notifId}/`, {
      method: "POST",
      headers: { "X-CSRFToken": getCookie("csrftoken") },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          const notifDiv = icon.closest(".notification");
          notifDiv.classList.add("fade-out");
          setTimeout(() => notifDiv.remove(), 200);
        }
      });
  });
});

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const markAllBtn = document.getElementById("markAllBtn");

if (markAllBtn) {
  markAllBtn.addEventListener("click", () => {
    Swal.fire({
      title: "Mark all as read?",
      text: "This will mark all unread notifications as read.",
      icon: "question",
      showCancelButton: true,
      confirmButtonText: "Yes, mark all",
      cancelButtonText: "Cancel",
      customClass: {
        title: "poppins-regular swal-title",
        htmlContainer: "poppins-regular swal-text",
        confirmButton: "poppins-medium swal-confirm",
        cancelButton: "poppins-medium swal-cancel",
      },
    }).then((result) => {
      if (result.isConfirmed) {
        fetch("/notifications/mark-all-read/", {
          method: "POST",
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.success) {
              Swal.fire({
                position: "top-end",
                icon: "success",
                title: data.message || "All notifications marked as read.",
                showConfirmButton: false,
                timer: 1500,
                customClass: {
                  popup: "my-swal-popup",
                  title: "poppins-medium my-swal-title",
                  icon: "my-swal-icon",
                },
              }).then(() => {
                document.querySelectorAll(".notification").forEach((notif) => {
                  notif.classList.add("read");
                  const checkIcon = notif.querySelector(".mark-read");
                  if (checkIcon) checkIcon.remove();
                });
              });
            } else {
              Swal.fire({
                title: "No unread notifications",
                text: data.message || "You’re already up to date!",
                icon: "info",
                confirmButtonText: "OK",
                customClass: {
                  title: "poppins-regular swal-title",
                  htmlContainer: "poppins-regular swal-text",
                  confirmButton: "poppins-medium swal-confirm",
                },
              });
            }
          })
          .catch((err) => {
            Swal.fire({
              title: "Error",
              text: "Something went wrong. Please try again later.",
              icon: "error",
              confirmButtonText: "OK",
              customClass: {
                title: "poppins-regular swal-title",
                htmlContainer: "poppins-regular swal-text",
                confirmButton: "poppins-medium swal-confirm",
              },
            });
            console.error(err);
          });
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", function () {
  const headers = document.querySelectorAll(".case-header");

  headers.forEach((header) => {
    header.addEventListener("click", function () {
      const targetId = this.getAttribute("data-target");
      const container = document.getElementById(targetId);
      const icon = this.querySelector(".toggle-icon");

      container.classList.toggle("collapsed");

      if (container.classList.contains("collapsed")) {
        container.style.display = "none";
        icon.style.transform = "rotate(-90deg)";
      } else {
        container.style.display = "block";
        icon.style.transform = "rotate(0deg)";
      }
    });
  });
});
//////////////////////////////////////////////////////////////////////////////////////////////////
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

    if (value === "cases") {
      window.location.href = "?group=cases";
    }

    if (value === "reset") {
      window.location.href = "?";
    }

    // Remove active class from all items in this dropdown
    dropdown.querySelectorAll("li").forEach((li) => li.classList.remove("active"));

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
    document.querySelectorAll(".dropdown").forEach((d) => d.classList.remove("active"));
  }
});

//////////////////////////////////////////////////////////////////////////////////////////////////
