async function controlService(service, action) {
    const response = await fetch(`/control/${service}/${action}`, {
        method: "POST",
    });

    const data = await response.json();

    if (response.ok) {
        alert(data.message);
        location.reload(); // Reload to update service status
    } else {
        alert(`Error: ${data.error}`);
    }
}