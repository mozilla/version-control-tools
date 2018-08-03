  $ . $TESTDIR/hgext/pushlog/tests/helpers.sh
  $ maketestrepousers > /dev/null

Get only the latest 10 pushes via pushlog

  $ http "http://localhost:$HGPORT/hg-test/pushlog" --header content-type --body-file body
  200
  content-type: application/atom+xml

  $ cat body
  <?xml version="1.0" encoding="ascii"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
   <id>http://localhost:$HGPORT/hg-test/pushlog</id>
   <link rel="self" href="http://localhost:$HGPORT/hg-test/pushlog"/>
   <link rel="alternate" href="http://localhost:$HGPORT/hg-test/pushloghtml"/>
   <title>hg-test Pushlog</title>
   <updated>*</updated> (glob)
   <entry>
    <title>Changeset 054cf6e47bbe2fb7a3e4061ded6763bed4fd4550</title>
    <id>http://www.selenic.com/mercurial/#changeset-054cf6e47bbe2fb7a3e4061ded6763bed4fd4550</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/054cf6e47bbe2fb7a3e4061ded6763bed4fd4550"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 7127e784b4ba3a5cf792b433b19d527e2bd0b44a</title>
    <id>http://www.selenic.com/mercurial/#changeset-7127e784b4ba3a5cf792b433b19d527e2bd0b44a</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/7127e784b4ba3a5cf792b433b19d527e2bd0b44a"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc</title>
    <id>http://www.selenic.com/mercurial/#changeset-f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 354174f3ddf9b07f9dd0670b698c97b59dfa78ea</title>
    <id>http://www.selenic.com/mercurial/#changeset-354174f3ddf9b07f9dd0670b698c97b59dfa78ea</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/354174f3ddf9b07f9dd0670b698c97b59dfa78ea"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 9fef10362adc35e72dfb3f38d6e540ef2bde785e</title>
    <id>http://www.selenic.com/mercurial/#changeset-9fef10362adc35e72dfb3f38d6e540ef2bde785e</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/9fef10362adc35e72dfb3f38d6e540ef2bde785e"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 2012c9f3b92d8153fd36f7388802a5e59527bf57</title>
    <id>http://www.selenic.com/mercurial/#changeset-2012c9f3b92d8153fd36f7388802a5e59527bf57</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/2012c9f3b92d8153fd36f7388802a5e59527bf57"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset bf9bdfe181e896c08c4f7332be751004b96e26f8</title>
    <id>http://www.selenic.com/mercurial/#changeset-bf9bdfe181e896c08c4f7332be751004b96e26f8</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/bf9bdfe181e896c08c4f7332be751004b96e26f8"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset e494a4d71f1905d661f88dd8865283dcb6b42be3</title>
    <id>http://www.selenic.com/mercurial/#changeset-e494a4d71f1905d661f88dd8865283dcb6b42be3</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/e494a4d71f1905d661f88dd8865283dcb6b42be3"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset badb82dde54097638883b824baa0009f4258d9f5</title>
    <id>http://www.selenic.com/mercurial/#changeset-badb82dde54097638883b824baa0009f4258d9f5</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/badb82dde54097638883b824baa0009f4258d9f5"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 2be12c9ad0c8a4dd783a639cb7512d64a96e7b93</title>
    <id>http://www.selenic.com/mercurial/#changeset-2be12c9ad0c8a4dd783a639cb7512d64a96e7b93</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/2be12c9ad0c8a4dd783a639cb7512d64a96e7b93"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset f2b859fb39c4378a084edf14efd76ea5bd5dc70f</title>
    <id>http://www.selenic.com/mercurial/#changeset-f2b859fb39c4378a084edf14efd76ea5bd5dc70f</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/f2b859fb39c4378a084edf14efd76ea5bd5dc70f"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 2274c682144a166997ed94a3a092a7df04ecebbb</title>
    <id>http://www.selenic.com/mercurial/#changeset-2274c682144a166997ed94a3a092a7df04ecebbb</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/2274c682144a166997ed94a3a092a7df04ecebbb"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset e706af4df5a146039c05ecaffade019b325b9abe</title>
    <id>http://www.selenic.com/mercurial/#changeset-e706af4df5a146039c05ecaffade019b325b9abe</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/e706af4df5a146039c05ecaffade019b325b9abe"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 57eaea907fcce462398e1fed38eb9b75fd2f4724</title>
    <id>http://www.selenic.com/mercurial/#changeset-57eaea907fcce462398e1fed38eb9b75fd2f4724</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/57eaea907fcce462398e1fed38eb9b75fd2f4724"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f</title>
    <id>http://www.selenic.com/mercurial/#changeset-e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 4b533377ba86200b561e423625ce0a7f17d1f9e3</title>
    <id>http://www.selenic.com/mercurial/#changeset-4b533377ba86200b561e423625ce0a7f17d1f9e3</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/4b533377ba86200b561e423625ce0a7f17d1f9e3"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 306b6389a9ad743bc619d5e62ea6a75bb842d09e</title>
    <id>http://www.selenic.com/mercurial/#changeset-306b6389a9ad743bc619d5e62ea6a75bb842d09e</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/306b6389a9ad743bc619d5e62ea6a75bb842d09e"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 773195adc944c860ad0fbb278921a6e2d27f4405</title>
    <id>http://www.selenic.com/mercurial/#changeset-773195adc944c860ad0fbb278921a6e2d27f4405</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/773195adc944c860ad0fbb278921a6e2d27f4405"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset f4835d42999840c490559b5f933036ee8f2ed6af</title>
    <id>http://www.selenic.com/mercurial/#changeset-f4835d42999840c490559b5f933036ee8f2ed6af</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/f4835d42999840c490559b5f933036ee8f2ed6af"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 59b7f60b3a3464abb7fd3ea2bf1798960136a7fe</title>
    <id>http://www.selenic.com/mercurial/#changeset-59b7f60b3a3464abb7fd3ea2bf1798960136a7fe</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/59b7f60b3a3464abb7fd3ea2bf1798960136a7fe"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
  
  </feed>


