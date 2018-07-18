  $ . $TESTDIR/hgext/pushlog-legacy/tests/helpers.sh
  $ maketestrepousers > /dev/null


Sanity check the html output

  $ http http://localhost:$HGPORT/pushloghtml --header content-type --body-file body
  200
  content-type: text/html; charset=ascii

  $ grep 7127e784b4ba body
  <tr class="pushlogentry parity0  id31"><td></td><td><a href="/rev/7127e784b4ba">7127e784b4ba</a></td><td><strong>johndoe &mdash; checkin 60</strong> <span class="logtags"></span></td></tr>

Get all JSON data

  $ http "http://localhost:$HGPORT/json-pushes?startID=0" --header content-type --body-file body
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
      "10": {
          "changesets": [
              "6a9848d7dc42eb0fd7dab35b06b366db93698e24",
              "4d0d5182c524fa92348319583ae7bf28c2b1b296"
          ],
          "date": 1228146600,
          "user": "johndoe"
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
      "13": {
          "changesets": [
              "53e334794d36467b2083d3b94fb1dc3f061d1cd9",
              "93f74182971010ac8a9a5726fb976f1d2e593ea5"
          ],
          "date": 1228405800,
          "user": "johndoe"
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
      "16": {
          "changesets": [
              "6fa979d08156ccfe22632af72d8408468e1e8ace",
              "7dc0e50f2e77447cd0f9de9c0fc51eadb2320ba7"
          ],
          "date": 1228751400,
          "user": "johndoe"
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
      "19": {
          "changesets": [
              "868ec41cad32bb84115253e226c88605b8f9f354",
              "069b8cf8dcac61e0771c795e8ffe8fcab2608233"
          ],
          "date": 1229010600,
          "user": "johndoe"
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
      "31": {
          "changesets": [
              "7127e784b4ba3a5cf792b433b19d527e2bd0b44a",
              "054cf6e47bbe2fb7a3e4061ded6763bed4fd4550"
          ],
          "date": 1229961000,
          "user": "johndoe"
      },
      "4": {
          "changesets": [
              "52d3fce08d691a87d01c8f4397a8b34d98427271",
              "12799c959e3ad5465a98d333408ae8a5296d90a6"
          ],
          "date": 1227541800,
          "user": "johndoe"
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
      "7": {
          "changesets": [
              "745197626166e61f2a5cc9834ecc1b55cd987f5f",
              "716b98766200cea4f925caa2952bd16252358376"
          ],
          "date": 1227887400,
          "user": "johndoe"
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


Get all JSON data with details

  $ http "http://localhost:$HGPORT/json-pushes?startID=0&full=1" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "1": {
          "changesets": [
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 1",
                  "files": [
                      "testfile"
                  ],
                  "node": "8c687ea0e27cd77b4fa5025327a41906800cfcd5",
                  "parents": [
                      "0000000000000000000000000000000000000000"
                  ],
                  "tags": []
              }
          ],
          "date": 1227282600,
          "user": "luser"
      },
      "10": {
          "changesets": [
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 18",
                  "files": [
                      "testfile"
                  ],
                  "node": "6a9848d7dc42eb0fd7dab35b06b366db93698e24",
                  "parents": [
                      "5fda1cecd054f1939b9d091768b335823ee04fc2"
                  ],
                  "tags": []
              },
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 19",
                  "files": [
                      "testfile"
                  ],
                  "node": "4d0d5182c524fa92348319583ae7bf28c2b1b296",
                  "parents": [
                      "6a9848d7dc42eb0fd7dab35b06b366db93698e24"
                  ],
                  "tags": []
              }
          ],
          "date": 1228146600,
          "user": "johndoe"
      },
      "11": {
          "changesets": [
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 20",
                  "files": [
                      "testfile"
                  ],
                  "node": "53e89e4e6258eed12b0dc67380015de479ce496e",
                  "parents": [
                      "4d0d5182c524fa92348319583ae7bf28c2b1b296"
                  ],
                  "tags": []
              },
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 21",
                  "files": [
                      "testfile"
                  ],
                  "node": "2e7c07446def93a7afb63517d9d6f2879b08653c",
                  "parents": [
                      "53e89e4e6258eed12b0dc67380015de479ce496e"
                  ],
                  "tags": []
              }
          ],
          "date": 1228233000,
          "user": "luser"
      },
      "12": {
          "changesets": [
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 22",
                  "files": [
                      "testfile"
                  ],
                  "node": "1980d3e0c05f3f3785168ea4dbe8da33a9de42ca",
                  "parents": [
                      "2e7c07446def93a7afb63517d9d6f2879b08653c"
                  ],
                  "tags": []
              },
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 23",
                  "files": [
                      "testfile"
                  ],
                  "node": "8a354cb74bae0bcc04550e5335612bbf922ef364",
                  "parents": [
                      "1980d3e0c05f3f3785168ea4dbe8da33a9de42ca"
                  ],
                  "tags": []
              }
          ],
          "date": 1228319400,
          "user": "someone"
      },
      "13": {
          "changesets": [
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 24",
                  "files": [
                      "testfile"
                  ],
                  "node": "53e334794d36467b2083d3b94fb1dc3f061d1cd9",
                  "parents": [
                      "8a354cb74bae0bcc04550e5335612bbf922ef364"
                  ],
                  "tags": []
              },
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 25",
                  "files": [
                      "testfile"
                  ],
                  "node": "93f74182971010ac8a9a5726fb976f1d2e593ea5",
                  "parents": [
                      "53e334794d36467b2083d3b94fb1dc3f061d1cd9"
                  ],
                  "tags": []
              }
          ],
          "date": 1228405800,
          "user": "johndoe"
      },
      "14": {
          "changesets": [
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 26",
                  "files": [
                      "testfile"
                  ],
                  "node": "3580f0821c4d0bb6d013d2973f8629541704ecd2",
                  "parents": [
                      "93f74182971010ac8a9a5726fb976f1d2e593ea5"
                  ],
                  "tags": []
              },
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 27",
                  "files": [
                      "testfile"
                  ],
                  "node": "4df5711a25e9daceb4d35fd566d3f22e8e024345",
                  "parents": [
                      "3580f0821c4d0bb6d013d2973f8629541704ecd2"
                  ],
                  "tags": []
              }
          ],
          "date": 1228492200,
          "user": "luser"
      },
      "15": {
          "changesets": [
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 28",
                  "files": [
                      "testfile"
                  ],
                  "node": "26bb8677e78db04f4bca2ea2f79985707fbb0b2a",
                  "parents": [
                      "4df5711a25e9daceb4d35fd566d3f22e8e024345"
                  ],
                  "tags": []
              },
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 29",
                  "files": [
                      "testfile"
                  ],
                  "node": "0e59804eb117f10112f6d0a8212002d7eab80de9",
                  "parents": [
                      "26bb8677e78db04f4bca2ea2f79985707fbb0b2a"
                  ],
                  "tags": []
              }
          ],
          "date": 1228578600,
          "user": "someone"
      },
      "16": {
          "changesets": [
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 30",
                  "files": [
                      "testfile"
                  ],
                  "node": "6fa979d08156ccfe22632af72d8408468e1e8ace",
                  "parents": [
                      "0e59804eb117f10112f6d0a8212002d7eab80de9"
                  ],
                  "tags": []
              },
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 31",
                  "files": [
                      "testfile"
                  ],
                  "node": "7dc0e50f2e77447cd0f9de9c0fc51eadb2320ba7",
                  "parents": [
                      "6fa979d08156ccfe22632af72d8408468e1e8ace"
                  ],
                  "tags": []
              }
          ],
          "date": 1228751400,
          "user": "johndoe"
      },
      "17": {
          "changesets": [
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 32",
                  "files": [
                      "testfile"
                  ],
                  "node": "9c9217ca80ce3cf8c140c1af4e254d817e9945f7",
                  "parents": [
                      "7dc0e50f2e77447cd0f9de9c0fc51eadb2320ba7"
                  ],
                  "tags": []
              },
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 33",
                  "files": [
                      "testfile"
                  ],
                  "node": "db44477aa15b0ac3ac403c0419140416697c3b92",
                  "parents": [
                      "9c9217ca80ce3cf8c140c1af4e254d817e9945f7"
                  ],
                  "tags": []
              }
          ],
          "date": 1228837800,
          "user": "luser"
      },
      "18": {
          "changesets": [
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 34",
                  "files": [
                      "testfile8"
                  ],
                  "node": "23dd64640c05568ff7aee57d3a4e7641795d667a",
                  "parents": [
                      "db44477aa15b0ac3ac403c0419140416697c3b92"
                  ],
                  "tags": []
              },
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 35",
                  "files": [
                      "testfile"
                  ],
                  "node": "e77d8a7d36c5707317dbad494a9947261a34d618",
                  "parents": [
                      "23dd64640c05568ff7aee57d3a4e7641795d667a"
                  ],
                  "tags": []
              }
          ],
          "date": 1228924200,
          "user": "someone"
      },
      "19": {
          "changesets": [
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 36",
                  "files": [
                      "testfile"
                  ],
                  "node": "868ec41cad32bb84115253e226c88605b8f9f354",
                  "parents": [
                      "e77d8a7d36c5707317dbad494a9947261a34d618"
                  ],
                  "tags": []
              },
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 37",
                  "files": [
                      "testfile"
                  ],
                  "node": "069b8cf8dcac61e0771c795e8ffe8fcab2608233",
                  "parents": [
                      "868ec41cad32bb84115253e226c88605b8f9f354"
                  ],
                  "tags": []
              }
          ],
          "date": 1229010600,
          "user": "johndoe"
      },
      "2": {
          "changesets": [
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 2",
                  "files": [
                      "testfile"
                  ],
                  "node": "90a0919e134179630db1a9cfea3476793e68230c",
                  "parents": [
                      "8c687ea0e27cd77b4fa5025327a41906800cfcd5"
                  ],
                  "tags": []
              },
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 3",
                  "files": [
                      "testfile"
                  ],
                  "node": "ea44848ca8aa9fa60c10936fdf8300f8868e9340",
                  "parents": [
                      "90a0919e134179630db1a9cfea3476793e68230c"
                  ],
                  "tags": []
              }
          ],
          "date": 1227369000,
          "user": "luser"
      },
      "20": {
          "changesets": [
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 38",
                  "files": [
                      "testfile"
                  ],
                  "node": "7b26724b897ca32275c3c83f770ef3761ed1be84",
                  "parents": [
                      "069b8cf8dcac61e0771c795e8ffe8fcab2608233"
                  ],
                  "tags": []
              },
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 39",
                  "files": [
                      "testfile"
                  ],
                  "node": "ac4a8b83057888133e9dab79d0d327a70e6a7f2a",
                  "parents": [
                      "7b26724b897ca32275c3c83f770ef3761ed1be84"
                  ],
                  "tags": []
              }
          ],
          "date": 1229097000,
          "user": "luser"
      },
      "21": {
          "changesets": [
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 40",
                  "files": [
                      "testfile"
                  ],
                  "node": "e752ca2d37f753b617382d8def58c090e2cb8ca6",
                  "parents": [
                      "ac4a8b83057888133e9dab79d0d327a70e6a7f2a"
                  ],
                  "tags": []
              },
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 41",
                  "files": [
                      "testfile"
                  ],
                  "node": "5af266358ee895496337d0c6f9646954c607d189",
                  "parents": [
                      "e752ca2d37f753b617382d8def58c090e2cb8ca6"
                  ],
                  "tags": []
              }
          ],
          "date": 1229140200,
          "user": "someone"
      },
      "22": {
          "changesets": [
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 42",
                  "files": [
                      "testfile"
                  ],
                  "node": "59b7f60b3a3464abb7fd3ea2bf1798960136a7fe",
                  "parents": [
                      "5af266358ee895496337d0c6f9646954c607d189"
                  ],
                  "tags": []
              },
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 43",
                  "files": [
                      "testfile"
                  ],
                  "node": "f4835d42999840c490559b5f933036ee8f2ed6af",
                  "parents": [
                      "59b7f60b3a3464abb7fd3ea2bf1798960136a7fe"
                  ],
                  "tags": []
              }
          ],
          "date": 1229183400,
          "user": "johndoe"
      },
      "23": {
          "changesets": [
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 44",
                  "files": [
                      "testfile"
                  ],
                  "node": "773195adc944c860ad0fbb278921a6e2d27f4405",
                  "parents": [
                      "f4835d42999840c490559b5f933036ee8f2ed6af"
                  ],
                  "tags": []
              },
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 45",
                  "files": [
                      "testfile"
                  ],
                  "node": "306b6389a9ad743bc619d5e62ea6a75bb842d09e",
                  "parents": [
                      "773195adc944c860ad0fbb278921a6e2d27f4405"
                  ],
                  "tags": []
              }
          ],
          "date": 1229269800,
          "user": "luser"
      },
      "24": {
          "changesets": [
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 46",
                  "files": [
                      "testfile"
                  ],
                  "node": "4b533377ba86200b561e423625ce0a7f17d1f9e3",
                  "parents": [
                      "306b6389a9ad743bc619d5e62ea6a75bb842d09e"
                  ],
                  "tags": []
              },
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 47",
                  "files": [
                      "testfile"
                  ],
                  "node": "e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f",
                  "parents": [
                      "4b533377ba86200b561e423625ce0a7f17d1f9e3"
                  ],
                  "tags": []
              }
          ],
          "date": 1229356200,
          "user": "someone"
      },
      "25": {
          "changesets": [
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 48",
                  "files": [
                      "testfile"
                  ],
                  "node": "57eaea907fcce462398e1fed38eb9b75fd2f4724",
                  "parents": [
                      "e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f"
                  ],
                  "tags": []
              },
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 49",
                  "files": [
                      "testfile"
                  ],
                  "node": "e706af4df5a146039c05ecaffade019b325b9abe",
                  "parents": [
                      "57eaea907fcce462398e1fed38eb9b75fd2f4724"
                  ],
                  "tags": []
              }
          ],
          "date": 1229442600,
          "user": "johndoe"
      },
      "26": {
          "changesets": [
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 50",
                  "files": [
                      "testfile"
                  ],
                  "node": "2274c682144a166997ed94a3a092a7df04ecebbb",
                  "parents": [
                      "e706af4df5a146039c05ecaffade019b325b9abe"
                  ],
                  "tags": []
              },
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 51",
                  "files": [
                      "testfile"
                  ],
                  "node": "f2b859fb39c4378a084edf14efd76ea5bd5dc70f",
                  "parents": [
                      "2274c682144a166997ed94a3a092a7df04ecebbb"
                  ],
                  "tags": []
              }
          ],
          "date": 1229529000,
          "user": "luser"
      },
      "27": {
          "changesets": [
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 52",
                  "files": [
                      "testfile"
                  ],
                  "node": "2be12c9ad0c8a4dd783a639cb7512d64a96e7b93",
                  "parents": [
                      "f2b859fb39c4378a084edf14efd76ea5bd5dc70f"
                  ],
                  "tags": []
              },
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 53",
                  "files": [
                      "testfile"
                  ],
                  "node": "badb82dde54097638883b824baa0009f4258d9f5",
                  "parents": [
                      "2be12c9ad0c8a4dd783a639cb7512d64a96e7b93"
                  ],
                  "tags": []
              }
          ],
          "date": 1229615400,
          "user": "someone"
      },
      "28": {
          "changesets": [
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 54",
                  "files": [
                      "testfile"
                  ],
                  "node": "e494a4d71f1905d661f88dd8865283dcb6b42be3",
                  "parents": [
                      "badb82dde54097638883b824baa0009f4258d9f5"
                  ],
                  "tags": []
              },
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 55",
                  "files": [
                      "testfile"
                  ],
                  "node": "bf9bdfe181e896c08c4f7332be751004b96e26f8",
                  "parents": [
                      "e494a4d71f1905d661f88dd8865283dcb6b42be3"
                  ],
                  "tags": []
              }
          ],
          "date": 1229701800,
          "user": "johndoe"
      },
      "29": {
          "changesets": [
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 56",
                  "files": [
                      "testfile"
                  ],
                  "node": "2012c9f3b92d8153fd36f7388802a5e59527bf57",
                  "parents": [
                      "bf9bdfe181e896c08c4f7332be751004b96e26f8"
                  ],
                  "tags": []
              },
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 57",
                  "files": [
                      "testfile"
                  ],
                  "node": "9fef10362adc35e72dfb3f38d6e540ef2bde785e",
                  "parents": [
                      "2012c9f3b92d8153fd36f7388802a5e59527bf57"
                  ],
                  "tags": []
              }
          ],
          "date": 1229788200,
          "user": "luser"
      },
      "3": {
          "changesets": [
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 4",
                  "files": [
                      "testfile"
                  ],
                  "node": "564169828a86df44c499a737a3e40489598a9387",
                  "parents": [
                      "ea44848ca8aa9fa60c10936fdf8300f8868e9340"
                  ],
                  "tags": []
              },
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 5",
                  "files": [
                      "testfile"
                  ],
                  "node": "0137424351053e5108ce5b8cf14d69a5bd44b568",
                  "parents": [
                      "564169828a86df44c499a737a3e40489598a9387"
                  ],
                  "tags": []
              }
          ],
          "date": 1227455400,
          "user": "someone"
      },
      "30": {
          "changesets": [
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 58",
                  "files": [
                      "testfile"
                  ],
                  "node": "354174f3ddf9b07f9dd0670b698c97b59dfa78ea",
                  "parents": [
                      "9fef10362adc35e72dfb3f38d6e540ef2bde785e"
                  ],
                  "tags": []
              },
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 59",
                  "files": [
                      "testfile"
                  ],
                  "node": "f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc",
                  "parents": [
                      "354174f3ddf9b07f9dd0670b698c97b59dfa78ea"
                  ],
                  "tags": []
              }
          ],
          "date": 1229874600,
          "user": "someone"
      },
      "31": {
          "changesets": [
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 60",
                  "files": [
                      "testfile"
                  ],
                  "node": "7127e784b4ba3a5cf792b433b19d527e2bd0b44a",
                  "parents": [
                      "f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc"
                  ],
                  "tags": []
              },
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 61",
                  "files": [
                      "testfile"
                  ],
                  "node": "054cf6e47bbe2fb7a3e4061ded6763bed4fd4550",
                  "parents": [
                      "7127e784b4ba3a5cf792b433b19d527e2bd0b44a"
                  ],
                  "tags": [
                      "tip"
                  ]
              }
          ],
          "date": 1229961000,
          "user": "johndoe"
      },
      "4": {
          "changesets": [
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 6",
                  "files": [
                      "testfile"
                  ],
                  "node": "52d3fce08d691a87d01c8f4397a8b34d98427271",
                  "parents": [
                      "0137424351053e5108ce5b8cf14d69a5bd44b568"
                  ],
                  "tags": []
              },
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 7",
                  "files": [
                      "testfile"
                  ],
                  "node": "12799c959e3ad5465a98d333408ae8a5296d90a6",
                  "parents": [
                      "52d3fce08d691a87d01c8f4397a8b34d98427271"
                  ],
                  "tags": []
              }
          ],
          "date": 1227541800,
          "user": "johndoe"
      },
      "5": {
          "changesets": [
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 8",
                  "files": [
                      "testfile"
                  ],
                  "node": "f1af4004fca66aaf0938f50daffa9d24bbbe3f07",
                  "parents": [
                      "12799c959e3ad5465a98d333408ae8a5296d90a6"
                  ],
                  "tags": []
              },
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 9",
                  "files": [
                      "testfile"
                  ],
                  "node": "0341cfc3072ffd468facf73e47f8624079616bfc",
                  "parents": [
                      "f1af4004fca66aaf0938f50daffa9d24bbbe3f07"
                  ],
                  "tags": []
              }
          ],
          "date": 1227714600,
          "user": "luser"
      },
      "6": {
          "changesets": [
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 10",
                  "files": [
                      "testfile"
                  ],
                  "node": "07386661f41722a95cdf640ee610ae759bb36168",
                  "parents": [
                      "0341cfc3072ffd468facf73e47f8624079616bfc"
                  ],
                  "tags": []
              },
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 11",
                  "files": [
                      "testfile"
                  ],
                  "node": "96ec854d523c3e43bf5e015f68fccfcb632525a6",
                  "parents": [
                      "07386661f41722a95cdf640ee610ae759bb36168"
                  ],
                  "tags": []
              }
          ],
          "date": 1227801000,
          "user": "someone"
      },
      "7": {
          "changesets": [
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 12",
                  "files": [
                      "testfile"
                  ],
                  "node": "745197626166e61f2a5cc9834ecc1b55cd987f5f",
                  "parents": [
                      "96ec854d523c3e43bf5e015f68fccfcb632525a6"
                  ],
                  "tags": []
              },
              {
                  "author": "johndoe@cuatro",
                  "branch": "default",
                  "desc": "checkin 13",
                  "files": [
                      "testfile"
                  ],
                  "node": "716b98766200cea4f925caa2952bd16252358376",
                  "parents": [
                      "745197626166e61f2a5cc9834ecc1b55cd987f5f"
                  ],
                  "tags": []
              }
          ],
          "date": 1227887400,
          "user": "johndoe"
      },
      "8": {
          "changesets": [
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 14",
                  "files": [
                      "testfile"
                  ],
                  "node": "7f9d2db01c2345f7d19964c01f997ab0e49de9d3",
                  "parents": [
                      "716b98766200cea4f925caa2952bd16252358376"
                  ],
                  "tags": []
              },
              {
                  "author": "luser",
                  "branch": "default",
                  "desc": "checkin 15",
                  "files": [
                      "testfile"
                  ],
                  "node": "d4b458f1c3351dd7500839e028f5bb1e2b2ff109",
                  "parents": [
                      "7f9d2db01c2345f7d19964c01f997ab0e49de9d3"
                  ],
                  "tags": []
              }
          ],
          "date": 1227973800,
          "user": "luser"
      },
      "9": {
          "changesets": [
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 16",
                  "files": [
                      "testfile"
                  ],
                  "node": "16d0fba6c77efcb0499a87fe91fd179b84888c5e",
                  "parents": [
                      "d4b458f1c3351dd7500839e028f5bb1e2b2ff109"
                  ],
                  "tags": []
              },
              {
                  "author": "someone@cuatro",
                  "branch": "default",
                  "desc": "checkin 17",
                  "files": [
                      "testfile"
                  ],
                  "node": "5fda1cecd054f1939b9d091768b335823ee04fc2",
                  "parents": [
                      "16d0fba6c77efcb0499a87fe91fd179b84888c5e"
                  ],
                  "tags": []
              }
          ],
          "date": 1228060200,
          "user": "someone"
      }
  }


