

def compare_attributes(lvc, sxs_metadata, count_errors):
    """Compares LVC attributes to SXS metadata"""
    import numpy as np
    from .metadata import sxs_id_from_alt_names, msun_seconds

    def compare_attribute(lvc_key, sxs_value):
        lvc_value = lvc.attrs[lvc_key]
        if lvc_value == sxs_value:
            count_errors("[=] {0} ({1})".format(lvc_key, lvc_value))
        else:
            count_errors("[x] {0} (lvc: {1}, sxs: {2})".format(lvc_key, lvc_value, sxs_value))

    count_errors("# Comparing metadata")
    sxs_id = sxs_id_from_alt_names(sxs_metadata["alternative_names"])
    compare_attribute("name", sxs_id)

    mass1 =  sxs_metadata["reference_mass1"]
    mass2 =  sxs_metadata["reference_mass2"]
    compare_attribute("mass1", mass1)
    compare_attribute("mass2", mass2)

    eta = (mass1 * mass2) / (mass1 + mass2)**2
    compare_attribute("eta", eta)

    compare_attribute("spin1x", sxs_metadata["reference_dimensionless_spin1"][0])
    compare_attribute("spin1y", sxs_metadata["reference_dimensionless_spin1"][1])
    compare_attribute("spin1z", sxs_metadata["reference_dimensionless_spin1"][2])
    compare_attribute("spin2x", sxs_metadata["reference_dimensionless_spin2"][0])
    compare_attribute("spin2y", sxs_metadata["reference_dimensionless_spin2"][1])
    compare_attribute("spin2z", sxs_metadata["reference_dimensionless_spin2"][2])

    omega_orbit_vec = sxs_metadata["reference_orbital_frequency"]
    omega_orbit = np.linalg.norm(omega_orbit_vec)
    compare_attribute("Omega", omega_orbit)

    f_lower_at_1_msun = 2.0 * omega_orbit / (2.0 * np.pi * msun_seconds)
    compare_attribute("f_lower_at_1MSUN", f_lower_at_1_msun)

    eccentricity = str(sxs_metadata['reference_eccentricity'])
    if eccentricity[0] == "<" or eccentricity[0] == ">":
        eccentricity = float(eccentricity[1:])
    elif eccentricity == '[simulation too short]' or eccentricity == '[unknown]':
        eccentricity = -44444444.44444444
    else:
        eccentricity = float(eccentricity)
    compare_attribute("eccentricity", eccentricity)

    mean_anomaly = sxs_metadata['reference_mean_anomaly']
    if mean_anomaly == '[unknown]':
        mean_anomaly = -1.0
    else:
        mean_anomaly = float(mean_anomaly)
    compare_attribute("mean_anomaly", mean_anomaly)

    compare_attribute("Omega", omega_orbit)


def compare_waveform_splines(lvc, sxs_waveform, mode_string, extrap_order="Extrapolated_N2"):
    import numpy as np
    from . import LVCDataset

    start_time = lvc.attrs["NR_start_time"]
    peak_time = lvc.attrs["NR_peak_time"]

    # Get SXS values
    sxs_key = "Y" + mode_string + ".dat"
    hlm = sxs_waveform[extrap_order + ".dir"][sxs_key]
    times_raw = hlm[:, 0]
    start_h = np.abs(times_raw - start_time).argmin() + 1
    sxs_values = hlm[start_h:, 1] + 1j * hlm[start_h:, 2]
    sxs_times = hlm[start_h:, 0] - peak_time

    # Get LVC values
    lvc_amp = LVCDataset.read(lvc["amp"+mode_string]).spline(sxs_times)
    lvc_phase = LVCDataset.read(lvc["phase"+mode_string]).spline(sxs_times)
    lvc_values = lvc_amp * np.exp(1j * lvc_phase)

    # Linf norm of difference
    diff = np.max(np.abs(lvc_values - sxs_values))
    return diff