Get the second page of 10 pushes via pushlog/2
  $ http "http://localhost:$HGPORT/hg-test/pushlog/2" --header content-type --body-file body
  200
  content-type: application/atom+xml

  $ cat body
  <?xml version="1.0" encoding="ascii"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
   <id>http://localhost:$HGPORT/hg-test/pushlog</id>
   <link rel="self" href="http://localhost:$HGPORT/hg-test/pushlog"/>
   <link rel="alternate" href="http://localhost:$HGPORT/hg-test/pushloghtml"/>
   <title>hg-test Pushlog</title>
   <updated>*</updated> (glob)
   <entry>
    <title>Changeset 5af266358ee895496337d0c6f9646954c607d189</title>
    <id>http://www.selenic.com/mercurial/#changeset-5af266358ee895496337d0c6f9646954c607d189</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/5af266358ee895496337d0c6f9646954c607d189"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset e752ca2d37f753b617382d8def58c090e2cb8ca6</title>
    <id>http://www.selenic.com/mercurial/#changeset-e752ca2d37f753b617382d8def58c090e2cb8ca6</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/e752ca2d37f753b617382d8def58c090e2cb8ca6"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset ac4a8b83057888133e9dab79d0d327a70e6a7f2a</title>
    <id>http://www.selenic.com/mercurial/#changeset-ac4a8b83057888133e9dab79d0d327a70e6a7f2a</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/ac4a8b83057888133e9dab79d0d327a70e6a7f2a"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 7b26724b897ca32275c3c83f770ef3761ed1be84</title>
    <id>http://www.selenic.com/mercurial/#changeset-7b26724b897ca32275c3c83f770ef3761ed1be84</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/7b26724b897ca32275c3c83f770ef3761ed1be84"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 069b8cf8dcac61e0771c795e8ffe8fcab2608233</title>
    <id>http://www.selenic.com/mercurial/#changeset-069b8cf8dcac61e0771c795e8ffe8fcab2608233</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/069b8cf8dcac61e0771c795e8ffe8fcab2608233"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 868ec41cad32bb84115253e226c88605b8f9f354</title>
    <id>http://www.selenic.com/mercurial/#changeset-868ec41cad32bb84115253e226c88605b8f9f354</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/868ec41cad32bb84115253e226c88605b8f9f354"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset e77d8a7d36c5707317dbad494a9947261a34d618</title>
    <id>http://www.selenic.com/mercurial/#changeset-e77d8a7d36c5707317dbad494a9947261a34d618</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/e77d8a7d36c5707317dbad494a9947261a34d618"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 23dd64640c05568ff7aee57d3a4e7641795d667a</title>
    <id>http://www.selenic.com/mercurial/#changeset-23dd64640c05568ff7aee57d3a4e7641795d667a</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/23dd64640c05568ff7aee57d3a4e7641795d667a"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile8</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset db44477aa15b0ac3ac403c0419140416697c3b92</title>
    <id>http://www.selenic.com/mercurial/#changeset-db44477aa15b0ac3ac403c0419140416697c3b92</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/db44477aa15b0ac3ac403c0419140416697c3b92"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 9c9217ca80ce3cf8c140c1af4e254d817e9945f7</title>
    <id>http://www.selenic.com/mercurial/#changeset-9c9217ca80ce3cf8c140c1af4e254d817e9945f7</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/9c9217ca80ce3cf8c140c1af4e254d817e9945f7"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 7dc0e50f2e77447cd0f9de9c0fc51eadb2320ba7</title>
    <id>http://www.selenic.com/mercurial/#changeset-7dc0e50f2e77447cd0f9de9c0fc51eadb2320ba7</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/7dc0e50f2e77447cd0f9de9c0fc51eadb2320ba7"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 6fa979d08156ccfe22632af72d8408468e1e8ace</title>
    <id>http://www.selenic.com/mercurial/#changeset-6fa979d08156ccfe22632af72d8408468e1e8ace</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/6fa979d08156ccfe22632af72d8408468e1e8ace"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 0e59804eb117f10112f6d0a8212002d7eab80de9</title>
    <id>http://www.selenic.com/mercurial/#changeset-0e59804eb117f10112f6d0a8212002d7eab80de9</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/0e59804eb117f10112f6d0a8212002d7eab80de9"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 26bb8677e78db04f4bca2ea2f79985707fbb0b2a</title>
    <id>http://www.selenic.com/mercurial/#changeset-26bb8677e78db04f4bca2ea2f79985707fbb0b2a</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/26bb8677e78db04f4bca2ea2f79985707fbb0b2a"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 4df5711a25e9daceb4d35fd566d3f22e8e024345</title>
    <id>http://www.selenic.com/mercurial/#changeset-4df5711a25e9daceb4d35fd566d3f22e8e024345</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/4df5711a25e9daceb4d35fd566d3f22e8e024345"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 3580f0821c4d0bb6d013d2973f8629541704ecd2</title>
    <id>http://www.selenic.com/mercurial/#changeset-3580f0821c4d0bb6d013d2973f8629541704ecd2</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/3580f0821c4d0bb6d013d2973f8629541704ecd2"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 93f74182971010ac8a9a5726fb976f1d2e593ea5</title>
    <id>http://www.selenic.com/mercurial/#changeset-93f74182971010ac8a9a5726fb976f1d2e593ea5</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/93f74182971010ac8a9a5726fb976f1d2e593ea5"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 53e334794d36467b2083d3b94fb1dc3f061d1cd9</title>
    <id>http://www.selenic.com/mercurial/#changeset-53e334794d36467b2083d3b94fb1dc3f061d1cd9</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/53e334794d36467b2083d3b94fb1dc3f061d1cd9"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 8a354cb74bae0bcc04550e5335612bbf922ef364</title>
    <id>http://www.selenic.com/mercurial/#changeset-8a354cb74bae0bcc04550e5335612bbf922ef364</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/8a354cb74bae0bcc04550e5335612bbf922ef364"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 1980d3e0c05f3f3785168ea4dbe8da33a9de42ca</title>
    <id>http://www.selenic.com/mercurial/#changeset-1980d3e0c05f3f3785168ea4dbe8da33a9de42ca</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/1980d3e0c05f3f3785168ea4dbe8da33a9de42ca"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
  
  </feed>


