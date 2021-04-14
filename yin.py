#%%

import numpy as np 
from scipy.io.wavfile import read
import matplotlib.pyplot as plt
import warnings
import time


def diff(x: np.array, 
         tau_max: int, 
         start: int,
         w: int) -> np.array:
    """
    B. Step 2: Difference Function. Calculate the difference function of one frame
    in Eq (6). 
    This is a sequential implementation, to be optimised

    Args:
        x (np.array): The input signal
        tau_max (int): An upper limit for the lag parameter tau (exclusive)
        start (int): The starting index in the signal
        w (int): integration window size

    Returns:
        np.array: A list of results calculated with different values of tau
    """
    
    # w < len(x)
    # tau_max - 1 + start + max_j (w) < len(x) => tau_max < len(x) + 1 - start - w
    assert tau_max < len(x) + 1 - start - w
    difference: np.array = np.zeros((tau_max, )) # allocate the difference function outputs
    x = np.array(x, dtype=np.int32)
    for t in range(tau_max):
        df = 0
        start_j = x[start + 1: start + w + 1]
        start_j_t = x[start + 1 + t: start + w + 1 + t]
        # for j in range(1, w + 1): 
        #     df += (x[start + j] - x[start + j + t]) ** 2
        df = ((start_j - start_j_t) ** 2).sum()
        difference[t] = df
    
    return np.array(difference, dtype=np.float64)

def cmndiff(difference: np.array) -> np.array:
    """C. Step 3: Cumulative Mean Normalized Difference Function. Calculate the cmndiff of 
    one frame in Eq (8)

    Args:
        difference (np.array): the difference function calculated from diff

    Returns:
        np.array: a list of results
    """
    
    # add a 0 at the beginning to make the index align 
    diff_cumulative = difference.cumsum()
    diff_zero_tau = 1
    diff_positive_tau = difference[1:] / ((1 / np.array([i for i in range(1, len(difference))])) * difference.cumsum()[1:])
    
    return np.concatenate((np.array([diff_zero_tau]), diff_positive_tau))

def abs_threshold(cmndiff: np.array, threshold: float = 0.1) -> int:
    """D. Step 4: Absolute Threshold. Choose an absolute threshold and take the minimum value of tau
    that gives the minimum of d' deeper than that threshold. If none is found, choose the global minimum instead.
    A minimum of d' deeper than the threshold is equivalent to choosing one threshold and find the minimum tau
    that gives the value that falls below this new threshold. So we will use threashold as (the threshold stated in paper - d')

    Args:
        cmndiff (np.array): The cumulative mean normalized difference function calculated from cmndiff.
        threshold (float, optional): The threshold set to prevent "octave error". Defaults to 0.1.

    Returns:
        int: returns the value of tau chosen
    """
    tau_global_mean = len(cmndiff) - 1
    for t in range(len(cmndiff)):
        if cmndiff[t] <= threshold:
            return t # return the minimum value of tau that gives the value below the threshold
        
        if cmndiff[t] < cmndiff[tau_global_mean]:
            tau_global_mean = t
    
    return tau_global_mean

def parabolic_interpolation(tau_selected: int, cmndiff: np.array):
    """E. Step 5: Parabolic Interpolation. Perform parabolic interpolation on the difference function calculated.

    Args:
        tau_selected (int): the tau value selected for minimum difference
        cmndiff (np.array): the result calculated from cmndiff function.
    """
    assert tau_selected > 0 and tau_selected < len(cmndiff) - 1
    ordinates = np.array(cmndiff[tau_selected - 1: tau_selected + 2]) # get the y coordinates
    abscissae = np.array([tau_selected - 1, tau_selected, tau_selected + 1])
    
    coeffs = np.polyfit(abscissae, ordinates, 2)
    p = np.poly1d(coeffs)
    
    critical_pts = p.deriv().r
    real_critical_pts = critical_pts[critical_pts.imag==0].real
    critical_pt = real_critical_pts[0] # take the critical point check if it's between the first and third points
    # if it is, then use it as the result, if not (should be impossible, implicitly)
    
    if critical_pt > tau_selected - 1 and real_critical_pts < tau_selected + 1:
        return critical_pt
    else:
        return min(abscissae, key=lambda abscissa: cmndiff[abscissa]) # return the minimum of the three points
     

# def best_local_estimate(w: int, cmndiff: np.array) -> int:
#     """F. Step 6: Best Local Estimate. Proceed with step 6 and run the abs_threshold algorithm on different 
#     time intervals to obtain the optimal result

#     Args:
#         w (int): the integration window, representing the largest estimated period possible
#         cmndiff (np.array): the cmndiff results calculated from previous step

#     Returns:
#         int: returns the optimal tau value
#     """
#   This part will be left out because we are trying to obtain real-time performance and this step
#   is very time-consuming. I will trade that 0.2% accuracy for a faster algorithm :)
    
    

#%%
def yin_algorithm_one_block(x: np.array, 
                            tau_max: int, 
                            start: int,
                            w: int,
                            threshold = 0.1, 
                            plot = False) -> int:
    """yin algorithm for one block

    Args:
        x (np.array): the input signal
        tau_max (int): the maximum frequency to be estimated, for step 2
        start (int): the starting index in the signal
        w (int): the integration window size
        threshold (float, optional): the threshold to select tau. Defaults to 0.1.

    Returns:
        int: returns the calculated estimated frequency
    """
    # start_time = time.time()
    diff_signal = diff(x, tau_max, start, w)
    # end_time = time.time()
    # print(f'execution time of diff: {end_time - start_time}')
    
    # start_time = time.time()
    cmndiff_signal = cmndiff(diff_signal)
    # end_time = time.time()
    # print(f'execution time of cmndiff: {end_time - start_time}')
    
    # start_time = time.time()
    tau = abs_threshold(cmndiff_signal, threshold=threshold)
    # end_time = time.time()
    # print(f'execution time of abs_threshold: {end_time - start_time}')

    tau_interpolated = parabolic_interpolation(tau, cmndiff_signal)
    tau_interpolated = parabolic_interpolation(tau, cmndiff_signal)
    detected_freq = 1 / (tau_interpolated / fs)
    
    if (plot):
        plt.figure(1)
        plt.plot(data)
        plt.title(f'The Input Signal from Sample {start} to Sample {start + w}')
        plt.figure(2)
        plt.title(f'The Difference Function')
        plt.plot(diff_signal)
        plt.figure(3)
        plt.title(f'The Cumulative Mean Normalized Difference Function')
        plt.plot(cmndiff_signal)
    return detected_freq
    

#%%


# test on flute sound
fs, data = read('audio/flute-alto-C-corrected.wav')
start_time = time.time()
detected_freq = yin_algorithm_one_block(data, 3000, 10000, 4410)
end_time = time.time()
print(f'------------------------------------------- TEST ON AUDIO FILES ----------------------------')
print(f'detected frequency: {detected_freq}')
print(f'execution time: {end_time - start_time}')

#%%

# test on sine waves
f1 = 400
f2 = 800
f3 = 1200
x = np.arange(100000)
data = np.sin(2 * np.pi * f1 * x / fs) + np.sin(2 * np.pi * f2 * x / fs) + np.sin(2 * np.pi * f3 * x / fs)
start_time = time.time()
detected_freq = yin_algorithm_one_block(data, 3000, 10000, 4410)
end_time = time.time()
print(f'------------------------------------------- TEST ON SINE WAVES ----------------------------')
print(f'detected frequency: {detected_freq}')
print(f'execution time: {end_time - start_time}')

# %%
