var MozReview = {};

$(document).ready(function() {
  // The back-end should have already supplied us with the squashed / root review
  // request ID (whether or not we're already looking at it), and set it as
  // the data-id attribute on the mozreview-commits-root element. Let's get that
  // first - because if we can't get it, we're stuck.
  var rootID = $("#mozreview-commits-root").data("id");
  if (!rootID) {
    console.error("Could not find a valid id for the root review " +
                  "request.");
    return;
  }

  console.log("Found root review request ID: " + rootID);

  // Setup a CSS class so we can differentiate between parent
  // and commit review requests.
  var currentID = RB.PageManager.getPage().reviewRequest.id;
  if (currentID == rootID) {
      $("body").addClass("parent-request");
  } else {
      $("body").addClass("commit-request");
  }

  MozReview.rootReviewRequest = new RB.ReviewRequest({id: rootID});

  var pageEditor = RB.PageManager.getPage().reviewRequestEditor;

  MozReview.currentIsMutableByUser = pageEditor.get("mutableByUser");

  MozReview.rootEditor = new RB.ReviewRequestEditor({
    reviewRequest: MozReview.rootReviewRequest,
    mutableByUser: MozReview.currentIsMutableByUser
  });
});