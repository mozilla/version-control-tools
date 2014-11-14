/**
 * This code manages the construction and functionality of the reviewers
 * lists for each commit in a push-based review request.
 */

$(document).ready(function() {
  // In order for us to successfully publish the review request on this page,
  // we need to account for the possibility that this is a child review request
  // and that no changes have been made directly to this request. For example,
  // we're looking at a child review request, and the user has changed the
  // reviewers on one of the other sibling review requests. In order to make
  // it possible to publish with that change, we need to change this review
  // request to suit - otherwise, Review Board will complain about us
  // attempting to publish a draft with no changes. The change we make is
  // to increment an extra_data value, the reviewer_epoch. This value is
  // never used anywhere, and is just a hacky way of getting around the
  // change requirement.
  var epochKey = "p2rb.reviewer_epoch";

  // We need to start by getting the reviewRequestEditor for the page
  // we're on, since we're going to need to (at the very least) bump
  // it's epoch and get ready to publish it.
  var rootEditor = RB.PageManager.getPage().reviewRequestEditor;
  var rootEditorView = RB.PageManager.getPage().reviewRequestEditorView;
  var rootRequest = rootEditor.get("reviewRequest");

  // We need this warning in case we enter a reviewer name that doesn't
  // exist. It's not the greatest warning interface, but it's what Review
  // Board uses itself, so I guess it's as native as it gets.
  var warning = $("#review-request-warning");

  // Depending on whether or not the current user has the ability to change
  // the review request will determine what we load. If, for example, there
  // is a draft for this review request, we will only attempt to load that
  // draft if the user can, in fact, see the draft.
  var isEditable = rootEditor.get("mutableByUser");
  var rootThingToLoad = isEditable ? rootRequest.draft : rootRequest;

  // Takes a review request. If that review request has a draft, returns the
  // draft - otherwise, it returns the review request. This is used when
  // loading the reviewer lists for each child commit.
  var requestOrDraft = function(reviewRequest) {
    return reviewRequest.draft.id !== undefined ?
           reviewRequest.draft :
           reviewRequest;
  };

  // Takes a review request or a draft, and returns a string for the reviewers
  // of that reviewable, comma-separated.
  var getReviewers = function(reviewable) {
    return reviewable.get('targetPeople')
                     .map(function(aItem) {
                       return aItem['username'] || aItem['title'];
                     })
                     .join(', ');
  };

  rootThingToLoad.ready({
    ready: function() {
      // The review request (or draft) for this page is loaded. Let's grab
      // any previous epoch off of it to increment if necessary.
      var epoch = parseInt(rootRequest.get("extraData")[epochKey], 10) || 0;
      console.log("Loaded epoch: " + epoch);

      var isSquashed = rootRequest.get("extraData")["p2rb.is_squashed"] == "True";
      console.log("This request is squashed?: " + isSquashed);

      // This function will check through all of the reviewers that have been set,
      // get the final, de-duped set of reviewers, and set those reviewers on the
      // squashed review request. For now, this will only get called if the current
      // review request we're viewing is the root review request.
      var updateSquashedReviewers = function() {
        var reviewerNames = [];
        // We could / should probably store each child review request object,
        // and query them rather than grabbing the text out of the nodes, but this
        // will do for now.
        $(".child-rr-reviewers").each(function(i, reviewerList) {
          reviewerNames = reviewerNames.concat($(reviewerList).text().split(', '));
        });
        reviewerNames = _.unique(reviewerNames).join(',');

        console.log("Setting root reviewer names to: " + reviewerNames);

        // Now set the reviewer names on the squashed review request!
        rootEditor.setDraftField("targetPeople", reviewerNames, {
          jsonFieldName: "target_people",
            success: function() {
              console.log('Successfully set reviewers on root review request.');
              // Now, because it's possible that the final set of the reviewers
              // didn't actually change for the squashed review request, we bump
              // the epoch so that publishing goes smoothly.
              epoch++;
              console.log("Setting epoch to: " + epoch);

              rootEditor.setDraftField(epochKey, epoch, {
                fieldID: epochKey,
                useExtraData: true,
                success: function() {
                  console.log('Reviewers and epoch correctly set.');
                },
                error: function(aErrorObject) {
                  console.error('Failed to bump epoch on squashed review request: '
                                 + aErrorObject.errorText);
                }
              })
            },
            error: function(aErrorObject) {
              console.error('Failed to set reviewers on squashed review: '
                             + aErrorObject.errorText);
            }
        });
      };

      // Now we populate the list of reviewers for each child review request,
      // and potentially make them editable if the user has edit rights on this
      // review request and this is the squashed review request.
      $(".child-rr-reviewers").each(function(i, reviewerList) {
        console.log("Constructing reviewer list for item at index " + i);
        var rid = $(reviewerList).data("id");
        console.log("Fetching info for review request with id: " + rid);
        var rr = new RB.ReviewRequest({id: rid});

        // As before, we might have a draft we can load if we have edit rights.
        var thingToLoad = isEditable ? rr.draft : rr;

        thingToLoad.ready({
          ready: function() {
            // If this review request is editable, but there's actually no draft
            // just yet, then we need to pull the target people from the review
            // request instead of the draft. That's where requestOrDraft comes in
            // handy.
            var thingToReview = requestOrDraft(rr);
            var reviewers = getReviewers(thingToReview);
            console.log("Got reviewers: " + reviewers);

            // Display the reviewers in the node.
            $(reviewerList).text(reviewers);

            // Construct the editor to allow the user to update
            // the reviewers.
            var editorOptions = {
              editIconClass: "rb-icon rb-icon-edit",
              useEditIconOnly: true,
              // For now, we only enable editing the reviewers on
              // child review requests when looking at the squashed
              // review request.
              enabled: isEditable && isSquashed,
            };

            $(reviewerList)
              .inlineEditor(editorOptions)
              .on({
                beginEdit: function() {
                  console.assert(isEditable, "User needs edit permissions on this review request.");
                  // The editCount is used to determine if we should warn the user before
                  // unloading the page because they still have an editor open.
                  rootEditor.incr("editCount");
                },
                cancel: _.bind(function() {
                  rootEditor.decr("editCount");
                }, this),
                complete: _.bind(function(e, value) {
                  console.assert(isEditable, 'User needs edit permissions on this review request.');

                  // The ReviewRequestEditor is the interface that we use to modify
                  // a review request easily.
                  var editor = new RB.ReviewRequestEditor({reviewRequest: rr});

                  // This sets the reviewers on the child review request.
                  editor.setDraftField(
                    "targetPeople",
                    value,
                    {
                      jsonFieldName: "target_people",
                      error: function(error) {
                        rootEditor.decr("editCount");
                        console.error(error);
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
                        $(reviewerList).text(reviewers);
                      },
                      success: function() {
                        rootEditor.decr("editCount");
                        // We need to set the reviewers on the root review request
                        // as well, or else Review Board is going to complain.
                        updateSquashedReviewers();
                        rootEditorView.showBanner();
                        $(reviewerList).text(getReviewers(rr.draft));
                      }
                    },
                    this);
                }, this)
            });

            // This next bit sets up the autocomplete popups for reviewers for
            // the inline editors.
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
            $(reviewerList).inlineEditor("field")
                           .rbautocomplete({
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
                   'api/' + (acOptions.resourceName || acOptions.fieldName) + '/',
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
          },
        });
      });
    },
    error: function(error) {
      // Maybe do something a bit louder here, since this
      // is a pretty awful case?
      console.error(error);
    }
  })
});
