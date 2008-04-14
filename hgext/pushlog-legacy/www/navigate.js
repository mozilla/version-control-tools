/* -*- Mode: Java; c-basic-offset: 2; indent-tabs-mode: nil -*- */

const BASEURL = '/hgwebdir.cgi/%REPO%/';
const SVGNS = 'http://www.w3.org/2000/svg';

const REVWIDTH = 254;
const HSPACING = 40;
const VSPACING = 30;
const TEXTSTYLE = '12px sans-serif';

const ANIMLENGTH = 500; /* milliseconds */
const ANIMINTERVAL = 75;

let gWidth, gHeight, gContext, gPendingRequest;
let gAnimating = false;

function startAnimating()
{
  if (!gAnimating) {
    gAnimating = true;
    setTimeout(doAnimate, ANIMINTERVAL);
  }
}

function doAnimate()
{
  redraw();

  let now = new Date().getTime();

  /* Clear our interval if there's nothing more to animate */
  for each (let rev in revs) {
    if (rev._atime != null && rev._atime + ANIMLENGTH > now) {
      setTimeout(doAnimate, ANIMINTERVAL);
      return;
    }
  }
  gAnimating = false;
}

function getCX()
{
  let cx = $('#drawcanvas')[0].getContext('2d');
  cx.mozTextStyle = TEXTSTYLE;
  return cx;
}

function measure(t, cx)
{
  if (!cx)
    cx = getCX();

  return cx.mozMeasureText(t);
}

/**
 * Take a string of text. Split it into up to as many as three lines. Yield
 * each line.
 */
function splitText(t, cx)
{
  if (!cx)
    cx = getCX();

  var syllables = t.split(' ');
  var unplaced = 0;

  for (var i = 0; i < 3 && unplaced < syllables.length; ++i) {
    for (var placed = unplaced + 2; placed < syllables.length; ++placed) {
      if (measure(syllables.slice(unplaced, placed).join(' '), cx) >
          REVWIDTH) {
        --placed;
        break;
      }
    }
    var str = syllables.slice(unplaced, placed).join(" ");
    if (i == 2 && placed < syllables.length)
      str += "…";

    yield str;
    unplaced = placed;
  }
}

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

function getRevision(node)
{
  if (!(node in revs)) {
    revs[node] = new Revision(node);
  }
  return revs[node];
}

function Revision(node)
{
  this.node = node;
  this.revnode = "??: " + this.shortnode();
  this.revnodelen = measure(this.revnode);
}

Revision.prototype = {
  parents: [],
  children: [],
  _x: null,
  _y: null,
  gc: false,

  _atime: null, /* the start time of an animation */
  /* constraint: _ax and _ay are meaningless unless _atime is set */

  loaded: function r_loaded()
  {
    return 'rev' in this;
  },

  update: function r_update(data)
  {
    if (data.node != this.node)
      throw Error("node doesn't match in Revision.update\nthis.node: " +
                  this.node + "\ndata.node: " + data.node);

    let cx = getCX();

    this.rev = data.rev;

    this.revnode = this.rev + ": " + this.shortnode();
    this.revnodelen = measure(this.revnode, cx);

    this.userlen = measure(data.user, cx);
    this.user = data.user;

    this.date = data.date;
    this.datelen = measure(data.date, cx);

    this.description = data.description;
    this.descSplit = [line for (line in splitText(data.description))];

    this.children = [getRevision(node) for each (node in data.children)];
    this.parents = [getRevision(node) for each (node in data.parents)];
  },

  /* x and y are the center of the revision */
  x: function r_x() {
    if (this._x == null)
      throw Error("Revision " + this.node + " is not positioned.");

    return this._x;
  },

  y: function r_y() {
    if (this._y == null)
      throw Error("Revision " + this.node + " is not positioned.");

    return this._y;
  },

  /* current animated position */

  /* from 0 to 1, how far are we through the animation? */
  easing: function r_easing()
  {
    let m = (new Date().getTime() - this._atime) / ANIMLENGTH;
    if (m >= 1) {
      this._atime = null;
      return 1;
    }
    return m;
  },

  ax: function r_ax() {
    let x = this.x();
    if (this._atime == null)
      return x;

    let e = this.easing();
    return x + (this._ax - x) * (1 - e);
  },

  ay: function r_ay() {
    let y = this.y();
    if (this._atime == null)
      return y;
  
    let e = this.easing();
    return y + (this._ay - y) * (1 - e);
  },

  /* height */
  height: function r_height() {
    if (this.loaded()) {
      return 12 * (3 + this.descSplit.length) + 4;
    }
    
    return 12 + 4;
  },

  /**
   * Move the center of the box to this point
   * context is optional: it specifies an already positioned revision
   * which we can animate against if we are not currently positioned.
   */
  moveTo: function r_move(x, y, context) {
    if (isNaN(x))
      throw Error("x is NaN");

    if (isNaN(y))
      throw Error("y is NaN");

    if (this._x += null) {
      this.animStart(this._x, this._y);
    }
    else if (context) {
      this.animStart(x + context.ax() - context.x(),
                     y + context.ay() - context.y());
    }

    this._x = x;
    this._y = y;
  },

  animStart: function r_animStart(x, y)
  {
    startAnimating();
    this._atime = new Date().getTime();
    this._ax = x;
    this._ay = y;
  },

  shortnode: function r_shortnode()
  {
    return this.node.slice(0, 12);
  },

  hittest: function r_hittest(x, y)
  {
    if (!this.gc)
      return false;

    let tx = this.x();
    let ty = this.y();
    let th = this.height();

    if (tx - REVWIDTH / 2 <= x &&
        tx + REVWIDTH / 2 >= x &&
        ty - th / 2 <= y &&
        ty + th / 2 >= y)
      return true;

    return false;
  },

  toString: function r_toString()
  {
    return "Revision:" +
    "\nnode: " + this.node +
    "\nposition: " + this._x + ", " + this._y +
    "\ndescSplit: " + uneval(this.descSplit);
  }
};

