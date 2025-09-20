import asyncio
import random

from playwright.async_api import Page


def rd(a, b, signed=False):
    val = random.randint(a, b)
    return -val if signed and random.random() < 0.5 else val


def three_bezier(t, p0, c1, c2, p1):
    # Cubic Bezier curve
    x = (
        (1 - t) ** 3 * p0[0]
        + 3 * (1 - t) ** 2 * t * c1[0]
        + 3 * (1 - t) * t**2 * c2[0]
        + t**3 * p1[0]
    )
    y = (
        (1 - t) ** 3 * p0[1]
        + 3 * (1 - t) ** 2 * t * c1[1]
        + 3 * (1 - t) * t**2 * c2[1]
        + t**3 * p1[1]
    )
    return x, y


def mouse_movement_track(start_pos, end_pos, max_points=30, cp_delta=1):
    nums = []
    max_num = 0
    move_step = 1

    for n in range(max_points):
        nums.append(max_num)
        if n < (max_points * 1) / 10:
            move_step += rd(60, 100)
        elif n >= (max_points * 9) / 10:
            move_step -= rd(60, 100)
            move_step = max(20, move_step)
        max_num += move_step

    p1 = [start_pos[0], start_pos[1]]
    cp1 = [
        (start_pos[0] + end_pos[0]) / 2 + rd(30, 100, True) * cp_delta,
        (start_pos[1] + end_pos[1]) / 2 + rd(30, 100, True) * cp_delta,
    ]
    cp2 = [
        (start_pos[0] + end_pos[0]) / 2 + rd(30, 100, True) * cp_delta,
        (start_pos[1] + end_pos[1]) / 2 + rd(30, 100, True) * cp_delta,
    ]
    p2 = [end_pos[0], end_pos[1]]

    result = []
    for num in nums:
        t = num / max_num if max_num else 0
        x, y = three_bezier(t, p1, cp1, cp2, p2)
        result.append((x, y))
    return result


async def sim_mouse_move(
    page: Page,
    start_pos,
    end_pos,
    max_points=None,
    cp_delta=1,
    min_delay=300,
    max_delay=800,
):
    if max_points is None:
        max_points = rd(15, 30)
    points = mouse_movement_track(start_pos, end_pos, max_points, cp_delta)
    for point in points:
        steps = rd(1, 2)
        await page.mouse.move(point[0], point[1], steps=steps)
        delay = rd(min_delay, max_delay) / len(points)
        await asyncio.sleep(delay / 1000.0)


async def sim_mouse_move_to(
    page: Page,
    mouse_pos,
    end_pos,
    min_delay=200,
    max_delay=600,
    max_points=30,
    cp_delta=1,
):
    close_to_end = (
        end_pos[0] + rd(5, 30, True),
        end_pos[1] + rd(5, 20, True),
    )
    await sim_mouse_move(
        page, mouse_pos, close_to_end, max_points, cp_delta, min_delay, max_delay
    )
    await page.mouse.move(end_pos[0], end_pos[1], steps=rd(5, 13))
    return end_pos


async def sim_click(page: Page, button="left"):
    await page.mouse.down(button=button)
    await asyncio.sleep(rd(30, 80) / 1000.0)
    await page.mouse.up(button=button)
    return True


MOUSE_TRACKER_SCRIPT = """
document.addEventListener('mousemove', function(e) {
    let id = 'debug-cursor-point';
    let el = document.getElementById(id);
    if (!el) {
        el = document.createElement('div');
        el.id = id;
        el.style.position = 'fixed';
        el.style.width = '10px';
        el.style.height = '10px';
        el.style.background = 'red';
        el.style.borderRadius = '50%';
        el.style.zIndex = 99999;
        el.style.pointerEvents = 'none';
        document.body.appendChild(el);
    }
    el.style.left = (e.clientX - 5) + 'px';
    el.style.top = (e.clientY - 5) + 'px';
});
"""
