import logging

from reviewboard.extensions.base import Extension
from reviewboard.diffviewer.chunk_generator import (
    get_diff_chunk_generator_class,
    set_diff_chunk_generator_class
)

from pygments_override.overridable_chunk_generator import (
    OverridableDiffChunkGenerator
)


logger = logging.getLogger(__name__)


class PygmentsOverride(Extension):
    metadata = {
        'Name': 'pygments-override',
        'Summary': 'Customize Pygments for specific file extensions',
    }

    default_settings = {'overrides': ''}

    is_configurable = True

    def initialize(self):
        self._original_chunk_generator_class = get_diff_chunk_generator_class()
        set_diff_chunk_generator_class(OverridableDiffChunkGenerator)

    def shutdown(self):
        set_diff_chunk_generator_class(self._original_chunk_generator_class)
        super(PygmentsOverride, self).shutdown()

    def get_overrides_map(self):
        overrides = self.settings['overrides'].splitlines()
        valid_overrides = [override for override in overrides
                           if '=' in override]
        if valid_overrides != overrides:
            invalid_overrides = set(overrides) - set(valid_overrides)
            formatted_list = '\n'.join(invalid_overrides)
            logger.error('ignoring malformed overrides:\n%s ' % formatted_list)

        return dict([override.split('=') for override in valid_overrides])
