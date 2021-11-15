function submitForm(){

    /* check input fields */
    pIdField = document.getElementById("projectId")

    pIdField.style.borderColor = "gray"

    invalidField = false
    if(pIdField.value == ""){
        pIdField.style.borderWidth = "2px"
        pIdField.style.borderColor = "red"
        invalidField = true
    }

    if(invalidField){
        return
    }

    /* show the waiting dialog
    dialog = document.getElementById("waiting-dialog")
    dialog.style.disply = "block"
    setMainBackgroundOpacity(0.5)
    */

    /* submit the form */
    xhr = new XMLHttpRequest();
    xhr.open("POST", "/"); 
    xhr.onload = formSubmitFinished
    formData = new FormData(document.getElementById("data-form")); 
    xhr.send(formData);
}

function deleteEntry(){
    projectId = document.getElementById("projectId-input").value
    console.log(projectId)
    xhr = new XMLHttpRequest();
    xhr.open("DELETE", "/");
    xhr.onload = formSubmitFinished
    formData = new FormData();
    formData.append("id", projectId)
    xhr.send(formData);
}

function formSubmitFinished(event){ 
    if(event.target.status < 200 || event.target.status >= 300){
        showErrorMessage(event.target); // blocking
    }else{
        window.location.href = event.target.responseText + "?code=0"
    }
}

function showErrorMessage(target){
    alert(target.responseText)
}
