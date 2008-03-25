const BASEURL = '/hgwebdir.cgi/';
const SVGNS = 'http://www.w3.org/2000/svg';

const REVWIDTH = 254;
const HSPACING = 40;
const VSPACING = 30;

/**
 * The nodeid of the "center" of the graph... mainly used for smart resizing
 * behavior.
 */
var rootContext;

/**
 * map from long node strings to the JSON data.
 * The following mappings are added to the JSON:
 *   .element from the node to the element
 *   .parentArrows is a *map* of nodes to the arrow element pointing to a parent
 */

var revs = {};

function short(node)
{
    return node.slice(0, 12);
}

function measure(r, prop)
{
    return Number(r.css(prop).replace('px', ''));
}

/**
 * given an object that represents a revision, return
 * a <div> element cloned from revision-template.
 */
function makeRev(node)
{
    var rev = revs[node];
    if (!rev) {
        alert("Missing revision: " + node);
        return;
    }

    var d = $('#revision-template').clone();
    d.attr('id', 'rev' + rev.node);
    $('.node', d).text(rev.rev + ": " + short(rev.node));
    $('.user', d).text(rev.user);
    $('.date', d).text(rev.date);
    $('.desc', d).text(rev.description);

    rev.element = d[0];

    d.appendTo('#inside-scrolling');
    d.click(navTo);

    return d;
}

function drawArrow(p1, p2)
{
    var a = $('#arrow-template').clone();
    a.removeAttr('id');
    a.attr('x1', p1.x);
    a.attr('x2', p2.x);
    a.attr('y1', p1.y);
    a.attr('y2', p2.y);
    a.appendTo('#scroller');
    return a;
}

function drawRelations(node, kind, limit)
{
    var context = revs[node];
    var count = context[kind].length;

    if (count == 0)
        return;

    var relations = [];
    var totalHeight = (count - 1) * 30;

    for (var i = 0; i < count; ++i) {
        var relationnode = context[kind][i];
        var relationrev = revs[relationnode];

        var relationel = makeRev(context[kind][i])
        relationrev.element = relationel;

        relations.push(relationel);
        totalHeight += measure(relations[i], 'height');
    }

    var left = measure($(context.element), 'left');
    var contextpoint = {};
    switch (kind) {
    case 'children':
        contextpoint.x = left + REVWIDTH;
        left += REVWIDTH + HSPACING;
        break;
    
    case 'parents':
        contextpoint.x = left;
        left -= REVWIDTH + HSPACING;
        break;

    default:
        alert("Unknown relationship!");
        return;
    }

    var el = $(context.element);
    var top = measure(el, 'top') + measure(el, 'height') / 2;

    contextpoint.y = top;
    
    top -= (totalHeight / 2);

    for (i = 0; i < count; ++i) {
        var relationnode = context[kind][i];
        var relationrev = revs[relationnode];

        relations[i].css('left', left);
        relations[i].css('top', top);

        var rheight = measure(relations[i], 'height');

        if (kind == 'children') {
            var arrowpoint = {x: left,
                              y: top + rheight / 2};
            var a = drawArrow(contextpoint, arrowpoint);
            relationrev.parentArrows[node] = a;
        } 
        else {
            var arrowpoint = {x: left + REVWIDTH,
                              y: top + rheight / 2};
            var a = drawArrow(arrowpoint, contextpoint);
            context.parentArrows[relationnode] = a;
        }

        top += rheight + VSPACING;

        if (limit > 1) {
            drawRelations(relationnode, kind, limit - 1);
        }
    }
}

function drawContext(data)
{
    for each (var node in data.nodes) {
        var nodeid = node.node;

        if (!(nodeid in revs)) {
            revs[nodeid] = node;
            revs[nodeid].element = null;
            revs[nodeid].parentArrows = {};
        }
    }

    var center = makeRev(data.context);
    center.css('left', (measure($('#inside-scrolling'), 'width') - REVWIDTH) / 2);
    center.css('top', 200 - measure(center, 'height') / 2);

    rootContext = data.context;

    drawRelations(data.context, 'parents', 2);
    drawRelations(data.context, 'children', 2);
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

    rootContext = null;

    /* Clear out lots of everything */
    for (var rev in revs) {
        rev.element = null;
        rev.parentArrows = {};
    }

    $('#inside-scrolling').empty();
    $('#scroller').empty();

    $.ajax({'url': BASEURL + repo + "/jsonfamily?node=" + context,
            'type': 'GET',
            'dataType': 'json',
            error: function(xhr, textStatus) {
                alert("Request failed: " + textStatus);
            },
            success: drawContext
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
