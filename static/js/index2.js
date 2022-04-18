var username = "Guest " + Math.floor(Math.random() * 1000000000);
var adminArray = ["N.E.O.N", "Lyagva"];
var subAdminArray = [];

function addTextToConsole(text) {
    var pTag = document.createElement("p");

    arrayText = text.split(" ");
    if (adminArray.indexOf(arrayText[0]) != -1) {
        command = arrayText[2];
        console.log(command, arrayText)
        if (command.indexOf("<") == 0) { // скрываем команду
            arrayText.splice(2, 1);

            if (command == "<warning>") {
                pTag.classList.add('admin-warning');
            }
            if (command == "<make-admin>") {
                pTag.classList.add("make-unmake-admin");
                arrayText.push("is admin");

                if (subAdminArray.indexOf(arrayText[2]) == -1) {
                    subAdminArray.push(arrayText[2]);
                }
            }
            if (command == "<unmake-admin>") {
                pTag.classList.add("make-unmake-admin");
                arrayText.push("is not admin");

                if (subAdminArray.indexOf(arrayText[2]) != -1) {
                    subAdminArray.splice(subAdminArray.indexOf(arrayText[2]), 1);
                }
            }
        }
    }
    else {
        if (subAdminArray.indexOf(arrayText[0]) != -1) {
            command = arrayText[2];
            console.log(command, arrayText)
            if (command.indexOf("<") == 0) { // скрываем команду
                arrayText.splice(2, 1);

                if (command == "<warning>") {
                    pTag.classList.add('subadmin-warning');
                }
            }
        }

    }

    text = arrayText.join(" ");

    var textNode = document.createTextNode(text);
    pTag.appendChild(textNode);

    var consoleObj = document.getElementById("console");
    consoleObj.appendChild(pTag);
}

function clearFirstChild() {
    var consoleObj = document.getElementById("console");
    consoleObj.removeChild(consoleObj.firstChild);
}

function updateConsole(outputs) {
    var consoleObj = document.getElementById("console");
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
    var textField = document.getElementById('commandInput');
    textField.value = "";
}


function sendData() { // Функция, вызываемая по кнопке
    $.ajax({
        // Настройки
        type: "POST",
        url: "/sendDataChat",
        data: $('form').serialize() + '&username=' + username + "&update=false",

        // Функции обработчики
        success: function(response) {
            var json = jQuery.parseJSON(response);
            var outputs = json.outputs;

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

function updateChatData() {
    $.ajax({
        // Настройки
        type: "POST",
        url: "/sendDataChat",
        data: $('form').serialize() + '&username=' + username + "&update=true",

        // Функции обработчики
        success: function(response) {
            var json = jQuery.parseJSON(response);
            var outputs = json.outputs;

            if (json.clearChild) {
                clearFirstChild()
            }

            updateConsole(outputs);
        },

        error: function(error) {
            console.log(error);
        },

        complete: function() {
            setTimeout(updateChatData, 500);
        }
    });
}


var timer = 0;
var max_timer = 100;


function onload() {
    if (timer > max_timer) {
    	document.getElementById("preloader").style.display = "none";
    	setTimeout(updateChatData, 500);
    }
    else {
        paint(document.getElementById("canvas"), "Lambda-14", timer / max_timer);
        timer ++;
        setTimeout(onload, 1);
    }
}

setTimeout(onload, 1);