function limit(str, len)
{
  if (str.length < len)
    return str;

  return str.slice(0, len) + "…";
}

function doLayout()
{
  let loadMore = [];
  let bottompositions = [];
  
  function drawChildren(rev, position)
  {
    if (rev.children.length == 0)
      return;
    
    let totalHeight = (rev.children.length - 1) * VSPACING;
    
    for each (child in rev.children) {
      totalHeight += child.height();
    }

    totalHeight -= rev.children[0].height() / 2;
    totalHeight -= rev.children[rev.children.length - 1].height() / 2;
  
    let x = rev.x();
    let y = rev.y();
    x += REVWIDTH + HSPACING;
    y -= totalHeight / 2;

    if (bottompositions[position]) {
      let p = bottompositions[position];
      let miny = p.y() + p.height() / 2 +
        rev.children[0].height() / 2 + VSPACING;
      if (y < miny)
        y = miny;
    }

    let rightEdge = gWidth; // XXX won't be true if we introduce scaling

    for each (let child in rev.children) {
      if (!child.gc) {
        child.gc = true;
        child.moveTo(x, y);
        y += child.height() + VSPACING;
        if (x < rightEdge) {
          drawChildren(child, position + 1);
        }
        if (!child.loaded())
          loadMore.push(child);

        bottompositions[position] = child;
      }
    }
  }
  
  function drawParents(rev, position)
  {
    if (rev.parents.length == 0)
      return;
    
    let totalHeight = 0;

    for each (let parent in rev.parents) {
      totalHeight += parent.height();
    }
    
    totalHeight -= rev.parents[0].height() / 2;
    totalHeight -= rev.parents[rev.parents.length - 1].height() / 2;
  
    let x = rev.x();
    let y = rev.y();
    x -= REVWIDTH + HSPACING;
    y -= totalHeight / 2;

    if (bottompositions[position]) {
      let p = bottompositions[position];
      let miny = p.y() + p.height() / 2 +
        rev.parents[0].height() / 2 + VSPACING;
      if (y < miny)
        y = miny;
    }
    
    var leftEdge = 0;
    
    for each (let parent in rev.parents) {
      if (!parent.gc) {
        parent.gc = true;
        parent.moveTo(x, y);
        y += parent.height() + VSPACING;
        
        if (x > leftEdge) {
          drawParents(parent, position - 1);
        }
        if (!parent.loaded())
          loadMore.push(parent);

        bottompositions[position] = parent;
      }
    }
  }  

  let contextrev = revs[gContext];
  
  if (contextrev.loaded()) {
    document.title = $('#select-repo')[0].value + " revision " +
      contextrev.rev + ": " +
      limit(contextrev.description, 60);
  }
  else {
    document.title = $('#select-repo')[0].value + " node " + contextrev.node;
  }

  // All the nodes which have .gc = false at the end are offscreen and can
  // be ignored
  for each (let rev in revs)
    rev.gc = false;

  contextrev.gc = true;
  contextrev.moveTo(gWidth / 2,
                    gHeight / 2);
  
  drawChildren(contextrev, 1);
  drawParents(contextrev, -1);

  for each (let rev in revs) {
    if (!rev.gc)
      rev._x = null;
  }
  
  redraw();

  if (loadMore.length) {
    /* Load the unloaded nodes */
    let repo = $('#select-repo')[0].value;
    $.ajax(
      {'url': BASEURL.replace('%REPO%', repo) + "jsoninfo?" +
                ["node=" + rev.node for each (rev in loadMore)].join('&'),
       'type': 'GET',
       'dataType': 'json',
       error: function(xhr, textStatus) {
         alert("Request failed: " + textStatus + "\nurl: " + this.url);
       },
       success: processInfoData,
      }
    );
  }
}