def compare_horizon_splines(lvc, sxs_horizons, key, count_errors):
    import numpy as np
    from . import LVCDataset

    start_time = lvc.attrs["NR_start_time"]
    peak_time = lvc.attrs["NR_peak_time"]

    if "remnant" in key:
        ah_key = "AhC.dir"
    elif "2" in key:
        ah_key = "AhB.dir"
    elif "1" in key:
        ah_key = "AhA.dir"
    else:
        count_errors('# Unknown key: {0}'.format(key))
        return np.inf

    if "mass" in key:
        quantity_key = "ChristodoulouMass"
        component_index = 1
    elif "spin" in key:
        quantity_key = "chiInertial"
        if 'x' in key:
            component_index = 1
        elif 'y' in key:
            component_index = 2
        elif 'z' in key:
            component_index = 3
    elif "position" in key:
        quantity_key = "CoordCenterInertial"
        if 'x' in key:
            component_index = 1
        elif 'y' in key:
            component_index = 2
        elif 'z' in key:
            component_index = 3
    quantity = sxs_horizons[ah_key][quantity_key + ".dat"]
    times_raw_ah = quantity[:, 0]
    start_ah = np.argmin(np.abs(times_raw_ah - start_time))
    sxs_values = quantity[start_ah:, component_index]
    sxs_times = quantity[start_ah:, 0] - peak_time

    # Linf norm of difference
    lvc_values = LVCDataset.read(lvc[key]).spline(sxs_times)
    diff = np.max(np.abs(lvc_values - sxs_values))
    return diff


def compare_time_series(lvc, sxs_horizons, key, extrap="Extrapolated_N2"):
    import numpy as np

    lvc_times = np.array(lvc[key])
    start_time = lvc.attrs["NR_start_time"]
    peak_time = lvc.attrs["NR_peak_time"]
    if "HorizonA" in key:
        times_raw_ah = sxs_horizons["AhA.dir"]["ArealMass.dat"][:, 0]
        start_ah = np.argmin(np.abs(times_raw_ah - start_time))
        sxs_times = times_raw_ah[start_ah:] - peak_time
    elif "HorizonB" in key:
        times_raw_ah = sxs_horizons["AhB.dir"]["ArealMass.dat"][:, 0]
        start_ah = np.argmin(np.abs(times_raw_ah - start_time))
        sxs_times = times_raw_ah[start_ah:] - peak_time
    elif "CommonHorizon" in key:
        times_raw_ah = sxs_horizons["AhC.dir"]["ArealMass.dat"][:, 0]
        start_ah = np.argmin(np.abs(times_raw_ah - start_time))
        sxs_times = times_raw_ah[start_ah:] - peak_time

    # Linf norm of difference
    diff = np.max(np.abs(lvc_times - sxs_times))
    return diff


def compare_wave_time_series(lvc, sxs_waveform, count_errors, extrap="Extrapolated_N2"):
    import numpy as np

    lvc_wave_times = np.array(lvc["NRtimes"])
    start_time = lvc.attrs["NR_start_time"]
    peak_time = lvc.attrs["NR_peak_time"]

    # Check that the time series is as expected
    sxs_key = "Y_l2_m2.dat"
    hlm = sxs_waveform[extrap + ".dir"][sxs_key]
    times_raw = hlm[:, 0]
    start_h = np.abs(times_raw - start_time).argmin()
    sxs_times = hlm[start_h:, 0] - peak_time

    diff = np.max(np.abs(sxs_times - lvc_wave_times))
    if diff != 0.0:
        count_errors("[x] NRtimes differs from SXS l=m=2 times (diff = {0})".format(diff))
    else:
        count_errors("[=] NRtimes agrees with SXS l=m=2 times (diff = {0})".format(diff))


