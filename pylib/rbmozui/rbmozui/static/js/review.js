$(document).ready(function() {
  // Workaround until we get a template hook point before
  // the draft banner thing.
  $("#new-navbar").insertBefore(".box.review-request");
  $("#new-navbar").show();

  // Disable all editable fields.
  $(".editable").inlineEditor("disable");

  // Remove any of the non-header text in the draft banner
  // that we can't get rid of nicely with CSS.
  $("#draft-banner").click(function() {
      window.location = (SITE_ROOT + 'rbmozui/commits/' + gReviewRequest.id);
  });
});
