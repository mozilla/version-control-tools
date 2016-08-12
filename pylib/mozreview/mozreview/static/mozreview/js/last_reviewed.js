$(document).ready(function() {
  var revision = $('#user_data').data('last-reviewed-revision');

  if (typeof revision !== 'undefined' && revision > 0) {
    $('#diff_revision_selector')
      .prepend($('<p/>')
      .text(gettext('You last reviewed revision ' + revision + '.')));
  }
});
