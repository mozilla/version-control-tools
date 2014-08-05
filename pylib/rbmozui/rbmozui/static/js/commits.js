var RBMozUI = RBMozUI || {};

(function() {

  var kIsP2RB = "p2rb";
  var kIsSquashed = "p2rb.is_squashed";
  var kCommits = "p2rb.commits";

  RBMozUI.CommitsList = Backbone.Collection.extend({
    model: RB.ReviewRequest
  });

  var Commits = new RBMozUI.CommitsList();

  RBMozUI.CommitView = Backbone.View.extend({
    tagName: 'li',
    render: function() {
      if (!this.template) {
        this.template = _.template($('#commit-template').html());
      }
      this.$el.html(this.template({
        summary: this.model.get('summary')
      }));
      return this;
    }
  });

  RBMozUI.CommitsView = Backbone.View.extend({
    initialize: function() {

      this.listenTo(Commits, 'add', this.addOne);

      this.squashed = new RB.ReviewRequest({id: this.id});
      var self = this;
      this.squashed.ready({
        ready: function() {
          var extraData = self.squashed.get('extraData');
          if (!extraData[kIsP2RB]) {
            // Do something reasonable here.
            console.error("This review request (id: " + self.id + ") does not appear to be a p2rb push.");
            return;
          }
          if (!extraData[kIsSquashed] == "True") {
            // Do something reasonable here.
            console.error("This review request (id: " + self.id + ") does not appear to be a squashed review.");
            return;
          }

          var commits = JSON.parse(extraData[kCommits]);
          var commitModels = commits.map(function(aTuple) {
            return new RB.ReviewRequest({id: aTuple[1]});
          });
          Commits.add(commitModels);
        }
      });
    },

    addOne: function(aCommit) {
      aCommit.ready({
        ready: function() {
          var view = new RBMozUI.CommitView({model: aCommit});
          this.$("#commit-list").append(view.render().el);
        }
      })
    }
  });

})();