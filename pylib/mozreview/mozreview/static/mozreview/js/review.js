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

  // Change string of "Edit Review" button in the review banner that
  // shows up when a pending review is waiting to be published.
  $("#review-banner-edit").val("Finish...");

  // Change string of "Review" button to be a verb so people better
  // understand what clicking it does.
  $("#review-link").text("Finish Review...");

  if (MozReview.isParent) {
    $('#review_request_extra').prepend(MRParents.parentWarning);
  }

  var reviewRequest = RB.PageManager.getPage().reviewRequest;
  RB.apiCall({
    type: 'GET',
    prefix: reviewRequest.get('sitePrefix'),
    noActivityIndicator: true,
    url: '/api/review-requests/'+reviewRequest.get('id')+'/reviews/'
       + '?max-results=200',
    success: function(data) {
      _.forEach(data.reviews, function(item) {
        var flag = item.extra_data['p2rb.review_flag'];
        var flagDesc = '';
        var reviewText = $('#review'+item.id+' .body');
        switch(flag){
          case ' ':
            flagDesc = 'Review flag cleared';
            break;
          case 'r-':
          case 'r+':
          case 'r?':
            flagDesc = 'Review flag: '+flag;
            break;
        }
        $(reviewText).prepend(
          $('<h4 class="body_top">'+flagDesc+'</h4>')
        );
      })
    }
  });
});
