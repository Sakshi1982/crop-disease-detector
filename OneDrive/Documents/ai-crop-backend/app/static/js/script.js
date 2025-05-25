// Preview image when selected
document.getElementById("imageInput").addEventListener("change", function () {
  const file = this.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      document.getElementById("preview").innerHTML = `<img src="${e.target.result}" alt="Preview" height="200">`;
    };
    reader.readAsDataURL(file);
  }
});

// Handle form submission and fetch prediction
document.getElementById("upload-form").addEventListener("submit", async function (e) {
  e.preventDefault();

  const form = document.getElementById("upload-form");
  const formData = new FormData(form);

  try {
    const response = await fetch("/predict", {
      method: "POST",
      body: formData
    });

    const data = await response.json();

    // Show results
    document.getElementById("result").innerHTML = `
      <h2>✅ Disease: ${data.prediction}</h2>
      <p>🧪 Confidence: ${data.confidence}%</p>
      <img src="static/uploads/${data.filename}" alt="Uploaded Image" height="200">
    `;

    // Show management tip
    document.getElementById("management").innerHTML = `
      <h3>🌿 Management Tip:</h3>
      <p>${data.management}</p>
    `;
  } catch (error) {
    console.error("Prediction failed:", error);
    document.getElementById("result").innerHTML = "<p style='color:red;'>Prediction failed. Please try again.</p>";
  }
});
