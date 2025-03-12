# -*- coding: utf-8 -*-
import numpy as np
import itertools

np.set_printoptions(precision=3)

def loc_init(Size_area, Dist_TX_RX, Num_D2D, Num_Ch):
    # Generate random locations for D2D transmitters within the area
    tx_loc = Size_area * (np.random.rand(Num_D2D, 2) - 0.5)
    rx_loc = np.zeros((Num_D2D + 1, 2))

    for i in range(Num_D2D):
        temp_chan = Feasible_Loc_Init(tx_loc[i, :], Size_area, Dist_TX_RX)
        rx_loc[i, :] = temp_chan
 
    tx_loc_CUE = Size_area * (np.random.rand(Num_Ch, 2) - 0.5)
    return rx_loc, tx_loc, tx_loc_CUE

def Feasible_Loc_Init(Cur_loc, Size_area, Dist_TX_RX):
    temp_dist = 2 * Dist_TX_RX * (np.random.rand(1, 2) - 0.5)
    temp_chan = Cur_loc + temp_dist

    while (np.max(abs(temp_chan)) > Size_area / 2) | (np.linalg.norm(temp_dist) > Dist_TX_RX):
        temp_dist = 2 * Dist_TX_RX * (np.random.rand(1, 2) - 0.5)
        temp_chan = Cur_loc + temp_dist

    return temp_chan

def ch_gen(Size_area, D2D_dist, Num_D2D, Num_Ch, Num_samples, PL_alpha=38., PL_const=34.5):
    ch_w_fading = []
    rx_loc_mat = []
    tx_loc_mat = []
    CUE_loc_mat = []

    rx_loc, tx_loc, tx_loc_CUE = loc_init(Size_area, D2D_dist, Num_D2D, Num_Ch)

    for i in range(Num_samples):
        rx_loc, tx_loc, tx_loc_CUE = loc_init(Size_area, D2D_dist, Num_D2D, Num_Ch)

        ch_w_temp_band = []
        for j in range(Num_Ch):
            tx_loc_with_CUE = np.vstack((tx_loc, tx_loc_CUE[j]))
            dist_vec = rx_loc.reshape(Num_D2D + 1, 1, 2) - tx_loc_with_CUE
            dist_vec = np.linalg.norm(dist_vec, axis=2)
            dist_vec = np.maximum(dist_vec, 3)

            pu_ch_gain_db = - PL_const - PL_alpha * np.log10(dist_vec)
            pu_ch_gain = 10 ** (pu_ch_gain_db / 10)

            multi_fading = (
                0.5 * np.random.randn(Num_D2D + 1, Num_D2D + 1) ** 2 +
                0.5 * np.random.randn(Num_D2D + 1, Num_D2D + 1) ** 2
            )

            final_ch = np.maximum(pu_ch_gain * multi_fading, np.exp(-30))
            ch_w_temp_band.append(np.transpose(final_ch))

        ch_w_fading.append(ch_w_temp_band)
        rx_loc_mat.append(rx_loc)
        tx_loc_mat.append(tx_loc)
        CUE_loc_mat.append(tx_loc_CUE)

    return np.array(ch_w_fading), np.array(rx_loc_mat), np.array(tx_loc_mat), np.array(CUE_loc_mat)

def cal_RATE_one_sample_one_channel(channel, tx_power, noise):
    diag_ch = np.diag(channel)
    inter_ch = channel - np.diag(diag_ch)
    tot_ch = np.multiply(channel, np.expand_dims(tx_power, -1))
    int_ch = np.multiply(inter_ch, np.expand_dims(tx_power, -1))
    sig_ch = np.sum(tot_ch - int_ch, axis=1)
    int_ch = np.sum(int_ch, axis=1)
    SINR_val = np.divide(sig_ch, int_ch + noise)
    cap_val = np.log2(1.0 + SINR_val)
    return cap_val

def cal_CUE_INTER_one_sample_one_channel(channel, tx_power):
    diag_ch = np.diag(channel)
    inter_ch = channel - np.diag(diag_ch)
    int_ch = np.multiply(inter_ch, np.expand_dims(tx_power, -1))
    int_ch = np.sum(int_ch, axis=1)
    return int_ch

