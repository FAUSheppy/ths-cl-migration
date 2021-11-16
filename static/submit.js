function submitForm(){

    /* check input fields */
    pIdField = document.getElementById("projectId-input")

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

function dropHandler(ev) {
  console.log('File(s) dropped');

  // Prevent default behavior (Prevent file from being opened)
  ev.preventDefault();

  if (ev.dataTransfer.items) {

    for (var i = 0; i < ev.dataTransfer.items.length; i++) {
      
      /* check if is file */
      if (ev.dataTransfer.items[i].kind === 'file') {
        var file = ev.dataTransfer.items[i].getAsFile();
        console.log('... file[' + i + '].name = ' + file.name);
        file =  ev.dataTransfer.files[i]
        formData = new FormData()
        formData.append('file', file)
        projectId = document.getElementById("projectId-input").value
        if(!projectId){
            alert("Projekt ID muss gesetzt sein!")
            return;
        }
        fetch("/files?projectId=" + projectId, {
            method: 'POST',
            body: formData
        })
      }

    }
  } else {
    /* Use DataTransfer interface to access the file(s) */
    for (var i = 0; i < ev.dataTransfer.files.length; i++) {
        console.log('... file[' + i + '].name = ' + ev.dataTransfer.files[i].name);
    }
  }
}

function dragOverHandler(ev) {
  /* prevent file from being opened */
  ev.preventDefault();
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

function modalSpawn(){

    colNames = []
    fetch("/schema", r => {
        r.json().then( json => {
            colNames = json.data()
        })
    })

    row = -1
    clickedCol = -1
    entryUrl = "/entry-content"
    if(typeof this.parentNode != 'undefined'){
        row = this.parentNode.rowIndex - 1
        clickedCol = this.cellIndex
        entryUrl += "?projectId=" + dt.row(row).data()[1]
    }
    
    /* fetch modal-content from server */
    modalBody = document.getElementById("modal-body")
    fetch(entryUrl).then( r => {
        if(r.status < 200 || r.status >= 300){
            console.log("Bad answer for this entry, cannot create modal")
            alert("Serverfehler: Keine Daten verfügbar oder falsche Anfrage.")
            return Promise.reject()
        }
        r.text().then( s => {
            modalBody.innerHTML = s
        }).then(() => {
    
            /* set delete button */
            deleteButton = document.getElementById("modal-delete-button")
            deleteButton.disabled = false
            deleteButton.style.display = "block"
    
            /* fetch file list */
            fileListContainer = document.getElementById("filelist-target")
            projectId = document.getElementById("projectId-input").value
            fetch("/file-list?projectId=" + projectId).then( r => {
                r.text().then( content => {
                    fileListContainer.innerHTML = content
                })
            })
    
            /* open modal */
            $('#dataModal').modal("toggle")
       
        /* end post modal set */
        })
    /* end fetch */
    })
}

$('#tableMain').on('click', 'tbody td', modalSpawn)
