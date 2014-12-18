import diana.packet as p
from nose.tools import *
import time
import functools
from nose import SkipTest

def xfail(test):
    @functools.wraps(test)
    def inner(*args, **kwargs):
        try:
            test(*args, **kwargs)
        except Exception:
            raise SkipTest
        else:
            raise AssertionError('Failure expected')
    return inner

def test_undecoded_round_trip():
    packet = (b'\xef\xbe\xad\xde' # packet heading
              b'\x1c\x00\x00\x00' # total packet length
              b'\x02\x00\x00\x00' # origin
              b'\x00\x00\x00\x00' # padding
              b'\x08\x00\x00\x00' # remaining length
              b'\xdd\xcc\xbb\xaa' # packet type
              b'\xfe\x83\x4c\x00') # packet data
    decoded, rest = p.decode(packet, provenance=p.PacketProvenance.client)
    eq_(len(decoded), 1)
    eq_(rest, b'')
    encoded = p.encode(decoded[0], provenance=p.PacketProvenance.client)
    eq_(packet, encoded)

def test_welcome_encode():
    wp = p.WelcomePacket('Welcome to eyes')
    encoding = p.encode(wp)
    eq_(encoding, b'\xef\xbe\xad\xde+\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x17\x00\x00\x00\xda\xb3\x04m\x0f\x00\x00\x00Welcome to eyes')

def test_welcome_decode():
    packet = b'\xef\xbe\xad\xde+\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x17\x00\x00\x00\xda\xb3\x04m\x0f\x00\x00\x00Welcome to eyes'
    decoded, trailer = p.decode(packet)
    eq_(len(decoded), 1)
    decoded = decoded[0]
    assert isinstance(decoded, p.WelcomePacket)
    eq_(decoded.message, 'Welcome to eyes')

def test_truncated_header():
    packet = b'\xef\xbe\xad\xde\x27\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00'
    decoded, trailer = p.decode(packet)
    eq_(decoded, [])
    eq_(trailer, packet)

def test_truncated_payload():
    packet = b'\xef\xbe\xad\xde\x27\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x13\x00\x00\x00\xda\xb3\x04\x6dWelcome to '
    decoded, trailer = p.decode(packet)
    eq_(decoded, [])
    eq_(trailer, packet)

def test_overflow_payload():
    packet = b'\xef\xbe\xad\xde+\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x17\x00\x00\x00\xda\xb3\x04m\x0f\x00\x00\x00Welcome to eyes\xef'
    decoded, trailer = p.decode(packet)
    eq_(trailer, b'\xef')

def test_double_decode():
    packet = b'\xef\xbe\xad\xde+\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x17\x00\x00\x00\xda\xb3\x04m\x0f\x00\x00\x00Welcome to eyes'
    packet = packet + packet
    decoded, trailer = p.decode(packet)
    eq_(len(decoded), 2)
    eq_(trailer, b'')

def test_version_encode():
    wp = p.VersionPacket(2, 1, 1)
    encoding = p.encode(wp)
    eq_(encoding, b'\xef\xbe\xad\xde\x2c\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x4a\xe7\x48\xe5\x00\x00\x00\x00ff\x06@\x02\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00')

def test_version_decode():
    packet = b'\xef\xbe\xad\xde\x2c\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x4a\xe7\x48\xe5\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00'
    decoded, trailer = p.decode(packet)
    eq_(len(decoded), 1)
    decoded = decoded[0]
    assert isinstance(decoded, p.VersionPacket)
    eq_(decoded.major, 2)
    eq_(decoded.minor, 1)
    eq_(decoded.patch, 1)

def test_difficulty_encode():
    dp = p.DifficultyPacket(5, p.GameType.deep_strike)
    eq_(dp.encode(), b'\x05\x00\x00\x00\x03\x00\x00\x00')

def test_difficulty_decode():
    dp = p.DifficultyPacket.decode(b'\x0a\x00\x00\x00\x02\x00\x00\x00')
    eq_(dp.difficulty, 10)
    eq_(dp.game_type, p.GameType.double_front)

def test_heartbeat_encode():
    hp = p.HeartbeatPacket()
    eq_(hp.encode(), b'')

def test_gm_start_encode():
    sp = p.GameStartPacket()
    eq_(sp.encode(), b'\x00\x00\x00\x00\x0a\x00\x00\x00\x00\x00\x00\x00')

def test_gm_start_decode():
    sp = p.GameMessagePacket.decode(b'\x00\x00\x00\x00\x0a\x00\x00\x00\xf6\x03\x00\x00')
    assert isinstance(sp, p.GameStartPacket)

