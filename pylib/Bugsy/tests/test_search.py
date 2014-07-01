import bugsy
from bugsy import Bugsy, BugsyException, LoginException
from bugsy import Bug

import responses
import json

@responses.activate
def test_we_only_ask_for_the_include_fields():
  include_return = {
         "bugs" : [
            {
               "component" : "Marionette",
               "flags" : [],
               "id" : 861874,
               "op_sys" : "Gonk (Firefox OS)",
               "platform" : "Other",
               "product" : "Testing",
               "resolution" : "",
               "status" : "REOPENED",
               "summary" : "Tracking bug for uplifting is_displayed issue fix for WebDriver",
               "version" : "unspecified"
            },
            {
               "component" : "Marionette",
               "flags" : [
                  {
                     "creation_date" : "2013-11-26T14:16:09Z",
                     "id" : 758758,
                     "modification_date" : "2013-11-26T14:16:09Z",
                     "name" : "needinfo",
                     "requestee" : "dkuo@mozilla.com",
                     "setter" : "bob.silverberg@gmail.com",
                     "status" : "?",
                     "type_id" : 800
                  }
               ],
               "id" : 862156,
               "op_sys" : "Gonk (Firefox OS)",
               "platform" : "ARM",
               "product" : "Testing",
               "resolution" : "",
               "status" : "NEW",
               "summary" : "Marionette thinks that the play button in the music app is not displayed",
               "version" : "unspecified"
            }
         ]
      }


  responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/bug?assigned_to=dburns@mozilla.com&whiteboard=affects&short_desc_type=allwordssubstr&include_fields=version&include_fields=id&include_fields=summary&include_fields=status&include_fields=op_sys&include_fields=resolution&include_fields=product&include_fields=component&include_fields=platform&include_fields=flags',
                    body=json.dumps(include_return), status=200,
                    content_type='application/json', match_querystring=True)

  bugzilla = Bugsy()
  bugs = bugzilla.search_for\
          .include_fields('flags')\
          .assigned_to("dburns@mozilla.com")\
          .whiteboard("affects")\
          .search()

  assert len(responses.calls) == 1
  assert len(bugs) == 2
  assert bugs[0].to_dict()['flags'] == include_return['bugs'][0]['flags']

@responses.activate
def test_we_only_ask_for_the_include_fields_while_logged_in():
  include_return = {
         "bugs" : [
            {
               "component" : "Marionette",
               "flags" : [],
               "id" : 861874,
               "op_sys" : "Gonk (Firefox OS)",
               "platform" : "Other",
               "product" : "Testing",
               "resolution" : "",
               "status" : "REOPENED",
               "summary" : "Tracking bug for uplifting is_displayed issue fix for WebDriver",
               "version" : "unspecified"
            },
            {
               "component" : "Marionette",
               "flags" : [
                  {
                     "creation_date" : "2013-11-26T14:16:09Z",
                     "id" : 758758,
                     "modification_date" : "2013-11-26T14:16:09Z",
                     "name" : "needinfo",
                     "requestee" : "dkuo@mozilla.com",
                     "setter" : "bob.silverberg@gmail.com",
                     "status" : "?",
                     "type_id" : 800
                  }
               ],
               "id" : 862156,
               "op_sys" : "Gonk (Firefox OS)",
               "platform" : "ARM",
               "product" : "Testing",
               "resolution" : "",
               "status" : "NEW",
               "summary" : "Marionette thinks that the play button in the music app is not displayed",
               "version" : "unspecified"
            }
         ]
      }
  responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/login?login=foo&password=bar',
                    body='{"token": "foobar"}', status=200,
                    content_type='application/json', match_querystring=True)

  responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/bug?include_fields=version&include_fields=id&include_fields=summary&include_fields=status&include_fields=op_sys&include_fields=resolution&include_fields=product&include_fields=component&include_fields=platform&include_fields=flags&token=foobar',
                    body=json.dumps(include_return), status=200,
                    content_type='application/json', match_querystring=True)

  bugzilla = Bugsy('foo', 'bar')
  bugs = bugzilla.search_for\
          .include_fields('flags')\
          .search()

  assert len(responses.calls) == 2
  assert len(bugs) == 2
  assert bugs[0].product == include_return['bugs'][0]['product']

