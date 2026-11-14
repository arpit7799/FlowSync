from traffic_intelligence.adaptive_control.controller import (
    AdaptiveSignalController,
    ControllerConfig,
)


def test_signal_clearance_configuration():
    controller = AdaptiveSignalController(
        ControllerConfig(
            min_green=10,
            max_green=60,
            yellow=3,
            all_red=1,
        )
    )

    assert controller.config.yellow == 3
    assert controller.config.all_red == 1


def test_green_duration_bounds():
    controller = AdaptiveSignalController()

    assert controller.config.min_green == 10
    assert controller.config.max_green == 60


def test_yellow_and_all_red_are_positive():
    controller = AdaptiveSignalController()

    assert controller.config.yellow > 0
    assert controller.config.all_red > 0
