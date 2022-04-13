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
setTimeout(updateData, 500);
