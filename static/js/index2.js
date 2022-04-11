username = "user1";

function addTextToConsole(text) {
    var pTag = document.createElement("p");
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
        data: $('form').serialize() + '&username=' + username,

        // Функции обработчики
        success: function(response) {
            var json = jQuery.parseJSON(response);
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

function updateData() { // Функция, вызываемая по кнопке
    $.ajax({
        // Настройки
        type: "POST",
        url: "/sendDataChat",
        data: $('form').serialize() + '&username=' + username,

        // Функции обработчики
        success: function(response) {
            var json = jQuery.parseJSON(response);

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
