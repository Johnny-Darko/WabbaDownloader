window.addEventListener('load', () => {
  // take the port from the storage
  chrome.storage.sync.get(['port'], (result) => {
    const port = result.port;
    // check if the login button exists
    if (!document.getElementById('login')) {
      fetch(`http://localhost:${port}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'Logged in' })
      });
    }
  });
});
