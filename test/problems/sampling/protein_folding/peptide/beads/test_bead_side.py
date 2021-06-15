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
"""Tests Side Bead."""
from test import QiskitNatureTestCase
from qiskit.opflow import I, Z

from problems.sampling.protein_folding.peptide.pauli_ops_builder import _build_full_identity
from qiskit_nature.problems.sampling.protein_folding.peptide.beads.side_bead import SideBead


class TestSideBead(QiskitNatureTestCase):
    """Tests Side Bead."""

    def test_side_bead_constructor(self):
        """Tests that a SideBead is created."""
        residue_type = "S"
        main_chain_len = 4
        num_turn_qubits = 2 * (main_chain_len - 1)
        main_chain_id = 3
        side_bead_id = 3
        turn_qubits = [
            0.5 * _build_full_identity(num_turn_qubits) - 0.5 * (I ^ I ^ I ^ I ^ I ^ Z),
            0.5 * _build_full_identity(num_turn_qubits) - 0.5 * (I ^ I ^ I ^ I ^ Z ^ I),
        ]
        side_bead = SideBead(main_chain_id, side_bead_id, residue_type, turn_qubits)

        indic_0, indic_1, indic_2, indic_3 = side_bead.get_indicator_functions()

        assert indic_0 == 0.25 * (I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I) + 0.25 * (
            I ^ I ^ I ^ I ^ Z ^ I ^ I ^ I ^ I ^ I ^ I ^ I
        ) + 0.25 * (I ^ I ^ I ^ I ^ I ^ Z ^ I ^ I ^ I ^ I ^ I ^ I) + 0.25 * (
            I ^ I ^ I ^ I ^ Z ^ Z ^ I ^ I ^ I ^ I ^ I ^ I
        )
        assert indic_1 == 0.25 * (I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I) - 0.25 * (
            I ^ I ^ I ^ I ^ Z ^ I ^ I ^ I ^ I ^ I ^ I ^ I
        ) + 0.25 * (I ^ I ^ I ^ I ^ I ^ Z ^ I ^ I ^ I ^ I ^ I ^ I) - 0.25 * (
            I ^ I ^ I ^ I ^ Z ^ Z ^ I ^ I ^ I ^ I ^ I ^ I
        )
        assert indic_2 == 0.25 * (I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I) + 0.25 * (
            I ^ I ^ I ^ I ^ Z ^ I ^ I ^ I ^ I ^ I ^ I ^ I
        ) - 0.25 * (I ^ I ^ I ^ I ^ I ^ Z ^ I ^ I ^ I ^ I ^ I ^ I) - 0.25 * (
            I ^ I ^ I ^ I ^ Z ^ Z ^ I ^ I ^ I ^ I ^ I ^ I
        )
        assert indic_3 == 0.25 * (I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I ^ I) - 0.25 * (
            I ^ I ^ I ^ I ^ Z ^ I ^ I ^ I ^ I ^ I ^ I ^ I
        ) - 0.25 * (I ^ I ^ I ^ I ^ I ^ Z ^ I ^ I ^ I ^ I ^ I ^ I) + 0.25 * (
            I ^ I ^ I ^ I ^ Z ^ Z ^ I ^ I ^ I ^ I ^ I ^ I
        )

    def test_side_bead_constructor_none(self):
        """Tests that a SideBead is created."""
        residue_type = None
        turn_qubits = [Z, Z]
        main_chain_id = 3
        side_bead_id = 3
        side_bead = SideBead(main_chain_id, side_bead_id, residue_type, turn_qubits)

        with self.assertRaises(AttributeError):
            _, _, _, _ = side_bead.get_indicator_functions()
