/**
 * Monkey-patch RB.TextCommentRowSelector so that double-clicks will
 * result in a comment being opened, a la Splinter.
 */
RB.TextCommentRowSelector = RB.TextCommentRowSelector.extend({
  events: _.extend({
    'dblclick': '_onDoubleClick',
  }, RB.TextCommentRowSelector.prototype.events),

  /*
   * Returns whether a node represents source code in the diff viewer.
   *
   * A node represents source code when it is within the section of
   * the diff viewer that's actually displaying code. That means
   * that it's within a <td> with a class "l", or a <td> with class
   * "r".
   */
  _isWithinCodeCell: function(node) {
    return $(node).parents('td.l, td.r').length > 0;
  },

  /*
   * Returns the ancestor <tr> in the diff viewer for some
   * node.
   */
  _getRowFromChild: function($node) {
    return $node.parents('tr[line]');
  },

  /*
   * Handler for when the user double-clicks on a row.
   *
   * This will open a comment dialog for the row that the user
   * double-clicked on.
   */
  _onDoubleClick: function(e) {
    var node = e.target,
        $row,
        lineNum;

    if (this._isWithinCodeCell(node)) {
      $row = this._getRowFromChild($(node));
      lineNum = this.getLineNum($row[0]);
      this.options.reviewableView.createAndEditCommentBlock({
        beginLineNum: lineNum,
        endLineNum: lineNum,
        $beginRow: $row,
        $endRow: $row
      });
    }
  }
});