costumes "costume.svg";

onflag {
    rad = 2 * (1 - sin(45));
    forever {
        clear;
        drawrectangle -100, -80, 100 + mousex(), 80 + mousey();
    }
}

def drawrectangle x, y, w, h {
    if $w < $h {
        p = $w;
        setpensize p;
        goto $x + ($w / 2), $y + $h - (p / 2);
        pendown;
        sety $y + (p / 2);
    } else {
        p = $h;
        setpensize p;
        goto $x + $h - (p / 2), $y + ($h / 2);
        pendown;
        setx $x + $w - (p / 2);
    }
    p = p / 2;
    until not p > 1 {
        p = (rad * p) / 4;
        setpensize p * 2;
        goto $x + p,      $y + p;
        goto $x + p,      $y + $h - p;
        goto $x + $w - p, $y + $h - p;
        goto $x + $w - p, $y + p;
        goto $x + p,      $y + p;
    }
    penup;
}
