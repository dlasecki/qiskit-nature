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
import numpy as np
from qiskit_nature.problems.sampling.protein_folding.interactions.interaction import Interaction


class RandomInteraction(Interaction):

    def calc_energy_matrix(self, num_beads, sequence):  # TODO unused arg
        pair_energies = - 1 - 4 * np.random.rand(num_beads + 1, 2, num_beads + 1, 2)
        return pair_energies
