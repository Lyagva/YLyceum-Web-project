// preloader
function paint(elem, phrase, procent) {
    var painter = elem.getContext("2d");

    grd = painter.createLinearGradient(0,0,500,0);
    grd.addColorStop(0,"black");
    grd.addColorStop(1,"white");

    painter.fillStyle = grd;

    painter.font = "60px Cambria Math";
    painter.fillText(phrase,  75,  140);

    max = 200
    painter.fillRect(120, 160, max * 1, 20);


    grd = painter.createLinearGradient(0, 0, 350, 0);
    grd.addColorStop(0,"white");
    grd.addColorStop(1,"black");

    painter.fillStyle = grd;
    painter.fillRect(120, 160, max * procent, 20);

    painter.font = "15px Cambria Math";
    painter.fillStyle = "white";

    painter.fillStyle = "black";
    painter.fillRect(120 + 1 + max * procent, 160 + 1,max * (1 - procent) - 2 , 20 - 2);

    painter.fillStyle = "white";
    if (procent <= 0.3333333333) {
        painter.fillText("Getting player data",  120 + max / 2 - 40,  175);
    }
    else {
        if (procent <= 0.6666666) {
            painter.fillText("Loading page",  120 + max / 2 - 20,  175);
        }
        else {
            painter.fillText("Getting server data",  120 + max / 2 - 40,  175);
        }
    }
}