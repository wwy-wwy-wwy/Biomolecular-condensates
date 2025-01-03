import numpy as np
import pymc3 as pm
import arviz as az
import seaborn as sns


def set_model(data,quantization,aged_time='other'):
    
    '''
    This function read in the experiment data, and generate an AR1 model based on it.
    
    input: 
    -----------------
    data: ndarray, 
    quantization: float
    aged_time: string
    
    return: 
    -----------------
    AR1 model
    
    '''

    # Bayesian parameter estimation with pymc3
    ar1_model = pm.Model()

    with ar1_model:
        observed_mean = np.mean(data)
        if aged_time=='2h':
            decay_time = pm.Exponential("decay_time", lam=1) 
        else:
            decay_time = pm.Uniform("decay_time", lower=0,upper=1.5*len(data)) 
        # we average over 25 pixels
        camera_noise_std = np.sqrt(data)/5
        # We use simulation noise parameter to infer
        if aged_time=='simulated':
             camera_noise_std = 1
        
        # stationarity is the phi in our model
        stationarity = pm.Deterministic("stationarity", np.exp(-1/decay_time))

        # 'precision' is 1/(variance of innovation). As we use normalized data, this term has to be divided by intensity_mean squared
        precision_AR1 = pm.Uniform("precision", lower = 0 , upper = 10) 
    
        true = pm.AR1("y", k=stationarity, tau_e=precision_AR1, shape=len(data))
        likelihood = pm.Normal("likelihood", mu=(true + observed_mean), sigma=camera_noise_std, observed=data)
        

    return ar1_model
               


def set_double_precision_model(data, quantization, aged_time='other'):
    '''
    This function read in the experiment data, and generate a two-timescale AR1 model based on it.
    
    input: 
    -----------------
    data: ndarray, 
    quantization: float
    aged_time: string
    
    return: 
    -----------------
    two-timescale AR1 model
    
    '''
    
    ar1_two_timescales_model = pm.Model()

    with ar1_two_timescales_model:
        decay_time1 = pm.Uniform("decay_time_1", lower=0, upper=500) 
        decay_time_split = pm.Uniform("decay_time_split",lower = 0, upper = 500)
        decay_time2 = pm.Deterministic("decay_time_2",decay_time1 + decay_time_split)
    
        stationarity1 = pm.Deterministic("stationarity_1", np.exp(-1/decay_time1))
        stationarity2 = pm.Deterministic("stationarity_2", np.exp(-1/decay_time2))

        # 'precision' is 1/(variance of innovation). As we use normalized data, this term has to be divided by intensity_mean squared
        precision_1 = pm.Uniform("precision_1", lower = 0 , upper = 10) 
        precision_2 = pm.Uniform("precision_2", lower = 0 , upper = 10) 
    
        # process mean: use observed mean since process is assumed to be stationary, and there should be the mean of the observed data
        observed_mean = np.mean(data)
        
        camera_noise_std = np.sqrt(data)/5
        # We use simulation noise parameter to infer
        if aged_time=='simulated':
            camera_noise_std=3
    
        true1 = pm.AR1("y1", k=stationarity1, tau_e=precision_1, shape=len(data))
        true2 = pm.AR1("y2", k=stationarity2, tau_e=precision_2, shape=len(data))
        likelihood = pm.Normal("likelihood", mu=(true1+ true2 + observed_mean), sigma=camera_noise_std, observed=data)
        
    return ar1_two_timescales_model


def run_model(model, draws = 1000, tune = 2000, init = "advi+adapt_diag", RANDOM_SEED = 10787):
    '''
    This function conducts sampling with Pymc3.
    
    Input parameters:
    -------------------
    model: pymc3 model
    draws: 
    tune:
    init:
    
    Output parameters:
    -------------------
    trace 
    '''
    
    with model:
        trace = pm.sample(draws, tune=tune, init=init, random_seed=RANDOM_SEED, return_inferencedata=True)
        
    return trace


def plot_trace(trace, n_time_scale = 1, var_names = ['decay_time','precision']):
    '''
    This function plot the traces of sampling from the single or the multiple time scale model
    
    Input parameters:
    -------------------
    trace
    n_time_scale: int, 1 or 2, determines the parameters of which the sampling results are plotted
    var_names: list of variables to be plotted
    
    '''
    if n_time_scale == 2:
        var_names = ['decay_time_1', 'decay_time_2', 'precision_1','precision_2']
    
    az.plot_trace(
    trace,
    var_names = var_names
);
    
    
def plot_posterior(trace, n_time_scale = 1, var_names = ['decay_time','precision']):
    '''
    This function plots the posterior of sampling from the single or the multiple time scale model
    
    Input parameters:
    -------------------
    trace
    n_time_scale: int, 1 or 2, determines the parameters of which the sampling results are plotted
    var_names: list of variables to be plotted
    
    '''
    
    if n_time_scale == 2:
        var_names = ['decay_time_1', 'decay_time_2', 'precision_1','precision_2']
    
    az.plot_posterior(
    trace,
    var_names = var_names
);
  
    
def plot_pair(trace, n_time_scale = 1, var_names = ['decay_time','precision']):
    '''
    This function plots the posterior of sampling from the single or the multiple time scale model
    
    Input parameters:
    -------------------
    trace
    n_time_scale: int, 1 or 2, determines the parameters of which the sampling results are plotted
    var_names: list of variables to be plotted
    
    '''
    
    if n_time_scale == 2:
        var_names = ['decay_time_1', 'decay_time_2','precision_1','precision_2']
    
    df_trace=trace.posterior[var_names].to_dataframe()
    sns.pairplot(df_trace,markers='.')
  