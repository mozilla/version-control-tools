$(document).ready(function () {
  // add click handler to the localize dates link
  $('#localize').show().click(function () {
     $(this).hide();
     $('.date').each(function (i) {
       $(this).text(new Date($(this).text()).toLocaleString());
     });
     return false;
  });
  // add click handler to toggle collapsible sections
  $('.expand').click(function () {
    if ($(this).text() == "[Expand]")
      $(this).text("[Collapse]");
    else
      $(this).text("[Expand]");

    var pushid = $(this).attr("class");
    pushid = '.' + pushid.match(/id\d+/);
    $(pushid).nextAll(pushid).toggle();
    return false;
  });
});
