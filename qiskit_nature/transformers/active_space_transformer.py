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

"""The Active-Space Reduction interface."""

from typing import List, Optional, Tuple
import copy
import logging
import numpy as np

from .base_transformer import BaseTransformer
from .. import QiskitNatureError
from ..drivers import QMolecule

logger = logging.getLogger(__name__)


class ActiveSpaceTransformer(BaseTransformer):
    r"""The Active-Space reduction.

    The reduction is done by computing the inactive Fock operator which is defined as
    :math:`F^I_{pq} = h_{pq} + \sum_i 2 g_{iipq} - g_{iqpi}` and the inactive energy which is
    given by :math:`E^I = \sum_j h_{jj} + F ^I_{jj}`, where :math:`i` and :math:`j` iterate over
    the inactive orbitals.
    By using the inactive Fock operator in place of the one-electron integrals, `h1`, the
    description of the active space contains an effective potential generated by the inactive
    electrons. Therefore, this method permits the exclusion of non-core electrons while
    retaining a high-quality description of the system.

    For more details on the computation of the inactive Fock operator refer to
    https://arxiv.org/abs/2009.01872.

    The active space can be configured in one of the following ways through the initializer:
        - when only `num_electrons` and `num_orbitals` are specified, these integers indicate the
          number of active electrons and orbitals, respectively. The active space will then be
          chosen around the Fermi level resulting in a unique choice for any pair of numbers.
          Nonetheless, the following criteria must be met:
              1. the remaining number of inactive electrons must be a positive, even number
              2. the number of active orbitals must not exceed the total number of orbitals minus
              the number of orbitals occupied by the inactive electrons
        - when, in addition to the above, `num_alpha` is specified, this can be used to disambiguate
          the active space in systems with non-zero spin. Thus, `num_alpha` determines the number of
          active alpha electrons. The number of active beta electrons can then be determined based
          via `num_beta = num_electrons - num_alpha`. The same requirements as listed in the
          previous case must be met.
        - finally, it is possible to select a custom set of active orbitals via their indices using
          `active_orbitals`. This allows selecting an active space which is not placed around the
          Fermi level as described in the first case, above. When using this keyword argument, the
          following criteria must be met *in addition* to the ones listed above:
              1. the length of `active_orbitals` must be equal to `num_orbitals`.
              2. the sum of electrons present in `active_orbitals` must be equal to `num_electrons`.

    References:
        - *M. Rossmannek, P. Barkoutsos, P. Ollitrault, and I. Tavernelli, arXiv:2009.01872
          (2020).*
    """

    def __init__(self, num_electrons: int, num_orbitals: int, num_alpha: Optional[int] = None,
                 active_orbitals: Optional[List[int]] = None):
        """Initializes a transformer which can reduce a `QMolecule` to a configured active space.

        Args:
            num_electrons: the number of active electrons.
            num_orbitals: the number of active orbitals.
            num_alpha: the optional number of active alpha-spin electrons.
            active_orbitals: A list of indices specifying the molecular orbitals of the active
                             space. This argument must match with the remaining arguments and should
                             only be used to enforce an active space that is not chosen purely
                             around the Fermi level.
        """
        self.num_electrons = num_electrons
        self.num_orbitals = num_orbitals
        self.num_alpha = num_alpha
        self.active_orbitals = active_orbitals

    def transform(self, q_molecule: QMolecule) -> QMolecule:  # type: ignore
        """Reduces the given `QMolecule` to a given active space.

        Args:
            q_molecule: the `QMolecule` to be transformed.

        Returns:
            A new `QMolecule` instance.

        Raises:
            QiskitNatureError: If more electrons or orbitals are requested than are available, if an
                               uneven number of inactive electrons remains, or if the number of
                               selected active orbital indices does not match `num_orbitals`.
        """
        # get molecular orbital coefficients
        mo_coeff_full = (q_molecule.mo_coeff, q_molecule.mo_coeff_b)
        beta = mo_coeff_full[1] is not None
        # get molecular orbital occupation numbers
        mo_occ_full = (q_molecule.mo_occ, q_molecule.mo_occ_b)
        if mo_occ_full[0] is None:
            # QMolecule provided by driver without `mo_occ` information available. Constructing
            # occupation numbers based on ground state HF case.
            occ_alpha = [1.] * q_molecule.num_alpha + [0.] * (q_molecule.num_orbitals -
                                                              q_molecule.num_alpha)
            if beta:
                occ_beta = [1.] * q_molecule.num_beta + [0.] * (q_molecule.num_orbitals -
                                                                q_molecule.num_beta)
            else:
                occ_alpha[:q_molecule.num_beta] = [o + 1 for o in occ_alpha[:q_molecule.num_beta]]
                occ_beta = None
            mo_occ_full = (np.asarray(occ_alpha), np.asarray(occ_beta))
        mo_occ_total = mo_occ_full[0] + mo_occ_full[1] if beta else mo_occ_full[0]

        # compute number of inactive electrons
        nelec_total = q_molecule.num_alpha + q_molecule.num_beta
        nelec_inactive = nelec_total - self.num_electrons
        if self.num_alpha is not None:
            if not beta:
                warning = 'The provided instance of QMolecule does not provide any beta ' \
                          + 'coefficients but you tried to specify a separate number of alpha ' \
                          + 'electrons. Continuing as if it does not matter.'
                logger.warning(warning)
            num_alpha = self.num_alpha
            num_beta = self.num_electrons - self.num_alpha
        else:
            num_beta = (self.num_electrons - (q_molecule.multiplicity - 1)) // 2
            num_alpha = self.num_electrons - num_beta

        self._validate_num_electrons(nelec_inactive)
        self._validate_num_orbitals(nelec_inactive, q_molecule, mo_occ_total)

        # determine active and inactive orbital indices
        if self.active_orbitals is None:
            norbs_inactive = nelec_inactive // 2
            inactive_orbs_idxs = list(range(norbs_inactive))
            active_orbs_idxs = list(range(norbs_inactive, norbs_inactive + self.num_orbitals))
        else:
            active_orbs_idxs = self.active_orbitals
            inactive_orbs_idxs = [o for o in range(nelec_total // 2) if o not in
                                  self.active_orbitals and mo_occ_total[o] > 0]

        # split molecular orbitals coefficients into active and inactive parts
        mo_coeff_inactive = (mo_coeff_full[0][:, inactive_orbs_idxs],
                             mo_coeff_full[1][:, inactive_orbs_idxs] if beta else None)
        mo_coeff_active = (mo_coeff_full[0][:, active_orbs_idxs],
                           mo_coeff_full[1][:, active_orbs_idxs] if beta else None)
        mo_occ_inactive = (mo_occ_full[0][inactive_orbs_idxs],
                           mo_occ_full[1][inactive_orbs_idxs] if beta else None)

        density_inactive = self._compute_inactive_density_matrix(mo_occ_inactive, mo_coeff_inactive)

        # extract core Hamiltonian and electron-repulsion-integral matrices from QMolecule
        hcore = (q_molecule.hcore, q_molecule.hcore_b if beta else None)
        eri = q_molecule.eri

        fock_inactive = self._compute_inactive_fock_op(hcore, eri, density_inactive)

        e_inactive = self._compute_inactive_energy(hcore, density_inactive, fock_inactive,
                                                   mo_coeff_inactive)

        hij, hijkl = self._compute_active_integrals(mo_coeff_active, fock_inactive, eri)

        # construct new QMolecule
        q_molecule_reduced = copy.deepcopy(q_molecule)
        # Energies and orbits
        q_molecule_reduced.energy_shift['ActiveSpaceTransformer'] = e_inactive
        q_molecule_reduced.num_orbitals = self.num_orbitals
        q_molecule_reduced.num_alpha = num_alpha
        q_molecule_reduced.num_beta = num_beta
        q_molecule_reduced.mo_coeff = mo_coeff_active[0]
        q_molecule_reduced.mo_coeff_b = mo_coeff_active[1]
        q_molecule_reduced.orbital_energies = q_molecule.orbital_energies[active_orbs_idxs]
        if beta:
            q_molecule_reduced.orbital_energies_b = q_molecule.orbital_energies_b[active_orbs_idxs]
        # 1 and 2 electron integrals in MO basis
        q_molecule_reduced.mo_onee_ints = hij[0]
        q_molecule_reduced.mo_onee_ints_b = hij[1]
        q_molecule_reduced.mo_eri_ints = hijkl[0]
        q_molecule_reduced.mo_eri_ints_ba = hijkl[1]
        q_molecule_reduced.mo_eri_ints_bb = hijkl[2]
        # invalidate AO basis integrals
        q_molecule_reduced.hcore = None
        q_molecule_reduced.hcore_b = None
        q_molecule_reduced.kinetic = None
        q_molecule_reduced.overlap = None
        q_molecule_reduced.eri = None
        # invalidate dipole integrals
        q_molecule_reduced.x_dip_ints = None
        q_molecule_reduced.y_dip_ints = None
        q_molecule_reduced.z_dip_ints = None
        q_molecule_reduced.x_dip_mo_ints = None
        q_molecule_reduced.x_dip_mo_ints_b = None
        q_molecule_reduced.y_dip_mo_ints = None
        q_molecule_reduced.y_dip_mo_ints_b = None
        q_molecule_reduced.z_dip_mo_ints = None
        q_molecule_reduced.z_dip_mo_ints_b = None

        return q_molecule_reduced

    def _validate_num_electrons(self, nelec_inactive: int):
        """Validates the number of electrons.

        Args:
            nelec_inactive: the computed number of inactive electrons.

        Raises:
            QiskitNatureError: if the number of inactive electrons is either negative or odd.
        """
        if nelec_inactive < 0:
            raise QiskitNatureError("More electrons requested than available.")
        if nelec_inactive % 2 != 0:
            raise QiskitNatureError("The number of inactive electrons must be even.")

    def _validate_num_orbitals(self,
                               nelec_inactive: int,
                               q_molecule: QMolecule,
                               mo_occ_total: np.ndarray):
        """Validates the number of orbitals.

        Args:
            nelec_inactive: the computed number of inactive electrons.
            q_molecule: the `QMolecule` to be transformed.
            mo_occ_total: the alpha- and beta-spin MO occupation vector pair.

        Raises:
            QiskitNatureError: if more orbitals were requested than are available in total or if the
                               number of selected orbitals mismatches the specified number of active
                               orbitals.
        """
        if self.active_orbitals is None:
            norbs_inactive = nelec_inactive // 2
            if norbs_inactive + self.num_orbitals > q_molecule.num_orbitals:
                raise QiskitNatureError("More orbitals requested than available.")
        else:
            if self.num_orbitals != len(self.active_orbitals):
                raise QiskitNatureError("The number of selected active orbital indices does not "
                                        "match the specified number of active orbitals.")
            if max(self.active_orbitals) >= q_molecule.num_orbitals:
                raise QiskitNatureError("More orbitals requested than available.")
            if sum(mo_occ_total[self.active_orbitals]) != self.num_electrons:
                raise QiskitNatureError("The number of electrons in the selected active orbitals "
                                        "does not match the specified number of active electrons.")

    def _compute_inactive_density_matrix(self,
                                         mo_occ_inactive: Tuple[np.ndarray, Optional[np.ndarray]],
                                         mo_coeff_inactive: Tuple[np.ndarray, Optional[np.ndarray]]
                                         ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Computes the inactive density matrix.

        Args:
            mo_occ_inactive: the alpha- and beta-spin inactive MO occupation vector pair.
            mo_coeff_inactive: the alpha- and beta-spin inactive MO coefficient matrix pair.

        Returns:
            The pair of alpha- and beta-spin inactive density matrices.
        """
        density_inactive_a = np.dot(mo_coeff_inactive[0] * mo_occ_inactive[0],
                                    np.transpose(mo_coeff_inactive[0]))
        density_inactive_b = None
        if mo_occ_inactive[1] is not None and mo_occ_inactive[1] is not None:
            density_inactive_b = np.dot(mo_coeff_inactive[1] * mo_occ_inactive[1],
                                        np.transpose(mo_coeff_inactive[1]))
        return (density_inactive_a, density_inactive_b)

    def _compute_inactive_fock_op(self,
                                  hcore: Tuple[np.ndarray, Optional[np.ndarray]],
                                  eri: np.ndarray,
                                  density_inactive: Tuple[np.ndarray, Optional[np.ndarray]]
                                  ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Computes the inactive Fock operator.

        Args:
            hcore: the alpha- and beta-spin core Hamiltonian pair.
            eri: the electron-repulsion-integrals in MO format.
            density_inactive: the alpha- and beta-spin inactive density matrix pair.

        Returns:
            The pair of alpha- and beta-spin inactive Fock operators.
        """
        # compute inactive Fock matrix
        coulomb_inactive = np.einsum('ijkl,ji->kl', eri, density_inactive[0])
        exchange_inactive = np.einsum('ijkl,jk->il', eri, density_inactive[0])
        fock_inactive = hcore[0] + coulomb_inactive - 0.5 * exchange_inactive
        fock_inactive_b = coulomb_inactive_b = exchange_inactive_b = None

        if density_inactive[1] is not None:
            # if hcore[1] is None we use the alpha-spin core Hamiltonian
            hcore_b = hcore[1] or hcore[0]
            coulomb_inactive_b = np.einsum('ijkl,ji->kl', eri, density_inactive[1])
            exchange_inactive_b = np.einsum('ijkl,jk->il', eri, density_inactive[1])
            fock_inactive = hcore[0] + coulomb_inactive + coulomb_inactive_b - exchange_inactive
            fock_inactive_b = hcore_b + coulomb_inactive + coulomb_inactive_b - exchange_inactive_b

        return (fock_inactive, fock_inactive_b)

    def _compute_inactive_energy(self,
                                 hcore: Tuple[np.ndarray, Optional[np.ndarray]],
                                 density_inactive: Tuple[np.ndarray, Optional[np.ndarray]],
                                 fock_inactive: Tuple[np.ndarray, Optional[np.ndarray]],
                                 mo_coeff_inactive: Tuple[np.ndarray, Optional[np.ndarray]],
                                 ) -> float:
        """Computes the inactive energy.

        Args:
            hcore: the alpha- and beta-spin core Hamiltonian pair.
            density_inactive: the alpha- and beta-spin inactive density matrix pair.
            fock_inactive: the alpha- and beta-spin inactive fock operator pair.
            mo_coeff_inactive: the alpha- and beta-spin inactive MO coefficient matrix pair.

        Returns:
            The inactive energy.
        """
        beta = mo_coeff_inactive[1] is not None
        # compute inactive energy
        e_inactive = 0.0
        if not beta and mo_coeff_inactive[0].size > 0:
            e_inactive += 0.5 * np.einsum('ij,ji', density_inactive[0], hcore[0] + fock_inactive[0])
        elif beta and mo_coeff_inactive[1].size > 0:
            e_inactive += 0.5 * np.einsum('ij,ji', density_inactive[0], hcore[0] + fock_inactive[0])
            e_inactive += 0.5 * np.einsum('ij,ji', density_inactive[1], hcore[1] + fock_inactive[1])

        return e_inactive

    def _compute_active_integrals(self,
                                  mo_coeff_active: Tuple[np.ndarray, Optional[np.ndarray]],
                                  fock_inactive: Tuple[np.ndarray, Optional[np.ndarray]],
                                  eri: np.ndarray,
                                  ) -> Tuple[
        Tuple[np.ndarray, Optional[np.ndarray]],
        Tuple[np.ndarray, Optional[np.ndarray], Optional[np.ndarray]]
    ]:
        """Computes the h1 and h2 integrals for the active space.

        Args:
            mo_coeff_active: the alpha- and beta-spin active MO coefficient matrix pair.
            fock_inactive: the alpha- and beta-spin inactive fock operator pair.
            eri: the electron-repulsion-integrals in MO format.

        Returns:
            The h1 and h2 integrals for the active space. The storage format is the following:
                ((alpha-spin h1, beta-spin h1),
                 (alpha-alpha-spin h2, beta-alpha-spin h2, beta-beta-spin h2))
        """
        # compute new 1- and 2-electron integrals
        hij = np.dot(np.dot(np.transpose(mo_coeff_active[0]), fock_inactive[0]), mo_coeff_active[0])
        hijkl = np.einsum('pqrs,pi,qj,rk,sl->ijkl', eri, mo_coeff_active[0], mo_coeff_active[0],
                          mo_coeff_active[0], mo_coeff_active[0], optimize=True)

        hij_b = hijkl_bb = hijkl_ba = None

        if mo_coeff_active[1] is not None:
            hij_b = np.dot(np.dot(np.transpose(mo_coeff_active[1]), fock_inactive[1]),
                           mo_coeff_active[1])
            hijkl_bb = np.einsum('pqrs,pi,qj,rk,sl->ijkl', eri, mo_coeff_active[1],
                                 mo_coeff_active[1], mo_coeff_active[1], mo_coeff_active[1],
                                 optimize=True)
            hijkl_ba = np.einsum('pqrs,pi,qj,rk,sl->ijkl', eri, mo_coeff_active[1],
                                 mo_coeff_active[1], mo_coeff_active[0], mo_coeff_active[0],
                                 optimize=True)

        return ((hij, hij_b), (hijkl, hijkl_ba, hijkl_bb))
