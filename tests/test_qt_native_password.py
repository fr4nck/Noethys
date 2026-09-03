import base64

from noethys_qt.activities_native import _decode_network_password


def test_decode_network_password_accepts_historical_noethys_format():
    plain = "mot-de-passe-test"
    encoded = "#64#" + base64.b64encode(plain.encode("utf-8")).decode("ascii")
    assert _decode_network_password(encoded) == plain


def test_decode_network_password_keeps_plain_value():
    assert _decode_network_password("plain-test") == "plain-test"
