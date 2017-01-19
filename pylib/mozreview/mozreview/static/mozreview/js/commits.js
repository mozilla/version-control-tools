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
  if (!RB.UserSession.instance.get("username")) {
    return;
  }

  // Simple case-insensitive array of strings comparison
  function arraysEqualsCI(a, b) {
    var i = a.length;
    if (i != b.length) {
      return false;
    }
    while (i--) {
      if (a[i].toLowerCase() != b[i].toLowerCase()) {
        return false;
      }
    }
    return true;
   }

  function showError(errorMessage, xhr) {
    if (xhr && xhr.responseJSON && xhr.responseJSON.err) {
      errorMessage = xhr.responseJSON.err.msg;
    }
    $("#review-request-warning")
      .delay(6000)
      .fadeOut(400, function() {
        $(this).hide();
      })
      .show()
      .text(errorMessage);
  }

  $("#error-close").click(function() {
    $("#error-container").attr("haserror", "false");
  });

  $("#error-stack-toggle").click(function() {
    $("#error-stack").toggle();
  });

  /*
   * Review Board only allows the review request submitter to change the
   * target reviewers.  As MozReview wants to allow 'anyone' to change the
   * reviewers, we expose the editor to all users (Bugzilla will perform the
   * permissions check for us).
   *
   * In order for this to work correctly there are two separate paths depending
   * on if the user is the submitter or not.
   *
   * Submitters use Review Board's normal draft mechanism, with a small tweak
   * that creates a draft on all children when any reviewers are updated.  This
   * causes Review Board to show the draft banner when viewing any review
   * request in the series.
   *
   * Non-submitters can't use a normal draft, as a review request can only have
   * one, and it's used by the submitter.  Instead we create a client-side
   * fake draft in local storage, and display a fake draft banner above the
   * commits table.
   */

  //
  // Local Drafts
  //

  function getLocalDraft() {
    var localDrafts = window.localStorage.localDrafts ?
      JSON.parse(window.localStorage.localDrafts) : {};
    var parent_rrid = $("#mozreview-data").data("parent-review-id");
    return localDrafts[parent_rrid] ? localDrafts[parent_rrid] : {};
  }

  function setLocalDraft(draft) {
    var localDrafts = window.localStorage.localDrafts ?
      JSON.parse(window.localStorage.localDrafts) : {};
    var parent_rrid = $("#mozreview-data").data("parent-review-id");
    if (draft) {
      localDrafts[parent_rrid] = draft;
    }
    else {
      delete localDrafts[parent_rrid];
    }
    window.localStorage.localDrafts = JSON.stringify(localDrafts);
  }

  function hasLocalDraft() {
    return Object.keys(getLocalDraft()).length !== 0;
  }

  function publishLocalDraft() {
    if (!hasLocalDraft()) {
      discardLocalDraft();
      return;
    }
    var draft = getLocalDraft();
    RB.setActivityIndicator(true, {});
    $.ajax({
      type: "POST",
      data: {
        parent_request_id: $("#mozreview-data").data("parent-review-id"),
        reviewers: JSON.stringify(draft)
      },
      url: "/api/extensions/mozreview.extension.MozReviewExtension/modify-reviewers/",
      success: function(rsp) {
        discardLocalDraft(true);
        window.location.reload(true);
      },
      error: function(xhr, textStatus, errorThrown) {
        RB.setActivityIndicator(false, {});
        showError(errorThrown, xhr);
      }
    });
  }

  function discardLocalDraft(silent) {
    setLocalDraft(undefined);
    if (!silent) {
      $(".mozreview-child-reviewer-list").each(function() {
        restoreOriginalReviewerState($(this));
      });
      hideLocalDraftBanner();
    }
  }

  function restoreLocalDraftState($reviewer_list) {
    var draft = getLocalDraft();
    if (!$reviewer_list) {
      $reviewer_list = $(".mozreview-child-reviewer-list");
    }
    $reviewer_list.each(function() {
      var $this = $(this);
      var rrid = $this.data("id");
      if (draft[rrid]) {
        saveOriginalReviewerState($this);
        $this.html(draft[rrid].join(", "));
      }
    });
  }

  function showLocalDraftBanner() {
    if (!hasLocalDraft()) {
      $("#local-draft-banner").remove();
      return;
    }
    if ($("#local-draft-banner").length) {
      return;
    }
    $("<div/>")
      .attr("id", "local-draft-banner")
      .addClass("banner")
      .addClass("box-inner")
      .append(
        $("<p>")
          .text("You have pending changes to this review.")
      )
      .append(
        $("<span/>")
          .addClass("banner-actions")
          .append(
            $("<input/>")
              .attr("type", "button")
              .addClass("publish-button")
              .val("Publish")
              .click(function(event) {
                event.preventDefault();
                publishLocalDraft();
              })
          )
          .append(" ")
          .append(
            $("<input/>")
              .attr("type", "button")
              .addClass("discard-button")
              .val("Discard")
              .click(function(event) {
                event.preventDefault();
                discardLocalDraft();
              })
          )
      )
      .insertBefore("#mozreview-child-requests");
      RB.PageManager.getPage().reviewRequestEditorView._scheduleResizeLayout();
  }

  function hideLocalDraftBanner() {
    $("#local-draft-banner").remove();
    RB.PageManager.getPage().reviewRequestEditorView._scheduleResizeLayout();
  }

  function saveOriginalReviewerState($reviewer_list) {
    if (!$reviewer_list.data("orig-html")) {
      $reviewer_list.data("orig-html", $reviewer_list.html().trim());
      var reviewers = $reviewer_list.find(".reviewer-name")
                                    .map(function() { return $(this).text(); })
                                    .sort();
      $reviewer_list.data("orig-reviewers", $.makeArray(reviewers));
    }
  }

  function restoreOriginalReviewerState($reviewer_list) {
    if ($reviewer_list.data("orig-html")) {
      $reviewer_list.html($reviewer_list.data("orig-html"));
    }
  }

  function ensureNativeDrafts() {
    RB.setActivityIndicator(true, {});
    $.ajax({
      type: "POST",
      data: {
        parent_request_id: $("#mozreview-data").data("parent-review-id")
      },
      url: "/api/extensions/mozreview.extension.MozReviewExtension/ensure-drafts/",
      success: function(rsp) {
        RB.setActivityIndicator(false, {});
      },
      error: function(xhr, textStatus, errorThrown) {
        RB.setActivityIndicator(false, {});
        showError(errorThrown, xhr);
      }
    });
  }

  function augmentNativeBanner() {
    var $draftBanner = $("#draft-banner");
    if (MozReview.isParent || $draftBanner.data("appended")) { return; }

    // Unfortunately we cannot publish from children, so provide a link
    // to the parent instead.
    var parent_rrid = $("#mozreview-data").data("parent-review-id");
    $draftBanner.data("appended", 1).append(
        $('<a href="/r/' + parent_rrid + '/" title="You can only Publish or Discard when ' +
          'viewing the \'Review Summary / Parent\'.">Publish or Discard my changes.</a>'));
  }

  var editors = {};

  function updateReviewers($reviewer_list, value) {
    var rrid = $reviewer_list.data("id");

    // Parse updated reviewer list.
    var reviewers = value.split(/[ ,]+/)
      .map(function(name) {
        name = name.trim();
        if (name.substr(name, 0, 1) === ":") {
          name = name.substring(1);
        }
        return name;
      })
      .filter(function(name) {
        return name !== "";
      })
      .sort();


    // No need to do anything if nothing is changed.
    if (arraysEqualsCI($reviewer_list.data("orig-reviewers"), reviewers)) {
      $reviewer_list.html($reviewer_list.data("orig-html"));
      return;
    }

    // TODO retain reviewer background status colour after an edit
    $reviewer_list.text(reviewers.join(" , "));

    if (MozReview.isSubmitter) {
      // When the submitter updates reviewers, use RB's native drafts.
      var editor;
      if (!editors[rrid]) {
        var rr = new RB.ReviewRequest({ id: rrid });
        editor = new RB.ReviewRequestEditor({ reviewRequest: rr });
        editors[rrid] = editor;
      } else {
        editor = editors[rrid];
      }

      editor.setDraftField(
        "targetPeople",
        reviewers.join(","),
        {
          jsonFieldName: "target_people",
          error: function(error) {
            showError(error.errorText);
            restoreOriginalReviewerState($reviewer_list);
          },
          success: function() {
            MozReview.reviewEditor.set("public", false);
            // Our draft relies on a field that isn't part of RB's front-end
            // model, so changes aren't picked up by the model automatically.
            // Manually record a draft exists so the banner will be displayed.
            var view = RB.PageManager.getPage().reviewRequestEditorView;
            view.model.set("hasDraft", true);
            MozReview.reviewEditor.trigger("saved");
            // Extend the draft to encompass the parent and all children, so
            // the draft banner is visible on all review requests in the set.
            ensureNativeDrafts();
            augmentNativeBanner();
          }
        }, this);

    } else {
      // Otherwise use our local draft.

      RB.setActivityIndicator(true, {});
      $.ajax({
        type: "POST",
        data: { reviewers: reviewers.join(",") },
        url: "/api/extensions/mozreview.extension.MozReviewExtension/verify-reviewers/",
        success: function(rsp) {
          RB.setActivityIndicator(false, {});
          // All reviewrs ok - create fake draft in localStorage.
          var localDraft = getLocalDraft();
          localDraft[rrid] = reviewers;
          setLocalDraft(localDraft);
          showLocalDraftBanner();
        },
        error: function(xhr, textStatus, errorThrown) {
          RB.setActivityIndicator(false, {});
          restoreLocalDraftState($reviewer_list);
          showError(errorThrown, xhr);
        }
      });
    }
  }

  $("#mozreview-child-requests").on("mr:commits_setup", function() {
    $(".mozreview-child-reviewer-list")
      .inlineEditor({
        editIconClass: "rb-icon rb-icon-edit",
        useEditIconOnly: true,
        enabled: true,
        setFieldValue: function(editor, value) {
          editor._field.val(value.trim());
        }
      })
      .on({
        beginEdit: function() {
          $reviewer_list = $(this);
          // Store the original html and reviewer list so we can restore later.
          saveOriginalReviewerState($reviewer_list);
          // store the current edit to support cancelling
          $reviewer_list.data("prior", $reviewer_list.html());
          // Inc editCount to enable "leave this page" warning.
          MozReview.reviewEditor.incr("editCount");
        },
        cancel: function() {
          $reviewer_list = $(this);
          // restoreOriginalReviewerState($reviewer_list);
          $reviewer_list.html($reviewer_list.data("prior"));
          $reviewer_list.data("prior", "");
          MozReview.reviewEditor.decr("editCount");
        },
        complete: function(e, value) {
          $reviewer_list = $(this);
          $reviewer_list.data("prior", "");
          MozReview.reviewEditor.decr("editCount");
          updateReviewers($reviewer_list, value);
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
  })
  .trigger("mr:commits_setup");

  // Update UI if there's an existing draft.
  if (MozReview.isSubmitter) {
    augmentNativeBanner();
  } else if (hasLocalDraft()) {
    showLocalDraftBanner();
    restoreLocalDraftState();
  }

  // Update state when issues are fixed/dropped/reopened.
  RB.PageManager.getPage().commentIssueManager.on('issueStatusUpdated',
    function(comment) {
      // Refresh the commits table.
      var parent_rrid = $("#mozreview-data").data("parent-review-id");
      var selected_rrid = $("#mozreview-data").data("selected-review-id");
      $("#mozreview-child-requests")
        .load("/mozreview/commits_summary_table/" + parent_rrid + "/" +
              selected_rrid + "/", function() {
          $(this).trigger('mr:commits_setup');
        });

      // Update the parentReviewRequest object, then update the autoland menu.
      MozReview.parentReviewRequest.fetch({
        success: function() {
          $(document).trigger('mr:update_autoland_menuitem');
        }
      });
    });

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
        s += " <span>(" + _.escape(data[acOptions.descKey]) + ")</span>";
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
         "api/" + (acOptions.resourceName || acOptions.fieldName) + "/",
    extraParams: acOptions.extraParams,
    cmp: acOptions.cmp,
    width: 350,
    error: function(xhr) {
      showError(xhr.statusText, xhr);
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

    var resultsPane = $(".ui-autocomplete-results:not(" +
                        ":has(.ui-autocomplete-footer))");
    if (resultsPane.length > 0) {
      $("<div/>")
        .addClass("ui-autocomplete-footer")
        .text(gettext("Press Tab to auto-complete."))
        .appendTo(resultsPane);
    }
  });
});