def test_gm_end_encode():
    ep = p.GameEndPacket()
    eq_(ep.encode(), b'\x06\x00\x00\x00')

def test_gm_end_decode():
    ep = p.GameMessagePacket.decode(b'\x06\x00\x00\x00')
    assert isinstance(ep, p.GameEndPacket)

def test_gm_dmx_encode():
    dp = p.DmxPacket(flag='bees', state=True)
    eq_(dp.encode(), b'\x10\x00\x00\x00\x05\x00\x00\x00b\x00e\x00e\x00s\x00\x00\x00\x01\x00\x00\x00')

def test_gm_dmx_decode():
    dp = p.GameMessagePacket.decode(b'\x10\x00\x00\x00\x01\x00\x00\x00y\x00\x00\x00\x00\x00\x00\x00')
    assert isinstance(dp, p.DmxPacket)
    eq_(dp.flag, 'y')
    eq_(dp.state, False)

def test_gm_jump_start_encode():
    ep = p.JumpStartPacket()
    eq_(ep.encode(), b'\x0c\x00\x00\x00')

def test_gm_jump_start_decode():
    ep = p.GameMessagePacket.decode(b'\x0c\x00\x00\x00')
    assert isinstance(ep, p.JumpStartPacket)

def test_gm_jump_end_encode():
    ep = p.JumpEndPacket()
    eq_(ep.encode(), b'\x0d\x00\x00\x00')

def test_gm_jump_end_decode():
    ep = p.GameMessagePacket.decode(b'\x0d\x00\x00\x00')
    assert isinstance(ep, p.JumpEndPacket)

def test_intel_encode():
    ip = p.IntelPacket(object=0xaabbccdd, intel='bees')
    eq_(ip.encode(), b'\xdd\xcc\xbb\xaa\x03\x05\x00\x00\x00b\x00e\x00e\x00s\x00\x00\x00')

def test_intel_decode():
    ip = p.IntelPacket.decode(b'\xdd\xcc\xbb\xaa\x03\x05\x00\x00\x00b\x00e\x00e\x00s\x00\x00\x00')
    eq_(ip.object, 0xaabbccdd)
    eq_(ip.intel, 'bees')

def test_gm_popup_encode():
    pp = p.PopupPacket(message='bees')
    eq_(pp.encode(), b'\x0a\x00\x00\x00\x05\x00\x00\x00b\x00e\x00e\x00s\x00\x00\x00')

def test_gm_popup_decode():
    pp = p.GameMessagePacket.decode(b'\x0a\x00\x00\x00\x05\x00\x00\x00b\x00e\x00e\x00s\x00\x00\x00')
    assert isinstance(pp, p.PopupPacket)
    eq_(pp.message, 'bees')

def test_gm_autonomous_damcon_encode():
    dp = p.AutonomousDamconPacket(autonomy=True)
    eq_(dp.encode(), b'\x0b\x00\x00\x00\x01\x00\x00\x00')

def test_gm_autonomous_damcon_decode():
    pp = p.GameMessagePacket.decode(b'\x0b\x00\x00\x00\x00\x00\x00\x00')
    assert isinstance(pp, p.AutonomousDamconPacket)
    eq_(pp.autonomy, False)

def test_steering_encode():
    pp = p.HelmSetSteeringPacket(0.0)
    eq_(pp.encode(), b'\x01\x00\x00\x00\x00\x00\x00\x00')

def test_steering_decode():
    pp = p.ShipAction3Packet.decode(b'\x01\x00\x00\x00\x00\x00\x00\x00')
    assert isinstance(pp, p.HelmSetSteeringPacket)
    eq_(pp.rudder, 0.0)

def test_impulse_encode():
    pp = p.HelmSetImpulsePacket(0.0)
    eq_(pp.encode(), b'\x00\x00\x00\x00\x00\x00\x00\x00')

def test_impulse_decode():
    pp = p.ShipAction3Packet.decode(b'\x00\x00\x00\x00\x00\x00\x00\x00')
    assert isinstance(pp, p.HelmSetImpulsePacket)
    eq_(pp.impulse, 0.0)

def test_warp_encode():
    pp = p.HelmSetWarpPacket(2)
    eq_(pp.encode(), b'\x00\x00\x00\x00\x02\x00\x00\x00')

def test_warp_decode():
    pp = p.ShipAction1Packet.decode(b'\x00\x00\x00\x00\x02\x00\x00\x00')
    assert isinstance(pp, p.HelmSetWarpPacket)
    eq_(pp.warp, 2)

