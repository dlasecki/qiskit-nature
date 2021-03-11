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
"""Tests Fermionic Operator builder."""
from test import QiskitNatureTestCase
from qiskit_nature.components.bosonic_bases import HarmonicBasis
from qiskit_nature.problems.second_quantization.vibrational.vibrational_label_builder import \
    create_labels
from qiskit_nature.drivers import GaussianForcesDriver


class TestVibrationalSpinOpBuilder(QiskitNatureTestCase):
    """Tests Vibrational Spin Op builder."""