Query with fromchange and an endID

  $ http "http://localhost:$HGPORT/json-pushes?fromchange=1980d3e0c05f&endID=15" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "13": {
          "changesets": [
              "53e334794d36467b2083d3b94fb1dc3f061d1cd9",
              "93f74182971010ac8a9a5726fb976f1d2e593ea5"
          ],
          "date": 1228405800,
          "user": "johndoe"
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
      }
  }

Query with a startID and tochange

  $ http "http://localhost:$HGPORT/json-pushes?startID=9&tochange=6a9848d7dc42" --header content-type --body-file body
  200
  content-type: application/json


  $ python -m json.tool body
  {
      "10": {
          "changesets": [
              "6a9848d7dc42eb0fd7dab35b06b366db93698e24",
              "4d0d5182c524fa92348319583ae7bf28c2b1b296"
          ],
          "date": 1228146600,
          "user": "johndoe"
      }
  }


Query for two changesets at once

  $ http "http://localhost:$HGPORT/json-pushes?changeset=6fa979d08156&changeset=069b8cf8dcac" --header content-type --body-file body
  200
  content-type: application/json


  $ python -m json.tool body
  {
      "16": {
          "changesets": [
              "6fa979d08156ccfe22632af72d8408468e1e8ace",
              "7dc0e50f2e77447cd0f9de9c0fc51eadb2320ba7"
          ],
          "date": 1228751400,
          "user": "johndoe"
      },
      "19": {
          "changesets": [
              "868ec41cad32bb84115253e226c88605b8f9f354",
              "069b8cf8dcac61e0771c795e8ffe8fcab2608233"
          ],
          "date": 1229010600,
          "user": "johndoe"
      }
  }

