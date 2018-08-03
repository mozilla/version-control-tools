  $ . $TESTDIR/hgext/pushlog/tests/helpers.sh
  $ maketestrepousers > /dev/null

Query for an individual user's pushes
  $ http "http://localhost:$HGPORT/hg-test/json-pushes?user=luser" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "1": {
          "changesets": [
              "8c687ea0e27cd77b4fa5025327a41906800cfcd5"
          ],
          "date": 1227282600,
          "user": "luser"
      },
      "11": {
          "changesets": [
              "53e89e4e6258eed12b0dc67380015de479ce496e",
              "2e7c07446def93a7afb63517d9d6f2879b08653c"
          ],
          "date": 1228233000,
          "user": "luser"
      },
      "14": {
          "changesets": [
              "3580f0821c4d0bb6d013d2973f8629541704ecd2",
              "4df5711a25e9daceb4d35fd566d3f22e8e024345"
          ],
          "date": 1228492200,
          "user": "luser"
      },
      "17": {
          "changesets": [
              "9c9217ca80ce3cf8c140c1af4e254d817e9945f7",
              "db44477aa15b0ac3ac403c0419140416697c3b92"
          ],
          "date": 1228837800,
          "user": "luser"
      },
      "2": {
          "changesets": [
              "90a0919e134179630db1a9cfea3476793e68230c",
              "ea44848ca8aa9fa60c10936fdf8300f8868e9340"
          ],
          "date": 1227369000,
          "user": "luser"
      },
      "20": {
          "changesets": [
              "7b26724b897ca32275c3c83f770ef3761ed1be84",
              "ac4a8b83057888133e9dab79d0d327a70e6a7f2a"
          ],
          "date": 1229097000,
          "user": "luser"
      },
      "23": {
          "changesets": [
              "773195adc944c860ad0fbb278921a6e2d27f4405",
              "306b6389a9ad743bc619d5e62ea6a75bb842d09e"
          ],
          "date": 1229269800,
          "user": "luser"
      },
      "26": {
          "changesets": [
              "2274c682144a166997ed94a3a092a7df04ecebbb",
              "f2b859fb39c4378a084edf14efd76ea5bd5dc70f"
          ],
          "date": 1229529000,
          "user": "luser"
      },
      "29": {
          "changesets": [
              "2012c9f3b92d8153fd36f7388802a5e59527bf57",
              "9fef10362adc35e72dfb3f38d6e540ef2bde785e"
          ],
          "date": 1229788200,
          "user": "luser"
      },
      "5": {
          "changesets": [
              "f1af4004fca66aaf0938f50daffa9d24bbbe3f07",
              "0341cfc3072ffd468facf73e47f8624079616bfc"
          ],
          "date": 1227714600,
          "user": "luser"
      },
      "8": {
          "changesets": [
              "7f9d2db01c2345f7d19964c01f997ab0e49de9d3",
              "d4b458f1c3351dd7500839e028f5bb1e2b2ff109"
          ],
          "date": 1227973800,
          "user": "luser"
      }
  }


  $ http "http://localhost:$HGPORT/hg-test/json-pushes?user=someone" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "12": {
          "changesets": [
              "1980d3e0c05f3f3785168ea4dbe8da33a9de42ca",
              "8a354cb74bae0bcc04550e5335612bbf922ef364"
          ],
          "date": 1228319400,
          "user": "someone"
      },
      "15": {
          "changesets": [
              "26bb8677e78db04f4bca2ea2f79985707fbb0b2a",
              "0e59804eb117f10112f6d0a8212002d7eab80de9"
          ],
          "date": 1228578600,
          "user": "someone"
      },
      "18": {
          "changesets": [
              "23dd64640c05568ff7aee57d3a4e7641795d667a",
              "e77d8a7d36c5707317dbad494a9947261a34d618"
          ],
          "date": 1228924200,
          "user": "someone"
      },
      "21": {
          "changesets": [
              "e752ca2d37f753b617382d8def58c090e2cb8ca6",
              "5af266358ee895496337d0c6f9646954c607d189"
          ],
          "date": 1229140200,
          "user": "someone"
      },
      "24": {
          "changesets": [
              "4b533377ba86200b561e423625ce0a7f17d1f9e3",
              "e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f"
          ],
          "date": 1229356200,
          "user": "someone"
      },
      "27": {
          "changesets": [
              "2be12c9ad0c8a4dd783a639cb7512d64a96e7b93",
              "badb82dde54097638883b824baa0009f4258d9f5"
          ],
          "date": 1229615400,
          "user": "someone"
      },
      "3": {
          "changesets": [
              "564169828a86df44c499a737a3e40489598a9387",
              "0137424351053e5108ce5b8cf14d69a5bd44b568"
          ],
          "date": 1227455400,
          "user": "someone"
      },
      "30": {
          "changesets": [
              "354174f3ddf9b07f9dd0670b698c97b59dfa78ea",
              "f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc"
          ],
          "date": 1229874600,
          "user": "someone"
      },
      "6": {
          "changesets": [
              "07386661f41722a95cdf640ee610ae759bb36168",
              "96ec854d523c3e43bf5e015f68fccfcb632525a6"
          ],
          "date": 1227801000,
          "user": "someone"
      },
      "9": {
          "changesets": [
              "16d0fba6c77efcb0499a87fe91fd179b84888c5e",
              "5fda1cecd054f1939b9d091768b335823ee04fc2"
          ],
          "date": 1228060200,
          "user": "someone"
      }
  }


