MRParents = {
  // Generic warning about parent (squashed) review requests, used in a
  // couple places. As noted, eventually we will probably want to make
  // further changes to them, possibly removing them altogether. See
  // mcote's post at <https://mrcote.info/blog/2015/10/22/parental-issues/>
  // and ensuing discussion.
  parentWarning: '<div class="parent-warning"><p>This is a squashed review ' +
        'request, containing the sum of all commits in the series. It is ' +
        'intended only to provide an overview of a series of commits. At ' +
        'the moment, you <i>can</i> leave review comments here, which ' +
        'will be mirrored to Bugzilla, but they will not affect the ' +
        'review status of individual commits, nor will they result in any ' +
        'changes to review flags in Bugzilla. Since the commits will land ' +
        'separately, please review them individually by using the links ' +
        'in the "Diff" and "Reviews" columns in the table above.</p>' +
        '<p>It is likely that squashed review requests will either be ' +
        'made read only or removed entirely at some point.</p></div>',
};


MRParents.ReviewDialogHookView = Backbone.View.extend({
  template: _.template(MRParents.parentWarning),

  render: function() {
    if ($('body').hasClass('parent-request')) {
      this.$el.html(this.template({}));
    }

    return this;
  }
});


MRParents.Extension = RB.Extension.extend({
  initialize: function() {
    _super(this).initialize.call(this);

    new RB.ReviewDialogHook({
      extension: this,
      viewType: MRParents.ReviewDialogHookView
    });
  }
});
