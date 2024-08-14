chrome.runtime.onInstalled.addListener(() => {
  // Set the port number from the port.txt file
  fetch(chrome.runtime.getURL('state/port.txt'))
    .then(response => response.text())
    .then(port => {
      chrome.storage.sync.set({ port: parseInt(port) });
    });
});
