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

  // Whether or not the repository has associated try and landing repositories
  // is in an invisible div.
  MozReview.hasTryRepository = $("#repository").data("has-try-repository");
  MozReview.landingRepository = $("#repository").data("landing-repository");

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

  var pageReviewRequest = page.reviewRequest;
  var pageEditor = page.reviewRequestEditor;
  var pageView = page.reviewRequestEditorView;

  MozReview.currentIsMutableByUser = pageEditor.get("mutableByUser");
  MozReview.isParent = (parentID == pageReviewRequest.id);
  MozReview.parentEditor = MozReview.isParent ? pageEditor
                                              : null;
  MozReview.parentView = MozReview.isParent ? pageView
                                            : null;

  // Review Board doesn't currently expose approval status in the
  // review request model so we extend it and use our own model
  // for the parent so we can access it.
  var patchedRR = RB.ReviewRequest.extend({
    defaults: function () {
      return _.defaults({
        approved: false,
        approvalFailure: null
      }, RB.ReviewRequest.prototype.defaults());
    },

    attrToJsonMap: _.defaults({
      approvalFailure: 'approval_failure'
    }, RB.ReviewRequest.prototype.attrToJsonMap),

    deserializedAttrs: [
      'approved',
      'approvalFailure'
    ].concat(RB.ReviewRequest.prototype.deserializedAttrs)
  });
  MozReview.parentReviewRequest = new patchedRR({id: parentID});
  // Kick off the fetch here so the data is ready ASAP,
  // we'll use it eventually.
  MozReview.parentReviewRequest.fetch();

  MozReview.reviewRequestPending = page.reviewRequest.attributes.state == RB.ReviewRequest.PENDING;

  $(document).trigger("mozreview_ready");
});
