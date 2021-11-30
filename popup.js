// var tabId = parseInt(window.location.search.substring(1));
// window.tabId=0;

window.addEventListener("load", function() {
  chrome.tabs.query({
    active: true, currentWindow: true}, function(tabs) {
    window.tabId = tabs[0].id;
    chrome.debugger.attach({tabId:tabs[0].id}, "1.0",
      function(err){
        if(err)
           console.log(err);
        else
           console.log("debugger attached");
      });
    chrome.debugger.sendCommand({tabId:tabs[0].id}, "Network.enable");
    chrome.debugger.sendCommand({tabId:tabs[0].id}, "Fetch.enable", { patterns: [{ urlPattern: '*' }] });
    chrome.debugger.onEvent.addListener(onEvent);
    chrome.tabs.reload(tabs[0].id);
    });
    fetch("http://127.0.0.1:5000/reload");
    var btn = document.getElementsByTagName("button");
    btn[0].addEventListener('click', reloadPage);
});

window.addEventListener("unload", function() {
  chrome.debugger.detach({tabId:tabId});
});

var stmt = {};

function reloadPage(){
  fetch("http://127.0.0.1:5000/reload");
  var url = [];

  var inputElements = document.getElementsByClassName('faulty_region');
  for(var i=0; i<inputElements.length; ++i){
        if(inputElements[i].checked){
          if(inputElements[i].value.includes('@')){
            var str = inputElements[i].value.split('@');
            if(!stmt.hasOwnProperty(str[0])){
              stmt[str[0]] = [];
            }
            stmt[str[0]].push([str[1],str[2],str[3]]);
          }
          else if (inputElements[i].value.includes('http')){
             url.push(inputElements[i].value);
          }
          else{
            const dom = "*://*."+inputElements[i].value+"/*";
            url.push(dom);
          }
        }
  } 
  if(url.length != 0){ 
    chrome.webRequest.onBeforeRequest.addListener(
      function(details) { return {cancel: true}; },
      {urls: url},
      ["blocking"]
  );}
  chrome.tabs.query({
    active: true, currentWindow: true}, function(tabs) {
    window.tabId = tabs[0].id;
    chrome.tabs.reload(tabs[0].id);});
    document.body.innerHTML = "Success";
    document.body.style.width= "60px";
    document.body.style.height= "20px";
    document.documentElement.style.width= "60px";
    document.documentElement.style.height= "20px";
}

function getHeaderString(headers) {
  let responseHeader = '';
  headers.forEach((header, key) => {
    responseHeader += key + ':' + header + '\n';
  });
  return responseHeader;
}
async function ajaxMe(url, headers, method, postData, success, error) {
  let finalResponse = {};
  let response = await fetch(url, {
    method,
    mode: 'cors',
    headers,
    redirect: 'follow',
    body: postData
  });
  finalResponse.response = await response.text();
  finalResponse.headers = getHeaderString(response.headers);
  if (response.ok) {
    success(finalResponse);
  } else {
    error(finalResponse);
  }
}
function editResponse(resp, lineNo, columnNo){
  var startLine;
  var endLine;
  var count = 0;
  console.log(resp);

  for(let i=0; i<resp.length; i++){
      if(resp[i]=='\n'){
        count++;
        if(count == lineNo){
          startLine = i;
          break;
        }
      }
  }
  startLine +=parseInt(columnNo)

  for(let i=columnNo; i<resp.length; i++){
      if(resp[i] == ';'){
        endLine = i;
        break;
      }
  }
  // console.log(resp[startLine]);
  // console.log(resp[startLine+1]);
  // console.log(resp[startLine+2]);
  // console.log(resp[startLine+3]);
  // console.log(resp[startLine+4]);
  // console.log(resp[startLine+5]);
  // console.log(resp[startLine+6]);

  return resp.substr(0, startLine-1) + resp.substr(endLine);
}
function replaceMethod(resp, methodName){
  
  // console.log(methodName);
  // console.log(resp);

  if(resp.includes("function "+ methodName)){
    // console.log("1");
    resp = resp.replaceAll("function "+ methodName, "donotExecuteMe");
  }
  else if(resp.includes(methodName + " = function")){
    // console.log("2");
    resp = resp.replaceAll(methodName + " = function", "donotExecuteMe");
  }
  else if(resp.includes(methodName + "=function")){
    // console.log("3");
    resp = resp.replaceAll(methodName + "=function", "donotExecuteMe");
  }
  // console.log(resp);
  return resp
}

