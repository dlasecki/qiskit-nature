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
from problems.sampling.protein_folding.builders.contact_qubits_builder import \
    _create_contact_qubits
from problems.sampling.protein_folding.peptide.pauli_ops_builder import _build_full_identity
from problems.sampling.protein_folding.peptide.peptide import Peptide


class ContactMap:

    def __init__(self, peptide: Peptide):
        self._peptide = peptide
        self._lower_main_upper_main, self._lower_side_upper_main, self._lower_main_upper_side, \
        self._lower_side_upper_side, self.r_contact = _create_contact_qubits(peptide)

    @property
    def peptide(self):
        return self._peptide

    @property
    def lower_main_upper_main(self):
        return self._lower_main_upper_main

    @property
    def lower_side_upper_main(self):
        return self._lower_side_upper_main

    @property
    def lower_main_upper_side(self):
        return self._lower_main_upper_side

    @property
    def lower_side_upper_side(self):
        return self._lower_side_upper_side

    def create_peptide_qubit_list(self):
        """
        Creates new set of contact qubits for second nearest neighbour
        interactions. Note, the need of multiple interaction qubits
        for each i,j pair.

        Args:
            main_chain_len: Number of total beads in peptide
            side_chain: List of side chains in peptide
            pauli_conf: Dictionary of Pauli operators to track conformation
            pauli_contacts: Dictionary of Pauli operators to track contacts between beads

        Returns:
            new_qubits: Dictionary of qubits in symbolic notation
        """
        main_chain_len = len(self.peptide.get_main_chain)
        side_chain = self.peptide.get_side_chain_hot_vector()
        old_qubits_conf = []
        old_qubits_contact = []
        num_qubits = 2 * (main_chain_len - 1)
        full_id = _build_full_identity(num_qubits)
        for q in range(3, main_chain_len):
            if q != 3:
                old_qubits_conf.append(full_id ^ self.peptide.get_main_chain[q - 1].turn_qubits[0])
                old_qubits_conf.append(full_id ^ self.peptide.get_main_chain[q - 1].turn_qubits[1])
            else:
                old_qubits_conf.append(full_id ^ self.peptide.get_main_chain[q - 1].turn_qubits[0])
            if side_chain[q - 1]:
                old_qubits_conf.append(
                    self.peptide.get_main_chain[q - 1].side_chain[0].turn_qubits[0] ^ full_id)
                old_qubits_conf.append(
                    self.peptide.get_main_chain[q - 1].side_chain[0].turn_qubits[1] ^ full_id)

        self._add_qubits(main_chain_len, old_qubits_contact, self._lower_main_upper_main)
        self._add_qubits(main_chain_len, old_qubits_contact, self._lower_side_upper_main)
        self._add_qubits(main_chain_len, old_qubits_contact, self._lower_main_upper_side)
        self._add_qubits(main_chain_len, old_qubits_contact, self._lower_side_upper_side)

        new_qubits = [0] + old_qubits_conf + old_qubits_contact
        return new_qubits

    @staticmethod
    def _add_qubits(main_chain_len, contact_qubits, contact_map):
        for lower_bead_id in range(1, main_chain_len - 3):
            for upper_bead_id in range(lower_bead_id + 4, main_chain_len + 1):
                try:
                    contact_op = contact_map[lower_bead_id][upper_bead_id]
                    contact_qubits.append(contact_op)
                except KeyError:
                    pass


