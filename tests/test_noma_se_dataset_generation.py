import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.noma_se_dataset_generation import (
    is_feasible,
    initialize_links,
    initialize,
    computeRates,
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

    # Suppose we want these positions to be infeasible. 
    # If your actual logic demands otherwise, adjust accordingly.
    assert is_feasible(
        bs_pos, ue1_pos, ue2_pos, 
        size_area, max_dist_bs_ue, max_dist_ue_ue, min_dist_ue_ue
    ) is False

    # Out-of-bounds scenario
    ue2_pos_far = [100, 100, 1]
    assert is_feasible(
        bs_pos, ue1_pos, ue2_pos_far, 
        size_area, max_dist_bs_ue, max_dist_ue_ue, min_dist_ue_ue
    ) is False

def test_initialize_links():
    class MockBaseStation:
        def __init__(self):
            self.name = "BS"
            self.n_antennas = 2
            self.position = [0, 0, 10]

    class MockUE:
        def __init__(self):
            self.name = "UE"
            self.n_antennas = 2
            self.position = [5, 5, 1]

    bs = MockBaseStation()
    ue1 = MockUE()
    ue2 = MockUE()

    n_antennas = 2
    mc = 1
    # Provide real-ish pathloss/fading args
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

@patch("src.noma_se_dataset_generation.get_distance", return_value=10)
def test_initialize(mock_get_distance):
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

    # The returned values should match the function’s signature
    bs, UEn, UEf, link_bs_uen, link_bs_uef, gain_f, gain_n = initialize(
        n_antennas,
        Pt_lin,
        max_distance_bs_ue,
        max_distance_ue_ue,
        min_distance_ue_ue,
        simulation_area_size,
        mc,
        fading_args,
        pathloss_args
    )
    # Gains should be shape (n_antennas, n_antennas, mc)
    assert gain_f.shape == (2, 2, 1)
    assert gain_n.shape == (2, 2, 1)

def test_computeRates():
    """
    Test the computeRates function, ensuring it returns a list of results 
    and each result has the expected keys.
    """
    class MockBS:
        def __init__(self, t_power):
            self.t_power = t_power
            self.allocations = {}

    class MockUE:
        # UEn and UEf
        pass

    bs = MockBS(t_power=np.array([1.0, 2.0]))  # Example power array
    UEn = MockUE()
    UEf = MockUE()

    allocation_factors = [0.2, 0.8]
    gain_n = np.ones((1,1,1))  # shape matches (n_antennas, n_antennas, mc)
    gain_f = np.ones((1,1,1))
    Pt = np.array([0, 1])  # in dBm
    mc = 1
    Pt_lin = np.array([0.001, 0.002])  # in Watts
    R_prime_n = 1.0
    R_prime_f = 1.0
    N0_lin = 1e-9
    P_c = 1

    results = computeRates(
        bs, UEn, UEf,
        allocation_factors,
        gain_n, gain_f,
        Pt, mc, Pt_lin,
        R_prime_n, R_prime_f,
        N0_lin, P_c
    )
    # Expect a list of dictionaries
    assert isinstance(results, list)
    if results:
        for r in results:
            assert 'alloc_UEn' in r
            assert 'operational_power' in r
            # If QoS not met, the entry might be omitted or partial. Adjust as needed.

def test_find_optimal_results():
    """
    Test that find_optimal_results picks the entry with the minimal SE_difference
    (or max_spectral_efficiency) depending on your code logic.
    """
    results = [
        {'SE_difference': 0.1, 'max_spectral_efficiency': 5},
        {'SE_difference': 0.05, 'max_spectral_efficiency': 3},
        {'SE_difference': 0.2, 'max_spectral_efficiency': 7},
    ]
    best = find_optimal_results(results)
    # By default, your code picks the entry with MINIMUM SE_difference
    assert len(best) == 1
    # The second entry has the smallest SE_difference of 0.05
    assert best[0]['SE_difference'] == 0.05
