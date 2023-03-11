var currentSuggestion = null

function getEntrySuggestions(){

    /* create XHR */
    xhr = new XMLHttpRequest();
    xhr.onload = entrySuggestionsResponse
    xhr.open("POST", "/entry-suggestions");
    
    /* server decides which fields (e.g. Project-Id) to ignore */
    formData = new FormData(document.getElementById("data-form"));
    xhr.send(formData);

}

function applySuggestion(){
    keys = Object.keys(currentSuggestion)
    for(i = 0; i < keys.length; i++){
        key = keys[i]
        field = document.getElementById(key + "-input")
        field.value = currentSuggestion[key]
    }
}

function entrySuggestionsResponse(event){
    
    /* get relevant HTML-objects */
    main = document.getElementById("suggestions")
    btn  =  document.getElementById("suggestions-btn")
    hr   =  document.getElementById("suggestions-hr")
    
    if(event.target.status == 200){
        
        /* parse response */
        obj = JSON.parse(event.target.responseText)
        currentSuggestion = obj
        values = Object.values(obj)
        htmlText = "<div class='mx-1 my-2 float-left'>Vorschlag:</div>"
        
        /* built cool HTML */
        for(i = 0; i < values.length; i++){
            val = values[i]
            htmlText += `<div class='mx-1 my-2 float-left color-${i}'>${val}</div>`
        }
        
        /* set HTML */
        main.innerHTML = htmlText
        
        /* display button */
        btn.style.display = "block"
        hr.style.display = ""
        
    }else if(event.target.status == 204){
        
        /* remove previous suggestion */
        main.innerHTML = ""
        /* remove button */
        btn.style.display = "none"
        hr.style.display = "none"

    }else{
        
        /* handle/log error */
        console.log("WTF bad response from entry suggestions")
        
    }
}