Query a changeset that doesn't exist

  $ http "http://localhost:$HGPORT/json-pushes?changeset=foobar" --header content-type --body-file body
  404
  content-type: application/json

  $ cat body
  "unknown revision 'foobar'" (no-eol)

Test paging

  $ http "http://localhost:$HGPORT/json-pushes/1?version=2" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "lastpushid": 31,
      "pushes": {
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
  }

  $ http "http://localhost:$HGPORT/json-pushes/2?version=2" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "lastpushid": 31,
      "pushes": {
          "12": {
              "changesets": [
                  "1980d3e0c05f3f3785168ea4dbe8da33a9de42ca",
                  "8a354cb74bae0bcc04550e5335612bbf922ef364"
              ],
              "date": 1228319400,
              "user": "someone"
          },
          "13": {
              "changesets": [
                  "53e334794d36467b2083d3b94fb1dc3f061d1cd9",
                  "93f74182971010ac8a9a5726fb976f1d2e593ea5"
              ],
              "date": 1228405800,
              "user": "johndoe"
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
          "16": {
              "changesets": [
                  "6fa979d08156ccfe22632af72d8408468e1e8ace",
                  "7dc0e50f2e77447cd0f9de9c0fc51eadb2320ba7"
              ],
              "date": 1228751400,
              "user": "johndoe"
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
          "19": {
              "changesets": [
                  "868ec41cad32bb84115253e226c88605b8f9f354",
                  "069b8cf8dcac61e0771c795e8ffe8fcab2608233"
              ],
              "date": 1229010600,
              "user": "johndoe"
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
          }
      }
  }

Format version 1 works

  $ http "http://localhost:$HGPORT/json-pushes?changeset=069b8cf8dcac&version=1" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool < body
  {
      "19": {
          "changesets": [
              "868ec41cad32bb84115253e226c88605b8f9f354",
              "069b8cf8dcac61e0771c795e8ffe8fcab2608233"
          ],
          "date": 1229010600,
          "user": "johndoe"
      }
  }

Format version 3 fails

  $ http "http://localhost:$HGPORT/json-pushes?changeset=f3afcf0b3c24&version=3" --header content-type --body-file body
  500
  content-type: application/json

  $ cat body
  "version parameter must be 1 or 2" (no-eol)

Format version 2 has pushes in a child object and a last push id

  $ http "http://localhost:$HGPORT/json-pushes?changeset=069b8cf8dcac&version=2" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool  body
  {
      "lastpushid": 31,
      "pushes": {
          "19": {
              "changesets": [
                  "868ec41cad32bb84115253e226c88605b8f9f354",
                  "069b8cf8dcac61e0771c795e8ffe8fcab2608233"
              ],
              "date": 1229010600,
              "user": "johndoe"
          }
      }
  }


Query with a startID and an enddate

  $ http "http://localhost:$HGPORT/json-pushes?startID=1&enddate=$MIDTIME" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "2": {
          "changesets": [
              "90a0919e134179630db1a9cfea3476793e68230c",
              "ea44848ca8aa9fa60c10936fdf8300f8868e9340"
          ],
          "date": 1227369000,
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
      "4": {
          "changesets": [
              "52d3fce08d691a87d01c8f4397a8b34d98427271",
              "12799c959e3ad5465a98d333408ae8a5296d90a6"
          ],
          "date": 1227541800,
          "user": "johndoe"
      }
  }

Query with a startdate and an endID

  $ http "http://localhost:$HGPORT/json-pushes?startdate=$STARTTIME&endID=3" --header content-type --body-file body
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
      },
      "3": {
          "changesets": [
              "564169828a86df44c499a737a3e40489598a9387",
              "0137424351053e5108ce5b8cf14d69a5bd44b568"
          ],
          "date": 1227455400,
          "user": "someone"
      }
  }

