$(document).ready(function() {
  function pollAutolandRequest(statusUrl, activityIndicator) {
    $.ajax({
        type: "GET",
        url: statusUrl
      })
      .done(function(requestStatus){
        var landed = requestStatus["landed"];

        if (landed !== null) {
          if (landed === true) {
            activityIndicator.hide();
            window.location.href = requestStatus["result"];
          } else {
            activityIndicator.addClass("error")
              .text(gettext("Importing the pull request failed: " + requestStatus["error_msg"]))
              .append(
                $("<a/>")
                  .text(gettext("Dismiss"))
                  .attr("href", "#")
                  .click(function() {
                    activityIndicator.fadeOut("fast");
                    return false;
                  })
              );
          }
        } else {
          setTimeout(pollAutolandRequest, 500, statusUrl, activityIndicator);
        }
      })
      .fail(function(xhr, textStatus, errorThrown){
        activityIndicator.addClass("error")
          .text(gettext("Error communicating with Autoland server"))
          .append(
            $("<a/>")
              .text(gettext("Dismiss"))
              .attr("href", "#")
              .click(function() {
                activityIndicator.fadeOut("fast");
                return false;
              })
          );
      });
  }

  $("#mozreview-import-pullrequest-trigger").click(function() {
    var activityIndicator = $("#activity-indicator")
      .removeClass("error")
      .text(gettext("Importing pull request..."))
      .show();

    $.ajax({
      type: "POST",
      url: PULLREQUEST_TRIGGER,
      data: {
        github_user: GITHUB_USER,
        github_repo: GITHUB_REPO,
        pullrequest: GITHUB_PULLREQUEST
      }
    })
    .done(function(data){
      pollAutolandRequest(data["status-url"], activityIndicator);
    })
    .fail(function(xhr, textStatus, errorThrown){
      activityIndicator.addClass("error")
        .text(gettext("Error submitting pull request"))
        .append(
          $("<a/>")
            .text(gettext("Dismiss"))
            .attr("href", "#")
            .click(function() {
              activityIndicator.fadeOut("fast");
              return false;
            })
        );
    });
  });
});