Query for two users' pushes
  $ http "http://localhost:$HGPORT/hg-test/json-pushes?user=luser&user=someone" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "1": {
          "changesets": [
              "8c687ea0e27cd77b4fa5025327a41906800cfcd5"
          ],
          "date": 1227282600,
          "user": "luser"
      },
      "11": {
          "changesets": [
              "53e89e4e6258eed12b0dc67380015de479ce496e",
              "2e7c07446def93a7afb63517d9d6f2879b08653c"
          ],
          "date": 1228233000,
          "user": "luser"
      },
      "12": {
          "changesets": [
              "1980d3e0c05f3f3785168ea4dbe8da33a9de42ca",
              "8a354cb74bae0bcc04550e5335612bbf922ef364"
          ],
          "date": 1228319400,
          "user": "someone"
      },
      "14": {
          "changesets": [
              "3580f0821c4d0bb6d013d2973f8629541704ecd2",
              "4df5711a25e9daceb4d35fd566d3f22e8e024345"
          ],
          "date": 1228492200,
          "user": "luser"
      },
      "15": {
          "changesets": [
              "26bb8677e78db04f4bca2ea2f79985707fbb0b2a",
              "0e59804eb117f10112f6d0a8212002d7eab80de9"
          ],
          "date": 1228578600,
          "user": "someone"
      },
      "17": {
          "changesets": [
              "9c9217ca80ce3cf8c140c1af4e254d817e9945f7",
              "db44477aa15b0ac3ac403c0419140416697c3b92"
          ],
          "date": 1228837800,
          "user": "luser"
      },
      "18": {
          "changesets": [
              "23dd64640c05568ff7aee57d3a4e7641795d667a",
              "e77d8a7d36c5707317dbad494a9947261a34d618"
          ],
          "date": 1228924200,
          "user": "someone"
      },
      "2": {
          "changesets": [
              "90a0919e134179630db1a9cfea3476793e68230c",
              "ea44848ca8aa9fa60c10936fdf8300f8868e9340"
          ],
          "date": 1227369000,
          "user": "luser"
      },
      "20": {
          "changesets": [
              "7b26724b897ca32275c3c83f770ef3761ed1be84",
              "ac4a8b83057888133e9dab79d0d327a70e6a7f2a"
          ],
          "date": 1229097000,
          "user": "luser"
      },
      "21": {
          "changesets": [
              "e752ca2d37f753b617382d8def58c090e2cb8ca6",
              "5af266358ee895496337d0c6f9646954c607d189"
          ],
          "date": 1229140200,
          "user": "someone"
      },
      "23": {
          "changesets": [
              "773195adc944c860ad0fbb278921a6e2d27f4405",
              "306b6389a9ad743bc619d5e62ea6a75bb842d09e"
          ],
          "date": 1229269800,
          "user": "luser"
      },
      "24": {
          "changesets": [
              "4b533377ba86200b561e423625ce0a7f17d1f9e3",
              "e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f"
          ],
          "date": 1229356200,
          "user": "someone"
      },
      "26": {
          "changesets": [
              "2274c682144a166997ed94a3a092a7df04ecebbb",
              "f2b859fb39c4378a084edf14efd76ea5bd5dc70f"
          ],
          "date": 1229529000,
          "user": "luser"
      },
      "27": {
          "changesets": [
              "2be12c9ad0c8a4dd783a639cb7512d64a96e7b93",
              "badb82dde54097638883b824baa0009f4258d9f5"
          ],
          "date": 1229615400,
          "user": "someone"
      },
      "29": {
          "changesets": [
              "2012c9f3b92d8153fd36f7388802a5e59527bf57",
              "9fef10362adc35e72dfb3f38d6e540ef2bde785e"
          ],
          "date": 1229788200,
          "user": "luser"
      },
      "3": {
          "changesets": [
              "564169828a86df44c499a737a3e40489598a9387",
              "0137424351053e5108ce5b8cf14d69a5bd44b568"
          ],
          "date": 1227455400,
          "user": "someone"
      },
      "30": {
          "changesets": [
              "354174f3ddf9b07f9dd0670b698c97b59dfa78ea",
              "f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc"
          ],
          "date": 1229874600,
          "user": "someone"
      },
      "5": {
          "changesets": [
              "f1af4004fca66aaf0938f50daffa9d24bbbe3f07",
              "0341cfc3072ffd468facf73e47f8624079616bfc"
          ],
          "date": 1227714600,
          "user": "luser"
      },
      "6": {
          "changesets": [
              "07386661f41722a95cdf640ee610ae759bb36168",
              "96ec854d523c3e43bf5e015f68fccfcb632525a6"
          ],
          "date": 1227801000,
          "user": "someone"
      },
      "8": {
          "changesets": [
              "7f9d2db01c2345f7d19964c01f997ab0e49de9d3",
              "d4b458f1c3351dd7500839e028f5bb1e2b2ff109"
          ],
          "date": 1227973800,
          "user": "luser"
      },
      "9": {
          "changesets": [
              "16d0fba6c77efcb0499a87fe91fd179b84888c5e",
              "5fda1cecd054f1939b9d091768b335823ee04fc2"
          ],
          "date": 1228060200,
          "user": "someone"
      }
  }


