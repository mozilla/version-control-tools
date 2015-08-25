$(document).on("mozreview_ready", function() {
  var TRY_AUTOLAND = "/api/extensions/mozreview.extension.MozReviewExtension/try-autoland-triggers/";

  $("#mozreview-autoland-try-trigger").click(function() {
    var box = $("<div/>")
        .addClass("formdlg")
        .keypress(function(e) {
            e.stopPropagation();
        });

    box.width("60em");
    var html = [
      '<label for="mozreview-autoland-try-syntax">TryChooser Syntax</label>',
      '<textarea id="mozreview-autoland-try-syntax" name="mozreview-autoland-try-syntax" placeholder="try: -b do -p win32 -u all -t none"/>',
      '<p>Enter TryChooser syntax here for your Try build. <a href="http://trychooser.pub.build.mozilla.org/" target="_blank">You can graphically build TryChooser syntax here.</a></p>',
      '<span id="try-error">You have an error in your try syntax</span>'
    ];

    for (var i = 0; i < html.length; ++i) {
      box.append($(html[i]).addClass("mozreview-autoland-try-chooser-element"));
    }

    box.modalBox({
        title: "Trigger a Try Build",
        buttons: [
          $('<input type="button"/>')
              .val(gettext("Cancel")),
          $('<input type="button"/>')
            .val("Submit")
            .click(function() {
              var submit = $(this);
              var tryInput = $("#mozreview-autoland-try-syntax");
              var trySyntax = $("#mozreview-autoland-try-syntax").val();

              if (trySyntax.indexOf('try: ') !== 0) {
                $('#try-syntax-error').css('display', 'block');
                return false;
              } else {
                $('#try-syntax-error').css('display', 'none')
                submit.enable(false);
                tryInput.enable(false);

                var activityIndicator = $("#activity-indicator")
                  .removeClass("error")
                  .text(gettext("Scheduling jobs..."))
                  .show();

                $.ajax({
                  type: "POST",
                  url: TRY_AUTOLAND,
                  data: {
                    review_request_id: MozReview.parentReviewRequest.id,
                    try_syntax: trySyntax
                  }
                })
                .done(function(){
                  // There may be a better way to get the review request updates
                  // but this is probably good enough for now
                  window.location.reload()
                })
                .fail(function(){
                  submit.enable(true);
                  tryInput.enable(true);

                  activityIndicator.addClass("error")
                    .text(gettext("A server error occurred.")) // TODO: Pump out diagnostic information somewhere
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
                  return false;
              }
            })
        ]
    });

    $("#mozreview-autoland-try-syntax").focus();

    return false;
  });

  var isDraft = $("#draft-banner").is(":visible");
  $("#mozreview-autoland-try-trigger").enable(!isDraft && MozReview.currentIsMutableByUser);
});
