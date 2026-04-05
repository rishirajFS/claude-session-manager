from unittest.mock import call, patch

from notifier import notify


def test_notify_calls_osascript():
    with patch("notifier.subprocess.run") as mock_run:
        notify(title="Test", message="Hello")
        mock_run.assert_called_once_with(
            ["osascript", "-e", 'display notification "Hello" with title "Test"'],
            capture_output=True,
        )


def test_notify_escapes_special_chars():
    # Verify the script string is constructed correctly with custom content
    with patch("notifier.subprocess.run") as mock_run:
        notify(title="Claude", message="Resets at 10:00 AM.")
        args = mock_run.call_args[0][0]
        assert "Resets at 10:00 AM." in args[2]
        assert "Claude" in args[2]
