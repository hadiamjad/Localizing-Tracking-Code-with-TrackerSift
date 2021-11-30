// chrome.browserAction.onClicked.addListener(function(tab) {
//     console.log(tab.id)
//     chrome.debugger.attach({tabId:tab.id}, version,
//         // onAttach.bind(null, tab.id));
//         function(err){
//           if(err)
//              console.log(err);
//           else
//              console.log("debugger attached");
//         });
//   });
  
//   var version = "1.0";
  
//   function onAttach(tabId) {
//     if (chrome.runtime.lastError) {
//       alert(chrome.runtime.lastError.message);
//       return;
//     }
//     // chrome.windows.create(
//     //      {url: "popup.html?" + tabId, type: "panel", width: 800, height: 600});
//   }