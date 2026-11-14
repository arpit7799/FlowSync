from traffic_intelligence.adaptive_control.sumo_adapter import (
    green_indices,
    partition_phase_indices,
)


def test_j1_phase_zero_indices():
    assert green_indices("GGggrrrrGGGg") == [
        0, 1, 2, 3, 8, 9, 10, 11
    ]


def test_j1_phase_two_indices():
    assert green_indices("rrrrGGGgGrrr") == [
        4, 5, 6, 7, 8
    ]


def test_j3_phase_zero_indices():
    assert green_indices("rrrrGGGgGGgg") == [
        4, 5, 6, 7, 8, 9, 10, 11
    ]


def test_j3_phase_two_indices():
    assert green_indices("GGGgGrrrrrrr") == [
        0, 1, 2, 3, 4
    ]


def test_no_green_indices():
    assert green_indices("rrrrrrrr") == []


def test_shared_j1_signal_is_excluded_from_both_phase_scores():
    exclusive, shared = partition_phase_indices({
        0: "GGggrrrrGGGg",
        2: "rrrrGGGgGrrr",
    })

    assert exclusive[0] == [0, 1, 2, 3, 9, 10, 11]
    assert exclusive[2] == [4, 5, 6, 7]
    assert shared == [8]


def test_shared_j3_signal_is_excluded_from_both_phase_scores():
    exclusive, shared = partition_phase_indices({
        0: "rrrrGGGgGGgg",
        2: "GGGgGrrrrrrr",
    })

    assert exclusive[0] == [5, 6, 7, 8, 9, 10, 11]
    assert exclusive[2] == [0, 1, 2, 3]
    assert shared == [4]