Get all ATOM data via pushlog
  $ http "http://localhost:$HGPORT/hg-test/pushlog?startdate=$STARTTIME&enddate=$ENDTIME" --header content-type --body-file body
  200
  content-type: application/atom+xml

  $ cat body
  <?xml version="1.0" encoding="ascii"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
   <id>http://localhost:$HGPORT/hg-test/pushlog</id>
   <link rel="self" href="http://localhost:$HGPORT/hg-test/pushlog"/>
   <link rel="alternate" href="http://localhost:$HGPORT/hg-test/pushloghtml"/>
   <title>hg-test Pushlog</title>
   <updated>*</updated> (glob)
   <entry>
    <title>Changeset 054cf6e47bbe2fb7a3e4061ded6763bed4fd4550</title>
    <id>http://www.selenic.com/mercurial/#changeset-054cf6e47bbe2fb7a3e4061ded6763bed4fd4550</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/054cf6e47bbe2fb7a3e4061ded6763bed4fd4550"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 7127e784b4ba3a5cf792b433b19d527e2bd0b44a</title>
    <id>http://www.selenic.com/mercurial/#changeset-7127e784b4ba3a5cf792b433b19d527e2bd0b44a</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/7127e784b4ba3a5cf792b433b19d527e2bd0b44a"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc</title>
    <id>http://www.selenic.com/mercurial/#changeset-f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 354174f3ddf9b07f9dd0670b698c97b59dfa78ea</title>
    <id>http://www.selenic.com/mercurial/#changeset-354174f3ddf9b07f9dd0670b698c97b59dfa78ea</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/354174f3ddf9b07f9dd0670b698c97b59dfa78ea"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 9fef10362adc35e72dfb3f38d6e540ef2bde785e</title>
    <id>http://www.selenic.com/mercurial/#changeset-9fef10362adc35e72dfb3f38d6e540ef2bde785e</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/9fef10362adc35e72dfb3f38d6e540ef2bde785e"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 2012c9f3b92d8153fd36f7388802a5e59527bf57</title>
    <id>http://www.selenic.com/mercurial/#changeset-2012c9f3b92d8153fd36f7388802a5e59527bf57</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/2012c9f3b92d8153fd36f7388802a5e59527bf57"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset bf9bdfe181e896c08c4f7332be751004b96e26f8</title>
    <id>http://www.selenic.com/mercurial/#changeset-bf9bdfe181e896c08c4f7332be751004b96e26f8</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/bf9bdfe181e896c08c4f7332be751004b96e26f8"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset e494a4d71f1905d661f88dd8865283dcb6b42be3</title>
    <id>http://www.selenic.com/mercurial/#changeset-e494a4d71f1905d661f88dd8865283dcb6b42be3</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/e494a4d71f1905d661f88dd8865283dcb6b42be3"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset badb82dde54097638883b824baa0009f4258d9f5</title>
    <id>http://www.selenic.com/mercurial/#changeset-badb82dde54097638883b824baa0009f4258d9f5</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/badb82dde54097638883b824baa0009f4258d9f5"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 2be12c9ad0c8a4dd783a639cb7512d64a96e7b93</title>
    <id>http://www.selenic.com/mercurial/#changeset-2be12c9ad0c8a4dd783a639cb7512d64a96e7b93</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/2be12c9ad0c8a4dd783a639cb7512d64a96e7b93"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset f2b859fb39c4378a084edf14efd76ea5bd5dc70f</title>
    <id>http://www.selenic.com/mercurial/#changeset-f2b859fb39c4378a084edf14efd76ea5bd5dc70f</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/f2b859fb39c4378a084edf14efd76ea5bd5dc70f"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 2274c682144a166997ed94a3a092a7df04ecebbb</title>
    <id>http://www.selenic.com/mercurial/#changeset-2274c682144a166997ed94a3a092a7df04ecebbb</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/2274c682144a166997ed94a3a092a7df04ecebbb"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset e706af4df5a146039c05ecaffade019b325b9abe</title>
    <id>http://www.selenic.com/mercurial/#changeset-e706af4df5a146039c05ecaffade019b325b9abe</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/e706af4df5a146039c05ecaffade019b325b9abe"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 57eaea907fcce462398e1fed38eb9b75fd2f4724</title>
    <id>http://www.selenic.com/mercurial/#changeset-57eaea907fcce462398e1fed38eb9b75fd2f4724</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/57eaea907fcce462398e1fed38eb9b75fd2f4724"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f</title>
    <id>http://www.selenic.com/mercurial/#changeset-e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 4b533377ba86200b561e423625ce0a7f17d1f9e3</title>
    <id>http://www.selenic.com/mercurial/#changeset-4b533377ba86200b561e423625ce0a7f17d1f9e3</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/4b533377ba86200b561e423625ce0a7f17d1f9e3"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 306b6389a9ad743bc619d5e62ea6a75bb842d09e</title>
    <id>http://www.selenic.com/mercurial/#changeset-306b6389a9ad743bc619d5e62ea6a75bb842d09e</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/306b6389a9ad743bc619d5e62ea6a75bb842d09e"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 773195adc944c860ad0fbb278921a6e2d27f4405</title>
    <id>http://www.selenic.com/mercurial/#changeset-773195adc944c860ad0fbb278921a6e2d27f4405</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/773195adc944c860ad0fbb278921a6e2d27f4405"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset f4835d42999840c490559b5f933036ee8f2ed6af</title>
    <id>http://www.selenic.com/mercurial/#changeset-f4835d42999840c490559b5f933036ee8f2ed6af</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/f4835d42999840c490559b5f933036ee8f2ed6af"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 59b7f60b3a3464abb7fd3ea2bf1798960136a7fe</title>
    <id>http://www.selenic.com/mercurial/#changeset-59b7f60b3a3464abb7fd3ea2bf1798960136a7fe</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/59b7f60b3a3464abb7fd3ea2bf1798960136a7fe"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 5af266358ee895496337d0c6f9646954c607d189</title>
    <id>http://www.selenic.com/mercurial/#changeset-5af266358ee895496337d0c6f9646954c607d189</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/5af266358ee895496337d0c6f9646954c607d189"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset e752ca2d37f753b617382d8def58c090e2cb8ca6</title>
    <id>http://www.selenic.com/mercurial/#changeset-e752ca2d37f753b617382d8def58c090e2cb8ca6</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/e752ca2d37f753b617382d8def58c090e2cb8ca6"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset ac4a8b83057888133e9dab79d0d327a70e6a7f2a</title>
    <id>http://www.selenic.com/mercurial/#changeset-ac4a8b83057888133e9dab79d0d327a70e6a7f2a</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/ac4a8b83057888133e9dab79d0d327a70e6a7f2a"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 7b26724b897ca32275c3c83f770ef3761ed1be84</title>
    <id>http://www.selenic.com/mercurial/#changeset-7b26724b897ca32275c3c83f770ef3761ed1be84</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/7b26724b897ca32275c3c83f770ef3761ed1be84"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 069b8cf8dcac61e0771c795e8ffe8fcab2608233</title>
    <id>http://www.selenic.com/mercurial/#changeset-069b8cf8dcac61e0771c795e8ffe8fcab2608233</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/069b8cf8dcac61e0771c795e8ffe8fcab2608233"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 868ec41cad32bb84115253e226c88605b8f9f354</title>
    <id>http://www.selenic.com/mercurial/#changeset-868ec41cad32bb84115253e226c88605b8f9f354</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/868ec41cad32bb84115253e226c88605b8f9f354"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset e77d8a7d36c5707317dbad494a9947261a34d618</title>
    <id>http://www.selenic.com/mercurial/#changeset-e77d8a7d36c5707317dbad494a9947261a34d618</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/e77d8a7d36c5707317dbad494a9947261a34d618"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 23dd64640c05568ff7aee57d3a4e7641795d667a</title>
    <id>http://www.selenic.com/mercurial/#changeset-23dd64640c05568ff7aee57d3a4e7641795d667a</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/23dd64640c05568ff7aee57d3a4e7641795d667a"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile8</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset db44477aa15b0ac3ac403c0419140416697c3b92</title>
    <id>http://www.selenic.com/mercurial/#changeset-db44477aa15b0ac3ac403c0419140416697c3b92</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/db44477aa15b0ac3ac403c0419140416697c3b92"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 9c9217ca80ce3cf8c140c1af4e254d817e9945f7</title>
    <id>http://www.selenic.com/mercurial/#changeset-9c9217ca80ce3cf8c140c1af4e254d817e9945f7</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/9c9217ca80ce3cf8c140c1af4e254d817e9945f7"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 7dc0e50f2e77447cd0f9de9c0fc51eadb2320ba7</title>
    <id>http://www.selenic.com/mercurial/#changeset-7dc0e50f2e77447cd0f9de9c0fc51eadb2320ba7</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/7dc0e50f2e77447cd0f9de9c0fc51eadb2320ba7"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 6fa979d08156ccfe22632af72d8408468e1e8ace</title>
    <id>http://www.selenic.com/mercurial/#changeset-6fa979d08156ccfe22632af72d8408468e1e8ace</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/6fa979d08156ccfe22632af72d8408468e1e8ace"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 0e59804eb117f10112f6d0a8212002d7eab80de9</title>
    <id>http://www.selenic.com/mercurial/#changeset-0e59804eb117f10112f6d0a8212002d7eab80de9</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/0e59804eb117f10112f6d0a8212002d7eab80de9"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 26bb8677e78db04f4bca2ea2f79985707fbb0b2a</title>
    <id>http://www.selenic.com/mercurial/#changeset-26bb8677e78db04f4bca2ea2f79985707fbb0b2a</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/26bb8677e78db04f4bca2ea2f79985707fbb0b2a"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 4df5711a25e9daceb4d35fd566d3f22e8e024345</title>
    <id>http://www.selenic.com/mercurial/#changeset-4df5711a25e9daceb4d35fd566d3f22e8e024345</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/4df5711a25e9daceb4d35fd566d3f22e8e024345"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 3580f0821c4d0bb6d013d2973f8629541704ecd2</title>
    <id>http://www.selenic.com/mercurial/#changeset-3580f0821c4d0bb6d013d2973f8629541704ecd2</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/3580f0821c4d0bb6d013d2973f8629541704ecd2"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 93f74182971010ac8a9a5726fb976f1d2e593ea5</title>
    <id>http://www.selenic.com/mercurial/#changeset-93f74182971010ac8a9a5726fb976f1d2e593ea5</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/93f74182971010ac8a9a5726fb976f1d2e593ea5"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 53e334794d36467b2083d3b94fb1dc3f061d1cd9</title>
    <id>http://www.selenic.com/mercurial/#changeset-53e334794d36467b2083d3b94fb1dc3f061d1cd9</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/53e334794d36467b2083d3b94fb1dc3f061d1cd9"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 8a354cb74bae0bcc04550e5335612bbf922ef364</title>
    <id>http://www.selenic.com/mercurial/#changeset-8a354cb74bae0bcc04550e5335612bbf922ef364</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/8a354cb74bae0bcc04550e5335612bbf922ef364"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 1980d3e0c05f3f3785168ea4dbe8da33a9de42ca</title>
    <id>http://www.selenic.com/mercurial/#changeset-1980d3e0c05f3f3785168ea4dbe8da33a9de42ca</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/1980d3e0c05f3f3785168ea4dbe8da33a9de42ca"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 2e7c07446def93a7afb63517d9d6f2879b08653c</title>
    <id>http://www.selenic.com/mercurial/#changeset-2e7c07446def93a7afb63517d9d6f2879b08653c</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/2e7c07446def93a7afb63517d9d6f2879b08653c"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 53e89e4e6258eed12b0dc67380015de479ce496e</title>
    <id>http://www.selenic.com/mercurial/#changeset-53e89e4e6258eed12b0dc67380015de479ce496e</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/53e89e4e6258eed12b0dc67380015de479ce496e"/>
    <updated>2008-12-02T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 4d0d5182c524fa92348319583ae7bf28c2b1b296</title>
    <id>http://www.selenic.com/mercurial/#changeset-4d0d5182c524fa92348319583ae7bf28c2b1b296</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/4d0d5182c524fa92348319583ae7bf28c2b1b296"/>
    <updated>2008-12-01T15:50:00Z</updated>
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 6a9848d7dc42eb0fd7dab35b06b366db93698e24</title>
    <id>http://www.selenic.com/mercurial/#changeset-6a9848d7dc42eb0fd7dab35b06b366db93698e24</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/6a9848d7dc42eb0fd7dab35b06b366db93698e24"/>
    <updated>2008-12-01T15:50:00Z</updated>
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 5fda1cecd054f1939b9d091768b335823ee04fc2</title>
    <id>http://www.selenic.com/mercurial/#changeset-5fda1cecd054f1939b9d091768b335823ee04fc2</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/5fda1cecd054f1939b9d091768b335823ee04fc2"/>
    <updated>2008-11-30T15:50:00Z</updated>
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 16d0fba6c77efcb0499a87fe91fd179b84888c5e</title>
    <id>http://www.selenic.com/mercurial/#changeset-16d0fba6c77efcb0499a87fe91fd179b84888c5e</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/16d0fba6c77efcb0499a87fe91fd179b84888c5e"/>
    <updated>2008-11-30T15:50:00Z</updated>
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset d4b458f1c3351dd7500839e028f5bb1e2b2ff109</title>
    <id>http://www.selenic.com/mercurial/#changeset-d4b458f1c3351dd7500839e028f5bb1e2b2ff109</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/d4b458f1c3351dd7500839e028f5bb1e2b2ff109"/>
    <updated>2008-11-29T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 7f9d2db01c2345f7d19964c01f997ab0e49de9d3</title>
    <id>http://www.selenic.com/mercurial/#changeset-7f9d2db01c2345f7d19964c01f997ab0e49de9d3</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/7f9d2db01c2345f7d19964c01f997ab0e49de9d3"/>
    <updated>2008-11-29T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 716b98766200cea4f925caa2952bd16252358376</title>
    <id>http://www.selenic.com/mercurial/#changeset-716b98766200cea4f925caa2952bd16252358376</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/716b98766200cea4f925caa2952bd16252358376"/>
    <updated>2008-11-28T15:50:00Z</updated>
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 745197626166e61f2a5cc9834ecc1b55cd987f5f</title>
    <id>http://www.selenic.com/mercurial/#changeset-745197626166e61f2a5cc9834ecc1b55cd987f5f</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/745197626166e61f2a5cc9834ecc1b55cd987f5f"/>
    <updated>2008-11-28T15:50:00Z</updated>
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 96ec854d523c3e43bf5e015f68fccfcb632525a6</title>
    <id>http://www.selenic.com/mercurial/#changeset-96ec854d523c3e43bf5e015f68fccfcb632525a6</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/96ec854d523c3e43bf5e015f68fccfcb632525a6"/>
    <updated>2008-11-27T15:50:00Z</updated>
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 07386661f41722a95cdf640ee610ae759bb36168</title>
    <id>http://www.selenic.com/mercurial/#changeset-07386661f41722a95cdf640ee610ae759bb36168</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/07386661f41722a95cdf640ee610ae759bb36168"/>
    <updated>2008-11-27T15:50:00Z</updated>
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 0341cfc3072ffd468facf73e47f8624079616bfc</title>
    <id>http://www.selenic.com/mercurial/#changeset-0341cfc3072ffd468facf73e47f8624079616bfc</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/0341cfc3072ffd468facf73e47f8624079616bfc"/>
    <updated>2008-11-26T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset f1af4004fca66aaf0938f50daffa9d24bbbe3f07</title>
    <id>http://www.selenic.com/mercurial/#changeset-f1af4004fca66aaf0938f50daffa9d24bbbe3f07</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/f1af4004fca66aaf0938f50daffa9d24bbbe3f07"/>
    <updated>2008-11-26T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 12799c959e3ad5465a98d333408ae8a5296d90a6</title>
    <id>http://www.selenic.com/mercurial/#changeset-12799c959e3ad5465a98d333408ae8a5296d90a6</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/12799c959e3ad5465a98d333408ae8a5296d90a6"/>
    <updated>2008-11-24T15:50:00Z</updated>
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 52d3fce08d691a87d01c8f4397a8b34d98427271</title>
    <id>http://www.selenic.com/mercurial/#changeset-52d3fce08d691a87d01c8f4397a8b34d98427271</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/52d3fce08d691a87d01c8f4397a8b34d98427271"/>
    <updated>2008-11-24T15:50:00Z</updated>
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 0137424351053e5108ce5b8cf14d69a5bd44b568</title>
    <id>http://www.selenic.com/mercurial/#changeset-0137424351053e5108ce5b8cf14d69a5bd44b568</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/0137424351053e5108ce5b8cf14d69a5bd44b568"/>
    <updated>2008-11-23T15:50:00Z</updated>
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 564169828a86df44c499a737a3e40489598a9387</title>
    <id>http://www.selenic.com/mercurial/#changeset-564169828a86df44c499a737a3e40489598a9387</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/564169828a86df44c499a737a3e40489598a9387"/>
    <updated>2008-11-23T15:50:00Z</updated>
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset ea44848ca8aa9fa60c10936fdf8300f8868e9340</title>
    <id>http://www.selenic.com/mercurial/#changeset-ea44848ca8aa9fa60c10936fdf8300f8868e9340</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/ea44848ca8aa9fa60c10936fdf8300f8868e9340"/>
    <updated>2008-11-22T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 90a0919e134179630db1a9cfea3476793e68230c</title>
    <id>http://www.selenic.com/mercurial/#changeset-90a0919e134179630db1a9cfea3476793e68230c</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/90a0919e134179630db1a9cfea3476793e68230c"/>
    <updated>2008-11-22T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 8c687ea0e27cd77b4fa5025327a41906800cfcd5</title>
    <id>http://www.selenic.com/mercurial/#changeset-8c687ea0e27cd77b4fa5025327a41906800cfcd5</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/8c687ea0e27cd77b4fa5025327a41906800cfcd5"/>
    <updated>2008-11-21T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
  
  </feed>


