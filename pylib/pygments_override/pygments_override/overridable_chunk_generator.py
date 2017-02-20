import logging
from os.path import splitext

from pygments import highlight
from pygments.lexers import guess_lexer_for_filename, get_lexer_by_name

from reviewboard.extensions.base import get_extension_manager
from reviewboard.diffviewer.diffutils import split_line_endings
from reviewboard.diffviewer.chunk_generator import (
    get_diff_chunk_generator_class,
    NoWrapperHtmlFormatter
)


logger = logging.getLogger(__name__)

DiffChunkGenerator = get_diff_chunk_generator_class()


class OverridableDiffChunkGenerator(DiffChunkGenerator):
    """A chunk generator which overrides syntax highlighting."""

    def _apply_pygments(self, data, filename):
        """Applies Pygments syntax-highlighting to a file's contents.

        Syntax highlight obeys a explicitly provided list of preferences by
        extension or it is derived from the contents of the file.

        The resulting HTML will be returned as a list of lines.
        """
        lexer = self._get_preferred_lexer(
            filename, stripnl=False, encoding='utf-8')
        logger.debug('preferred lexer for %s: %s' % (filename, lexer))
        if not lexer:
            lexer = guess_lexer_for_filename(
                filename, data, stripnl=False,
                encoding='utf-8')

        lexer.add_filter('codetagify')

        return split_line_endings(highlight(data, lexer,
                                            NoWrapperHtmlFormatter()))

    def _get_preferred_lexer(self, filename, **options):
        ext = splitext(filename)[1]
        lexername = get_overrides().get(ext, None)
        try:
            lexer = get_lexer_by_name(lexername, **options)
        except:
            lexer = None
        return lexer


def get_overrides():
    extension = get_extension_manager().get_enabled_extension(
        'pygments_override.extension.PygmentsOverride')
    return extension.get_overrides_map()
