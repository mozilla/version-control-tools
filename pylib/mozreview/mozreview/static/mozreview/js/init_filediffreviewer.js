$(document).ready(function() {
  var page = RB.PageManager.getPage();

    var FileDiffReviewerData = $('#file-diff-reviewer-data')
                               .data('file-diff-reviewer');
    var fileDiffReviewerModels = FileDiffReviewerData.map(function(item){
      return new RB.FileDiffReviewerModel(item);
    })
    var fileDiffReviewerCollection = new RB.FileDiffReviewerCollection(
      fileDiffReviewerModels
    );

    var getButtonText = function(elem) {
      if (elem.get('reviewed')) {
        return 'reviewed';
      } else {
        return 'not reviewed';
      }
    };

    $.funcQueue('diff_files').add(function(){
      fileDiffReviewerCollection.each(function(elem){
        var diff_box_table = document.getElementById(
          'file' + elem.get('file_diff_id')
        );

        if (diff_box_table != null) {
          var reviewButton = document.createElement('button');
          reviewButton.textContent = getButtonText(elem);
          reviewButton.classList.add('diff-file-btn');
          if (elem.get('reviewed')) {
            reviewButton.classList.add('reviewed');
          }

          reviewButton.addEventListener('click', function(event){
            reviewButton.disabled = true;
            elem.save({'reviewed': !elem.get('reviewed')},{
              success: function(){
                reviewButton.disabled = false;
                reviewButton.textContent = getButtonText(elem);
                reviewButton.classList.toggle('reviewed');
              },
              error: function(model, response){
                reviewButton.disabled = false;
              }
            });
          });
          diff_box_table.parentElement.appendChild(reviewButton);
        } else {
          console.debug('no diff table found')
        }
      });
    });
});
