const BASEURL = '/hgwebdir.cgi/';
const SVGNS = 'http://www.w3.org/2000/svg';

const REVWIDTH = 254;
const HSPACING = 40;
const VSPACING = 30;

/**
 * map from long node strings to Revision objects
 * The following mappings are added to the JSON:
 *   .element from the node to the element
 *   .parentArrows is a map of arrows pointing to this element, keyed on
 *                 parent node
 *   .childArrows  is a map of arrows pointing from this element, keyed on
 *                 child node
 */

var revs = {};

function Revision(data)
{
    var i, d, a;

    this.node = data.node;
    this.rev = data.rev;
    this.user = data.user;
    this.date = data.date
    this.description = data.description;
    this.children = data.children;
    this.parents = data.parents;

    d = $('#revision-template').clone();
    d.attr('id', 'rev' + shortrev(this.node));
    $('.node', d).text(this.rev + ": " + shortrev(this.node));
    $('.user', d).text(this.user);
    $('.date', d).text(this.date);
    $('.desc', d).text(this.description);

    this.element = d[0];

    d.appendTo('#inside-scrolling');
    d.click(navTo);
    this.height = measure($(d), 'height');

    this.childArrows = {};
    this.parentArrows = {};

    for (i in this.children) {
        if (revs[this.children[i]]) {
            a = revs[this.children[i]].parentArrows[this.node];
            this.childArrows[this.children[i]] = a;
        }
        else {
            // We haven't met this child yet... make an arrow for it
            a = $('#arrow-template').clone();
            a.attr('id', 'ar' + shortrev(this.node) + ':' + shortrev(this.children[i]));
            a.appendTo('#scroller');
            this.childArrows[this.children[i]] = a[0];
        }
    }

    for (i in this.parents) {
        if (revs[this.parents[i]]) {
            var a = revs[this.parents[i]].childArrows[this.node];
            this.parentArrows[this.parents[i]] = a;
        }
        else {
            // We haven't met this parent yet... make an arrow for it
            a = $('#arrow-template').clone();
            a.attr('id', 'ar' + shortrev(this.parents[i] + ':' + shortrev(this.node)));
            a.appendTo('#scroller');
            this.parentArrows[this.parents[i]] = a[0];
        }
    }

    revs[this.node] = this;
}

Revision.prototype = {
  visible: function r_visible() {
    return $(this.element).css('visibility') != 'hidden';
  },

  x: function r_x() {
    if (!this.visible())
      throw Error("Revision " + this.node + " is not visible.");

    return measure($(this.element), 'left');
  },

  y: function r_y() {
    if (!this.visible())
      throw Error("Revision " + this.node + " is not visible.");

    return measure($(this.element), 'top');
  },

  center: function r_center() {
    if (!this.visible())
      throw Error("Revision " + this.node + " is not visible.");
    
    return {x: this.x() + REVWIDTH / 2,
            y: this.y() + this.height / 2};
  },

  parentPoint: function r_parentPoint() {
    if (!this.visible())
      throw Error("Revision " + this.node + " is not visible.");

    return {x: this.x(),
            y: this.y() + this.height / 2 };
  },
  
  childPoint: function r_childPoint() {
    if (!this.visible())
      throw Error("Revision " + this.node + " is not visible.");

    var e = $(this.element);
    return {x: this.x() + REVWIDTH,
            y: this.y() + this.height / 2 };
  },
  
  /**
   * Move the center of the box to this point
   */
  moveTo: function r_move(point) {
    var e, child, parent, p, a;
    
    e = $(this.element);
    e.css('visibility', 'visible');
    e.css('left', point.x - REVWIDTH / 2);
    e.css('top', point.y - this.height / 2);
    
    p = this.childPoint();
    for each (child in this.children) {
      a = $(this.childArrows[child]);
      a.attr('x1', p.x);
      a.attr('y1', p.y);
      if (!(child in revs)) {
        a.attr('x2', p.x + 25);
        a.attr('y2', p.y);
      }
      a.css('visibility', 'visible');
    }
    
    p = this.parentPoint();
    for each (parent in this.parents) {
      a = $(this.parentArrows[parent]);
      a.attr('x2', p.x);
      a.attr('y2', p.y);
      if (!(parent in revs)) {
        a.attr('x1', p.x - 25);
        a.attr('y1', p.y);
      }
      a.css('visibility', 'visible');
    }
  },
  
  /**
   * Hide gc'ed revisions, set arrow visibility, and move the other end of unbounded arrows.
   * Each node is responsible for all its parent arrows, as well as child arrows pointing to unknown revisions.
   */
  cleanLayout: function r_moveArrows()
  {
    var child, parent, p, a, i;

    if (!this.gc) {
      $(this.element).css('visibility', 'hidden');

      for each (child in this.children) {
        if (!(child in revs)) {
          $(this.childArrows[child]).css('visibility', 'hidden');
        }
      }
      
      for each (parent in this.parents) {
        if (!(parent in revs) || !(revs[parent].gc)) {
          $(this.parentArrows[parent]).css('visibility', 'hidden');
        }
      }
    }
    else {
      // We've already been positioned and are visible; all we need is to position the "other" end
      // of arrows that point to offscreen revisions
      p = this.childPoint();
      for (i in this.children) {
        child = this.children[i];
        
        if (!(child in revs) || !revs[child].gc) {
          this.childArrows[child].setAttribute('class', 'arrow ambiguous');
          a = $(this.childArrows[child]);
          a.attr('x2', p.x + 25);
          a.attr('y2', this.y() + (Number(i) + 0.5) * (this.height / this.children.length));
        }
      }

      p = this.parentPoint();
      for (i in this.parents) {
        parent = this.parents[i];
        
        if (!(parent in revs) || !revs[parent].gc) {
          this.parentArrows[parent].setAttribute('class', 'arrow ambiguous');
          a = $(this.parentArrows[parent]);
          a.attr('x1', p.x - 25);
          a.attr('y1', this.y() + (Number(i) + 0.5) * (this.height / this.parents.length));
        }
        else {
          this.parentArrows[parent].setAttribute('class', 'arrow');
        }
      }
    }
  }
};

