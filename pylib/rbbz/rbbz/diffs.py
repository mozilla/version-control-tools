import HTMLParser

from django.contrib.sites.models import Site
from django.template.loader import render_to_string

from djblets.siteconfig.models import SiteConfiguration
from reviewboard.diffviewer.diffutils import (get_diff_files,
                                              populate_diff_chunks)
from reviewboard.diffviewer.views import exception_traceback_string


def get_file_chunks_in_range_custom(context, filediff, interfilediff,
                                    first_line, num_lines):
    """
    A generator that yields chunks within a range of lines in the specified
    filediff/interfilediff.

    This function was mostly copied from the Review Board source code. The
    main modification is to always set syntax highlighting to False so that
    plain code is returned in the chunks instead of html.

    This is primarily intended for use with templates. It takes a
    RequestContext for looking up the user and for caching file lists,
    in order to improve performance and reduce lookup times for files that have
    already been fetched.

    Each returned chunk is a dictionary with the following fields:

      ============= ========================================================
      Variable      Description
      ============= ========================================================
      ``change``    The change type ("equal", "replace", "insert", "delete")
      ``numlines``  The number of lines in the chunk.
      ``lines``     The list of lines in the chunk.
      ``meta``      A dictionary containing metadata on the chunk
      ============= ========================================================


    Each line in the list of lines is an array with the following data:

      ======== =============================================================
      Index    Description
      ======== =============================================================
      0        Virtual line number (union of the original and patched files)
      1        Real line number in the original file
      2        HTML markup of the original file
      3        Changed regions of the original line (for "replace" chunks)
      4        Real line number in the patched file
      5        HTML markup of the patched file
      6        Changed regions of the patched line (for "replace" chunks)
      7        True if line consists of only whitespace changes
      ======== =============================================================
    """
    def find_header(headers):
        for header in reversed(headers):
            if header[0] < first_line:
                return {
                    'line': header[0],
                    'text': header[1],
                }

    interdiffset = None

    key = "_diff_files_%s_%s" % (filediff.diffset.id, filediff.id)

    if interfilediff:
        key += "_%s" % (interfilediff.id)
        interdiffset = interfilediff.diffset

    if key in context:
        files = context[key]
    else:
        assert 'user' in context

        request = context.get('request', None)
        files = get_diff_files(filediff.diffset, filediff, interdiffset,
                               request=request)
        populate_diff_chunks(files, False,
                             request=request)
        context[key] = files

    if not files:
        raise StopIteration

    assert len(files) == 1
    last_header = [None, None]

    for chunk in files[0]['chunks']:
        if ('headers' in chunk['meta'] and
                (chunk['meta']['headers'][0] or chunk['meta']['headers'][1])):
            last_header = chunk['meta']['headers']

        lines = chunk['lines']

        if lines[-1][0] >= first_line >= lines[0][0]:
            start_index = first_line - lines[0][0]

            if first_line + num_lines <= lines[-1][0]:
                last_index = start_index + num_lines
            else:
                last_index = len(lines)

            new_chunk = {
                'lines': chunk['lines'][start_index:last_index],
                'numlines': last_index - start_index,
                'change': chunk['change'],
                'meta': chunk.get('meta', {}),
            }

            if 'left_headers' in chunk['meta']:
                left_header = find_header(chunk['meta']['left_headers'])
                right_header = find_header(chunk['meta']['right_headers'])
                del new_chunk['meta']['left_headers']
                del new_chunk['meta']['right_headers']

                if left_header or right_header:
                    header = (left_header, right_header)
                else:
                    header = last_header

                new_chunk['meta']['headers'] = header

            yield new_chunk

            first_line += new_chunk['numlines']
            num_lines -= new_chunk['numlines']

            assert num_lines >= 0
            if num_lines == 0:
                break


