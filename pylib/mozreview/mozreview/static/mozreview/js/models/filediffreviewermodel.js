/*
 * A model to keep track of file reviewed by a reviewer.
 */
RB.FileDiffReviewerModel = Backbone.Model.extend({
    defaults: {
      reviewed: false
    },
    url: function(){
      return '/api/extensions/mozreview.extension.MozReviewExtension/file-diff-reviewers/'+this.get('id')+'/'
    },
    /*
     * Parse the data given to us by the server.
     */
    parse: function(rsp) {
      var fileDiffReviewer = rsp.file_diff_reviewer;
      return {
          fileDiffId: fileDiffReviewer.file_diff_id,
          id: fileDiffReviewer.id,
          lastModified: fileDiffReviewer.last_modified,
          reviewed: fileDiffReviewer.reviewed,
          reviewerId: fileDiffReviewer.reviewer_id,
      };
    },

    toJSON: function() {
        return {
            reviewed: this.get('reviewed')
        };
    },

    /*
     * Performs AJAX requests against the server-side API.
     */
    sync: function(method, model, options) {
        Backbone.sync.call(this, method, model, _.defaults({
            contentType: 'application/x-www-form-urlencoded',
            data: model.toJSON(options),
            processData: true,
            error: _.bind(function(xhr) {
                var rsp = null,
                    loadError,
                    text;

                try {
                    rsp = $.parseJSON(xhr.responseText);
                    text = rsp.err.msg;
                    loadError = rsp.load_error;
                } catch (e) {
                    text = 'HTTP ' + xhr.status + ' ' + xhr.statusText;
                }

                if (_.isFunction(options.error)) {
                    xhr.errorText = text;
                    xhr.errorRsp = rsp;
                    options.error(xhr, options);
                }
            }, this)
        }, options));
    }
});
