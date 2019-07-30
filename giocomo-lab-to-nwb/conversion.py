import uuid
from datetime import datetime

import hdf5storage
import numpy as np
import pytz
from pynwb import NWBFile, NWBHDF5IO
from pynwb.misc import Units

def convert(input_file, subject_id, subject_date_of_birth, subject_description, subject_sex, subject_species,
             subject_weight, session_id, session_start_time, experimenter, experiment_description, institution,
             lab_name):
    """
    Read in the .mat file specified by input_file and convert to .nwb format.

    Parameters
    ----------
    input_file : ndarray (..., n_channels, n_time)
        the .mat file to be converted
    subject_id : string
        the unique subject ID number for the subject of the experiment
    subject_date_of_birth : datetime ISO 8601
        the date and time the subject was born
    subject_description : string
        important information specific to this subject that differentiates it from other members of it's species
    subject_sex : string
        Male or Female
    subject_species : string
        the name of the species of the subject
    subject_weight :
        the weight of the subject around the time of the experiment
    session_id: string
        human-readable ID# for the experiment sesssion that has a one-to-one relationship with a recording session
    session_start_time : datetime
        date and time that the experiment started
    experimenter : string
        who ran the experiment, first and last name
    experiment_description : string
        what was happening during the experiment
    institution : string
        what institution was the experiment performed in

    Returns
    -------
    nwbfile : NWBFile
        The contents of the .mat file converted into the NWB format.  The nwbfile is saved to disk using NDWHDF5
    """


    # General experiment settings
    print("input file = ", input_file)
    print("subject id = ", subject_id)
    print("subject date of birth = ", subject_date_of_birth)
    print("subject_description = ", subject_description)
    print("subject sex = ", subject_sex)
    print("subject species = ", subject_species)
    print("subject weight = ", subject_weight)
    print("session id = ", session_id)
    print("session start time = ", session_start_time)
    print("experimenter = ", experimenter)
    print("experiment_description = ", experiment_description)
    print("institution = ", institution)
    print("lab name = ", lab_name, "\n")

    # input matlab data
    #matfile = hdf5storage.loadmat('G:\\My Drive\\Giocomo\\data\\npI5_0417_baseline_1.mat')
    matfile = hdf5storage.loadmat(input_file)

    # output path for nwb data
    out_path = 'D:\\Data\\scenda\\giocomo\\npI5_0417_baseline_1.nwb'
    #out_path = 'G:\\My Drive\\Giocomo\\data\\npI5_0417_baseline_1.nwb'

    # print variables inside matlab data
    print(matfile.keys())

    # setup general experimental variables
    # timezones
    timezone_cali = pytz.timezone('US/Pacific')
    timezone_pa = pytz.timezone('US/Eastern')

    # create times with the correct time zone
    start_time = datetime(2018, 4, 3, 11)  # start of experiment
    start_time_tz = timezone_cali.localize(start_time)

    create_date = datetime.today()
    create_date_tz = timezone_pa.localize(create_date)

    uuid_identifier = uuid.uuid1()

    # Create NWB file
    nwbfile = NWBFile(session_description='demonstrate NWBFile basics',  # required
                      identifier=uuid_identifier.hex,  # required
                      session_id=session_id,
                      experiment_description=experiment_description,
                      experimenter=experimenter,
                      institution=institution,
                      lab=lab_name,
                      session_start_time=start_time_tz,  # required
                      file_create_date=create_date_tz)  # optional
    print(nwbfile)

    # add information about the subject of the experiment
    from pynwb.file import Subject

    birthday = datetime(2019, 1, 1)  # start of experiment
    birthday_tz = timezone_cali.localize(birthday)

    experiment_subject = Subject(subject_id=subject_id,
                                 species=subject_species,
                                 description=subject_description,
                                 date_of_birth=birthday_tz,
                                 weight='11',
                                 sex=subject_sex)

    nwbfile.subject = experiment_subject

    print(nwbfile.subject)

    # Adding trial information
    nwbfile.add_trial_column('trial_contrast', 'visual contrast of the maze through which the mouse is running')
    trial = np.ravel(matfile['trial'])
    trial_nums = np.unique(trial)
    position_time = np.ravel(matfile['post'])
    # matlab trial numbers start at 1. To correctly index trial_contract vector, subtracting 1 from 'num' so index starts at 0
    for num in trial_nums:
        trial_times = position_time[trial == num]
        nwbfile.add_trial(start_time=trial_times[0],
                          stop_time=trial_times[-1],
                          trial_contrast=matfile['trial_contrast'][num-1])

    print(nwbfile)

    # Add mouse position inside:
    from pynwb.behavior import Position

    position = Position()
    position_virtual = np.ravel(matfile['posx'])
    # position inside the virtual environment
    position.create_spatial_series(name='Position',
                                   data=position_virtual,
                                   timestamps = position_time,
                                   reference_frame='The start of the trial, which begins at the start of the virtual hallway.',
                                   conversion=0.01,
                                   description='Mouse location in the virtual hallway.',
                                   comments='The values should be >0 and <400cm. Values greater than 400cm mean that the mouse briefly exited the maze.',)

    # physical position on the mouse wheel
    physical_posx = position_virtual
    trial_gain = np.ravel(matfile['trial_gain'])
    for num in trial_nums:
        physical_posx[trial == num] = physical_posx[trial == num]/trial_gain[num-1]

    position.create_spatial_series(name='PhysicalPosition',
                                   data=physical_posx,
                                   timestamps=position_time,
                                   reference_frame='Location on wheel re-referenced to zero at the start of each trial.',
                                   conversion=0.01,
                                   description='Physical location on the wheel since the beginning of the trial.',
                                   comments='Physical location found by dividing the virtual position by the "trial_gain"')
    nwbfile.add_acquisition(position)
    print(nwbfile)

    print(nwbfile.acquisition['Position'].get_spatial_series('PhysicalPosition'))

    # Add timing of lick events, as well as mouse's virtual position during lick event
    from pynwb.behavior import BehavioralEvents

    lick_events = BehavioralEvents()
    lick_events.create_timeseries('LickEvents',
                                  data=np.ravel(matfile['lickx']),
                                  timestamps=np.ravel(matfile['lickt']),
                                  unit='unitless sensor values',
                                  description = 'Mouse location in virtual hallway during a lick.')
    nwbfile.add_acquisition(lick_events)
    print(nwbfile)

    # Add the recording device, a neuropixel probe
    recording_device = nwbfile.create_device(name='neuropixel_probes')
    electrode_group_description = 'single neuropixels probe http://www.open-ephys.org/neuropixelscorded'
    electrode_group_name = 'probe1'
    electrode_group_location = 'medial entorhinal cortex'

    electrode_group = nwbfile.create_electrode_group(electrode_group_name,
                                                     description=electrode_group_description,
                                                     location=electrode_group_location,
                                                     device=recording_device)

    # Add information about each electrode
    xcoords = np.ravel(matfile['sp'][0]['xcoords'][0])
    ycoords = np.ravel(matfile['sp'][0]['ycoords'][0])
    data_filtered_flag = matfile['sp'][0]['hp_filtered'][0][0]
    if data_filtered_flag:
        filter_desc = 'The raw voltage signals from the electrodes were high-pass filtered'
    else:
        filter_desc = 'The raw voltage signals from the electrodes were not high-pass filtered'

    num_recording_electrodes = xcoords.shape[0]
    recording_electrodes = range(0, num_recording_electrodes)

    # create electrode columns for the x,y location on the neuropixel  probe
    # the standard x,y,z locations are reserved for Allen Brain Atlas location
    nwbfile.add_electrode_column('relativex','electrode x-location on the probe')
    nwbfile.add_electrode_column('relativey','electrode y-location on the probe')

    for idx in recording_electrodes:
        nwbfile.add_electrode(idx,
                              x=np.nan,
                              y=np.nan,
                              z=np.nan,
                              relativex=float(xcoords[idx]),
                              relativey=float(ycoords[idx]),
                              imp=np.nan,
                              location='medial entorhinal cortex',
                              filtering=filter_desc,
                              group=electrode_group)

    print(nwbfile.electrodes[10])

    # Add information about each unit, termed 'cluster' in giocomo data
    # create new columns in unit table
    nwbfile.add_unit_column('quality', 'the labels that you gave to the clusters during manual sorting in phy (1=MUA, '
                                       '2=Good, 3=Unsorted)')
    cluster_ids = matfile['sp'][0]['cids'][0][0]
    cluster_quality = matfile['sp'][0]['cgs'][0][0]
    # spikes in time
    spike_times = np.ravel(matfile['sp'][0]['st'][0])  # the time of each spike
    spike_cluster = np.ravel(matfile['sp'][0]['clu'][0])  # the cluster_id that spiked at that time

    for i, cluster_id in enumerate(cluster_ids):
        unit_spike_times = spike_times[spike_cluster == cluster_id]
        waveforms = matfile['sp'][0]['temps'][0][cluster_id]
        nwbfile.add_unit(id=int(cluster_id),
                         spike_times=unit_spike_times,
                         quality=cluster_quality[i],
                         waveform_mean=waveforms,
                         electrode_group=electrode_group)

    print(nwbfile.units['waveform_mean'][4].shape)

    # Trying to add another Units table to hold the results of the automatic spike sorting
    spike_templates = np.ravel(matfile['sp'][0]['spikeTemplates'][0])
    spike_template_ids = np.unique(spike_templates)

    # create TemplateUnits units table
    template_units = Units(name='TemplateUnits',
                          description='units assigned during automatic spike sorting')

    for i, spike_template_id in enumerate(spike_template_ids):
        template_spike_times = spike_times[spike_templates == spike_template_id]
        template_units.add_unit(id=int(spike_template_id),
                                spike_times=template_spike_times,
                                electrode_group=electrode_group)

    # add TemplateUnits table to a processing module
    from pynwb import ProcessingModule
    spike_template_module = ProcessingModule(name='TemplateUnits',
                                             description='units assigned during automatic spike sorting')

    # add spike_template_module (processing module) to the NWB file
    spike_template_module.add(template_units)
    nwbfile.add_processing_module(spike_template_module)

    print(nwbfile)


    with NWBHDF5IO(out_path, 'w') as io:
        io.write(nwbfile)