Querying for all users' pushes + a startID should be equivalent to just querying for that startID
  $ http "http://localhost:$HGPORT/hg-test/json-pushes?user=luser&user=someone&user=johndoe&startID=20" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "21": {
          "changesets": [
              "e752ca2d37f753b617382d8def58c090e2cb8ca6",
              "5af266358ee895496337d0c6f9646954c607d189"
          ],
          "date": 1229140200,
          "user": "someone"
      },
      "22": {
          "changesets": [
              "59b7f60b3a3464abb7fd3ea2bf1798960136a7fe",
              "f4835d42999840c490559b5f933036ee8f2ed6af"
          ],
          "date": 1229183400,
          "user": "johndoe"
      },
      "23": {
          "changesets": [
              "773195adc944c860ad0fbb278921a6e2d27f4405",
              "306b6389a9ad743bc619d5e62ea6a75bb842d09e"
          ],
          "date": 1229269800,
          "user": "luser"
      },
      "24": {
          "changesets": [
              "4b533377ba86200b561e423625ce0a7f17d1f9e3",
              "e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f"
          ],
          "date": 1229356200,
          "user": "someone"
      },
      "25": {
          "changesets": [
              "57eaea907fcce462398e1fed38eb9b75fd2f4724",
              "e706af4df5a146039c05ecaffade019b325b9abe"
          ],
          "date": 1229442600,
          "user": "johndoe"
      },
      "26": {
          "changesets": [
              "2274c682144a166997ed94a3a092a7df04ecebbb",
              "f2b859fb39c4378a084edf14efd76ea5bd5dc70f"
          ],
          "date": 1229529000,
          "user": "luser"
      },
      "27": {
          "changesets": [
              "2be12c9ad0c8a4dd783a639cb7512d64a96e7b93",
              "badb82dde54097638883b824baa0009f4258d9f5"
          ],
          "date": 1229615400,
          "user": "someone"
      },
      "28": {
          "changesets": [
              "e494a4d71f1905d661f88dd8865283dcb6b42be3",
              "bf9bdfe181e896c08c4f7332be751004b96e26f8"
          ],
          "date": 1229701800,
          "user": "johndoe"
      },
      "29": {
          "changesets": [
              "2012c9f3b92d8153fd36f7388802a5e59527bf57",
              "9fef10362adc35e72dfb3f38d6e540ef2bde785e"
          ],
          "date": 1229788200,
          "user": "luser"
      },
      "30": {
          "changesets": [
              "354174f3ddf9b07f9dd0670b698c97b59dfa78ea",
              "f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc"
          ],
          "date": 1229874600,
          "user": "someone"
      },
      "31": {
          "changesets": [
              "7127e784b4ba3a5cf792b433b19d527e2bd0b44a",
              "054cf6e47bbe2fb7a3e4061ded6763bed4fd4550"
          ],
          "date": 1229961000,
          "user": "johndoe"
      }
  }


  $ http "http://localhost:$HGPORT/hg-test/json-pushes?startID=20" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "21": {
          "changesets": [
              "e752ca2d37f753b617382d8def58c090e2cb8ca6",
              "5af266358ee895496337d0c6f9646954c607d189"
          ],
          "date": 1229140200,
          "user": "someone"
      },
      "22": {
          "changesets": [
              "59b7f60b3a3464abb7fd3ea2bf1798960136a7fe",
              "f4835d42999840c490559b5f933036ee8f2ed6af"
          ],
          "date": 1229183400,
          "user": "johndoe"
      },
      "23": {
          "changesets": [
              "773195adc944c860ad0fbb278921a6e2d27f4405",
              "306b6389a9ad743bc619d5e62ea6a75bb842d09e"
          ],
          "date": 1229269800,
          "user": "luser"
      },
      "24": {
          "changesets": [
              "4b533377ba86200b561e423625ce0a7f17d1f9e3",
              "e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f"
          ],
          "date": 1229356200,
          "user": "someone"
      },
      "25": {
          "changesets": [
              "57eaea907fcce462398e1fed38eb9b75fd2f4724",
              "e706af4df5a146039c05ecaffade019b325b9abe"
          ],
          "date": 1229442600,
          "user": "johndoe"
      },
      "26": {
          "changesets": [
              "2274c682144a166997ed94a3a092a7df04ecebbb",
              "f2b859fb39c4378a084edf14efd76ea5bd5dc70f"
          ],
          "date": 1229529000,
          "user": "luser"
      },
      "27": {
          "changesets": [
              "2be12c9ad0c8a4dd783a639cb7512d64a96e7b93",
              "badb82dde54097638883b824baa0009f4258d9f5"
          ],
          "date": 1229615400,
          "user": "someone"
      },
      "28": {
          "changesets": [
              "e494a4d71f1905d661f88dd8865283dcb6b42be3",
              "bf9bdfe181e896c08c4f7332be751004b96e26f8"
          ],
          "date": 1229701800,
          "user": "johndoe"
      },
      "29": {
          "changesets": [
              "2012c9f3b92d8153fd36f7388802a5e59527bf57",
              "9fef10362adc35e72dfb3f38d6e540ef2bde785e"
          ],
          "date": 1229788200,
          "user": "luser"
      },
      "30": {
          "changesets": [
              "354174f3ddf9b07f9dd0670b698c97b59dfa78ea",
              "f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc"
          ],
          "date": 1229874600,
          "user": "someone"
      },
      "31": {
          "changesets": [
              "7127e784b4ba3a5cf792b433b19d527e2bd0b44a",
              "054cf6e47bbe2fb7a3e4061ded6763bed4fd4550"
          ],
          "date": 1229961000,
          "user": "johndoe"
      }
  }


