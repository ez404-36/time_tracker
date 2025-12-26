- Добавить тултип о важности настройки Ubuntu + Wayland:
WAYLAND
    This will not work on Wayland unless you activate unsafe_mode:
       - Press alt + f2
       - write "lg" (without the quotation marks) and press Enter
       - In the command entry box (at the bottom of the window), write "global.context.unsafe_mode = true" (without the quotation marks) and press Enter
       - To exit the "lg" program, click on any of the options in the upper right corner, then press Escape (it seems a lg bug!)
       - You can set unsafe_mode off again by following the same steps, but in this case, using "global.context.unsafe_mode = false"
    Anyway, it will not work with all windows (especially built-in/"official" apps do not populate xid nor X-Window object)
