from __future__ import unicode_literals

from reviewboard.diffviewer.opcode_generator import (
    DiffOpcodeGenerator,
)


class NoFilterDiffOpcodeGenerator(DiffOpcodeGenerator):
    """A DiffOpcodeGenerator which does not filter interdiffs"""
    def _apply_processors(self, opcodes):
        # We override Review Board's internal `_apply_processors()`
        # to stop calling `filter_interdiff_opcodes()`. This is a
        # temporary hack to avoid hitting misleading interdiffs
        # due to bugs in the filter code. This will result in
        # unrelated changes present in a rebase slipping into the
        # interdiffs.
        for opcode in opcodes:
            yield opcode
