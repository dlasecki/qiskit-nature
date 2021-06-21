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
"""An interface for sampling qubit operator builders."""
from abc import ABC, abstractmethod
from typing import Union

from qiskit.opflow import PauliOp, PauliSumOp


class SamplingQubitOpBuilder(ABC):
    """An interface for sampling qubit operator builders."""

    @abstractmethod
    def build_qubit_op(self) -> Union[PauliOp, PauliSumOp]:
        """Builds a qubit operator that represents a Hamiltonian encoding the sampling problem."""
        pass