Get some ATOM data via pushlog date query
  $ http "http://localhost:$HGPORT/hg-test/pushlog?startdate=$STARTTIME&enddate=$MIDTIME" --header content-type --body-file body
  200
  content-type: application/atom+xml

  $ cat body
  <?xml version="1.0" encoding="ascii"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
   <id>http://localhost:$HGPORT/hg-test/pushlog</id>
   <link rel="self" href="http://localhost:$HGPORT/hg-test/pushlog"/>
   <link rel="alternate" href="http://localhost:$HGPORT/hg-test/pushloghtml"/>
   <title>hg-test Pushlog</title>
   <updated>*</updated> (glob)
   <entry>
    <title>Changeset 12799c959e3ad5465a98d333408ae8a5296d90a6</title>
    <id>http://www.selenic.com/mercurial/#changeset-12799c959e3ad5465a98d333408ae8a5296d90a6</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/12799c959e3ad5465a98d333408ae8a5296d90a6"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 52d3fce08d691a87d01c8f4397a8b34d98427271</title>
    <id>http://www.selenic.com/mercurial/#changeset-52d3fce08d691a87d01c8f4397a8b34d98427271</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/52d3fce08d691a87d01c8f4397a8b34d98427271"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 0137424351053e5108ce5b8cf14d69a5bd44b568</title>
    <id>http://www.selenic.com/mercurial/#changeset-0137424351053e5108ce5b8cf14d69a5bd44b568</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/0137424351053e5108ce5b8cf14d69a5bd44b568"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 564169828a86df44c499a737a3e40489598a9387</title>
    <id>http://www.selenic.com/mercurial/#changeset-564169828a86df44c499a737a3e40489598a9387</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/564169828a86df44c499a737a3e40489598a9387"/>
    <updated>2008-11-23T15:50:00Z</updated>
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset ea44848ca8aa9fa60c10936fdf8300f8868e9340</title>
    <id>http://www.selenic.com/mercurial/#changeset-ea44848ca8aa9fa60c10936fdf8300f8868e9340</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/ea44848ca8aa9fa60c10936fdf8300f8868e9340"/>
    <updated>2008-11-22T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 90a0919e134179630db1a9cfea3476793e68230c</title>
    <id>http://www.selenic.com/mercurial/#changeset-90a0919e134179630db1a9cfea3476793e68230c</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/90a0919e134179630db1a9cfea3476793e68230c"/>
    <updated>2008-11-22T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 8c687ea0e27cd77b4fa5025327a41906800cfcd5</title>
    <id>http://www.selenic.com/mercurial/#changeset-8c687ea0e27cd77b4fa5025327a41906800cfcd5</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/8c687ea0e27cd77b4fa5025327a41906800cfcd5"/>
    <updated>2008-11-21T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
  
  </feed>


