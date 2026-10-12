"""Shared pixel-art background library (read-only for scene agents).

    from bg import common as C, kabukicho as K, yorozuya as Y, edo as E

tod (time of day) everywhere: 'day' | 'dusk' | 'night' | 'dawn' | 'storm'
(C.TODS). Interiors: C.indoor(tod) -> warm lamp-lit grade ('night_in' ...).
Every call is a pure function of its args (t = scene time), cached, < 8 ms.

bg.common    sky, clouds, big_moon, far_mountains, river, bridge (+bridge_deck_y),
             cherry_tree, lantern, stone_street, wood_floor, tatami, dirt_ground,
             room_wall, storm_flash, grade_color
bg.kabukicho street (scrolling world, FLOOR_Y=160), street_fg, yorozuya_front
             (+ yorozuya_front_fg), YOROZUYA_X / WINDOW / DOOR / BALCONY_Y ...
bg.yorozuya  office (+ office_fg, desk_fg), SOFA_*/DESK_*/DOOR_*/WINDOW_BOX
bg.edo       skyline (Terminal, castle, roofs, ships, armada), terminal, ship,
             fleet, roof_walk

Each module's docstring lists exact signatures and constants.
Demo / QA sheet: python build/bg/demo.py  -> build/bg/demo_<tod>.png
"""
