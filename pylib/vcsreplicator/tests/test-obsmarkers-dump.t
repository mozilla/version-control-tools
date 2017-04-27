#require vcsreplicator

  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > vcsreplicator = $TESTDIR/pylib/vcsreplicator/vcsreplicator/hgext.py
  > [replicationproducer]
  > hosts = dummy
  > clientid = 1
  > topic = foo
  > partitionmap.0 = 0:.*
  > reqacks = 1
  > acktimeout = 5000
  > EOF

  $ hg debugbase85obsmarkers '0096106hRrrvtb3n{p3QPjH%`e(f=Wx*E-WXguWQVT*bSa5J>he{3kS!1uyrVRU6WF*G+ZIXF2nG&U|aFgP$dG9WMjb#rBMI#gwIbRbo8WpW@qb8l^BZ*FBkWq4t2aBO8RV{dIf'
  [
      {
          "date": [
              1471989146.608092,
              0
          ],
          "flags": 0,
          "metadata": [
              [
                  "user",
                  "Test User <someone@example.com>"
              ]
          ],
          "parents": null,
          "precursor": "4da703b7f59b720f524f709aa07eed3182ba1acd",
          "successors": [
              "7d683ce4e5618b7a0a7033b4d27f6c28b2c0f7c2"
          ]
      }
  ] (no-eol)

Dumping a marker without successors works

  $ hg debugbase85obsmarkers '00000051S%v{hB2A5EP{3fxZ~)30NZk7N{NVRU6WF*G+aFgG<aGchhWG%`0fHy|(ob#rBMI&yDsbU<P=H8)~oHe)$sIWY'
  [
      {
          "date": [
              1472075231.842767,
              0
          ],
          "flags": 0,
          "metadata": [
              [
                  "user",
                  "root@b357bc6c9c91"
              ]
          ],
          "parents": null,
          "precursor": "67b45555a21f4d9d470adc4f1ed3af63918f6414",
          "successors": []
      }
  ] (no-eol)

Multiple markers are represented properly

  $ hg debugbase85obsmarkers '0096106hR>)mG|TpRWkW#2943{I5M%`G&|ROwrkft0ao94f~pqFMDi)J+8!LVRU6WF*G+aFgG_iI5sXfH8(IhHy|(ob#rBMI#gwIbRbo8WpW@qb8l^BZ*FBkWq4t2aBO8RV{dIf0RR91JphN&(gi8!9g?_5@w(Yej=KOLGB79Y+juY^Xln?R+S;Ptw%@x50V8B#bY(g*G&eFZH#ayqHZC_cH#IakATR)Rb7gWmRAqB?AXRf^av(f&Z*667Ze>7acwudDY-KKEZ*4v'
  [
      {
          "date": [
              1472077886.757097,
              0
          ],
          "flags": 0,
          "metadata": [
              [
                  "user",
                  "Test User <someone@example.com>"
              ]
          ],
          "parents": null,
          "precursor": "63d556ea5b9faf08c8c41864c1fcaf3d57f986c8",
          "successors": [
              "274cd1d986ab248aae0dfb9a902f7b6c823daec4"
          ]
      },
      {
          "date": [
              1472077886.757548,
              0
          ],
          "flags": 0,
          "metadata": [
              [
                  "user",
                  "Test User <someone@example.com>"
              ]
          ],
          "parents": null,
          "precursor": "87d2d20529e71d92b847f1bad94c8ebb00203230",
          "successors": [
              "27eddb78301f686b0894dadaa2deb6dfbb080123"
          ]
      }
  ] (no-eol)