Get some ATOM data via pushlog changeset query
  $ http "http://localhost:$HGPORT/hg-test/pushlog?fromchange=52d3fce08d69&tochange=d4b458f1c335" --header content-type --body-file body
  200
  content-type: application/atom+xml

  $ cat body
  <?xml version="1.0" encoding="ascii"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
   <id>http://localhost:$HGPORT/hg-test/pushlog</id>
   <link rel="self" href="http://localhost:$HGPORT/hg-test/pushlog"/>
   <link rel="alternate" href="http://localhost:$HGPORT/hg-test/pushloghtml"/>
   <title>hg-test Pushlog</title>
   <updated>*</updated> (glob)
   <entry>
    <title>Changeset d4b458f1c3351dd7500839e028f5bb1e2b2ff109</title>
    <id>http://www.selenic.com/mercurial/#changeset-d4b458f1c3351dd7500839e028f5bb1e2b2ff109</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/d4b458f1c3351dd7500839e028f5bb1e2b2ff109"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 7f9d2db01c2345f7d19964c01f997ab0e49de9d3</title>
    <id>http://www.selenic.com/mercurial/#changeset-7f9d2db01c2345f7d19964c01f997ab0e49de9d3</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/7f9d2db01c2345f7d19964c01f997ab0e49de9d3"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 716b98766200cea4f925caa2952bd16252358376</title>
    <id>http://www.selenic.com/mercurial/#changeset-716b98766200cea4f925caa2952bd16252358376</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/716b98766200cea4f925caa2952bd16252358376"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 745197626166e61f2a5cc9834ecc1b55cd987f5f</title>
    <id>http://www.selenic.com/mercurial/#changeset-745197626166e61f2a5cc9834ecc1b55cd987f5f</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/745197626166e61f2a5cc9834ecc1b55cd987f5f"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 96ec854d523c3e43bf5e015f68fccfcb632525a6</title>
    <id>http://www.selenic.com/mercurial/#changeset-96ec854d523c3e43bf5e015f68fccfcb632525a6</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/96ec854d523c3e43bf5e015f68fccfcb632525a6"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 07386661f41722a95cdf640ee610ae759bb36168</title>
    <id>http://www.selenic.com/mercurial/#changeset-07386661f41722a95cdf640ee610ae759bb36168</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/07386661f41722a95cdf640ee610ae759bb36168"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 0341cfc3072ffd468facf73e47f8624079616bfc</title>
    <id>http://www.selenic.com/mercurial/#changeset-0341cfc3072ffd468facf73e47f8624079616bfc</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/0341cfc3072ffd468facf73e47f8624079616bfc"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset f1af4004fca66aaf0938f50daffa9d24bbbe3f07</title>
    <id>http://www.selenic.com/mercurial/#changeset-f1af4004fca66aaf0938f50daffa9d24bbbe3f07</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/f1af4004fca66aaf0938f50daffa9d24bbbe3f07"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
  
  </feed>


