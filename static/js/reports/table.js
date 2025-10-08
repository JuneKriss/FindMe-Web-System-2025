const table = document.getElementById("cases-table");

table.addEventListener("click", function (e) {
  const trashIcon = e.target.closest("[data-lucide='trash']");
  if (!trashIcon) return;

  const row = trashIcon.closest("tr");
  const reportId = row.dataset.id;

  Swal.fire({
    title: "Are you sure?",
    html: `Are you sure you want to permanently delete report #${reportId}? <br>This action cannot be undone.`,
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Yes, delete it!",
    cancelButtonText: "Cancel",
    buttonsStyling: false,
    customClass: {
      popup: "swal-custom-popup",
      title: "poppins-regular swal-title-custom",
      htmlContainer: "poppins-regular swal-text-custom",
      confirmButton: "swal-confirm-btn poppins-medium",
      cancelButton: "swal-cancel-btn poppins-medium",
    },
    background: "#ffffff",
    color: "#14213d",
  }).then((result) => {
    if (result.isConfirmed) {
      fetch(deleteReportUrl, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ report_id: reportId }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            Swal.fire({
              position: "top-end",
              icon: "success",
              title: data.message,
              showConfirmButton: false,
              timer: 1000,
              timerProgressBar: true,
              customClass: {
                popup: "my-swal-popup",
                title: "poppins-medium my-swal-title",
                icon: "my-swal-icon",
              },
              background: "#ffffff",
              color: "#14213d",
            }).then(() => {
              // wait before reloading so the user sees it
              setTimeout(() => {
                location.reload();
              }, 400);
            });
          } else {
            Swal.fire({
              position: "top-end",
              icon: "error",
              title: data.message,
              showConfirmButton: false,
              timer: 2000,
              timerProgressBar: true,
              customClass: {
                popup: "my-swal-popup",
                title: "poppins-medium my-swal-title",
                icon: "my-swal-icon",
              },
              background: "#ffffff",
              color: "#14213d",
            });
          }
        })
        .catch(() => {
          Swal.fire({
            position: "top-end",
            icon: "error",
            title: "Something went wrong.",
            showConfirmButton: false,
            timer: 2000,
            timerProgressBar: true,
            customClass: {
              popup: "my-swal-popup",
              title: "poppins-medium my-swal-title",
              icon: "my-swal-icon",
            },
            background: "#ffffff",
            color: "#14213d",
          });
        });
    }
  });
});
