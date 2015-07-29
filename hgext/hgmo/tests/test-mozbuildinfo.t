  $ cat >> $HGRCPATH << EOF
  > [extensions]
  > hgmo = $TESTDIR/hgext/hgmo
  > EOF

  $ hg init repo
  $ cd repo

Empty repos should report no moz.build info

  $ hg mozbuildinfo
  {
    "error": "no moz.build info available"
  }

Repo without moz.build info should report no moz.build info

  $ echo initial > foo
  $ hg -q commit -A -m initial
  $ hg mozbuildinfo
  {
    "error": "no moz.build info available"
  }

Empty moz.build file shows empty info

  $ echo '# empty' > moz.build
  $ hg -q commit -A -m 'add empty moz.build'
  $ hg mozbuildinfo
  {
    "aggregate": {
      "bug_component_counts": [], 
      "recommended_bug_component": null
    }, 
    "files": {
      "moz.build": {}
    }
  }

Reading an old version before moz.build added says no moz.build

  $ hg mozbuildinfo -r 0
  {
    "error": "no moz.build info available"
  }

Meaningful data is reported from moz.build files

  $ cat > moz.build << EOF
  > with Files('**'):
  >     BUG_COMPONENT = ('Product1', 'Component1')
  > EOF

  $ hg commit -m 'associate with product1'

  $ hg mozbuildinfo
  {
    "aggregate": {
      "bug_component_counts": [
        [
          [
            "Product1", 
            "Component1"
          ], 
          1
        ]
      ], 
      "recommended_bug_component": [
        "Product1", 
        "Component1"
      ]
    }, 
    "files": {
      "moz.build": {
        "bug_component": [
          "Product1", 
          "Component1"
        ]
      }
    }
  }

  $ cat > moz.build << EOF
  > with Files('**'):
  >     BUG_COMPONENT = ('Product2', 'Component2')
  > EOF

  $ hg commit -m 'associate with product2'
  $ hg mozbuildinfo
  {
    "aggregate": {
      "bug_component_counts": [
        [
          [
            "Product2", 
            "Component2"
          ], 
          1
        ]
      ], 
      "recommended_bug_component": [
        "Product2", 
        "Component2"
      ]
    }, 
    "files": {
      "moz.build": {
        "bug_component": [
          "Product2", 
          "Component2"
        ]
      }
    }
  }

Reading old revision works

  $ hg mozbuildinfo -r a949ee5fce4a
  {
    "aggregate": {
      "bug_component_counts": [
        [
          [
            "Product1", 
            "Component1"
          ], 
          1
        ]
      ], 
      "recommended_bug_component": [
        "Product1", 
        "Component1"
      ]
    }, 
    "files": {
      "moz.build": {
        "bug_component": [
          "Product1", 
          "Component1"
        ]
      }
    }
  }

Specifying which files to query works

  $ hg mozbuildinfo foo
  {
    "aggregate": {
      "bug_component_counts": [
        [
          [
            "Product2", 
            "Component2"
          ], 
          1
        ]
      ], 
      "recommended_bug_component": [
        "Product2", 
        "Component2"
      ]
    }, 
    "files": {
      "foo": {
        "bug_component": [
          "Product2", 
          "Component2"
        ]
      }
    }
  }

Empty working directories continue to work

  $ hg -q up -r null
  $ hg mozbuildinfo -r tip
  {
    "aggregate": {
      "bug_component_counts": [
        [
          [
            "Product2", 
            "Component2"
          ], 
          1
        ]
      ], 
      "recommended_bug_component": [
        "Product2", 
        "Component2"
      ]
    }, 
    "files": {
      "moz.build": {
        "bug_component": [
          "Product2", 
          "Component2"
        ]
      }
    }
  }
