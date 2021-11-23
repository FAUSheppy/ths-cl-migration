JSON_HEADERS = { "Content-Type": "application/json" , "Accept" : "application/json" }

function submitForm(){

    /* check input fields */
    pIdField = document.getElementById("projectid-input")

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

function submitProjectPath(){
    projectId = document.getElementById("projectId").value
    path = document.getElementById("path-input").value
    data = { projectId : projectId, path : path }
    console.log("Submitting Project Path", data)
    fetch(window.location.origin + "/submit-project-path", { method: "POST", 
                                    mode: 'cors',
                                    credentials: 'same-origin',
                                    headers : JSON_HEADERS,
                                    body: JSON.stringify(data) }).then( r => {
        if(r.status == 200 || r.status == 204){
            reloadFileList()
        }else{
            r.text().then( s => {
                msg = "Cannot set path: " + s
                console.log(msg)
                errorContainer = document.getElementById("error-info")
                errorContainer.innerHTML = msg
            })
        }
    })
}

function deleteProjectPath(){
    console.log("Deleting Project Path")
    projectId = document.getElementById("projectid-input").value
    fetch("/submit-project-path", {  method : 'DELETE', 
                                     mode: 'cors',
                                     credentials: 'same-origin',
                                     headers : JSON_HEADERS,
                                     body: JSON.stringify({ projectId : projectId }) 
    }).then( r => {
        if(r.status == 200 || r.status == 204){
            reloadFileList()
        }else{
            r.text().then( s => {
                msg = "Cannot delete path: " + s
                console.log(msg)
                errorContainer = document.getElementById("error-info")
                errorContainer.innerHTML = msg
            })
        }
    })
}

function deleteEntry(){
    projectId = document.getElementById("projectid-input").value
    xhr = new XMLHttpRequest();
    xhr.open("DELETE", "/");
    xhr.onload = formSubmitFinished
    formData = new FormData();
    formData.append("id", projectId)
    xhr.send(formData);
}

function deleteFile(fullpath){
    console.log("DELETE: " + fullpath)
    fetch("/files?fullpath=" + fullpath, { method : "DELETE" }).then(r => {
        if(r.status == 204){
            reloadFileList()
        }else{
            alert("Unable to delete file, see server logs for details.")
        }
    })
}

function reloadFileList(){
    console.log("reloading file list")
    fileListContainer = document.getElementById("filelist-target")
    fileListContainerSamba = document.getElementById("smb-filelist-target")
    projectId = document.getElementById("projectid-input").value
    fetch("/file-list?projectId=" + projectId).then( r => {
        r.text().then( content => {
            fileListContainer.innerHTML = content
        })
    })

    fileListContainerSamba.innerHTML = '<div class="spinner-border" role="status"><span class="sr-only">Loading...</span></div>'
    fetch("/smb-file-list?projectId=" + projectId).then( r => {
        r.text().then( content => {
            /* make sure modal/id hasn't changed in the meantime */
            if(projectId == document.getElementById("projectid-input").value){
                fileListContainerSamba.innerHTML = content
            }
        })
    })
    
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
        projectId = document.getElementById("projectid-input").value
        if(!projectId){
            alert("Projekt ID muss gesetzt sein!")
            return;
        }
        fetch("/files?projectId=" + projectId, {
            method: 'POST',
            body: formData
        }).then( () => {
            reloadFileList()
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
    projectId = ""
    if(typeof this.parentNode != 'undefined'){
        row = this.parentNode.rowIndex - 1
        clickedCol = this.cellIndex
        projectId = dt.row(row).data()[1]
        entryUrl += "?projectId=" + projectId
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
            createDocButton = document.getElementById("modal-create-doc-button")
            if(typeof this.parentNode != 'undefined'){

                deleteButton.disabled = false
                deleteButton.style.display = "block"
                createDocButton.disabled = false
                createDocButton.style.display = "block"
    
                /* fetch file list */
                reloadFileList()

            }else{
                /* meaning this is a new entry */
                deleteButton.disabled = true
                deleteButton.style.display = "none"
                createDocButton.disabled = true
                createDocButton.style.display = "none"

                /* sugest a projectId & lfn */
                lfnInput = document.getElementById("lfn-input")
                projectIdInput = document.getElementById("projectid-input")
                laufNr = document.getElementById("laufNr-input")
                fetch("/id-suggestions").then( r => {
                    r.json().then( json => {
                        lfnNew = json["max"]
                        projectIdNew = json["projectId"]
                        console.log("LFN: " + lfnNew + " suggested PDI: " + projectIdNew)

                        /* set placeholders and values */
                        projectIdInput.placeholder = projectIdNew
                        lfnInput.placeholder = lfnNew

                        projectIdInput.value = projectIdNew
                        lfnInput.value = lfnNew

                        updateModalTitle(true)
                    })
                })
            }

            /* additional dates section */
            fetch("/additional-dates?projectId=" + projectId).then( r => {
                r.text().then( s => {
                    document.getElementById("additional-dates-target").innerHTML = s
                })
            })

            /* open modal */
            $('#dataModal').modal("toggle")
       
        /* end post modal set */
        })
    /* end fetch */
    })
}

function updateModalTitle(updateListener){

    if(updateListener){
        document.getElementById("projectid-input").removeEventListener('input', pIdInput)
        document.getElementById("projectid-input").addEventListener('input', pIdInput)

        document.getElementById("auftragsdatum-input").removeEventListener('input', pIdInput)
        document.getElementById("auftragsdatum-input").addEventListener('input', pIdInput)
    }

    titleContainer = document.getElementById("dataModalLabel")
    pIdString = "" + document.getElementById("projectid-input").value
    part1 = pIdString.substring(0,4)
    part2 = pIdString.substring(4)
    titleContainer.innerHTML = "Vorschlag Projektname: P-" + part1 + "-" + part2

}

function documentCreation(){
    projectId = document.getElementById("projectid-input").value
    url = "/new-document?projectId=" + projectId
    window.open(url, '_blank').focus();
}

function pIdInput(){
    updateModalTitle(false)
}

function saveDocumentTemplate(projectId, templateKey, samba){
    url = "/new-document?projectId=" + projectId + "&template=" + templateKey

    field = document.getElementById("save-document-error-field-" + templateKey)
    if(samba){
        url += "&saveToSamba=" + "True"
        fetch(url).then( r => {
            if(r.status == 200){
                field.style.color = "lightgreen"
                field.innerHTML   = "Erfolgreich gespeichert"
            }else{
                r.text().then( s => {
                    field.innerHTML = s
                })
            }
        })
    }else{
        field.style.color = "lightgreen"
        field.innerHTML   = "Ok!"
        window.location = url
    }

}

$('#tableMain').on('click', 'tbody td', modalSpawn)
