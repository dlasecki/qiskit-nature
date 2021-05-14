# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
from typing import List, Union

from qiskit_nature.problems.sampling.protein_folding.peptide.beads.side_bead import SideBead
from qiskit_nature.problems.sampling.protein_folding.peptide.chains.base_chain import BaseChain


class SideChain(BaseChain):

    def __init__(self, side_chain_len, side_chain_residue_sequences):
        beads_list = self._build_side_chain(side_chain_len, side_chain_residue_sequences)
        super().__init__(beads_list)

    def _build_side_chain(self, side_chain_len, side_chain_residue_sequences) -> \
            Union[List[SideBead], None]:
        if side_chain_len > 1:
            raise Exception(
                f"Only side chains of length 1 supported, length {side_chain_len} was given.")
        if side_chain_len == 0:
            return None
        side_chain = []
        for side_bead_id in range(side_chain_len):
            bead_turn_qubit_1 = self._build_turn_qubit(side_chain_len, side_bead_id)
            bead_turn_qubit_2 = self._build_turn_qubit(side_chain_len, side_bead_id)
            side_bead = SideBead(side_chain_residue_sequences[side_bead_id],
                                 [bead_turn_qubit_1, bead_turn_qubit_2])
            side_chain.append(side_bead)
        return side_chain
