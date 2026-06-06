(function() {
  const script = document.currentScript;
  const apiKey = script ? script.getAttribute("data-key") : null;
  if (!apiKey) return;

  const backendUrl = "http://localhost:8000";

  fetch(`${backendUrl}/api/v1/widget/config?api_key=${apiKey}`)
    .then(res => {
      if (!res.ok) throw new Error("Unauthorized");
      return res.json();
    })
    .then(config => {
      // Create Bubble Button
      const btn = document.createElement("button");
      btn.id = "cc-chatiq-bubble";
      btn.innerText = "💬";
      btn.style.position = "fixed";
      btn.style.bottom = "20px";
      btn.style.right = "20px";
      btn.style.width = "60px";
      btn.style.height = "60px";
      btn.style.borderRadius = "30px";
      btn.style.border = "none";
      btn.style.backgroundColor = config.primary_color;
      btn.style.color = "#fff";
      btn.style.fontSize = "24px";
      btn.style.cursor = "pointer";
      btn.style.zIndex = "999999";
      btn.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
      document.body.appendChild(btn);

      // Create Iframe Sandbox Container
      const iframe = document.createElement("iframe");
      iframe.src = `${config.widget_url}?tenant_id=${config.tenant_id}&color=${encodeURIComponent(config.primary_color)}`;
      iframe.style.position = "fixed";
      iframe.style.bottom = "90px";
      iframe.style.right = "20px";
      iframe.style.width = "380px";
      iframe.style.height = "600px";
      iframe.style.border = "none";
      iframe.style.borderRadius = "12px";
      iframe.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
      iframe.style.zIndex = "999999";
      iframe.style.display = "none";
      document.body.appendChild(iframe);

      btn.addEventListener("click", () => {
        iframe.style.display = iframe.style.display === "none" ? "block" : "none";
      });
    })
    .catch(err => console.error("Failed to load CC-ChatIQ widget:", err));
  })();
