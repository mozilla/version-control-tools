document.addEventListener("DOMContentLoaded", function () {
  // Add click handler to the localize dates link.
  var localize = document.getElementById("localize");
  if (localize) {
    localize.style.display = "";
    localize.addEventListener("click", function (event) {
      event.preventDefault();
      this.style.display = "none";
      var dates = document.querySelectorAll(".date");
      for (var i = 0; i < dates.length; i++) {
        dates[i].textContent = new Date(dates[i].textContent).toLocaleString();
      }
    });
  }

  // Add click handlers to toggle collapsible merge sections.
  var expanders = document.querySelectorAll(".expand");
  for (var i = 0; i < expanders.length; i++) {
    expanders[i].addEventListener("click", function (event) {
      event.preventDefault();

      // Expanding when currently collapsed, otherwise collapsing.
      var expanding = this.textContent == "[Expand]";
      this.textContent = expanding ? "[Collapse]" : "[Expand]";

      // The expander class looks like "expand hideid42"; derive the row
      // class ("id42") shared by every changeset row in this push.
      var match = this.className.match(/id\d+/);
      if (!match) {
        return;
      }

      // Toggle every row of this push except the first one, mirroring
      // jQuery's $('.idN').nextAll('.idN').
      var rows = document.querySelectorAll("." + match[0]);
      for (var j = 1; j < rows.length; j++) {
        rows[j].style.display = expanding ? "" : "none";
      }
    });
  }
});
