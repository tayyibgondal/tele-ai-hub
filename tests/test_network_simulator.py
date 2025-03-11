import pytest
import numpy as np

# Adjust this import path if network_simulator.py is in a different location.
# For example, if it's inside `src/`, do: from src.network_simulator import ...
from src.network_simulator import (
    loc_init,
    Feasible_Loc_Init,
    ch_gen,
    cal_RATE_one_sample_one_channel,
    cal_CUE_INTER_one_sample_one_channel,
    cal_rate_NP,
    all_possible_tx_power,
    optimal_power_w_chan,
    generate_data
)

def test_loc_init():
    """Test loc_init() returns correct shapes."""
    Size_area = 100
    Dist_TX_RX = 10
    Num_D2D = 2
    Num_Ch = 1

    rx_loc, tx_loc, tx_loc_CUE = loc_init(Size_area, Dist_TX_RX, Num_D2D, Num_Ch)
    # rx_loc should have shape (Num_D2D+1, 2)
    assert rx_loc.shape == (Num_D2D + 1, 2)
    # tx_loc should have shape (Num_D2D, 2)
    assert tx_loc.shape == (Num_D2D, 2)
    # tx_loc_CUE should have shape (Num_Ch, 2)
    assert tx_loc_CUE.shape == (Num_Ch, 2)

def test_Feasible_Loc_Init():
    """Test Feasible_Loc_Init() ensures the location is within allowed distance and area."""
    Cur_loc = np.array([0.0, 0.0])
    Size_area = 10
    Dist_TX_RX = 3
    loc = Feasible_Loc_Init(Cur_loc, Size_area, Dist_TX_RX)
    # Must be within the half-area boundary
    assert abs(loc[0, 0]) <= Size_area / 2
    assert abs(loc[0, 1]) <= Size_area / 2
    # Must not exceed Dist_TX_RX from Cur_loc
    distance = np.linalg.norm(loc - Cur_loc)
    assert distance <= Dist_TX_RX

def test_ch_gen():
    """Smoke test for ch_gen() ensuring shapes are correct."""
    Size_area = 100
    D2D_dist = 10
    Num_D2D = 2
    Num_Ch = 2
    Num_samples = 5

    ch_w_fading, rx_loc_mat, tx_loc_mat, CUE_loc_mat = ch_gen(Size_area, D2D_dist, Num_D2D, Num_Ch, Num_samples)

    # ch_w_fading shape:
    #   (Num_samples, Num_Ch, (Num_D2D+1), (Num_D2D+1))
    assert ch_w_fading.shape == (Num_samples, Num_Ch, Num_D2D + 1, Num_D2D + 1)
    # rx_loc_mat shape: (Num_samples, Num_D2D+1, 2)
    assert rx_loc_mat.shape == (Num_samples, Num_D2D + 1, 2)
    # tx_loc_mat shape: (Num_samples, Num_D2D, 2)
    assert tx_loc_mat.shape == (Num_samples, Num_D2D, 2)
    # CUE_loc_mat shape: (Num_samples, Num_Ch, 2)
    assert CUE_loc_mat.shape == (Num_samples, Num_Ch, 2)

def test_cal_RATE_one_sample_one_channel():
    """Check that cal_RATE_one_sample_one_channel returns capacity values with correct shape."""
    # channel is a square matrix, e.g., 3x3 for 2 D2D users + 1
    channel = np.array([
        [10, 0.5, 0.2],
        [0.5, 10, 0.3],
        [0.2, 0.3, 10]
    ])
    tx_power = np.array([[2, 2, 2]])  # shape (1, 3)
    noise = 1e-9

    capacity = cal_RATE_one_sample_one_channel(channel, tx_power, noise)
    # capacity should be shape (3,) for 3 users
    assert capacity.shape == (1, 3)

def test_cal_CUE_INTER_one_sample_one_channel():
    """Ensure interference calculation returns correct shape."""
    channel = np.array([
        [10, 0.5, 0.2],
        [0.5, 10, 0.3],
        [0.2, 0.3, 10]
    ])
    tx_power = np.array([[2, 2, 2]])  # shape (1, 3)
    interference = cal_CUE_INTER_one_sample_one_channel(channel, tx_power)
    # interference should be shape (3,) for 3 users
    assert interference.shape == (1, 3)

def test_cal_rate_NP():
    """Basic check on cal_rate_NP() returns the correct values and shapes."""
    # Suppose we have 1 sample, 1 channel, 2 D2D users -> total 3
    # channel shape: (num_sample, num_channel, num_users, num_users)
    channel = np.array([[
        [[10, 0.5, 0.1],
         [0.5, 10, 0.2],
         [0.1, 0.2, 10]]
    ]])
    # tx_power_in shape: (num_sample, num_user, num_channel)
    tx_power_in = np.array([
        [[1],
         [1]]
    ])
    noise = 1e-9
    DUE_thr = 2
    I_thr = 1  # interference threshold
    P_c = 1

    tot_SE, tot_EE, PRO_CUE_vio, PRO_DUE_vio = cal_rate_NP(channel, tx_power_in, noise, DUE_thr, I_thr, P_c)
    # Just check they return floats
    assert isinstance(tot_SE, float)
    assert isinstance(tot_EE, float)
    assert isinstance(PRO_CUE_vio, float)
    assert isinstance(PRO_DUE_vio, float)

def test_all_possible_tx_power():
    """Check that all_possible_tx_power() returns correct shape and not empty for small inputs."""
    num_channel = 2
    num_user = 2
    granuty = 3  # small
    power_mat = all_possible_tx_power(num_channel, num_user, granuty)
    # power_mat shape: (some_number, num_user, num_channel)
    assert len(power_mat.shape) == 3
    assert power_mat.shape[1] == num_user
    assert power_mat.shape[2] == num_channel
    # Should not be empty if granuty > 1
    assert power_mat.size > 0

