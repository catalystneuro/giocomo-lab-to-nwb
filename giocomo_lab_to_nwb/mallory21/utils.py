from pathlib import Path

import h5py

year = '19'


def get_data(file: h5py.File, str_: str, row=0):
    return file[file['cell_info'][str_][row][0]][:].ravel()


def get_str(file: h5py.File, str_: str, row=0) -> str:
    return ''.join([chr(x) for x in file[file['cell_info'][str_][row][0]]])


def find_session_folder(spikeglx_path, subject_id: str, session_id: str) -> Path:
    """
    Find the raw SpikeGLX folder of one session.

    The folder name must start with '{subject_id}_{session_id}', using the full session id. The first four
    characters of the session id are the month and day, so they are the same for every session that an animal ran on
    one day and cannot identify a recording on their own.

    Parameters
    ----------
    spikeglx_path : str or Path
        Folder that holds one SpikeGLX folder per session.
    subject_id : str
    session_id : str
        The full session id, as stored in the cell_info file.

    Returns
    -------
    Path
        The only folder that matches.

    Raises
    ------
    ValueError
        If no folder matches, or if more than one folder matches.
    """
    subject_session = '{}_{}'.format(subject_id, session_id)
    matches = sorted(
        path for path in Path(spikeglx_path).iterdir()
        if path.is_dir() and path.name.startswith(subject_session)
    )
    if len(matches) != 1:
        same_day = '{}_{}'.format(subject_id, session_id[:4])
        candidates = sorted(
            path.name for path in Path(spikeglx_path).iterdir()
            if path.is_dir() and path.name.startswith(same_day)
        )
        raise ValueError(
            "Expected exactly one SpikeGLX folder starting with '{}' in '{}', found {}: {}. "
            "Folders of this subject on this day: {}.".format(
                subject_session, spikeglx_path, len(matches), [path.name for path in matches], candidates
            )
        )
    return matches[0]
