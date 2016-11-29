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

  if (MozReview.isParent) {
    $('#review_request_extra').prepend(MRParents.parentWarning);
  }

  // Show all commits when link is clicked
  $('#mozreview-all-commits').on('click', function(e) {
    e.preventDefault();
    $('#mozreview-child-requests tr[hidden]').removeAttr('hidden');
    $(this).hide();
  });

  var reviewRequest = RB.PageManager.getPage().reviewRequest;
  RB.apiCall({
    type: 'GET',
    prefix: reviewRequest.get('sitePrefix'),
    noActivityIndicator: true,
    url: '/api/review-requests/' + reviewRequest.get('id') + '/reviews/' +
         '?max-results=200',
    success: function(data) {
      _.forEach(data.reviews, function(item) {
        var flag = item.extra_data['p2rb.review_flag'];
        var flagDesc = '';
        var reviewText = $('#review'+item.id+' .body');
        switch (flag) {
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
      });
    }
  });

  // Tooltips for landable and "r?" cells
  $('#mozreview-child-requests tbody .status').each(function() {
     var $element = $(this);
     var text = $element.attr('title');

     if (!text) return;

     $element.attr('title', '');

     // Draw the tooltip title and text
     var $tip = $('<div></div>').attr('class', 'review-tooltip').appendTo($element.parent());
     $('<div></div>').attr('class', 'review-tooltip-text').text(text).appendTo($tip);
  });

  // Add a link to the parent on submitted children.
  if (!MozReview.isParent) {
    $('#submitted-banner').append(
      $('<a></a>')
        .addClass('reopen')
        .attr('href', '/r/' + MozReview.parentID)
        .attr('title', "You can only Reopen when viewing the 'Review Summary / Parent'")
        .text('Reopen')
    );
  }
});