function shortrev(node)
{
    return node.slice(0, 12);
}

/**
 * Limit a string to len characters... if it is too long, add an ellipsis.
 */
function limit(str, len)
{
    if (str.length < len) {
        return str;
    }

    return str.slice(0, len) + "…";
}

function measure(r, prop)
{
    return Number(r.css(prop).replace('px', ''));
}

function doLayout(node)
{
  var contextrev, rev, i, loadMore;
  
  loadMore = [];
  
  function drawChildren(rev)
  {
    var p, child, totalHeight, avgHeight, c, childrev;
  
    if (rev.children.length == 0)
      return;
    
    totalHeight = 0;
    c = 0;
    
    for each (child in rev.children) {
      if (child in revs) {
        totalHeight += revs[child].height;
        revs[child].gc = true;
        ++c;
      }
    }
  
    avgHeight = totalHeight / c;
    
    p = new Object(rev.center());
    p.x += REVWIDTH + HSPACING;
    p.y -= (totalHeight - avgHeight) / 2;
    
    var rightEdge = measure($('#inside-scrolling'), 'left') + measure($('#inside-scrolling'), 'width');
    
    for each (child in rev.children) {
      if (child in revs) {
        childrev = revs[child];
        childrev.moveTo(p);
        p.y += childrev.height + VSPACING;
  
        if (p.x < rightEdge) {
          drawChildren(childrev);
        }
      }
      else {
        loadMore.push(child);
      }
    }
  }
  
  function drawParents(rev)
  {
    var p, parent, totalHeight, avgHeight, c, parentrev;
    
    if (rev.parents.length == 0)
      return;
    
    totalHeight = 0;
    c = 0;
    
    for each (parent in rev.parents) {
      if (parent in revs) {
        totalHeight += revs[parent].height;
        revs[parent].gc = true;
        ++c;
      }
    }
    
    avgHeight = totalHeight / c;
    
    p = new Object(rev.center());
    p.x -= REVWIDTH + HSPACING;
    p.y -= (totalHeight - avgHeight) / 2;
    
    var leftEdge = measure($('#inside-scrolling'), 'left');
    
    for each (parent in rev.parents) {
      if (parent in revs) {
        parentrev = revs[parent];
        parentrev.moveTo(p);
        p.y += parentrev.height + VSPACING;
        
        if (p.x > leftEdge) {
          drawParents(parentrev);
        }
      }
      else {
        loadMore.push(parent);
      }
    }
  }  
  
  contextrev = revs[node];
    
  document.title = $('#select-repo')[0].value + " revision " +
    contextrev.rev + ": " +
    limit(contextrev.description, 60);

  // All the nodes which have .gc = false at the end will be hidden
  for each (rev in revs)
    rev.gc = false;

  contextrev.gc = true;
  i = $('#inside-scrolling');
  contextrev.moveTo({x: measure(i, 'width') / 2,
                     y: measure(i, 'height') / 2});
  
  drawChildren(contextrev);
  drawParents(contextrev);
  
  for each (rev in revs)
    rev.cleanLayout();
}



function processContextData(data)
{
  for each (var node in data.nodes) {
      if (node.node in revs)
          continue;

      new Revision(node);
  }

  doLayout(data.context);
}

function startContext(hash)
{
    var repo, context;

    if (hash == '') {
        repo = $('#select-repo')[0].value;
        context = $('#node-input')[0].value;
    }
    else {
        var l = hash.split(':');
        repo = l[0];
        context = l[1];
        $('#select-repo')[0].value = repo;
        $('#node-input')[0].value = context;
    }

    $.ajax({'url': BASEURL + repo + "/jsonfamily?node=" + context,
            'type': 'GET',
            'dataType': 'json',
            error: function(xhr, textStatus) {
                alert("Request failed: " + textStatus);
            },
            success: processContextData
           });
}

function navTo()
{
    $('#node-input')[0].value = this.id.replace('rev', '');
    setHash();
}

function setHash()
{
    $.history.load($('#select-repo')[0].value + ':' + $('#node-input')[0].value)
}

function init()
{
    $('#select-repo').change(setHash);
    $('#node-choose').click(setHash);
    $.history.init(startContext);
}