Get only the tips as ATOM data from pushlog?tipsonly=1
  $ http "http://localhost:$HGPORT/hg-test/pushlog?tipsonly=1" --header content-type --body-file body
  200
  content-type: application/atom+xml

  $ cat body
  <?xml version="1.0" encoding="ascii"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
   <id>http://localhost:$HGPORT/hg-test/pushlog</id>
   <link rel="self" href="http://localhost:$HGPORT/hg-test/pushlog"/>
   <link rel="alternate" href="http://localhost:$HGPORT/hg-test/pushloghtml"/>
   <title>hg-test Pushlog</title>
   <updated>*</updated> (glob)
   <entry>
    <title>Changeset 054cf6e47bbe2fb7a3e4061ded6763bed4fd4550</title>
    <id>http://www.selenic.com/mercurial/#changeset-054cf6e47bbe2fb7a3e4061ded6763bed4fd4550</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/054cf6e47bbe2fb7a3e4061ded6763bed4fd4550"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc</title>
    <id>http://www.selenic.com/mercurial/#changeset-f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/f3fbe77f4d47e4cc9c1f0ccb32257adaa84f96cc"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 9fef10362adc35e72dfb3f38d6e540ef2bde785e</title>
    <id>http://www.selenic.com/mercurial/#changeset-9fef10362adc35e72dfb3f38d6e540ef2bde785e</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/9fef10362adc35e72dfb3f38d6e540ef2bde785e"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset bf9bdfe181e896c08c4f7332be751004b96e26f8</title>
    <id>http://www.selenic.com/mercurial/#changeset-bf9bdfe181e896c08c4f7332be751004b96e26f8</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/bf9bdfe181e896c08c4f7332be751004b96e26f8"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset badb82dde54097638883b824baa0009f4258d9f5</title>
    <id>http://www.selenic.com/mercurial/#changeset-badb82dde54097638883b824baa0009f4258d9f5</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/badb82dde54097638883b824baa0009f4258d9f5"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset f2b859fb39c4378a084edf14efd76ea5bd5dc70f</title>
    <id>http://www.selenic.com/mercurial/#changeset-f2b859fb39c4378a084edf14efd76ea5bd5dc70f</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/f2b859fb39c4378a084edf14efd76ea5bd5dc70f"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset e706af4df5a146039c05ecaffade019b325b9abe</title>
    <id>http://www.selenic.com/mercurial/#changeset-e706af4df5a146039c05ecaffade019b325b9abe</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/e706af4df5a146039c05ecaffade019b325b9abe"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f</title>
    <id>http://www.selenic.com/mercurial/#changeset-e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/e7a863a267bf3f59cdf5f38fc4d02b360bf4f25f"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 306b6389a9ad743bc619d5e62ea6a75bb842d09e</title>
    <id>http://www.selenic.com/mercurial/#changeset-306b6389a9ad743bc619d5e62ea6a75bb842d09e</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/306b6389a9ad743bc619d5e62ea6a75bb842d09e"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset f4835d42999840c490559b5f933036ee8f2ed6af</title>
    <id>http://www.selenic.com/mercurial/#changeset-f4835d42999840c490559b5f933036ee8f2ed6af</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/f4835d42999840c490559b5f933036ee8f2ed6af"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
  
  </feed>


