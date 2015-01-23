var RBMozUI = {};

$(document).ready(function() {
  // The back-end should have already supplied us with the squashed / root review
  // request ID (whether or not we're already looking at it), and set it as
  // the data-id attribute on the rbmozui-commits-root element. Let's get that
  // first - because if we can't get it, we're stuck.
  var rootID = $("#rbmozui-commits-root").data("id");
  if (!rootID) {
    console.error("Could not find a valid id for the root review " +
                  "request.");
    return;
  }

  console.log("Found root review request ID: " + rootID);

  RBMozUI.rootReviewRequest = new RB.ReviewRequest({id: rootID});

  var pageEditor = RB.PageManager.getPage().reviewRequestEditor;

  RBMozUI.currentIsMutableByUser = pageEditor.get("mutableByUser");

  RBMozUI.rootEditor = new RB.ReviewRequestEditor({
    reviewRequest: RBMozUI.rootReviewRequest,
    mutableByUser: RBMozUI.currentIsMutableByUser
  });
});