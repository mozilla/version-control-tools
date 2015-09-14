/**
 * This code manages the setting of reviewers in the Review Series list
 * for pushed review requests.
 *
 * Portions of this code (mentioned below) are
 * Copyright (c) 2007-2014 Beanbag, Inc.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of
 * this software and associated documentation files (the "Software"), to deal in
 * the Software without restriction, including without limitation the rights to
 * use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is furnished to do
 * so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

$(document).on("mozreview_ready", function() {
  if (!MozReview.isParent) {
    // At this time, there's no need to set up the editors for the reviewers if
    // we're not looking at the parent review request.
    return;
  }

  console.assert(MozReview.parentEditor, "We should have a parent commit editor");
  console.assert(MozReview.parentView, "We should have a parent commit editor view");

  /**
   * A not-amazing error reporting mechanism that depends on a DOM
   * node with ID "error-container" existing on the page somewhere.
   */
  var $ErrorContainer = $("#error-container");
  function reportError(aMsg) {
    if (typeof(aMsg) == "object") {
      if (aMsg.errorText) {
        aMsg = aMsg.errorText;
      } else {
        aMsg = JSON.stringify(aMsg, null, "\t");
      }
    }

    $("#error-info").text(aMsg);
    $("#error-stack").text(new Error().stack);
    $ErrorContainer.attr("haserror", "true");
    RB.PageManager.getPage().reviewRequestEditorView._scheduleResizeLayout();
  }

  $("#error-close").click(function() {
    $ErrorContainer.attr("haserror", "false");
  });

  $("#error-stack-toggle").click(function() {
    $("#error-stack").toggle();
  });

  // Hook up the inline editor for each commit's reviewer list. This inline editor
  // code is mostly copied from Review Board itself - please see the copyright
  // notice in the header.
  var editorOptions = {
    editIconClass: "rb-icon rb-icon-edit",
    useEditIconOnly: true,
    enabled: true
  };

  var reviewerList = $(".mozreview-child-reviewer-list");
  var editors = {};

  if(MozReview.currentIsMutableByUser){
  var reviewerListEditors = reviewerList
    .inlineEditor(editorOptions)
    .on({
      beginEdit: function() {
        // The editCount is used to determine if we should warn the user before
        // unloading the page because they still have an editor open.
        console.log("beginning edit " + $(this).data("id"));
        MozReview.parentEditor.incr("editCount");
      },
      cancel: function() {
        MozReview.parentEditor.decr("editCount");
      },
      complete: function(e, value) {
        // The ReviewRequestEditor is the interface that we use to modify
        // a review request easily.
        var editor, reviewRequest;
        var id = $(this).data("id");
        if (!editors[id]) {
          reviewRequest = new RB.ReviewRequest({id: $(this).data("id")});
          editor = new RB.ReviewRequestEditor({reviewRequest: reviewRequest});
          editors[id] = editor;
        } else {
          editor = editors[id];
        }

        var originalContents = $(this).text();

        var warning = $("#review-request-warning");
        // For Mozilla, we sometimes use colons as a prefix for searching for
        // IRC nicks - that's just a convention that has developed over time.
        // Since IRC nicks are what MozReview recognizes, we need to be careful
        // that the user hasn't actually included those colon prefixes, otherwise
        // MozReview is going to complain that it doesn't recognize the user (since
        // MozReview's notion of a username doesn't include the colon prefix).
        var sanitized = value.split(" ").map(function(aName) {
          var trimmed = aName.trim();
          if (trimmed.indexOf(":") == 0) {
            trimmed = trimmed.substring(1);
          }
          return trimmed;
        });

        // This sets the reviewers on the child review request.
        editor.setDraftField(
          "targetPeople",
          sanitized.join(", "),
          {
            jsonFieldName: "target_people",
            error: function(error) {
              MozReview.parentEditor.decr("editCount");
              console.error(error.errorText);

              // This error display code is copied pretty much verbatim
              // from Review Board core to match the behaviour of attempting
              // to set a target reviewer to one or more users that does not
              // exist.
              warning
                .delay(6000)
                .fadeOut(400, function() {
                  $(this).hide();
                })
                .show()
                .html(error.errorText);

              // Revert the list back to what we started with.
              $(this).text(originalContents);
            },
            success: function() {
              MozReview.parentEditor.decr("editCount");
              MozReview.parentEditor.set('public', false);
              MozReview.parentEditor.trigger('saved');

            }
          }, this);
      }
    });
  }

  // This next bit sets up the autocomplete popups for reviewers. This
  // code is mostly copied from Review Board itself - please see the
  // copyright notice in the header.
  var acOptions = {
    fieldName: "users",
    nameKey: "username",
    descKey: "fullname",
    extraParams: {
      fullname: 1
    },

    cmp: function(term, a, b) {
      /*
       * Sort the results with username matches first (in
       * alphabetical order), followed by real name matches (in
       * alphabetical order)
       */

      var aUsername = a.data.username,
          bUsername = b.data.username,
          aFullname = a.data.fullname || "",
          bFullname = a.data.fullname || "";

      if (aUsername.indexOf(term) === 0) {
        if (bUsername.indexOf(term) === 0) {
          return aUsername.localeCompare(bUsername);
        }
        return -1;
      } else if (bUsername.indexOf(term) === 0) {
        return 1;
      } else {
        return aFullname.localeCompare(bFullname);
      }
    }
  };

  // Again, this is copied almost verbatim from Review Board core to
  // mimic traditional behaviour for this kind of field.
  $("#mozreview-child-requests input[type=text]").mozreviewautocomplete({
    formatItem: function(data) {
      var s = data[acOptions.nameKey];
      if (acOptions.descKey && data[acOptions.descKey]) {
        s += ' <span>(' + _.escape(data[acOptions.descKey]) +
             ')</span>';
      }

      return s;
    },
    matchCase: false,
    multiple: true,
    searchPrefix: ":",
    parse: function(data) {
      var items = data[acOptions.fieldName],
          itemsLen = items.length,
          parsed = [],
          value,
          i;

      for (i = 0; i < itemsLen; i++) {
        value = items[i];

        parsed.push({
          data: value,
          value: value[acOptions.nameKey],
          result: value[acOptions.nameKey]
        });
      }

      return parsed;
    },
    url: SITE_ROOT +
         "api/" + (acOptions.resourceName || acOptions.fieldName) + '/',
    extraParams: acOptions.extraParams,
    cmp: acOptions.cmp,
    width: 350,
    error: function(xhr) {
      var text;
      try {
        text = $.parseJSON(xhr.responseText).err.msg;
      } catch (e) {
        text = 'HTTP ' + xhr.status + ' ' + xhr.statusText;
      }
      reportError(text);
    }
  }).on("autocompleteshow", function() {
    /*
     * Add the footer to the bottom of the results pane the
     * first time it's created.
     *
     * Note that we may have multiple .ui-autocomplete-results
     * elements, and we don't necessarily know which is tied to
     * this. So, we'll look for all instances that don't contain
     * a footer.
     */

    var resultsPane = $('.ui-autocomplete-results:not(' +
                        ':has(.ui-autocomplete-footer))');
    if (resultsPane.length > 0) {
      $('<div/>')
        .addClass('ui-autocomplete-footer')
        .text(gettext('Press Tab to auto-complete.'))
        .appendTo(resultsPane);
    }
  });

  $('.action-landed').each(function(index, elem){
    var repository = $(elem).data('repository');
    var revision = $(elem).data('revision');
    var actionHeading = $(elem).find('.action-info > .action-heading')[0];
    var actionMeta = $(elem).find('.action-info > .action-meta')[0];

    $.ajax({
      url: 'https://treeherder.mozilla.org/api/project/'+repository+'/resultset/?revision='+revision,
    })
    .done(function(response) {
      if (response.results.length != 1) {
        $(actionHeading).text('Error fetching the results for '+revision+' from Treeherder');
        $(elem).addClass('action-failure')
        if (response.results.lenght == 0) {
          $(actionMeta).text('Revision not found');
        } else {
          $(actionMeta).text('Too many results found');
        }
      } else {
        var resultset = response.results[0]
        $.ajax({
          url: 'https://treeherder.mozilla.org/api/project/'+repository+'/resultset/'+resultset.id+'/status/'
        }).done(function(status){
          if (status.testfailed || status.busted || status.exception) {
            $(actionHeading).text('Some jobs failed on Try');
            $(elem).addClass('action-failure');
          } else {
            if (status.pending || status.running) {
              $(actionHeading).text('Some jobs are still in progress on Try');
              $(elem).addClass('action-pending');
            } else {
              $(actionHeading).text('All the jobs passed on Try');
              $(elem).addClass('action-success');
            }
          }
          var actionMetaText = $.map(status, function(num, s) {
            return num+' jobs '+s;
          });
          $(actionMeta).text(actionMetaText.join());
        })
      }
        $( this ).addClass( "done" );
    });
  })

});
