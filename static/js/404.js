function paint_4(elem) {
    var painter = elem.getContext("2d");
    painter.fillStyle = "white";
    painter.fillRect(10, 10, 10, 50);
    painter.fillRect(10, 10 + 50, 50, 10);
    painter.fillRect(10 + 50, 10, 10, 100);
}

function paint_0(elem) {
    var painter = elem.getContext("2d");
    painter.fillStyle = "white";
    painter.fillRect(10, 10, 60, 10);
    painter.fillRect(10 + 50, 10, 10, 100);
    painter.fillRect(10, 10 + 90, 60, 10);
    painter.fillRect(10, 10, 10, 100);

}

function paint_phrase(elem, phrase) {
    var painter = elem.getContext("2d");
    painter.fillStyle = "white";

    painter.font = "24px Georgia";
    painter.fillText(phrase, 10, 35);

}

function update() {
    var all_canvas = document.getElementById("all_canvas");

    var canvas_pos = {
      top: window.pageYOffset + all_canvas.getBoundingClientRect().top,
      left: window.pageXOffset + all_canvas.getBoundingClientRect().left,
      right: window.pageXOffset + all_canvas.getBoundingClientRect().right,
      bottom: window.pageYOffset + all_canvas.getBoundingClientRect().bottom
    };
    var window_pos = {
      top: window.pageYOffset,
      left: window.pageXOffset,
      right: window.pageXOffset + document.documentElement.clientWidth,
      bottom: window.pageYOffset + document.documentElement.clientHeight
    };

    positionLeft += speed_x;
    if (canvas_pos.left - 5 < window_pos.left || canvas_pos.right + 5 > window_pos.right) {
        console.log("x = -x")
        speed_x = -speed_x;
        positionLeft += 7 * speed_x;
    }

    positionTop += speed_y;
    if (canvas_pos.top - 5 < window_pos.top || canvas_pos.bottom + 5 > window_pos.bottom) {
        console.log("y = -y")

        speed_y = -speed_y;
        positionTop += 7 * speed_y;

    }

    all_canvas.style.marginLeft = positionLeft + "px";
    all_canvas.style.marginTop = positionTop + "px";

    setTimeout(update, 20);
}
var pageWidth = window.innerWidth;
var pageHeight = window.innerHeight;

var positionLeft = 0
var positionTop = 0

var speed_x = 1
var speed_y = 1

paint_4(document.querySelector("#c1"));
paint_0(document.querySelector("#c2"));
paint_4(document.querySelector("#c3"));
paint_phrase(document.querySelector("#c4"), "Page not found error")

setTimeout(update, 20);
