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
"""A class defining a main bead of a peptide."""
from typing import List

from qiskit.opflow import PauliOp

from ...peptide.beads.base_bead import BaseBead
from ...peptide.chains.side_chain import SideChain


class MainBead(BaseBead):
    """A class defining a main bead of a peptide."""

    def __init__(
        self, main_index: int, residue_type: str, turn_qubits: List[PauliOp], side_chain: SideChain
    ):

        super().__init__(
            "main_chain",
            main_index,
            residue_type,
            turn_qubits,
            self._build_turn_indicator_fun_0,
            self._build_turn_indicator_fun_1,
            self._build_turn_indicator_fun_2,
            self._build_turn_indicator_fun_3,
        )
        self._side_chain = side_chain

    def __str__(self):
        return self.chain_type + "_" + str(self.main_index)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return self.main_index == other.index and self.chain_type == other.chain_type

    def _build_turn_indicator_fun_0(self, full_id):
        return (
            full_id ^ ((full_id - self._turn_qubits[0]) @ (full_id - self._turn_qubits[1]))
        ).reduce()

    def _build_turn_indicator_fun_1(self, full_id):
        return (
            full_id ^ (self._turn_qubits[1] @ (self._turn_qubits[1] - self._turn_qubits[0]))
        ).reduce()

    def _build_turn_indicator_fun_2(self, full_id):
        return (
            full_id ^ (self._turn_qubits[0] @ (self._turn_qubits[0] - self._turn_qubits[1]))
        ).reduce()

    def _build_turn_indicator_fun_3(self, full_id):
        return (full_id ^ (self._turn_qubits[0] @ self._turn_qubits[1])).reduce()

    @property
    def side_chain(self) -> SideChain:
        """Returns a side chain."""
        return self._side_chain
