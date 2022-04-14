var username = "Guest " + Math.floor(Math.random() * 1000000000);

function addTextToConsole(text) {
    pTag = document.createElement("p");
    textNode = document.createTextNode(text);
    pTag.appendChild(textNode);

    consoleObj = document.getElementById("console");
    consoleObj.appendChild(pTag);
}

function clearFirstChild() {
    consoleObj = document.getElementById("console");
    consoleObj.removeChild(consoleObj.firstChild);
}

function updateConsole(outputs) {
    consoleObj = document.getElementById("console");
    if (outputs.length == 0) {
        consoleObj.innerHTML = '';
        return;
    }

    console.log(outputs.length, consoleObj.children.length);
    if (outputs.length <= consoleObj.children.length) {
        return;
    }

    index = consoleObj.children.length;
    for (_ = 0; index < outputs.length; index++) {
        console.log("Adding '" + outputs[index] + "' to console");
        addTextToConsole(outputs[index]);
    }
}


function submitForm() {
    sendData();
    textField = document.getElementById('commandInput');
    textField.value = "";
}


function sendData() { // Функция, вызываемая по кнопке
    $.ajax({
        // Настройки
        type: "POST",
        url: "/sendData",
        data: $('form').serialize() + '&username=' + username + "&update=false",

        // Функции обработчики
        success: function(response) {
            json = jQuery.parseJSON(response);
            username = json.username;
            console.log(username);

            outputs = json.outputs;

            if (json.clearChild) {
                clearFirstChild()
            }

            updateConsole(outputs);
        },

        error: function(error) {
            console.log(error);
        }
    });
}


function updateData() {
    $.ajax({
        // Настройки
        type: "POST",
        url: "/sendData",
        data: $('form').serialize() + "&username=" + username + "&update=true",


        // Функции обработчики
        success: function(response) {
            json = jQuery.parseJSON(response);
            username = json.username;

            if (json.clearChild) {
                clearFirstChild()
            }

            updateConsole(json.outputs);
        },

        error: function(error) {
            console.log(error);
        },

        complete: function() {
            setTimeout(updateData, 500);
        }
    });
}

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
    painter.fillText("Loading...",  120 + max / 2 - 20,  175);


    painter.fillStyle = "black";
    painter.fillRect(120 + 1 + max * procent, 160 + 1,max * (1 - procent) - 2 , 20 - 2);

}

var timer = 0;
function onload() {
    if (timer > 255) {
    	document.getElementById("preloader").style.display = "none";
    	setTimeout(updateData, 500);
    }
    else {
        paint(document.getElementById("canvas"), "Lambda-14", timer / 255);
        timer ++;
        setTimeout(onload, 10);
    }


}

onload();
