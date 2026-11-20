"""Tests of the match between a session and its raw SpikeGLX folder. The folder names are made up."""
import pytest

from giocomo_lab_to_nwb.mallory21.utils import find_session_folder


@pytest.fixture
def spikeglx_path(tmp_path):
    for name in (
        'npA1_0421_baseline_1_g0',
        'npA1_0421_gain_2_g0',
        'npA1_0422_baseline_1_g0',
        'npA2_0421_baseline_1_g0',
    ):
        (tmp_path / name).mkdir()
    return tmp_path


def test_two_sessions_on_one_day_get_their_own_folder(spikeglx_path):
    first = find_session_folder(spikeglx_path, 'npA1', '0421_baseline_1')
    second = find_session_folder(spikeglx_path, 'npA1', '0421_gain_2')

    assert first.name == 'npA1_0421_baseline_1_g0'
    assert second.name == 'npA1_0421_gain_2_g0'


def test_accepts_a_string_path(spikeglx_path):
    folder = find_session_folder(str(spikeglx_path), 'npA2', '0421_baseline_1')

    assert folder == spikeglx_path / 'npA2_0421_baseline_1_g0'


def test_no_match_raises(spikeglx_path):
    with pytest.raises(ValueError, match='found 0') as error:
        find_session_folder(spikeglx_path, 'npA1', '0421_dark_3')

    # the message lists the folders of the same subject and day
    assert 'npA1_0421_baseline_1_g0' in str(error.value)
    assert 'npA1_0421_gain_2_g0' in str(error.value)


def test_month_and_day_alone_do_not_match(spikeglx_path):
    with pytest.raises(ValueError, match='found 2'):
        find_session_folder(spikeglx_path, 'npA1', '0421')


def test_more_than_one_match_raises(spikeglx_path):
    (spikeglx_path / 'npA1_0421_baseline_1_g1').mkdir()

    with pytest.raises(ValueError, match='found 2'):
        find_session_folder(spikeglx_path, 'npA1', '0421_baseline_1')


def test_files_are_ignored(spikeglx_path):
    (spikeglx_path / 'npA1_0421_baseline_1_notes.txt').write_text('not a recording folder')

    folder = find_session_folder(spikeglx_path, 'npA1', '0421_baseline_1')

    assert folder.name == 'npA1_0421_baseline_1_g0'
