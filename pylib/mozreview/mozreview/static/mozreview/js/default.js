$(document).ready(function() {

  // Fix logout url
  $("a[href='/account/logout/']").attr("href", "/mozreview/logout/");
  $("#accountnav li").css("visibility", "visible");

  // Hide "Close Discarded" and "Close Submitted" in request listings
  $('#page_sidebar').find('a.discard, a.submit').remove();

  // Open MozReview subnav items in a new window
  $('#nav-mozreview-menu').parent().find('li a').attr('target', '_blank');
});