Query for a user and a startdate
  $ http "http://localhost:$HGPORT/hg-test/json-pushes?user=luser&startdate=$MIDTIME" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "11": {
          "changesets": [
              "53e89e4e6258eed12b0dc67380015de479ce496e",
              "2e7c07446def93a7afb63517d9d6f2879b08653c"
          ],
          "date": 1228233000,
          "user": "luser"
      },
      "14": {
          "changesets": [
              "3580f0821c4d0bb6d013d2973f8629541704ecd2",
              "4df5711a25e9daceb4d35fd566d3f22e8e024345"
          ],
          "date": 1228492200,
          "user": "luser"
      },
      "17": {
          "changesets": [
              "9c9217ca80ce3cf8c140c1af4e254d817e9945f7",
              "db44477aa15b0ac3ac403c0419140416697c3b92"
          ],
          "date": 1228837800,
          "user": "luser"
      },
      "20": {
          "changesets": [
              "7b26724b897ca32275c3c83f770ef3761ed1be84",
              "ac4a8b83057888133e9dab79d0d327a70e6a7f2a"
          ],
          "date": 1229097000,
          "user": "luser"
      },
      "23": {
          "changesets": [
              "773195adc944c860ad0fbb278921a6e2d27f4405",
              "306b6389a9ad743bc619d5e62ea6a75bb842d09e"
          ],
          "date": 1229269800,
          "user": "luser"
      },
      "26": {
          "changesets": [
              "2274c682144a166997ed94a3a092a7df04ecebbb",
              "f2b859fb39c4378a084edf14efd76ea5bd5dc70f"
          ],
          "date": 1229529000,
          "user": "luser"
      },
      "29": {
          "changesets": [
              "2012c9f3b92d8153fd36f7388802a5e59527bf57",
              "9fef10362adc35e72dfb3f38d6e540ef2bde785e"
          ],
          "date": 1229788200,
          "user": "luser"
      },
      "5": {
          "changesets": [
              "f1af4004fca66aaf0938f50daffa9d24bbbe3f07",
              "0341cfc3072ffd468facf73e47f8624079616bfc"
          ],
          "date": 1227714600,
          "user": "luser"
      },
      "8": {
          "changesets": [
              "7f9d2db01c2345f7d19964c01f997ab0e49de9d3",
              "d4b458f1c3351dd7500839e028f5bb1e2b2ff109"
          ],
          "date": 1227973800,
          "user": "luser"
      }
  }


