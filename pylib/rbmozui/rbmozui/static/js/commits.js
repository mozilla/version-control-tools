RBMozUI = {};

$(document).ready(function() {

  var $ErrorContainer = $("#error-container");
  function reportError(aMsg) {
    // A pretty terrible error reporting mechanism, but it sure
    // beats modal alert dialogs.
    $("#error-info").text(aMsg);
    $ErrorContainer.attr("haserror", "true");;
  }

  $("#error-close").click(function(aEvent) {
    $ErrorContainer.attr("haserror", false);
  });

  RBMozUI.Reviewer = RB.BaseResource.extend({
    defaults: {
      username: ""
    },

    initialize: function(aOptions) {
      var person = aOptions.person;
      if (person.hasOwnProperty('username')) {
        this.set('username', person['username']);
      } else {
        this.set('username', person['title']);
      }
    }
  });

  RBMozUI.ReviewerList = Backbone.Collection.extend({
    model: RBMozUI.Reviewer
  });

  RBMozUI.Commit = Backbone.Model.extend({
    defaults: {
      loaded: false,
    },

    requestOrDraft: function() {
      return this.reviewRequest.draft.id !== undefined ?
             this.reviewRequest.draft :
             this.reviewRequest;
    },

    hasDraft: function() {
      return this.reviewRequest.draft.id !== undefined;
    },

    initialize: function(options) {
      this.reviewers = new RBMozUI.ReviewerList();
      this.reviewRequest = new RB.ReviewRequest({
        id: options.reviewRequestID,
      });
      this.commitID = options.commitID;
      this.commitNum = options.commitNum;
      this.editor = new RB.ReviewRequestEditor({
        reviewRequest: this.reviewRequest
      });
    },

    ready: function(aSuccess, aFailure) {
      this.reviewRequest.draft.ready({
        ready: function() {
          aSuccess();
          this.resetReviewers();
          this.set("loaded", true);
        },
        error: function(aMessage) {
          aFailure(aMessage);
        }
      }, this);
    },

    resetReviewers: function() {
      var targetPeople = this.requestOrDraft().get('targetPeople');
      var reviewers = _.map(targetPeople, function(aTargetPerson) {
        return new RBMozUI.Reviewer({person: aTargetPerson});
      });
      this.reviewers.reset(reviewers);
    },

    removeReviewer: function(aUsername) {
      var usernames = this.reviewers
                          .pluck('username')
                          .filter(function(username) {
                            return username != aUsername;
                          }).join(',');
      var self = this;
      this.editor.setDraftField('targetPeople', usernames, {
        jsonFieldName: 'target_people',
        success: function() {
          console.log('Successfully removed reviewer ' + aUsername);
          self.resetReviewers();
        },
        error: function(aErrorObject) {
          console.error(aErrorObject.errorText);
        }
      });
    },

    addReviewer: function(aUsername) {
      var usernames = this.reviewers.pluck('username');
      usernames.push(aUsername);

      var usernameString = usernames.join(',');
      var self = this;

      this.editor.setDraftField('targetPeople', usernameString, {
        jsonFieldName: 'target_people',
        success: function() {
          console.log('Successfully added reviewer ' + aUsername);
          self.resetReviewers();
        },
        error: function(aErrorObject) {
          reportError(aErrorObject.errorText);
        }
      });
    }
  })


  RBMozUI.CommitsList = Backbone.Collection.extend({
    model: RB.ReviewRequest
  });

  var Commits = new RBMozUI.CommitsList();

  RBMozUI.CommitView = Backbone.View.extend({
    tagName: 'li',
    className: 'commit-list-item',
    events: {
      'click .remove': 'removeReviewer',
      'submit .reviewer-form': 'onReviewerSubmit'
    },
    loadingTemplate: _.template($('#loading-template').html()),
    commitTemplate: _.template($('#commit-template').html()),
    reviewerTemplate: _.template($('#reviewer-template').html()),

    initialize: function(aOptions) {
      this.listenTo(this.model, "change", this.render);
      this.listenTo(this.model.reviewRequest, "change", this.render);
      this.listenTo(this.model.reviewRequest.draft, "change", this.render);
      this.listenTo(this.model.reviewers, "reset", this.reviewersChanged);
      // Kick off loading the Commit that we're holding onto.
      this.model.ready(function() {
        console.log('Successfully loaded Commit with ID' + this.model.commitID);
      }.bind(this), this.handleError.bind(this));
    },

    handleError: function(aErrorMessage) {
      reportError(aErrorMessage);
    },

    computeState: function() {
      if (!this.model.reviewRequest.get('public')) {
        return "needs-publishing";
      }

      if (this.model.hasDraft()) {
        return "unsaved-changes";
      }

      return "published";
    },

    reviewersChanged: function() {
      this.render();
      this.$el.find('input.reviewer-input').focus();
    },

    render: function() {
      // Hack alert - if an autocomplete GET request is still making the round
      // trip by the time we re-render (if the user, for example, new the
      // email address and just typed it in and pressed enter), in order to
      // prevent the autocomplete popup from showing up anyways (and anchoring
      // to the top left corner of the screen since the .reviewer-input is about
      // to be replaced), we blur the input so that rbautocomplete ignores any
      // requests coming in for it until it's refocused.
      var input = this.$el.find('input.reviewer-input');
      if (input) {
        input.blur();
      }

      // In the base case, we've just kicked off the request to populate
      // our review request and draft models, so we show a loading spinner.
      if (!this.model.get("loaded")) {
        this.$el.html(this.loadingTemplate({
          commitID: this.model.commitID
        }));
        return this;
      }

      var reviewable = this.model.requestOrDraft();
      var commitLink = SITE_ROOT + 'r/' + this.model.reviewRequest.id;

      this.$el.html(this.commitTemplate({
        reviewerTemplate: this.reviewerTemplate,
        commitLink: commitLink,
        commitNum: this.model.commitNum,
        summary: reviewable.get('summary'),
        description: reviewable.get('description'),
        hasReviewers: reviewable.get('targetPeople').length > 0,
        reviewers: this.model.reviewers,
        commitID: this.model.commitID,
        state: this.computeState()
      }));

      this.buildReviewerAutocomplete(
        this.$el.find('input.reviewer-input')
      );
      return this;
    },

    buildReviewerAutocomplete: function($elArray) {
      if (!$elArray.length) {
        reportError("Couldn't find reviewer input for commit " + this.model.commitID);
      }
      var reviewRequest = this.model.reviewRequest;
      var $el = $($elArray[0]);
      var options = {
        fieldName: 'users',
        nameKey: 'username',
        descKey: 'fullname',
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
              aFullname = a.data.fullname,
              bFullname = a.data.fullname;

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

      $el.rbautocomplete({
        formatItem: function(data) {
            var s = data[options.nameKey];

            if (options.descKey && data[options.descKey]) {
                s += ' <span>(' + _.escape(data[options.descKey]) +
                     ')</span>';
            }

            return s;
        },
        matchCase: false,
        multiple: false,
        parse: function(data) {
            var items = data[options.fieldName],
                itemsLen = items.length,
                parsed = [],
                value,
                i;

            for (i = 0; i < itemsLen; i++) {
                value = items[i];

                parsed.push({
                    data: value,
                    value: value[options.nameKey],
                    result: value[options.nameKey]
                });
            }

            return parsed;
        },
        url: SITE_ROOT +
             'api/' + (options.resourceName || options.fieldName) + '/',
        extraParams: options.extraParams,
        cmp: options.cmp,
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
      }).on('autocompleteshow', function() {
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

    removeReviewer: function(aEvent) {
      var username = aEvent.target.dataset.username;
      console.log('Removing reviewer with id: ' + username);
      this.model.removeReviewer(username);
    },

    onReviewerSubmit: function(aEvent) {
      aEvent.preventDefault();
      var username = this.$el.find('.reviewer-input').first().val();
      console.log('Adding reviewer with id: ' + username);
      this.model.addReviewer(username);
    }
  });

  RBMozUI.CommitsView = Backbone.View.extend({
    initialize: function(aOptions) {
      this.listenTo(Commits, 'add', this.add);
      this.model = new RB.ReviewRequest({id: aOptions.squashedID});

      $("#publish").click(this.publish.bind(this));

      var commits = aOptions.commits;
      var commitModels = commits.map(function(aTuple, aIndex) {
        return new RBMozUI.Commit({
          reviewRequestID: aTuple[1],
          commitNum: aIndex,
          commitID: aTuple[0]
        });
      });
      Commits.add(commitModels);
    },

    add: function(aCommit) {
      var view = new RBMozUI.CommitView({model: aCommit});
      // At this point, we don't have to worry about commit
      // removal, so let's just add this and forget about it.
      $("#commit-list").append(view.render().el);
    },

    publish: function() {
      $("#publish").prop("disabled", true);
      this.model.draft.ready({
        ready: function() {
          var editor = new RB.ReviewRequestEditor({reviewRequest: this.model});
          // This bit of functional programming iterates each commit
          // returning an array of reviewer usernames for each, which
          // we union, unique, and then join in a string separated
          // by commas. We use an apply because the Commits.map will
          // return an array of arrays.
          var reviewers = _.unique(_.union.apply(this, Commits.map(function(aCommit) {
            return aCommit.reviewers.pluck('username');
          }))).join(',');

          console.log("Setting reviewers on squashed request to: "
                      + reviewers);

          editor.setDraftField('targetPeople', reviewers, {
            jsonFieldName: 'target_people',
              success: function() {
                editor.setDraftField('public', true, {
                  jsonFieldName: 'public',
                  success: function() {
                    console.log('Successfully published - reloading page...');
                    $("#publish").prop("disabled", false);
                    location.reload();
                  },
                  error: function(aMsg) {
                    $("#publish").prop("disabled", false);
                    reportError(aMsg);
                  }
                })
              },
              error: function(aErrorObject) {
                reportError('Failed to set reviewers on squashed review: '
                            + aErrorObject.errorText);
              }
          });
        }
      }, this);
    }
  });

  // I'll bet you're wondering what kicks this all off. Well, that'd be
  // in the commits.html template, which calls into RBMozUI and gets all
  // of this machinery working.
});