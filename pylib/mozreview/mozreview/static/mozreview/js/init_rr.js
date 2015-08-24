var MozReview = {};

$(document).ready(function() {
  // The back-end should have already supplied us with the parent review
  // request ID (whether or not we're already looking at it), and set it as
  // the data-id attribute on the mozreview-parent-request element. Let's get
  // that first - because if we can't get it, we're stuck.
  var parentID = $("#mozreview-parent-request").data("id");

  if (!parentID) {
    console.error("Could not find a valid id for the parent review " +
                  "request.");
    return;
  }

  // The current user's scm level has been injected in an invisible div.
  MozReview.scmLevel = $("#scm-level").data("scm-level");
  MozReview.hasScmLevel1 = MozReview.scmLevel >= 1;
  MozReview.hasScmLevel3 = MozReview.scmLevel == 3;

  console.log("Found parent review request ID: " + parentID);

  var page = RB.PageManager.getPage();

  // Setup a CSS class so we can differentiate between parent
  // and commit review requests.
  var currentID = page.reviewRequest.id;

  if (currentID == parentID) {
      $("body").addClass("parent-request");
  } else {
      $("body").addClass("commit-request");
  }

  MozReview.parentReviewRequest = new RB.ReviewRequest({id: parentID});

  var pageReviewRequest = page.reviewRequest;
  var pageEditor = page.reviewRequestEditor;
  var pageView = page.reviewRequestEditorView;

  MozReview.currentIsMutableByUser = pageEditor.get("mutableByUser");
  MozReview.isParent = (parentID == pageReviewRequest.id);
  MozReview.parentEditor = MozReview.isParent ? pageEditor
                                              : null;
  MozReview.parentView = MozReview.isParent ? pageView
                                            : null;
  $(document).trigger("mozreview_ready");
});
