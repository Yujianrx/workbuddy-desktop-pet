from dataclasses import replace
from PySide6.QtCore import Qt
from workbuddy_pet.settings import Settings,load_settings,save_settings


def test_overlay_defaults_and_persistence(tmp_path):
    s=load_settings(tmp_path)
    assert s.pet_topmost and s.capsule_topmost and s.auto_hide_fullscreen
    s=replace(s,pet_topmost=False,capsule_topmost=False,auto_hide_fullscreen=False)
    save_settings(tmp_path,s);assert load_settings(tmp_path)==s


def test_fullscreen_geometry_excludes_maximized_and_handles_other_monitors():
    from workbuddy_pet.fullscreen import covers_monitor
    assert covers_monitor((-1920,0,0,1080),(-1920,0,0,1080))
    assert not covers_monitor((0,30,1920,1040),(0,0,1920,1080))
    assert not covers_monitor((0,0,0,0),(0,0,1920,1080))


def test_fullscreen_restores_mode_and_honors_manual_visibility(qt_app,tmp_path):
    from workbuddy_pet.app import Controller
    save_settings(tmp_path,Settings(window_mode=True,character='builtin-dragon-maid',notifications=False))
    c=Controller(qt_app,tmp_path,True,tmp_path/'absent');c.timer.stop();c.demo_timer.stop()
    try:
        before=(c.settings,c.pet.pos(),c.bubble.pos())
        c.fullscreen_probe=lambda:True;c.poll_fullscreen()
        assert c.fullscreen_hidden and not c.pet.isVisible() and not c.bubble.isVisible() and not c.player.visible
        assert c.settings==before[0]
        c.fullscreen_probe=lambda:None;c.poll_fullscreen();assert c.fullscreen_hidden
        c.fullscreen_probe=lambda:False;c.poll_fullscreen();assert c.fullscreen_hidden
        c.poll_fullscreen();assert c.pet.isVisible() and c.bubble.isVisible() and c.bubble.mode=='window'
        assert c.pet.pos()==before[1] and c.bubble.pos()==before[2]
        c.collapse_avatar();c.fullscreen_probe=lambda:True;c.poll_fullscreen()
        c.fullscreen_probe=lambda:False;c.poll_fullscreen();c.poll_fullscreen()
        assert not c.pet.isVisible() and c.bubble.isVisible()
        c.toggle_visible();c.fullscreen_probe=lambda:True;c.poll_fullscreen()
        c.fullscreen_probe=lambda:False;c.poll_fullscreen();c.poll_fullscreen()
        assert not c.pet.isVisible() and not c.bubble.isVisible()
    finally:c.shutdown()


def test_independent_topmost_and_disable_auto_hide(qt_app,tmp_path):
    from workbuddy_pet.app import Controller
    c=Controller(qt_app,tmp_path,True,tmp_path/'absent');c.timer.stop();c.demo_timer.stop()
    try:
        c.open_page('overlay:pet_topmost:0')
        assert not c.pet.windowFlags()&Qt.WindowType.WindowStaysOnTopHint
        assert c.bubble.windowFlags()&Qt.WindowType.WindowStaysOnTopHint
        c.fullscreen_probe=lambda:True;c.poll_fullscreen()
        c.open_page('overlay:capsule_topmost:0');assert not c.bubble.isVisible()
        c.open_page('overlay:auto_hide_fullscreen:0')
        assert c.pet.isVisible() and c.bubble.isVisible() and not c.fullscreen_hidden
        assert not c.bubble.windowFlags()&Qt.WindowType.WindowStaysOnTopHint
        loaded=load_settings(tmp_path);assert not loaded.pet_topmost and not loaded.capsule_topmost and not loaded.auto_hide_fullscreen
    finally:c.shutdown()


def test_short_capsule_preserves_title_tooltip_and_numeric_badge(qt_app):
    from workbuddy_pet.ui.card import CardWindow
    from workbuddy_pet.local_data import UsageSnapshot,SessionInfo
    from workbuddy_pet.state import DisplayState
    card=CardWindow();card.set_compact(True)
    title='这是一个需要完整保留在提示中的很长的任务名称'
    card.set_snapshot(UsageSnapshot(True,sessions=(SessionInfo('s',title,'example'),)))
    card.set_display(DisplayState('working','connected','s'));card.set_balance(1234567)
    assert card.capsule.width()==150 and title in card.capsule.toolTip()
    assert card.balance_badge.text()=='1,234,567'
    assert card.capsule.fontMetrics().horizontalAdvance(card.capsule.text())<=136
    assert card.width()==36+150+card.balance_badge.width()+12
    card.close()


def test_fullscreen_defers_dialog_and_cancels_drag(qt_app,tmp_path):
    from workbuddy_pet.app import Controller
    save_settings(tmp_path,Settings(character='builtin-dragon-maid',notifications=False))
    c=Controller(qt_app,tmp_path,True,tmp_path/'absent');c.timer.stop();c.demo_timer.stop();c.fullscreen_timer.stop();c.sessions={}
    try:
        c.start_drag();assert c.drag_action=='drag_lift'
        c.fullscreen_probe=lambda:True;c.poll_fullscreen()
        assert c.drag_action is None and c.pet.press_position is None
        c.show_overlay_dialog(c.updates.dialog);assert not c.updates.dialog.isVisible()
        c.open_page('usage');assert not c.bubble.isVisible()
        c.refresh();assert not c.bubble.isVisible()
        c.fullscreen_probe=lambda:False;c.poll_fullscreen()
        c.fullscreen_probe=lambda:None;c.poll_fullscreen()
        c.fullscreen_probe=lambda:False;c.poll_fullscreen();assert c.fullscreen_hidden
        c.poll_fullscreen();assert c.updates.dialog.isVisible() and c.bubble.isVisible()
    finally:c.shutdown()


def test_menu_and_settings_overlay_controls_stay_in_sync(qt_app,tmp_path):
    from workbuddy_pet.app import Controller
    c=Controller(qt_app,tmp_path,True,tmp_path/'absent');c.timer.stop();c.demo_timer.stop();c.fullscreen_timer.stop()
    try:
        c.populate_menu(c.pet.context_menu)
        c.pet.context_menu.overlay_actions['pet_topmost'].trigger()
        assert not c.settings.pet_topmost and not c.dialog.pet_topmost.isChecked()
        c.populate_menu(c.bubble.context_menu)
        assert not c.bubble.context_menu.overlay_actions['pet_topmost'].isChecked()
        c.dialog.capsule_topmost.setChecked(False);c.dialog.save()
        assert not c.settings.capsule_topmost and not c.bubble.windowFlags()&Qt.WindowType.WindowStaysOnTopHint
    finally:c.shutdown()
