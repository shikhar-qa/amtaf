import pytest

from amtaf.drivers.hardware import CommandNotAllowed, check_command


@pytest.mark.parametrize(
    "cmd", ["cat /etc/device.conf", "tail -n 50 /var/log/device.log", "uname -a"]
)
def test_allowed(cmd):
    check_command(cmd)


@pytest.mark.parametrize(
    "cmd",
    [
        "reboot",
        "rm -rf /",
        "cat /etc/shadow",
        "cat /etc/device.conf; reboot",
        "tail -n 5 /var/log/device.log && reboot",
    ],
)
def test_rejected(cmd):
    with pytest.raises(CommandNotAllowed):
        check_command(cmd)
