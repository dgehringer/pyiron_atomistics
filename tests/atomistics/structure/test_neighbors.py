# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import unittest
import numpy as np
from pyiron_atomistics.atomistics.structure.atoms import Atoms, CrystalStructure
from pyiron_atomistics.atomistics.structure.factory import StructureFactory
import warnings


class TestAtoms(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def setUpClass(cls):
        pass

    def test_allow_ragged(self):
        struct = CrystalStructure(elements='Al', lattice_constants=4, bravais_basis='fcc').repeat(10)
        del struct[0]
        neigh = struct.get_neighbors_by_distance(cutoff_radius=3)
        self.assertTrue(neigh.allow_ragged)
        self.assertTrue(isinstance(neigh.indices, list))
        indices = neigh.indices.copy()
        with self.assertRaises(ValueError):
            neigh.allow_ragged = 'yes'
        neigh.allow_ragged = False
        self.assertTrue(isinstance(neigh.indices, np.ndarray))
        self.assertGreater(len(neigh.indices[0]), len(indices[0]))
        with self.assertRaises(IndexError):
            struct.positions[neigh.indices] = struct.positions[neigh.indices]
        neigh.allow_ragged = True
        self.assertTrue(np.array_equal(neigh.indices[0], indices[0]))
        neigh = struct.get_neighbors(cutoff_radius=3, num_neighbors=None)
        self.assertFalse(neigh.allow_ragged)
        self.assertTrue(isinstance(neigh.indices, np.ndarray))

    def test_getter_and_ragged(self):
        struct = CrystalStructure(elements='Al', lattice_constants=4, bravais_basis='fcc').repeat(2)
        del struct[0]
        neigh = struct.get_neighbors_by_distance(cutoff_radius=3, mode='filled')
        vecs = neigh.filled.vecs
        distances = neigh.filled.distances
        indices = neigh.filled.indices
        self.assertTrue(np.array_equal(neigh.distances, distances))
        self.assertTrue(np.array_equal(neigh.indices, indices))
        self.assertTrue(np.array_equal(neigh.vecs, vecs))

    def test_get_neighborhood_single(self):
        struct = CrystalStructure(elements='Al', lattice_constants=4, bravais_basis='fcc')
        neigh = struct.get_neighborhood(np.random.random(3), cutoff_radius=3)
        distances = neigh.distances.copy()
        neigh.allow_ragged = False
        self.assertTrue(np.array_equal(neigh.distances, distances))
        neigh.allow_ragged = True
        self.assertTrue(np.array_equal(neigh.distances, distances))
        neigh.allow_ragged = False
        self.assertTrue(np.array_equal(neigh.distances, distances))

    def test_get_neighbors(self):
        struct = CrystalStructure(
            elements='Fe', lattice_constants=2.85, bravais_basis='bcc'
        ).repeat(10)
        cell = struct.cell.copy()
        cell += np.random.random((3,3))-0.5
        struct.positions += np.random.random((len(struct), 3))-0.5
        struct.set_cell(cell, scale_atoms=True)
        neigh = struct.get_neighbors()
        self.assertAlmostEqual(
            np.absolute(neigh.distances-np.linalg.norm(neigh.vecs, axis=-1)).max(), 0
        )
        myself = np.ones_like(neigh.indices)
        myself = myself*np.arange(len(myself))[:,np.newaxis]
        dist = struct.get_distances(myself.flatten(), neigh.indices.flatten(), mic=True)
        self.assertAlmostEqual(np.absolute(dist-neigh.distances.flatten()).max(), 0)
        vecs = struct.get_distances(
            myself.flatten(), neigh.indices.flatten(), mic=True, vector=True
        )
        self.assertAlmostEqual(np.absolute(vecs-neigh.vecs.reshape(-1, 3)).max(), 0)
        dist = struct.get_scaled_positions()
        dist = dist[:,np.newaxis,:]-dist[np.newaxis,:,:]
        dist -= np.rint(dist)
        dist = np.einsum('nmi,ij->nmj', dist, struct.cell)
        dist = np.linalg.norm(dist, axis=-1).flatten()
        dist = dist[dist>0]
        self.assertAlmostEqual(neigh.distances.min(), dist.min())

    def test_pbc_false(self):
        struct = CrystalStructure(
            elements='Fe', lattice_constants=2.85, bravais_basis='bcc'
        ).repeat(10)
        struct.pbc = False
        cell = struct.cell.copy()
        cell += np.random.random((3,3))-0.5
        struct.set_cell(cell, scale_atoms=True)
        neigh = struct.get_neighbors()
        self.assertAlmostEqual(
            np.absolute(neigh.distances-np.linalg.norm(neigh.vecs, axis=-1)).max(), 0
        )
        myself = np.ones_like(neigh.indices)
        myself = myself*np.arange(len(myself))[:,np.newaxis]
        dist = np.linalg.norm(
            struct.positions[myself]-struct.positions[neigh.indices], axis=-1
        )
        self.assertAlmostEqual(np.absolute(dist-neigh.distances).max(), 0)

    def test_fe_large(self):
        struct = CrystalStructure(
            elements='Fe', lattice_constants=2.85, bravais_basis='bcc'
        ).repeat(10)
        neigh = struct.get_neighbors()
        self.assertAlmostEqual(
            np.absolute(neigh.distances-np.linalg.norm(neigh.vecs, axis=-1)).max(), 0
        )
        self.assertAlmostEqual(neigh.vecs[neigh.shells==1].sum(), 0)
        self.assertAlmostEqual(neigh.vecs[0, neigh.shells[0]==1].sum(), 0)

    def test_fe_small(self):
        struct = CrystalStructure(elements='Fe', lattice_constants=2.85, bravais_basis='bcc')
        neigh = struct.get_neighbors()
        self.assertAlmostEqual(neigh.vecs[neigh.shells==1].sum(), 0)
        with self.assertRaises(ValueError):
            _ = struct.get_neighbors(num_neighbors=None)

    def test_al_large(self):
        struct = CrystalStructure(
            elements='Al', lattice_constants=4.04, bravais_basis='fcc'
        ).repeat(10)
        neigh = struct.get_neighbors()
        self.assertAlmostEqual(
            np.absolute(neigh.distances-np.linalg.norm(neigh.vecs, axis=-1)).max(), 0
        )
        self.assertAlmostEqual(neigh.vecs[neigh.shells==1].sum(), 0)
        self.assertAlmostEqual(neigh.vecs[0, neigh.shells[0]==1].sum(), 0)

    def test_al_small(self):
        struct = CrystalStructure(elements='Al', lattice_constants=4.04, bravais_basis='fcc')
        neigh = struct.get_neighbors()
        self.assertAlmostEqual(
            np.absolute(neigh.distances-np.linalg.norm(neigh.vecs, axis=-1)).max(), 0
        )
        self.assertAlmostEqual(neigh.vecs[neigh.shells==1].sum(), 0)
        with self.assertRaises(ValueError):
            struct.get_neighbors(num_neighbors=0)

    def test_wrapped_positions(self):
        structure = CrystalStructure(
            elements='Al', lattice_constants=4, bravais_basis='fcc'
        ).repeat(2)
        neigh = structure.get_neighbors()
        distances = neigh.distances
        new_positions = structure.positions+structure.cell.diagonal()*2
        self.assertFalse(
            np.all(np.isclose(distances, neigh.get_neighborhood(new_positions, num_neighbors=13).distances[:,1:]))
        )
        neigh.wrap_positions = True
        self.assertTrue(
            np.all(np.isclose(distances, neigh.get_neighborhood(new_positions, num_neighbors=13).distances[:,1:]))
        )

    def test_get_global_shells(self):
        structure = CrystalStructure(
            elements='Al', lattice_constants=4, bravais_basis='fcc'
        ).repeat(2)
        neigh = structure.get_neighbors()
        self.assertTrue(np.array_equal(neigh.shells, neigh.get_global_shells()))
        structure += Atoms(elements='C', positions=[[0, 0, 0.5*4]])
        neigh = structure.get_neighbors()
        self.assertFalse(np.array_equal(neigh.shells, neigh.get_global_shells()))
        structure = CrystalStructure(
            elements='Al', lattice_constants=4, bravais_basis='fcc'
        ).repeat(2)
        neigh = structure.get_neighbors()
        shells = neigh.get_global_shells()
        structure.positions += 0.01*(np.random.random((len(structure), 3))-0.5)
        structure.center_coordinates_in_unit_cell()
        neigh = structure.get_neighbors()
        self.assertTrue(
            np.array_equal(
                shells, neigh.get_global_shells(cluster_by_vecs=True, cluster_by_distances=True)
            )
        )
        neigh.reset_clusters()
        self.assertTrue(np.array_equal(shells, neigh.get_global_shells(cluster_by_vecs=True)))
        self.assertFalse(np.array_equal(shells, neigh.get_global_shells()))

    def test_get_local_shells(self):
        structure = CrystalStructure(
            elements='Al', lattice_constants=4, bravais_basis='fcc'
        ).repeat(2)
        neigh = structure.get_neighbors()
        shells = neigh.get_local_shells()
        structure.positions += 0.01*(np.random.random((len(structure), 3))-0.5)
        neigh = structure.get_neighbors()
        self.assertTrue(
            np.array_equal(
                shells, neigh.get_local_shells(cluster_by_vecs=True, cluster_by_distances=True)
            )
        )
        neigh.reset_clusters()
        self.assertTrue(np.array_equal(shells, neigh.get_local_shells(cluster_by_vecs=True)))
        self.assertFalse(np.array_equal(shells, neigh.get_local_shells()))

    def test_get_global_shells_ragged(self):
        structure = CrystalStructure(
            elements='Al', lattice_constants=4, bravais_basis='fcc'
        ).repeat(2)
        del structure[0]
        neigh = structure.get_neighbors(cutoff_radius=3.5, num_neighbors=None)
        self.assertEqual(np.sum(neigh.get_global_shells()==-1), 12)
        self.assertEqual(np.sum(neigh.get_global_shells(cluster_by_distances=True)==-1), 12)
        self.assertEqual(np.sum(neigh.get_global_shells(cluster_by_vecs=True)==-1), 12)
        self.assertEqual(
            np.sum(neigh.get_global_shells(cluster_by_distances=True, cluster_by_vecs=True)==-1), 12
        )
        neigh.allow_ragged = True
        self.assertEqual(np.sum([len(s)==11 for s in neigh.get_global_shells()]), 12)
        self.assertEqual(np.sum([len(s)==11 for s in neigh.get_global_shells(cluster_by_distances=True)]), 12)
        self.assertEqual(np.sum([len(s)==11 for s in neigh.get_global_shells(cluster_by_vecs=True)]), 12)
        self.assertEqual(np.sum([len(s)==11 for s in neigh.get_global_shells(cluster_by_distances=True, cluster_by_vecs=True)]), 12)

    def test_get_local_shells_ragged(self):
        structure = CrystalStructure(
            elements='Al', lattice_constants=4, bravais_basis='fcc'
        ).repeat(2)
        del structure[0]
        neigh = structure.get_neighbors(cutoff_radius=3.5, num_neighbors=None)
        self.assertEqual(np.sum(neigh.shells==-1), 12)
        self.assertEqual(np.sum(neigh.get_local_shells(cluster_by_distances=True)==-1), 12)
        self.assertEqual(np.sum(neigh.get_local_shells(cluster_by_vecs=True)==-1), 12)
        self.assertEqual(
            np.sum(neigh.get_local_shells(cluster_by_distances=True, cluster_by_vecs=True)==-1), 12
        )
        neigh = structure.get_neighbors(cutoff_radius=3.5, num_neighbors=None, mode='ragged')
        self.assertEqual(np.sum([len(s)==11 for s in neigh.shells]), 12)
        self.assertEqual(np.sum([len(s)==11 for s in neigh.get_local_shells(cluster_by_distances=True)]), 12)
        self.assertEqual(np.sum([len(s)==11 for s in neigh.get_local_shells(cluster_by_vecs=True)]), 12)
        self.assertEqual(np.sum([len(s)==11 for s in neigh.get_local_shells(cluster_by_distances=True, cluster_by_vecs=True)]), 12)

    def test_get_shells_flattened(self):
        structure = StructureFactory().ase.bulk('Al', cubic=True).repeat(2)
        del structure[0]
        r = structure.cell[0,0]*0.49
        neigh = structure.get_neighbors(cutoff_radius=r, num_neighbors=None, mode='flattened')
        self.assertEqual(len(np.unique(neigh.shells)), 1)
        self.assertEqual(len(neigh.shells), 360)
        self.assertEqual(len(np.unique(neigh.get_local_shells())), 1)
        self.assertEqual(len(neigh.get_local_shells()), 360)
        self.assertEqual(len(np.unique(neigh.get_global_shells())), 1)
        self.assertEqual(len(neigh.get_global_shells()), 360)
        neigh = structure.get_neighbors(cutoff_radius=r, num_neighbors=None)
        self.assertEqual(len(np.unique(neigh.flattened.shells)), 1)
        self.assertEqual(len(neigh.flattened.shells), 360)

    def test_get_distances_flattened(self):
        structure = StructureFactory().ase.bulk('Al', cubic=True).repeat(2)
        del structure[0]
        r = structure.cell[0,0]*0.49
        neigh = structure.get_neighbors(cutoff_radius=r, num_neighbors=None, mode='flattened')
        self.assertAlmostEqual(np.std(neigh.distances), 0)
        self.assertEqual(len(neigh.distances), 360)
        self.assertEqual(neigh.vecs.shape, (360, 3, ))

    def test_atom_numbers(self):
        structure = StructureFactory().ase.bulk('Al', cubic=True).repeat(2)
        del structure[0]
        r = structure.cell[0,0]*0.49
        neigh = structure.get_neighbors(cutoff_radius=r, num_neighbors=None, mode='filled')
        n = len(structure)
        self.assertEqual(neigh.atom_numbers.sum(), int(n*(n-1)/2*12))
        neigh = structure.get_neighbors(cutoff_radius=r, num_neighbors=None, mode='ragged')
        for i, (a, d) in enumerate(zip(neigh.atom_numbers, neigh.distances)):
            self.assertEqual(np.sum(a-len(d)*[i]), 0)
        neigh = structure.get_neighbors(cutoff_radius=r, num_neighbors=None, mode='flattened')
        labels, counts = np.unique(
            np.unique(neigh.atom_numbers, return_counts=True)[1], return_counts=True
        )
        self.assertEqual(labels.tolist(), [11, 12])
        self.assertEqual(counts.tolist(), [12, 19])

    def test_get_shell_matrix(self):
        structure = CrystalStructure(
            elements='Fe', lattice_constants=2.83, bravais_basis='bcc'
        ).repeat(2)
        structure[0] = 'Ni'
        neigh = structure.get_neighbors(num_neighbors=8)
        mat = neigh.get_shell_matrix()
        self.assertEqual(mat[0].sum(), 8*len(structure))
        mat = neigh.get_shell_matrix(chemical_pair=['Fe', 'Ni'])
        self.assertEqual(mat[0].sum(), 16)
        mat = neigh.get_shell_matrix(chemical_pair=['Ni', 'Ni'])
        self.assertEqual(mat[0].sum(), 0)

    def test_cluster_analysis(self):
        basis = CrystalStructure("Al", bravais_basis="fcc", lattice_constants=4.2).repeat(10)
        neigh = basis.get_neighbors(num_neighbors=100)
        key, counts = neigh.cluster_analysis(id_list=[0,1], return_cluster_sizes=True)
        self.assertTrue(np.array_equal(key[1], [0,1]))
        self.assertEqual(counts[0], 2)
        key, counts = neigh.cluster_analysis(
            id_list=[0,int(len(basis)/2)], return_cluster_sizes=True
        )
        self.assertTrue(np.array_equal(key[1], [0]))
        self.assertEqual(counts[0], 1)

    def test_get_bonds(self):
        basis = CrystalStructure("Al", bravais_basis="fcc", lattice_constants=4.2).repeat(5)
        neigh = basis.get_neighbors(num_neighbors=20)
        bonds = neigh.get_bonds()
        self.assertTrue(np.array_equal(np.sort(bonds[0]['Al'][0]),
                        np.sort(neigh.indices[0, neigh.shells[0]==1])))

    def test_find_neighbors_by_vector(self):
        basis = Atoms(symbols=2*["Fe"],
                      scaled_positions=[(0, 0, 0), (0.5, 0.5, 0.5)],
                      cell=np.identity(3),
                      pbc=True)
        neigh = basis.get_neighbors(num_neighbors=14)
        id_lst, dist = neigh.find_neighbors_by_vector([0, 0, 1],
                                                      return_deviation=True)
        self.assertEqual(len(np.unique(np.unique(id_lst, return_counts=True)[1])), 1)
        self.assertLess(np.linalg.norm(dist), 1.0e-4)
        id_lst = neigh.find_neighbors_by_vector([0, 0, 0])
        self.assertTrue(np.array_equal(id_lst, np.arange(len(basis))))

    def test_get_distances_arbitrary_array(self):
        basis = CrystalStructure("Al", bravais_basis="fcc", lattice_constants=4.2).repeat(3)
        neigh = basis.get_neighbors(cutoff_radius=3.5, num_neighbors=None)
        self.assertEqual(len(neigh.get_neighborhood(np.random.random(3), num_neighbors=12).indices), 12)
        self.assertEqual(
            len(neigh.get_neighborhood(np.random.random(3), num_neighbors=12).ragged.distances), 12
        )
        self.assertLessEqual(
            len(neigh.get_neighborhood(np.random.random(3), num_neighbors=12, cutoff_radius=3.5).ragged.vecs), 12
        )
        self.assertTrue(neigh.get_neighborhood(np.random.random((2,3)), num_neighbors=12).vecs.shape==(2,12,3))
        neigh = basis.get_neighbors(num_neighbors=50)
        self.assertTrue(neigh.get_neighborhood(np.random.random(3)).distances.shape==(50,))
        self.assertTrue(neigh.get_neighborhood(np.random.random((2,3))).indices.shape==(2,50))
        self.assertTrue(neigh.get_neighborhood(np.random.random((2,2,3))).vecs.shape==(2,2,50,3))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = neigh.get_neighborhood(np.random.random(3), num_neighbors=51)
            self.assertEqual(len(w), 1)
            _ = neigh.get_neighborhood(np.random.random(3), num_neighbors=51).distances
            self.assertEqual(len(w), 2)

    def test_repr(self):
        basis = CrystalStructure("Al", bravais_basis="fcc", lattice_constants=4.2).repeat(3)
        neigh = basis.get_neighbors(cutoff_radius=3.5, num_neighbors=None)
        self.assertTrue('each atom' in neigh.__repr__())

    def test_norm_order(self):
        a_0 = 2.8
        basis = CrystalStructure("Fe", bravais_basis="bcc", lattice_constants=a_0).repeat(10)
        neigh = basis.get_neighbors(num_neighbors=None, norm_order=np.inf, cutoff_radius=a_0+0.01)
        self.assertEqual(len(neigh.indices[0]), 34)
        with self.assertRaises(ValueError):
            neigh.norm_order = 3

    def test_chemical_symbols(self):
        basis = StructureFactory().ase_bulk('Fe', cubic=True)
        basis[0] = 'Ni'
        neigh = basis.get_neighbors(num_neighbors=1)
        self.assertEqual(neigh.chemical_symbols[0,0], 'Fe')
        self.assertEqual(neigh.chemical_symbols[1,0], 'Ni')
        vacancy = StructureFactory().ase_bulk('Fe', cubic=True).repeat(4)
        del vacancy[0]
        neigh = vacancy.get_neighbors(num_neighbors=None, cutoff_radius=3)
        self.assertEqual(neigh.chemical_symbols[0,-1], 'v')

    def test_steinhardt_parameters(self):
        neigh = StructureFactory().ase_bulk('Al').get_neighbors(num_neighbors=12)
        # values obtained with pyscal
        self.assertAlmostEqual(0, neigh.get_steinhardt_parameter(2)[0])
        self.assertAlmostEqual(0.19094065395649323, neigh.get_steinhardt_parameter(4)[0])
        self.assertAlmostEqual(0.5745242597140696, neigh.get_steinhardt_parameter(6)[0])
        neigh = StructureFactory().ase_bulk('Mg', a=1, c=np.sqrt(8/3)).get_neighbors(num_neighbors=12)
        self.assertAlmostEqual(0, neigh.get_steinhardt_parameter(2)[0])
        self.assertAlmostEqual(0.097222222, neigh.get_steinhardt_parameter(4)[0])
        self.assertAlmostEqual(0.484761685, neigh.get_steinhardt_parameter(6)[0])
        neigh = StructureFactory().ase_bulk('Fe').get_neighbors(num_neighbors=14)
        self.assertAlmostEqual(0.03636964837266537, neigh.get_steinhardt_parameter(4)[0])
        self.assertAlmostEqual(0.5106882308569508, neigh.get_steinhardt_parameter(6)[0])
        self.assertRaises(ValueError, neigh.get_steinhardt_parameter, 2, 2)

    def test_numbers_of_neighbors(self):
        basis = StructureFactory().ase.bulk('Al', cubic=True).repeat(2)
        del basis[0]
        neigh = basis.get_neighbors(num_neighbors=None, cutoff_radius=0.45*basis.cell[0,0])
        n, c = np.unique(neigh.numbers_of_neighbors, return_counts=True)
        self.assertEqual(n.tolist(), [11, 12])
        self.assertEqual(c.tolist(), [12, 19])

    def test_modes(self):
        basis = StructureFactory().ase.bulk('Al', cubic=True)
        neigh = basis.get_neighbors()
        self.assertTrue(neigh.mode=='filled')
        with self.assertRaises(KeyError):
            neigh = basis.get_neighbors(mode='random_key')

    def test_centrosymmetry(self):
        structure = StructureFactory().ase_bulk('Fe').repeat(4)
        cs = structure.get_neighbors(num_neighbors=8).centrosymmetry
        self.assertAlmostEqual(cs.max(), 0)
        self.assertAlmostEqual(cs.min(), 0)
        structure.positions += 0.01*(2*np.random.random(structure.positions.shape)-1)
        neigh = structure.get_neighbors(num_neighbors=8)
        self.assertGreater(neigh.centrosymmetry.min(), 0)
        self.assertTrue(
            np.allclose(
                neigh.centrosymmetry, structure.analyse.pyscal_centro_symmetry(num_neighbors=8)
            )
        )

    def test_get_all_pairs(self):
        structure = StructureFactory().ase_bulk('Fe').repeat(4)
        neigh = structure.get_neighbors(num_neighbors=8)
        for n in [2, 4, 6]:
            pairs = neigh._get_all_possible_pairs(n)
            self.assertEqual(
                (np.prod(np.arange(int(n/2))*2+1), int(n/2), 2),
                pairs.shape
            )
            for i in range(2**(n-2)):
                a = np.sort(np.random.choice(np.arange(n), 2, replace=False))
                self.assertEqual(
                    np.sum(np.all(a==pairs, axis=-1)), np.prod(np.arange(int((n-1)/2))*2+1)
                )
        self.assertEqual(
            np.ptp(np.unique(neigh._get_all_possible_pairs(6), return_counts=True)[1]), 0
        )

if __name__ == "__main__":
    unittest.main()
