$(document).ready(function() {
  var page = RB.PageManager.getPage();

  // Adjust the styling of comment blocks to draw attention to their
  // existance.  Unfortunately the template is opaque to us, so we
  // have to resort to MutationObserver shenanigans.
  try {
    var observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        var $target = $(mutation.target);
        if ($target.hasClass('diff-box')) {
          // initial page layout
          var $flags = $target.find('.commentflag');
          $flags
            .filter(':not(.draft)')
            .parents('tr')
            .addClass('comment-block-container');
          $flags
            .filter('.draft')
            .parents('tr')
            .addClass('comment-block-container-draft');
        } else if ($target.prop('nodeName') === 'TH') {
          // comment added/removed
          var $tr = $target.parent('tr');
          $tr
            .removeClass('comment-block-container')
            .removeClass('comment-block-container-draft');
          if ($target.find('.commentflag').length) {
            $tr.addClass($target.find('.commentflag.draft').length ?
                         'comment-block-container-draft' :
                         'comment-block-container');
          }
        }
      });
    });
    observer.observe(document.querySelector('#diffs'),
                     { childList: true, subtree: true });
  } catch (e) {
    // we don't care if this fails
  }

  var FileDiffReviewerData = $('#file-diff-reviewer-data')
                             .data('file-diff-reviewer');
  var fileDiffReviewerModels = FileDiffReviewerData.map(function(item) {
    return new RB.FileDiffReviewerModel(item);
  });
  var fileDiffReviewerCollection = new RB.FileDiffReviewerCollection(
    fileDiffReviewerModels
  );

  var getButtonText = function(diff) {
    return diff.get('reviewed') ? 'reviewed' : 'not reviewed';
  };

  var renderDiffButton = function(fileDiffID) {
    var diffReviewable = fileDiffReviewerCollection.find(function(diff) {
      return diff.get('file_diff_id') == fileDiffID &&
        document.getElementById('file' + fileDiffID);
      });
    if (!diffReviewable) return;

    var reviewButton = document.createElement('button');
    reviewButton.title = 'Toggle the review status of this file';
    reviewButton.textContent = getButtonText(diffReviewable);
    reviewButton.classList.add('diff-file-btn');
    if (diffReviewable.get('reviewed')) {
      reviewButton.classList.add('reviewed');
    }

    reviewButton.addEventListener('click', function(event) {
      reviewButton.disabled = true;
      diffReviewable.save({ reviewed: !diffReviewable.get('reviewed') }, {
        success: function() {
          reviewButton.disabled = false;
          reviewButton.textContent = getButtonText(diffReviewable);
          reviewButton.classList.toggle('reviewed');
        },
        error: function(model, response) {
          reviewButton.disabled = false;
        }
      });
    });
    document.getElementById('file' + fileDiffID)
      .parentElement
      .appendChild(reviewButton);
  };

  // Listen for the diffview-loaded event, which is triggered when the
  // diffview has completed loaded, so we can add the buttons.
  if (!page.model.get('revision').get('isInterdiff')) {
    $(document).on('mr:diffview-loaded', function(event, fileDiffID) {
      renderDiffButton(fileDiffID);
    });
  }

  // Listening to a route change seems to be the only way
  // to know if the user requested an interdiff or a revision
  // using the revision slider. The 'isInterdiff' property above
  // can only be used once on page load because it's not updated
  // when the user selects a different revision range using the slider.
  page.router.on('route:revision', function(revision) {
    // If the user requests an interdiff `revision` is a range of revision
    // numbers separated by a dash.
    if (revision.indexOf('-') === -1) {
      // We still need to wait for an update of the FileDiff collection
      // to make sure we trigger a render of the diff buttons AFTER
      // the DiffFile views are rendered.
      page.model.get('files').once('update', renderDiffButton);
    }
  });

  // Restyle and modify content if commit message FileDiff is present.
  // commitMsgIds is an array holding a commit message FileDiff ids in
  // relation to Revision numbers.
  var commitMsgIds = [];
  var commitMsgData = $('#commit-message-filediff-data');
  var currentRevisionNumber = commitMsgData.data('currentRevisionNumber');
  if (currentRevisionNumber) {
    commitMsgIds = commitMsgData.data('commitMessageIds');
  }

  function changeCommitMsgIndexFileName() {
    // Change the fileName of the first FileDiff index if commit msg
    // FileDiff is present.
    $('.with-commit-msg-filediff #diff_index tbody tr:first td a')
      .text('commit-message');
  }

  function changeCommitMsgFileDiff(page) {
    // Commit message FileDiff element is displayed only on the first page.
    if (page !== 1) {
      // Remove styling of the first FileDiff element
      $('#review_request').removeClass('with-commit-msg-filediff');
      return;
    }
    // Add styling of the first FileDiff element
    $('#review_request').addClass('with-commit-msg-filediff');
    // Set the diff_index's commit message fileName
    changeCommitMsgIndexFileName();
  }

  function detectPageAndChangeCommitMsgFileDiff() {
    var page;
    if ($('#pagination1').children().length == 0) {
      page = 1;
    } else {
      page = +$('#pagination1 span.paginate-current').text();
    }
    changeCommitMsgFileDiff(page);
  }

  // Old ReviewRequests don't have commit message FileDiff. In such case
  // commitMsgIds is an empty array.
  if (currentRevisionNumber && commitMsgIds[currentRevisionNumber]) {
    // Check the initial stage of the pager.
    detectPageAndChangeCommitMsgFileDiff();
    // Listen to pagination events.
    page._paginationView1.on('pageSelected', changeCommitMsgFileDiff);
    page._paginationView2.on('pageSelected', changeCommitMsgFileDiff);
    // Listen to context loaded event and change name if needed.
    $(document).on('mr:diff-context-loaded',
                   detectPageAndChangeCommitMsgFileDiff);
  }
});
