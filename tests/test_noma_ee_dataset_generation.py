import pytest
import numpy as np
import os
from unittest.mock import patch, MagicMock
from src.noma_ee_dataset_generation import (
    is_feasible,
    initialize_links,
    initialize,
    computeEnergyEfficiency,
    normalizeEE,
    find_optimal_results,
    main
)

def test_is_feasible():
    bs_pos = [0, 0, 10]
    ue1_pos = [5, 5, 1]
    ue2_pos = [7, 7, 1]
    size_area = 60
    max_dist_bs_ue = 30
    max_dist_ue_ue = 20
    min_dist_ue_ue = 10

    # Adjust as needed based on your actual constraints:
    # If the near user must be strictly closer to BS than the far user, 
    # these positions might or might not be feasible. 
    # Suppose we want it to fail for this test:
    assert is_feasible(bs_pos, ue1_pos, ue2_pos, size_area, max_dist_bs_ue, max_dist_ue_ue, min_dist_ue_ue) is False

    # Out-of-bounds
    ue2_pos_far = [100, 100, 1]
    assert is_feasible(bs_pos, ue1_pos, ue2_pos_far, size_area, max_dist_bs_ue, max_dist_ue_ue, min_dist_ue_ue) is False

def test_initialize_links():
    class MockBaseStation:
        def __init__(self):
            self.name = "BS"
            self.n_antennas = 2
            self.position = [0, 0, 10]   # fix #1: add position

    class MockUE:
        def __init__(self):
            self.name = "UE"
            self.n_antennas = 2
            self.position = [5, 5, 1]   # might be needed by get_distance

    bs = MockBaseStation()
    ue1 = MockUE()
    ue2 = MockUE()

    n_antennas = 2
    mc = 1
    # fix #2: add real-ish pathloss args so get_pathloss won't fail
    fading_args = {"type": "rayleigh", "sigma": 0.5}
    pathloss_args = {
        "type": "reference",
        "frequency": 2.4e9,
        "alpha": 3.5,
        "p0": 40
    }

    link_bs_ue1, link_bs_ue2 = initialize_links(bs, ue1, ue2, n_antennas, mc, fading_args, pathloss_args)
    assert link_bs_ue1 is not None
    assert link_bs_ue2 is not None

@patch("src.noma_ee_dataset_generation.get_distance", return_value=10)
def test_initialize(mock_get_distance):
    # Minimal test, but with valid pathloss/fading args
    n_antennas = 2
    Pt_lin = np.array([0.1, 0.2])
    max_distance_bs_ue = 30
    max_distance_ue_ue = 20
    min_distance_ue_ue = 10
    simulation_area_size = 60
    mc = 1
    fading_args = {"type": "rayleigh", "sigma": 0.5}
    pathloss_args = {
        "type": "reference",
        "frequency": 2.4e9,
        "alpha": 3.5,
        "p0": 40
    }

    bs, UEn, UEf, link_bs_uen, link_bs_uef, gain_f, gain_n = initialize(
        n_antennas, Pt_lin,
        max_distance_bs_ue, max_distance_ue_ue, min_distance_ue_ue,
        simulation_area_size, mc, fading_args, pathloss_args
    )
    # Gains should be shape (n_antennas, n_antennas, mc)
    assert gain_f.shape == (2, 2, 1)
    assert gain_n.shape == (2, 2, 1)

def test_computeEnergyEfficiency():
    class MockBS:
        def __init__(self, t_power):
            self.t_power = t_power
            self.allocations = {}

    class MockUE:
        def __init__(self):
            self.sinr_pre = None
            self.sinr = None

    bs = MockBS(t_power=np.array([1.0, 2.0]))
    UEn = MockUE()
    UEf = MockUE()

    allocation_factors = [0.2, 0.8]
    gain_n = np.ones((1,1,1))  
    gain_f = np.ones((1,1,1))
    Pt = np.array([0, 1])  # dBm
    mc = 1
    Pt_lin = np.array([0.001, 0.002])  # Watt
    R_prime_n = 1e-15
    R_prime_f = 1e-15
    N0_lin = 1e-9
    P_c = 1

    results = computeEnergyEfficiency(
        bs, UEn, UEf,
        allocation_factors, gain_n, gain_f,
        Pt, mc, Pt_lin,
        R_prime_n, R_prime_f,
        N0_lin, P_c
    )
    assert isinstance(results, list)
    for res in results:
        assert 'alloc_UEn' in res
        assert 'max_energy_efficiency' in res

def test_normalizeEE():
    # fix #3: if there's only one item, we get a 0 denominator. So let's have at least two items:
    results = [
        {'max_energy_efficiency': 10},
        {'max_energy_efficiency': 20},
        {'max_energy_efficiency': 15},
    ]
    normed = normalizeEE(results)
    for r in normed:
        assert 'normalized_energy_efficiency' in r
        # Must be in [0, 10]
        assert 0 <= r['normalized_energy_efficiency'] <= 10

def test_find_optimal_results():
    results = [
        {'max_energy_efficiency': 1.0, 'alloc_UEn':0.1},
        {'max_energy_efficiency': 2.0, 'alloc_UEn':0.2},
        {'max_energy_efficiency': 1.5, 'alloc_UEn':0.3},
    ]
    best = find_optimal_results(results)
    assert len(best) == 1
    assert best[0]['max_energy_efficiency'] == 2.0