function redraw()
{
  var cx = getCX();

  /**
   * Draw some text. Advance the translation down by 12px
   */
  function drawText(t, xoffset)
  {
    if (xoffset < 2)
      xoffset = 2;

    cx.translate(0, 12);
    cx.save();
    cx.translate(xoffset, 0);
    cx.mozDrawText(t);
    cx.restore();
  }

  function drawRev(r)
  {
    let h = r.height();
    let left = r.ax() - REVWIDTH / 2;
    let top = r.ay() - h / 2;

    cx.save();
    // clip the text to the box
    cx.beginPath();
    cx.rect(left, top, REVWIDTH, h);
    cx.stroke();
    cx.clip();

    cx.save();
    cx.fillStyle = "white";
    cx.fill();
    cx.restore();

    if (!r.loaded())
      cx.fillStyle = "#900";

    cx.translate(left, top);
    drawText(r.revnode, (REVWIDTH - r.revnodelen) / 2);
    if (r.loaded()) {
      drawText(r.user, (REVWIDTH - r.userlen) / 2);
      drawText(r.date, (REVWIDTH - r.datelen) / 2);
      for each (let line in r.descSplit) {
        drawText(line, 2);
      }
    }
    cx.restore();
  }

  function drawArrows(r)
  {
    /* draw all arrows from this rev */
    for each (let child in r.children) {
      let childx = r.ax() + 100;
      let childy = r.ay();
      if (child.gc) {
        childx = child.ax() - REVWIDTH / 2;
        childy = child.ay();
      }
      cx.beginPath();
      cx.moveTo(r.ax(), r.ay());
      cx.lineTo(childx, childy);
      cx.stroke();
    }
  }

  cx.clearRect(0, 0, gWidth, gHeight);

  cx.save();
  cx.lineWidth = 2;
  for each (let rev in revs) {
    if (rev.gc)
      drawArrows(rev);
  }
  cx.restore();

  for each (let rev in revs) {
    if (rev.gc)
      drawRev(rev);
  }
}

function processContextData(data)
{
  for each (var nodeObj in data.nodes) {
    getRevision(nodeObj.node).update(nodeObj);
  }

  if (this.changeContext)
    gContext = data.context;

  doLayout();
}

function processInfoData(data)
{
  for each (var infoNode in data) {
    getRevision(infoNode.node).update(infoNode);
  }
  doLayout();
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

    gPendingRequest =
      {'url': BASEURL.replace('%REPO%', repo) + "jsonfamily?node=" + context,
       'type': 'GET',
       'dataType': 'json',
       error: function(xhr, textStatus) {
          alert("Request failed: " + textStatus);
        },
       success: processContextData,
       changeContext: true
      };

    $.ajax(gPendingRequest);
}

function navTo(node)
{
  $('#node-input')[0].value = node;
  gContext = node;
  if (gPendingRequest)
    gPendingRequest.changeContext = false;

  doLayout();
  setHash();
}

function setHash()
{
    $.history.load($('#select-repo')[0].value + ':' + $('#node-input')[0].value)
}

function doResize()
{
  var w = $(window);
  var c = $('#drawcanvas');

  gWidth = w.width();
  gHeight = w.height() - $('#topnav').height();

  c.attr('width', gWidth);
  c.attr('height', gHeight);

  if (gContext)
    doLayout();
}

function clickCanvas(e)
{
  let o = $(this).offset();
  let canvasX = e.clientX - o.left;
  let canvasY = e.clientY - o.top;

  for each (let rev in revs) {
    if (rev.hittest(canvasX, canvasY)) {
      navTo(rev.node);
      break;
    }
  }
}

function init()
{
  $('#drawcanvas').click(clickCanvas);
  $('#select-repo').change(setHash);
  $('#node-choose').click(setHash);
  $.history.init(startContext);

  $(window).resize(doResize);
  doResize();
}