def render_equal_chunk(chunk, parser):
    indents = chunk['meta'].get('indentation_changes', {})
    lines = [] # Rendered lines.
    indent_count = 0 # How many indentation lines have we seen in a row.

    for line in chunk['lines']:
        indent_key = "%s-%s" % (line[1], line[4])

        if indent_key not in indents:
            indent_count = 0
            lines.append(">  %s" % parser.unescape(line[5]))
            continue

        # Unpack the indent data., is_indent indicates if the change added
        # more indentation (True added, False removed), num_chars is the
        # raw count of spaces and tabs in the indentation change, and
        # normalized_len is the length of the indentation change where
        # tab characters are treated as 8 spaces.
        #
        # e.g. if the following characters were added:
        #    "   \t  "
        # it would result in the following data:
        #     (True, 6, 10)
        # and it would appear in the line as:
        #    <span class="indent">&gt;&gt;&gt;&gt;---|&gt;&gt;</span>
        is_indent, num_chars, normalized_len = indents[indent_key]

        chars = None
        remainder = None
        original_len = len(line[2])
        patched_len = len(line[5])

        # Grab the characters we need to parse.
        if is_indent:
            chars = line[5][21:(patched_len - original_len)]
            remainder = line[2]
        else:
            remainder = line[5]
            chars = line[2][21:(original_len - patched_len)]

        index = 0
        replace_chars = []
        current_width = 0

        # Parse the indentation characters
        while index < len(chars):
            if chars[index] == "&" and chars[index + 1] == "g": # "&gt;".
                # Space character
                replace_chars.append(" ");
                current_width += 1
                index += 4

            elif chars[index] == "&" and chars[index + 1] == "m": # "&mdash;".
                # One of the spaces we translated before
                # was actually part of this tab we've
                # found
                replace_chars.pop()

                # find the end of the tab.
                while chars[index] != "|":
                    current_width += 1
                    index += 7

                replace_chars.append("\t")
                current_width += 1
                index += 1

            elif chars[index] == "|":
                # We've hit an ambiguous case. The previous character might
                # be a space or might be part of this tab. For now, lets just
                # be stupid and assume it's part of the tab (mixed indentation
                # is evil anyways).
                replace_chars.pop()
                replace_chars.append("\t")
                current_width += 1
                index += 1

            else:
                # We really shouldn't hit this case... if we did, something
                # went terribly wrong. lets just fill the rest of the
                # characters with spaces and bail
                replace_chars.append(" " * (normalized_len - current_width))
                index = len(chars)

        add_line = None
        remove_line = None
        remainder = parser.unescape(remainder)

        if is_indent:
            add_line = "> +%s%s" % ("".join(replace_chars), remainder)
            remove_line = "> -%s" % remainder
        else:
            add_line = "> +%s" % remainder
            remove_line = "> -%s%s" % ("".join(replace_chars), remainder)

        lines.insert(len(lines) - indent_count, remove_line)
        lines.append(add_line)

    return lines

def render_comment_plain(comment, context):
    parser = HTMLParser.HTMLParser()
    chunks = list(get_file_chunks_in_range_custom(
        context,
        comment.filediff,
        comment.interfilediff,
        comment.first_line,
        comment.num_lines))

    lines = [
        "::: %s" % comment.filediff.dest_file_display,
    ]

    if comment.interfilediff:
        lines.append(
            "(Diff revisions %s - %s)" % (
                comment.filediff.diffset.revision,
                comment.interfilediff.diffset.revision))
    else:
        lines.append(
            "(Diff revision %s)" % comment.filediff.diffset.revision)

    for chunk in chunks:
        if chunk['change'] == "equal":
            lines.extend(render_equal_chunk(chunk, parser))
        elif chunk['change'] == "insert":
            for line in chunk['lines']:
                lines.append("> +%s" % parser.unescape(line[5]))
        elif chunk['change'] == "delete":
            for line in chunk['lines']:
                lines.append("> -%s" % parser.unescape(line[2]))
        elif chunk['change'] == "replace":
            for line in chunk['lines']:
                lines.append("> -%s" % parser.unescape(line[2]))
            for line in chunk['lines']:
                lines.append("> +%s" % parser.unescape(line[5]))

    lines.append("%s" % comment)

    return "\n".join(lines)


def build_plaintext_review(review, context):
    """Create a plaintext patch style representation of a review"""
    comment_entries = []
    review_text = []
    siteconfig = SiteConfiguration.objects.get_current()

    if review.body_top:
        review_text.append(review.body_top)

    for comment in review.comments.all():
        review_text.append(render_comment_plain(comment, context))

    if review.body_bottom:
        review_text.append(review.body_bottom)

    return "\n\n".join(review_text)