def cal_rate_NP(channel, tx_power_in, noise, DUE_thr, I_thr, P_c):
    num_sample = channel.shape[0]
    num_channel = channel.shape[1]
    num_D2D_user = channel.shape[2] - 1

    tot_SE = 0
    tot_EE = 0
    DUE_violation = 0
    CUE_violation = 0

    tx_power = np.hstack((tx_power_in, 0 * np.ones((tx_power_in.shape[0], 1, num_channel))))

    for i in range(num_sample):
        cur_cap = 0
        DUE_mask = 1
        CUE_mask = 1

        for j in range(num_channel):
            cur_ch = channel[i][j]
            cur_power = tx_power[i, :, j]
            cur_power = np.array([cur_power])

            cur_ch_cap = cal_RATE_one_sample_one_channel(cur_ch, cur_power, noise)
            inter = cal_CUE_INTER_one_sample_one_channel(cur_ch, cur_power)

            cur_cap = cur_cap + cur_ch_cap[0]
            CUE_mask = CUE_mask * (inter[0, num_D2D_user] <= I_thr)

        for j in range(num_D2D_user):
            DUE_mask = DUE_mask * (cur_cap[j] >= DUE_thr)

        D2D_SE_sum = np.sum(cur_cap[:-1]) * CUE_mask * DUE_mask
        D2D_EE_sum = np.sum(cur_cap[:-1] / (np.sum(tx_power_in[i], axis=1) + P_c)) * CUE_mask * DUE_mask

        if CUE_mask == 0:
            CUE_violation = CUE_violation + 1

        if DUE_mask == 0:
            DUE_violation = DUE_violation + 1

        tot_SE = tot_SE + D2D_SE_sum
        tot_EE = tot_EE + D2D_EE_sum

    tot_SE = tot_SE / num_D2D_user / num_sample
    tot_EE = tot_EE / num_D2D_user / num_sample

    PRO_DUE_vio = DUE_violation / (num_sample)
    PRO_CUE_vio = CUE_violation / (num_sample)

    return tot_SE, tot_EE, PRO_CUE_vio, PRO_DUE_vio

def all_possible_tx_power(num_channel, num_user, granuty):
    items = [np.arange(granuty)] * (num_user * num_channel)
    temp_power = list(itertools.product(*items))
    temp_power = np.reshape(temp_power, (-1, num_user, num_channel))
    power_check = np.sum(temp_power, axis=2)
    flag = (power_check / (granuty - 1) <= 1).astype(int)
    flag = (np.sum(flag, axis=1) / num_user == 1).astype(int)
    flag = np.reshape(flag, (-1, 1))
    temp_power_1 = np.reshape(temp_power, (-1, num_user * num_channel))
    temp_power = temp_power_1 * flag
    power = np.reshape(temp_power, (-1, num_user, num_channel)) / (granuty - 1)
    power_mat = []

    for i in range(power.shape[0]):
        sum_val = np.sum(power[i])
        if sum_val != 0:
            power_mat.append(power[i])

    return np.array(power_mat)

def optimal_power_w_chan(channel, tx_max, noise, DUE_thr, I_thr, P_c, tx_power_set, opt="SE"):
    num_channel = channel.shape[1]
    num_D2D_user = channel.shape[2] - 1
    num_samples = channel.shape[0]

    tot_SE = 0
    power_mat_SE = []
    chan_infea_mat = []

    for i in range(num_samples):
        cur_cap = 0
        DUE_mask = 1
        CUE_mask = 1

        tx_power = tx_max * np.hstack((tx_power_set, 0 * np.ones((tx_power_set.shape[0], 1, num_channel))))

        for j in range(num_channel):
            cur_ch = channel[i][j]
            cur_ch_cap = cal_RATE_one_sample_one_channel(cur_ch, tx_power[:, :, j], noise)
            inter = cal_CUE_INTER_one_sample_one_channel(cur_ch, tx_power[:, :, j])
            cur_cap += cur_ch_cap
            CUE_mask *= (inter[:, num_D2D_user] < I_thr)

        for j in range(num_D2D_user):
            DUE_mask *= (cur_cap[:, j] > DUE_thr)

        CUE_mask = np.expand_dims(CUE_mask, -1)
        DUE_mask = np.expand_dims(DUE_mask, -1)

        sum_D2D_SE_temp = np.expand_dims(np.sum(cur_cap[:, :-1], axis=1), -1)
        sum_D2D_EE_temp = np.expand_dims(np.sum(cur_cap[:, :-1] / (np.sum(tx_power[:, :-1, :], axis=2) + P_c), axis=1), -1)

        D2D_SE_sum = sum_D2D_SE_temp
        D2D_EE_sum = sum_D2D_EE_temp

        if opt == "SE":
            arg_max_val = np.argmax(D2D_SE_sum)
        else:
            arg_max_val = np.argmax(D2D_EE_sum)

        max_SE = np.max(D2D_SE_sum)
        found_tx_val = tx_power[arg_max_val][:-1]
        power_mat_SE.append(found_tx_val)

        if max_SE == 0:
            chan_infea_mat.append(channel[i])

    power_mat_SE = np.array(power_mat_SE)
    tot_SE, tot_EE, PRO_CUE_vio, PRO_DUE_vio = cal_rate_NP(channel, power_mat_SE, noise, DUE_thr, I_thr, P_c)

    return tot_SE, tot_EE, PRO_CUE_vio, PRO_DUE_vio, np.array(chan_infea_mat), np.array(power_mat_SE), np.array(channel)