def compare_sxs_vs_lvc(lvc_file, sxs_waveform_file, sxs_horizons_file, sxs_metadata_file, quiet=True):
    """Compare SXS- and LVC-format data files

    Parameters
    ==========
    lvc_file: str
        Path to SXS_BBH_????_Res?.h5 file
    sxs_waveform_file: str
        Path to rhOverM_Asymptotic_GeometricUnits_Com.h5
    sxs_horizons_file: str
        Path to Horizons.h5
    sxs_metadata_file: str
        Path to metadata.json

    """
    import numpy as np
    import h5py
    import json

    class ErrorCounter(object):
        def __init__(self, quiet):
            self.quiet = quiet
            self.errors = 0

        def __call__(self, string):
            if string.startswith('[x]'):
                self.errors += 1
            if not self.quiet:
                print(string)

    count_errors = ErrorCounter(quiet)

    with open(sxs_metadata_file, 'r') as m:
        sxs_metadata = json.load(m)

    with h5py.File(lvc_file, 'r') as lvc:

        compare_attributes(lvc, sxs_metadata, count_errors)

        # Divide lvc keys into groups
        lvc_keys = list(lvc)
        lvc_amp_keys = [key for key in lvc_keys if key.startswith('amp_l')]
        lvc_phase_keys = [key for key in lvc_keys if key.startswith('phase_l')]
        lvc_vs_time_keys = [key for key in lvc_keys if key.endswith('-vs-time')]
        lvc_horizon_time_keys = [key for key in lvc_keys if key in ['CommonHorizonTimes', 'HorizonATimes', 'HorizonBTimes']]

        # Check to make sure we understand exactly what keys are here
        lvc_ignored_keys = ['auxiliary-info']
        lvc_known_keys = set(lvc_amp_keys + lvc_phase_keys + ['NRtimes']
                             + lvc_vs_time_keys + lvc_horizon_time_keys + lvc_ignored_keys)
        if set(lvc_keys).symmetric_difference(lvc_known_keys):
            count_errors('[x] Unclassified keys:', set(lvc_keys).symmetric_difference(lvc_known_keys))

        # Ensure that waveform keys are properly matched
        amp_modes = [k[3:] for k in lvc_amp_keys]
        phase_modes = [k[5:] for k in lvc_phase_keys]
        if set(amp_modes).symmetric_difference(phase_modes):
            count_errors('[x] Mismatched amp and phase modes:', set(amp_modes).symmetric_difference(phase_modes))

        # Compare waveforms
        with h5py.File(sxs_waveform_file, 'r') as sxs_waveform:
            count_errors("# Comparing waveforms")
            compare_wave_time_series(lvc, sxs_waveform, count_errors)
            for mode_string in amp_modes:
                diff = compare_waveform_splines(lvc, sxs_waveform, mode_string)
                tol = lvc['phase'+mode_string]['tol'][()] + lvc['amp'+mode_string]['tol'][()]
                result = '=' if np.abs(diff) < tol else 'x'
                count_errors("[{0}] Y{1} (diff = {2}, tol = {3})".format(result, mode_string, diff, tol))

        # Compare horizon quantities
        with h5py.File(sxs_horizons_file, 'r') as sxs_horizons:
            count_errors("# Comparing horizon splines")
            for key in lvc_vs_time_keys:
                if key.startswith('LNhat') or key.startswith('nhat') or key.startswith('Omega'):
                    count_errors("[?] {0}".format(key))
                else:
                    diff = compare_horizon_splines(lvc, sxs_horizons, key, count_errors)
                    tol = lvc[key]['tol'][()]
                    result = '=' if np.abs(diff) < tol else 'x'
                    count_errors("[{0}] {1} (diff = {2}, tol = {3})".format(result, key, diff, tol))
            
            count_errors("# Comparing time series")
            eps = 1.e-15
            for key in lvc_horizon_time_keys:
                try:
                    diff = compare_time_series(lvc, sxs_horizons, key)
                    result = '=' if diff < eps else 'x'
                    count_errors("[{0}] {1} (diff = {2})".format(result, key, diff))
                except:
                    count_errors("[x] Cannot diff time series {0}".format(key))

    return count_errors.errors