Get some tipsonly ATOM data via pushlog date query
  $ http "http://localhost:$HGPORT/hg-test/pushlog?startdate=$STARTTIME&enddate=$MIDTIME&tipsonly=1" --header content-type --body-file body
  200
  content-type: application/atom+xml

  $ cat body
  <?xml version="1.0" encoding="ascii"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
   <id>http://localhost:$HGPORT/hg-test/pushlog</id>
   <link rel="self" href="http://localhost:$HGPORT/hg-test/pushlog"/>
   <link rel="alternate" href="http://localhost:$HGPORT/hg-test/pushloghtml"/>
   <title>hg-test Pushlog</title>
   <updated>*</updated> (glob)
   <entry>
    <title>Changeset 12799c959e3ad5465a98d333408ae8a5296d90a6</title>
    <id>http://www.selenic.com/mercurial/#changeset-12799c959e3ad5465a98d333408ae8a5296d90a6</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/12799c959e3ad5465a98d333408ae8a5296d90a6"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 0137424351053e5108ce5b8cf14d69a5bd44b568</title>
    <id>http://www.selenic.com/mercurial/#changeset-0137424351053e5108ce5b8cf14d69a5bd44b568</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/0137424351053e5108ce5b8cf14d69a5bd44b568"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset ea44848ca8aa9fa60c10936fdf8300f8868e9340</title>
    <id>http://www.selenic.com/mercurial/#changeset-ea44848ca8aa9fa60c10936fdf8300f8868e9340</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/ea44848ca8aa9fa60c10936fdf8300f8868e9340"/>
    <updated>2008-11-22T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 8c687ea0e27cd77b4fa5025327a41906800cfcd5</title>
    <id>http://www.selenic.com/mercurial/#changeset-8c687ea0e27cd77b4fa5025327a41906800cfcd5</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/8c687ea0e27cd77b4fa5025327a41906800cfcd5"/>
    <updated>2008-11-21T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
  
  </feed>