import json
import numpy as np

def generate_data(Num_sample, Size_area, Num_user, Num_channel, mode="SE"):
    """
    Generate synthetic channel data for D2D and CUE communication links.

    Parameters:
    - Num_sample: Number of samples to generate.
    - Size_area: Size of the simulation area.
    - Num_user: Number of users.
    - Num_channel: Number of channels.
    - mode: Optimization mode ("SE" for Spectral Efficiency or "EE" for Energy Efficiency).

    Returns:
    - A dictionary containing the generated data.
    """

    Num_channel = int(Num_channel)
    Size_area = int(Size_area)
    Num_user = int(Num_user)
    Num_sample = int(Num_sample)

    # Default simulation settings
    D2D_dist = 15  # Maximum distance between D2D transmitters and receivers
    tx_max = 100  # Maximum transmission power
    P_c = 5 * 10**2.0  # Constant power consumption
    BW = 1e7  # Bandwidth
    noise = BW * 10**-17.4  # Noise level
    DUE_thr = 4.0  # D2D user threshold
    I_thr = 10**(-55.0 / 10)  # Interference threshold for CUE

    # Generate channel data
    ch_mat, rx_mat, tx_mat, CUE_mat = ch_gen(Size_area, D2D_dist, Num_user, Num_channel, Num_sample)
    ch_mat_log = np.log(ch_mat)
    chan_avg = np.mean(ch_mat_log)
    chan_std = np.std(ch_mat_log)

    # Generate all possible transmission power configurations
    Num_power_level = 100
    tx_power_set = all_possible_tx_power(Num_channel, Num_user, Num_power_level - 1)

    # Calculate optimal power settings
    SE_OPT, EE_OPT, CUE_vio_OPT, DUE_vio_OPT, INF_CHAN_MAT, PW_VEC, CHAN_VEC = optimal_power_w_chan(
        ch_mat, tx_max, noise, DUE_thr, I_thr, P_c, tx_power_set, opt=mode
    ) 

    # Prepare data for JSON serialization
    samples_data = []  
    for i in range(PW_VEC.shape[0]):
        chan_revised = (np.log(ch_mat[i, 0, :, :]) - chan_avg) / chan_std * 100

        sample_record = {
            "sample_index": i,
            "tx_max": tx_max,
            "noise": noise,
            "DUE_thr": DUE_thr, 
            "I_thr": I_thr,
            "P_c": P_c,
            "critera": mode,
            "chan_mat_values": ch_mat[i, 0, :, :].tolist(),
            "pw_vec_values": PW_VEC[i].tolist(),
            "chan_revised_values": chan_revised.tolist(),
            "query_text": f'If A is {", ".join(f"{x:0.0f}" for x in chan_revised.flatten())}, then B is {", ".join(f"{x:0.0f}" for x in PW_VEC[i].flatten())}.\n'
        }
        samples_data.append(sample_record)
    
    filename = mode + "_dataset.json"

    # Save the data to a JSON file
    with open(filename, 'w') as json_file:
        json.dump(samples_data, json_file, indent=4)

    return samples_data
