$(document).on("mozreview_ready", function() {
  // Workaround until we get a template hook point before
  // the draft banner thing.
  $("#new-navbar").insertBefore(".box.review-request");
  $("#new-navbar").show();

  // Disable all editable fields in the review
  // request box.
  $(".main .editable").inlineEditor("disable");
  // And then re-enable just the ones for reviewers in
  // the commits list.
  $("#mozreview-child-requests .editable").inlineEditor("enable");

  $('label[for="field_target_people"]').parent().parent().hide();

  // Change string of "Edit Review" button in the review banner that
  // shows up when a pending review is waiting to be published.
  $("#review-banner-edit").val("Finish...");

  // Change string of "Review" button to be a verb so people better
  // understand what clicking it does.
  $("#review-link").text("Finish Review...");
});