@responses.activate
def test_we_can_return_keyword_search():
    keyword_return = {
      "bugs" : [
      {
         "component" : "Networking: HTTP",
         "product" : "Core",
         "summary" : "IsPending broken for requests without Content-Type"
      },
      {
         "component" : "Developer Tools: Graphic Commandline and Toolbar",
         "product" : "Firefox",
         "summary" : "GCLI Command to open Profile Directory"
      },
      {
         "component" : "Video/Audio Controls",
         "product" : "Toolkit",
         "summary" : "Fullscreen video should disable screensaver during playback on Linux"
      },
      {
         "component" : "Reader Mode",
         "product" : "Firefox for Android",
         "summary" : "Article showing twice in reader mode"
      },
      {
         "component" : "Message Reader UI",
         "product" : "Thunderbird",
         "summary" : "Make \"visited link\" coloring work in thunderbird"
      }]
    }

    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/bug?include_fields=version&include_fields=id&include_fields=summary&include_fields=status&include_fields=op_sys&include_fields=resolution&include_fields=product&include_fields=component&include_fields=platform&keywords=checkin-needed&',
                    body=json.dumps(keyword_return), status=200,
                    content_type='application/json', match_querystring=True)

    bugzilla = Bugsy()
    bugs = bugzilla.search_for\
            .keywords('checkin-needed')\
            .search()

    assert len(responses.calls) == 1
    assert len(bugs) == 5
    assert bugs[0].product == keyword_return['bugs'][0]['product']
    assert bugs[0].component == keyword_return['bugs'][0]['component']

@responses.activate
def test_that_we_can_search_for_a_specific_user():
    user_return = {
        "bugs" : [
            {
              "product" : "addons.mozilla.org",
               "summary" : "Add Selenium tests to the repository"
            },
            {
               "product" : "addons.mozilla.org",
               "summary" : "Add Ids to links to help with testability"
            },
            {
               "product" : "addons.mozilla.org",
               "summary" : "Add a name for AMO Themes sort links for testability"
            },
            {
               "product" : "addons.mozilla.org",
               "summary" : "Missing ID for div with class \"feature ryff\" (Mobile Add-on: Foursquare)"
            }
           ]
        }
    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/bug?include_fields=version&include_fields=id&include_fields=summary&include_fields=status&include_fields=op_sys&include_fields=resolution&include_fields=product&include_fields=component&include_fields=platform&assigned_to=dburns@mozilla.com&',
                    body=json.dumps(user_return), status=200,
                    content_type='application/json', match_querystring=True)

    bugzilla = Bugsy()
    bugs = bugzilla.search_for\
            .assigned_to('dburns@mozilla.com')\
            .search()

    assert len(responses.calls) == 1
    assert len(bugs) == 4
    assert bugs[0].product == user_return['bugs'][0]['product']
    assert bugs[0].summary == user_return['bugs'][0]['summary']

@responses.activate
def test_we_can_search_summary_fields():
    summary_return = {
     "bugs" : [
        {
           "component" : "CSS Parsing and Computation",
           "product" : "Core",
           "summary" : "Map \"rebeccapurple\" to #663399 in named color list."
        }
      ]
    }


    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/bug?assigned_to=dburns@mozilla.com&short_desc=rebecca&short_desc_type=allwordssubstr&include_fields=version&include_fields=id&include_fields=summary&include_fields=status&include_fields=op_sys&include_fields=resolution&include_fields=product&include_fields=component&include_fields=platform&',
                    body=json.dumps(summary_return), status=200,
                    content_type='application/json', match_querystring=True)

    bugzilla = Bugsy()
    bugs = bugzilla.search_for\
            .assigned_to('dburns@mozilla.com')\
            .summary("rebecca")\
            .search()

    assert len(responses.calls) == 1
    assert len(bugs) == 1
    assert bugs[0].product == summary_return['bugs'][0]['product']
    assert bugs[0].summary == summary_return['bugs'][0]['summary']


@responses.activate
def test_we_can_search_whiteboard_fields():
    whiteboard_return = {
       "bugs" : [
          {
             "component" : "Marionette",
             "product" : "Testing",
             "summary" : "Tracking bug for uplifting is_displayed issue fix for WebDriver"
          },
          {
             "component" : "Marionette",
             "product" : "Testing",
             "summary" : "Marionette thinks that the play button in the music app is not displayed"
          }
       ]
    }


    responses.add(responses.GET, 'https://bugzilla.mozilla.org/rest/bug?assigned_to=dburns@mozilla.com&whiteboard=affects&short_desc_type=allwordssubstr&include_fields=version&include_fields=id&include_fields=summary&include_fields=status&include_fields=op_sys&include_fields=resolution&include_fields=product&include_fields=component&include_fields=platform&',
                    body=json.dumps(whiteboard_return), status=200,
                    content_type='application/json', match_querystring=True)

    bugzilla = Bugsy()
    bugs = bugzilla.search_for\
            .assigned_to('dburns@mozilla.com')\
            .whiteboard("affects")\
            .search()

    assert len(responses.calls) == 1
    assert len(bugs) == 2
    assert bugs[0].product == whiteboard_return['bugs'][0]['product']
    assert bugs[0].summary == whiteboard_return['bugs'][0]['summary']