function onEvent(debuggeeId, message, params) {
    if (tabId != debuggeeId.tabId){console.log("debugger not attached");return;}
      
    if (message == "Network.requestWillBeSent") {
      chrome.tabs.query({
        active: true,
        lastFocusedWindow: true}, function(tabs) {
        // and use that tab to fill in out title and url
        var tab = tabs[0];
        try{
            fetch("http://127.0.0.1:5000/request", {
              method: "POST", 
              body: JSON.stringify({"http_req": params.request.url,
              "request_id":params.requestId,
              "top_level_url": tab.url,
              "frame_url":params.documentURL,
              "resource_type":params.type,
              "header": params.request.headers,
              "timestamp": params.timestamp,
              "frameId": params.frameId,
              "call_stack":params.initiator}),
              mode: 'cors',
              headers: {
                "Access-Control-Allow-Origin":"*",
                "Content-Type": "application/json"
              }
          }).then(res => res.json())
          .then(function(json){
            // <div class="dropdown">
            //   <p class="dropbtn"><input type="checkbox">Dropdown</p>
            //   <div class="dropdown-content">
            //     <p>Link 1</p>
            //     <p>Link 1</p>
            //   </div>
            // </div>
              try{    
                var parent_div = document.getElementById("container");
                parent_div.innerHTML = "";
                for(var key in json){
                  var main_div = document.createElement("div");
                  main_div.className = "dropdown";
                  var para = document.createElement("p");
                  para.className = "dropbtn";
                  if(json[key][1] == "Domain"){
                    para.style.backgroundColor = '#F8D568';
                  }
                  else if (json[key][1] == "Hostname"){
                    para.style.backgroundColor = '#F9B75D';
                  }
                  else if (json[key][1] == "Script"){
                    para.style.backgroundColor = '#F99853';
                  }
                  else{
                    para.style.backgroundColor = '#FA7A48';
                  }
                  para.innerHTML = json[key][1] + " : " +key;
                  var inp = document.createElement("input");
                  inp.className = "faulty_region";
                  inp.type = "checkbox";
                  inp.value = key;
                  inp.checked = true;
                  para.appendChild(inp);

                  var inner_div = document.createElement("div");
                  inner_div.className="dropdown-content";
                  for (index = 0; index < json[key][0].length; index++) {
                    var inner_para = document.createElement("p");
                    inner_para.innerHTML = json[key][0][index];
                    inner_div.appendChild(inner_para);
                  }

                  main_div.appendChild(para);
                  main_div.appendChild(inner_div);
                  parent_div.appendChild(main_div);
                
                }
            }
            catch{
              console.log('reloading page');
            }

            
            });
      }
        catch{
          console.log("not sending")
        }
            
    })
  }
    var continueParams = {
      requestId: params.requestId,
    };
    
    if (message == "Fetch.requestPaused"){
        if (stmt.hasOwnProperty(params.request.url)){ 
          ajaxMe(params.request.url, params.request.headers, params.request.method, params.request.postData, (data) => {
              continueParams.responseCode = 200;
              for(let i=0; i<stmt[params.request.url].length; i++){
                console.log("requestPaused");
                // data.response = editResponse(data.response, stmt[params.request.url][i][1], stmt[params.request.url][i][2]);
                data.response = replaceMethod(data.response, stmt[params.request.url][i][0]);
              }
              continueParams.binaryResponseHeaders = btoa(unescape(encodeURIComponent(data.headers.replace(/(?:\r\n|\r|\n)/g, '\0'))));
              continueParams.body = btoa(unescape(encodeURIComponent(data.response)));
              chrome.debugger.sendCommand({tabId:debuggeeId.tabId}, 'Fetch.fulfillRequest', continueParams);
          }, (status) => {
            chrome.debugger.sendCommand({tabId:debuggeeId.tabId}, 'Fetch.continueRequest', continueParams);
          });
        }
        else {
          chrome.debugger.sendCommand({tabId:debuggeeId.tabId}, 'Fetch.continueRequest', continueParams);}
  }

}