@xfail
def test_ra_encode():
    rp = p.ToggleRedAlertPacket()
    eq_(rp.encode(), b'\x0a\x00\x00\x00\x00\x00\x00\x00')

@xfail
def test_ra_decode():
    rp = p.ShipAction1Packet.decode(b'\x0a\x00\x00\x00\x00\x00\x00\x00')
    assert isinstance(rp, p.ToggleRedAlertPacket)

@xfail
def test_shields_encode():
    rp = p.ToggleShieldsPacket()
    eq_(rp.encode(), b'\x04\x00\x00\x00\x00\x00\x00\x00')

@xfail
def test_shields_decode():
    rp = p.ShipAction1Packet.decode(b'\x04\x00\x00\x00\x00\x00\x00\x00')
    assert isinstance(rp, p.ToggleShieldsPacket)

@xfail
def test_perspective_encode():
    rp = p.TogglePerspectivePacket()
    eq_(rp.encode(), b'\x1a\x00\x00\x00\x00\x00\x00\x00')

@xfail
def test_perspective_decode():
    rp = p.ShipAction1Packet.decode(b'\x1a\x00\x00\x00\x00\x00\x00\x00')
    assert isinstance(rp, p.TogglePerspectivePacket)

@xfail
def test_auto_beams_encode():
    rp = p.ToggleAutoBeamsPacket()
    eq_(rp.encode(), b'\x03\x00\x00\x00\x00\x00\x00\x00')

@xfail
def test_auto_beams_decode():
    rp = p.ShipAction1Packet.decode(b'\x03\x00\x00\x00\x00\x00\x00\x00')
    assert isinstance(rp, p.ToggleAutoBeamsPacket)

@xfail
def test_pitch_encode():
    pp = p.ClimbDivePacket(-1)
    eq_(pp.encode(), b'\x1b\x00\x00\x00\xff\xff\xff\xff')

@xfail
def test_pitch_decode():
    pp = p.ShipAction1Packet.decode(b'\x1b\x00\x00\x00\xff\xff\xff\xff')
    assert isinstance(pp, p.ClimbDivePacket)
    eq_(pp.direction, -1)

def test_main_screen_encode():
    pp = p.SetMainScreenPacket(p.MainView.aft)
    eq_(pp.encode(), b'\x01\x00\x00\x00\x03\x00\x00\x00')

def test_main_screen_decode():
    pp = p.ShipAction1Packet.decode(b'\x01\x00\x00\x00\x02\x00\x00\x00')
    assert isinstance(pp, p.SetMainScreenPacket)
    eq_(pp.screen, p.MainView.starboard)

def test_set_ship_encode():
    pp = p.SetShipPacket(4)
    eq_(pp.encode(), b'\x0d\x00\x00\x00\x04\x00\x00\x00')

def test_set_ship_decode():
    pp = p.ShipAction1Packet.decode(b'\x0d\x00\x00\x00\x07\x00\x00\x00')
    assert isinstance(pp, p.SetShipPacket)
    eq_(pp.ship, 7)

def test_console_encode():
    pp = p.SetConsolePacket(p.Console.data, True)
    eq_(pp.encode(), b'\x0e\x00\x00\x00\x06\x00\x00\x00\x01\x00\x00\x00')

def test_console_decode():
    pp = p.ShipAction1Packet.decode(b'\x0e\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00')
    assert isinstance(pp, p.SetConsolePacket)
    eq_(pp.console, p.Console.science)
    eq_(pp.selected, False)

def test_dock_encode():
    pp = p.HelmRequestDockPacket()
    eq_(pp.encode(), b'\x07\x00\x00\x00\x00\x00\x00\x00')

def test_dock_decode():
    pp = p.ShipAction1Packet.decode(b'\x07\x00\x00\x00\x00\x00\x00\x00')
    assert isinstance(pp, p.HelmRequestDockPacket)

def test_cs_encode():
    cp = p.ConsoleStatusPacket(2, {p.Console.helm: p.ConsoleStatus.yours, p.Console.weapons: p.ConsoleStatus.unavailable})
    eq_(cp.encode(), b'\x02\x00\x00\x00\x00\x01\x02\x00\x00\x00\x00\x00\x00\x00')

def test_cs_decode():
    cp = p.ConsoleStatusPacket.decode(b'\x02\x00\x00\x00\x00\x01\x02\x00\x00\x00\x00\x00\x00\x00')
    eq_(cp.ship, 2)
    eq_(cp.consoles[p.Console.helm], p.ConsoleStatus.yours)
    eq_(cp.consoles[p.Console.weapons], p.ConsoleStatus.unavailable)
    eq_(cp.consoles[p.Console.data], p.ConsoleStatus.available)