Query for a user with a startdate and an enddate  
  $ http "http://localhost:$HGPORT/hg-test/json-pushes?user=luser&startdate=$STARTTIME&enddate=$MIDTIME" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "1": {
          "changesets": [
              "8c687ea0e27cd77b4fa5025327a41906800cfcd5"
          ],
          "date": 1227282600,
          "user": "luser"
      },
      "2": {
          "changesets": [
              "90a0919e134179630db1a9cfea3476793e68230c",
              "ea44848ca8aa9fa60c10936fdf8300f8868e9340"
          ],
          "date": 1227369000,
          "user": "luser"
      }
  }


Query for multiple changesets and a user
Should be the same as just querying for the one changeset,
as only one changeset was pushed by this user

  $ http "http://localhost:$HGPORT/hg-test/json-pushes?user=luser&changeset=3580f0821c4d" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "14": {
          "changesets": [
              "3580f0821c4d0bb6d013d2973f8629541704ecd2",
              "4df5711a25e9daceb4d35fd566d3f22e8e024345"
          ],
          "date": 1228492200,
          "user": "luser"
      }
  }


  $ http "http://localhost:$HGPORT/hg-test/json-pushes?user=luser&changeset=3580f0821c4d&changeset=26bb8677e78d" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "14": {
          "changesets": [
              "3580f0821c4d0bb6d013d2973f8629541704ecd2",
              "4df5711a25e9daceb4d35fd566d3f22e8e024345"
          ],
          "date": 1228492200,
          "user": "luser"
      }
  }
