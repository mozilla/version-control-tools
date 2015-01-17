/**
 * This code manages the construction and functionality of the reviewers
 * lists for each commit in a push-based review request.
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

$(document).ready(function() {
  var EPOCH_KEY = "p2rb.reviewer_epoch";
  var rootEditor = RB.PageManager.getPage().reviewRequestEditor;
  var rootEditorView = RB.PageManager.getPage().reviewRequestEditorView;

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

  /**
   * A representation of a reviewer for a review request. This is a pretty
   * simple Model, and it's almost worth not having, except that it
   * encapsulates an inconsistency in the Review Board WebAPI with regards
   * to how it provides usernames for reviewers.
   */
  var Reviewer = RB.BaseResource.extend({
    defaults: {
      username: ""
    },

    /**
     * Options:
     *   person: An Object with a property of username where the
     *           username is a string. If no username property is found,
     *           it also tries the title property.
     */
    initialize: function(options) {
      var person = options.person;
      // For some reason, sometimes the RB WebAPI represents reviewers as having
      // usernames or titles. This tries to account for that weirdness.
      if (person.hasOwnProperty("username")) {
        this.set("username", person["username"]);
      } else {
        this.set("username", person["title"]);
      }
    }
  });

  /**
   * The collection of reviewers per Commit.
   */
  var ReviewerList = Backbone.Collection.extend({
    model: Reviewer
  });

  var ReviewerListView = Backbone.View.extend({
    render: function() {
      return this.collection.pluck("username").join(", ");
    }
  });

  /**
   * This represents a single commit, and knows about the review request
   * for that commit.
   */
  var Commit = Backbone.Model.extend({
    defaults: {
      loaded: false,
      editable: false,
      canViewDraft: false
    },

    /**
     * If the review request has a visible draft, returns the draft,
     * otherwise, returns just the review request.
     */
    requestOrDraft: function() {
      return this.reviewRequest.draft.id !== undefined ?
             this.reviewRequest.draft :
             this.reviewRequest;
    },

    /**
     * Returns true if this review request has a draft associated with it.
     */
    hasDraft: function() {
      return this.reviewRequest.draft.id !== undefined;
    },

    /**
     * Options:
     *   reviewRequestID: The ID of the review request that this commit belongs
     *                    to.
     *   commitID: The SHA-1 representing this commit.
     */
    initialize: function(options) {
      this.reviewers = new ReviewerList();
      this.reviewRequest = new RB.ReviewRequest({
        id: options.reviewRequestID,
      });
      this.commitID = options.commitID;
      this.id = options.reviewRequestID;
      this.editor = new RB.ReviewRequestEditor({
        reviewRequest: this.reviewRequest
      });
    },

    /**
     * Asynchronously loads the review request representing this commit
     * and does any other preperatory work. Takes a success function and
     * a failure function. The success function is not passed anything on
     * success, but the failure function gets an error message if called.
     */
    ready: function(aSuccess, aFailure) {
      var reviewable = this.get("canViewDraft") ? this.reviewRequest.draft
                                                : this.reviewRequest;
      reviewable.ready({
        ready: function() {
          this.updateReviewers();
          this.set("loaded", true);
          aSuccess();
        },
        error: function(aMessage) {
          aFailure(aMessage);
        }
      }, this);
    },

    updateReviewers: function() {
      var targetPeople = this.requestOrDraft().get("targetPeople");
      var reviewers = _.map(targetPeople, function(aTargetPerson) {
        return new Reviewer({person: aTargetPerson});
      });
      this.reviewers.reset(reviewers);
    },

    getReviewerNames: function() {
      return this.reviewers.pluck("username");
    }
  });

  /**
   * A collection of Commit models that is represented by
   * CommitListView.
   */
  var CommitList = Backbone.Collection.extend({
    model: Commit
  });

  /**
   * Just one of the commits in the list.
   */
  var CommitView = Backbone.View.extend({
    tagName: "li",
    commitTemplate: _.template($("#rbmozui-commits-child").html()),
    linksTemplate: _.template($("#rbmozui-commit-links").html()),

    initialize: function(options) {
      this.listenTo(this.model, "change", this.render);
      this.listenTo(this.model.reviewers, "reset", this.render);
      this.listenTo(this.model.reviewRequest, "change", this.render);
      this.listenTo(this.model.reviewRequest.draft, "change", this.render);
      this.listView = options.listView;
      // Kick off loading the Commit that we're holding onto.
      this.model.ready(function() {
        console.log("Successfully loaded Commit with ID " + this.model.commitID +
                    " at review request with ID " + this.model.id);
      }.bind(this), reportError);
    },

    render: function() {
      var isCurrent = (this.model.id == gReviewRequest.id);
      this.$el.attr("current", isCurrent);

      if (!this.model.get("loaded")) {
        this.$el.html("Loading...");
        return this;
      }

      var reviewers = new ReviewerListView({collection: this.model.reviewers});
      // Because this user might be able to see drafts of the review request
      // for this commit, we call requestOrDraft which will give us the draft
      // if we can see it. Otherwise, we get the public review request.
      var reviewable = this.model.requestOrDraft();

      var links = this.linksTemplate({
        childURL: this.model.reviewRequest.get("reviewURL")
      });

      this.$el.html(this.commitTemplate({
        commitID: this.model.commitID,
        commitIDShort: this.model.commitID.substring(0, 8),
        description: reviewable.get("description"),
        summary: reviewable.get("summary"),
        childID: this.model.id,
        reviewers: reviewers.render(),
        links: links
      }));

      var editable = this.model.get("editable");

      // Hook up the inline editor for the reviewer list. This inline editor
      // code is mostly copied from Review Board itself - please see the
      // copyright notice in the header.
      var editorOptions = {
        editIconClass: "rb-icon rb-icon-edit",
        useEditIconOnly: true,
        enabled: editable,
        deferEventSetup: true
      };

      var reviewerList = this.$el.find(".child-rr-reviewers");

      reviewerList
        .inlineEditor(editorOptions)
        .on({
          beginEdit: function() {
            // The editCount is used to determine if we should warn the user before
            // unloading the page because they still have an editor open.
            rootEditor.incr("editCount");
          },
          cancel: function() {
            rootEditor.decr("editCount");
          },
          complete: _.bind(function(e, value) {
            // The ReviewRequestEditor is the interface that we use to modify
            // a review request easily.
            var editor = new RB.ReviewRequestEditor({reviewRequest: this.model.reviewRequest});
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
                  rootEditor.decr("editCount");
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
                  $(reviewerList).text(reviewers.render());
                },
                success: function() {
                  rootEditor.decr("editCount");
                  // We need to set the reviewers on the root review request
                  // as well, or else Review Board is going to complain.

                  this.model.updateReviewers();
                  this.listView.updateRootReviewers();
                  rootEditorView.showBanner();
                }
              }, this);
          }, this)
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
      $(reviewerList).inlineEditor("field")
                     .rbmozuiautocomplete({
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

      $(reviewerList).inlineEditor("setupEvents");

      // We've changed the layout of the page by fleshing out the commit view,
      // so we need to schedule a resize of the main review request area.
      RB.PageManager.getPage().reviewRequestEditorView._scheduleResizeLayout();

      return this;
    }
  });


  /**
   * This is really the prime mover, or main view for the whole thing.
   */
  var CommitListView = Backbone.View.extend({
    linksTemplate: _.template($("#rbmozui-commit-links").html()),

    /**
     * Options:
     *   rootID: the ID of the root / squashed review request.
     */
    initialize: function(options) {
      console.log("Initializing CommitListView");
      this.model = new RB.ReviewRequest({id: options.rootID});
      this.commitList = new CommitList();
      this.listenTo(this.commitList, "add", this.add);
      // Now we need to retrieve the data for this review request - the
      // extra_data is most important, since it's what we'll use to populate
      // the CommitList. I fetch on the draft even though this user might not
      // have access to the draft. That way, if we detect a draft, we'll use its
      // data - otherwise, we'll just use the data on the review request itself.

      // Doing the ol' self-hack since I don't want to use bind everywhere.
      var self = this;
      console.log("Requesting root review request and draft");

      var mutableByUser = rootEditor.get("mutableByUser");
      var reviewable = mutableByUser ? this.model.draft : this.model;
      reviewable.ready({
        ready: function() {
          console.log("Loaded root review request.");
          var reviewable = self.model.draft.id ? self.model.draft : self.model;

          var extraData = reviewable.get("extraData");
          var isSquashed = extraData["p2rb.is_squashed"] == "True";
          if (!isSquashed) {
            reportError("Root review request with ID: " + self.model.id + " does not " +
                        "have p2rb.is_squashed set to True");
            return;
          }

          var isMutable = rootEditor.get("mutableByUser");
          var isViewingRoot = (self.model.id == gReviewRequest.id);

          // Now we need the child review requests in the extra_data...
          var childIDs = extraData["p2rb.commits"];
          if (!childIDs) {
            reportError("Root review request with ID: " + self.model.id + " does not " +
                        "have p2rb.commits set.");
            return;
          }

          self.epoch = parseInt(reviewable.get("extraData")[EPOCH_KEY], 10) || 0;
          console.log("Root review request loaded with epoch set at " + self.epoch);

          childIDs = JSON.parse(childIDs);
          // Remember, p2rb.commits is a list of tuples. Now that we're in JavaScript,
          // that means an Array of Arrays, where each sub-Array has two elements. The
          // first element at index 0 is the SHA of the commit, and the second element
          // at index 1 is the review request ID for the child review request.
          var commits = childIDs.map(function(tuple, index) {
            return new Commit({
              commitID: tuple[0],
              reviewRequestID: tuple[1],
              // Next we need to see if the review request for the page we're on is
              // the same as the squashed one. If so, then the commits are editable.
              editable: isViewingRoot && isMutable,
              canViewDraft: isMutable
            });
          });

          self.commitList.add(commits);

          var links = self.linksTemplate({
            childURL: self.model.get("reviewURL")
          });

          $("#rbmozui-commits-root-links").html(links);

          // Finally, set the arrow on the root review request in the list
          // if that's what we're viewing.
          if (isViewingRoot) {
            $("#rbmozui-commits-root").attr("current", "true");
          }
        },
        error: function(errorObject) {
          console.error("Error: " + errorObject);
          reportError(errorObject);
        }
      });
    },

    add: function(commit) {
      var view = new CommitView({model: commit, listView: this});
      $("#rbmozui-commits-children").append(view.render().el);
    },

    updateRootReviewers: function() {
      var reviewerNameList = [];
      this.commitList.forEach(function(commit) {
        reviewerNameList = reviewerNameList.concat(commit.getReviewerNames());
      });

      var self = this;
      var reviewerNames = _.unique(reviewerNameList).join(",");
      console.log("Setting reviewers on root review request to: " + reviewerNames);

      rootEditor.setDraftField("targetPeople", reviewerNames, {
        jsonFieldName: "target_people",
        success: function() {
          console.log("Successfully set reviewers on root review request");
          // Now, because it's possible that the final set of the reviewers
          // didn't actually change for the root review request, we bump
          // the epoch so that publishing goes smoothly.
          self.epoch++;
          console.log("Setting epoch to " + self.epoch);

          rootEditor.setDraftField(EPOCH_KEY, self.epoch, {
            fieldID: EPOCH_KEY,
            useExtraData: true,
            success: function() {
              console.log("Root review request epoch has been set to " + self.epoch);
            },
            error: function(errorObject) {
              console.error("Failed to bump root review request epoch. Error was: " +
                            errorObject.errorText)
            }
          });
        },

        error: function(errorObject) {
          console.error("Failed to set reviewers on root review request: " +
                        errorObject.errorText);
        }
      });
    }
  });

  // End of Backbone model / collection / view definitions.

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
  new CommitListView({rootID: rootID});
});
