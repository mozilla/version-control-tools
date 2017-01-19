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
  var toggleTable = function(forceOpen) {
    var $commitsViewLink = $('#mozreview-all-commits');
    var $commitsTable = $('#mozreview-child-requests');
    var isExpanded = $commitsTable.hasClass('expanded');

    if (forceOpen || !isExpanded) {
      $commitsTable.addClass('expanded');
      $commitsViewLink.attr('data-expanded', true).text($commitsViewLink.attr('data-one-text'));
    }
    else {
      $commitsTable.removeClass('expanded');
      $commitsViewLink.attr('data-expanded', false).text($commitsViewLink.attr('data-all-text'));
    }
  };

  $('body').on('click', '#mozreview-all-commits', function(e) {
    e.preventDefault();
    toggleTable();
  });

  // Toggle "always show all commits" in table cookie
  $('body').on('change', '#mozreview-commits-presist input', function(e) {
    RB.UserSession.instance.set('commitsTableAlwaysShowFull', this.checked + '');
    if (this.checked) {
      toggleTable(true);
    }
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
