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
from typing import List

from problems.sampling.protein_folding.peptide.chains.side_chain import SideChain
from qiskit_nature.problems.sampling.protein_folding.peptide.chains.main_chain import MainChain


class Peptide:
    def __init__(self, main_chain_len: int, main_chain_residue_seq: List[str],
                 side_chain_lens: List[int],
                 side_chain_residue_sequences: List[str]):
        self._main_chain = MainChain(main_chain_len, main_chain_residue_seq, side_chain_lens,
                                     side_chain_residue_sequences)

    def get_side_chains(self) -> List[SideChain]:
        """
        Returns the list of all side chains in a peptide.

        Returns:
            side_chains: the list of all side chains in a peptide.
        """
        side_chains = []
        for main_bead in self._main_chain.beads_list:
            side_chains.append(main_bead.side_chain)
        return side_chains

    def get_side_chain_hot_vector(self) -> List[bool]:
        """
        Returns a one-hot encoding list for side chains in a peptide which indicates which side
        chains are present.

        Returns:
            side_chain_hot_vector: a one-hot encoding list for side chains in a peptide.
        """
        side_chain_hot_vector = []
        for main_bead in self._main_chain.beads_list:
            if main_bead.side_chain is not None:
                side_chain_hot_vector.append(True)
            else:
                side_chain_hot_vector.append(False)
        return side_chain_hot_vector

    @property
    def get_main_chain(self) -> MainChain:
        return self._main_chain