Query with fromchange and an enddate


  $ http "http://localhost:$HGPORT/json-pushes?fromchange=8c687ea0e27c&enddate=$MIDTIME" --header content-type --body-file body
  200
  content-type: application/json

  $ python -m json.tool body
  {
      "2": {
          "changesets": [
              "90a0919e134179630db1a9cfea3476793e68230c",
              "ea44848ca8aa9fa60c10936fdf8300f8868e9340"
          ],
          "date": 1227369000,
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
      "4": {
          "changesets": [
              "52d3fce08d691a87d01c8f4397a8b34d98427271",
              "12799c959e3ad5465a98d333408ae8a5296d90a6"
          ],
          "date": 1227541800,
          "user": "johndoe"
      }
  }

Query with a startdate and tochange


  $ http "http://localhost:$HGPORT/json-pushes?startdate=$STARTTIME&tochange=ea44848ca8aa" --header content-type --body-file body
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

Test that we can parse partial dates, missing seconds

  >>> import os
  >>> os.environ['MIDTIME'] = os.environ['MIDTIME'][:-3]

  $ http "http://localhost:$HGPORT/json-pushes?startdate=$STARTTIME&enddate=$MIDTIME" --header content-type --body-file body
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
      },
      "3": {
          "changesets": [
              "564169828a86df44c499a737a3e40489598a9387",
              "0137424351053e5108ce5b8cf14d69a5bd44b568"
          ],
          "date": 1227455400,
          "user": "someone"
      },
      "4": {
          "changesets": [
              "52d3fce08d691a87d01c8f4397a8b34d98427271",
              "12799c959e3ad5465a98d333408ae8a5296d90a6"
          ],
          "date": 1227541800,
          "user": "johndoe"
      }
  }