Get some tipsonly ATOM data via pushlog changeset query
  $ http "http://localhost:$HGPORT/hg-test/pushlog?fromchange=52d3fce08d69&tochange=d4b458f1c335&tipsonly=1" --header content-type --body-file body
  200
  content-type: application/atom+xml

  $ cat body
  <?xml version="1.0" encoding="ascii"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
   <id>http://localhost:$HGPORT/hg-test/pushlog</id>
   <link rel="self" href="http://localhost:$HGPORT/hg-test/pushlog"/>
   <link rel="alternate" href="http://localhost:$HGPORT/hg-test/pushloghtml"/>
   <title>hg-test Pushlog</title>
   <updated>*</updated> (glob)
   <entry>
    <title>Changeset d4b458f1c3351dd7500839e028f5bb1e2b2ff109</title>
    <id>http://www.selenic.com/mercurial/#changeset-d4b458f1c3351dd7500839e028f5bb1e2b2ff109</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/d4b458f1c3351dd7500839e028f5bb1e2b2ff109"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 716b98766200cea4f925caa2952bd16252358376</title>
    <id>http://www.selenic.com/mercurial/#changeset-716b98766200cea4f925caa2952bd16252358376</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/716b98766200cea4f925caa2952bd16252358376"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 96ec854d523c3e43bf5e015f68fccfcb632525a6</title>
    <id>http://www.selenic.com/mercurial/#changeset-96ec854d523c3e43bf5e015f68fccfcb632525a6</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/96ec854d523c3e43bf5e015f68fccfcb632525a6"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 0341cfc3072ffd468facf73e47f8624079616bfc</title>
    <id>http://www.selenic.com/mercurial/#changeset-0341cfc3072ffd468facf73e47f8624079616bfc</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/0341cfc3072ffd468facf73e47f8624079616bfc"/>
    <updated>*</updated> (glob)
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
  
  </feed>


Dates with leading/trailing spaces should work properly
  $ http "http://localhost:$HGPORT/hg-test/pushlog?startdate=%20$STARTTIME&enddate=$MIDTIME%20&tipsonly=1" --header content-type --body-file body
  200
  content-type: application/atom+xml

  $ cat body
  <?xml version="1.0" encoding="ascii"?>
  <feed xmlns="http://www.w3.org/2005/Atom">
   <id>http://localhost:$HGPORT/hg-test/pushlog</id>
   <link rel="self" href="http://localhost:$HGPORT/hg-test/pushlog"/>
   <link rel="alternate" href="http://localhost:$HGPORT/hg-test/pushloghtml"/>
   <title>hg-test Pushlog</title>
   <updated>*</updated> (glob)
   <entry>
    <title>Changeset 12799c959e3ad5465a98d333408ae8a5296d90a6</title>
    <id>http://www.selenic.com/mercurial/#changeset-12799c959e3ad5465a98d333408ae8a5296d90a6</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/12799c959e3ad5465a98d333408ae8a5296d90a6"/>
    <updated>*</updated> (glob)
    <author>
     <name>johndoe</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 0137424351053e5108ce5b8cf14d69a5bd44b568</title>
    <id>http://www.selenic.com/mercurial/#changeset-0137424351053e5108ce5b8cf14d69a5bd44b568</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/0137424351053e5108ce5b8cf14d69a5bd44b568"/>
    <updated>*</updated> (glob)
    <author>
     <name>someone</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset ea44848ca8aa9fa60c10936fdf8300f8868e9340</title>
    <id>http://www.selenic.com/mercurial/#changeset-ea44848ca8aa9fa60c10936fdf8300f8868e9340</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/ea44848ca8aa9fa60c10936fdf8300f8868e9340"/>
    <updated>2008-11-22T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
   <entry>
    <title>Changeset 8c687ea0e27cd77b4fa5025327a41906800cfcd5</title>
    <id>http://www.selenic.com/mercurial/#changeset-8c687ea0e27cd77b4fa5025327a41906800cfcd5</id>
    <link href="http://localhost:$HGPORT/hg-test/rev/8c687ea0e27cd77b4fa5025327a41906800cfcd5"/>
    <updated>2008-11-21T15:50:00Z</updated>
    <author>
     <name>luser</name>
    </author>
    <content type="xhtml">
     <div xmlns="http://www.w3.org/1999/xhtml">
      <ul class="filelist"><li class="file">testfile</li></ul>
     </div>
    </content>
   </entry>
  
  </feed>

Confirm no errors in log output

  $ cat ../hg-test/error.log