Test that we can parse partial dates, missing seconds and minutes

  >>> import os
  >>> os.environ['MIDTIME'] = os.environ['MIDTIME'][:-3]

  $ http "http://localhost:$HGPORT/json-pushes?startdate=$STARTTIME&enddate=$MIDTIME" --header content-type --body-file body
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
      },
      "3": {
          "changesets": [
              "564169828a86df44c499a737a3e40489598a9387",
              "0137424351053e5108ce5b8cf14d69a5bd44b568"
          ],
          "date": 1227455400,
          "user": "someone"
      },
      "4": {
          "changesets": [
              "52d3fce08d691a87d01c8f4397a8b34d98427271",
              "12799c959e3ad5465a98d333408ae8a5296d90a6"
          ],
          "date": 1227541800,
          "user": "johndoe"
      }
  }


Test that we can parse partial dates, missing seconds, minutes and hours

  >>> import os
  >>> os.environ['MIDTIME'] = os.environ['MIDTIME'][:-3]

  $ http "http://localhost:$HGPORT/json-pushes?startdate=$STARTTIME&enddate=$MIDTIME" --header content-type --body-file body
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
      },
      "3": {
          "changesets": [
              "564169828a86df44c499a737a3e40489598a9387",
              "0137424351053e5108ce5b8cf14d69a5bd44b568"
          ],
          "date": 1227455400,
          "user": "someone"
      },
      "4": {
          "changesets": [
              "52d3fce08d691a87d01c8f4397a8b34d98427271",
              "12799c959e3ad5465a98d333408ae8a5296d90a6"
          ],
          "date": 1227541800,
          "user": "johndoe"
      }
  }


Confirm no errors in log
  $ cat ../hg-test/error.log
